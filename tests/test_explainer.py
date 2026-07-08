"""Tests for src/explainer.py, focused on the anti-hallucination guard: the
LLM must never be trusted to add issues beyond what was sent to it.

The LLM call itself is mocked throughout (via monkeypatching
src.explainer.call_llm) - these tests exercise the batching, JSON parsing,
and validation/matching logic without hitting a real provider.
"""

from __future__ import annotations

import json

import pytest

from src import explainer
from src.explainer import (
    _extract_json_object,
    _validate_and_match,
    build_components_by_id,
    explain_violations,
)
from src.guidelines import guideline_ids_for_rule
from src.llm_providers import LLMError


def _violations_doc(violations: list[dict]) -> dict:
    return {
        "schema_version": "1.0",
        "screen_id": "screen_001",
        "image_path": "data/screenshots/screen_001.png",
        "xml_path": "data/xml/window_001.xml",
        "total_violations": len(violations),
        "violations": violations,
    }


def _components_json(components: list[dict]) -> dict:
    return {
        "schema_version": "1.0",
        "screen_id": "screen_001",
        "image_path": "data/screenshots/screen_001.png",
        "xml_path": "data/xml/window_001.xml",
        "components": components,
    }


VIOLATION_R02 = {
    "rule_id": "R02",
    "issue": "Image button without description",
    "component_id": "c_001",
    "class": "android.widget.ImageButton",
    "bounds": [32, 50, 80, 98],
    "guideline": "G02 — Image button without description",
    "severity": "High",
    "recommendation": "Add android:contentDescription with the action name, such as Back.",
}

VIOLATION_R05 = {
    "rule_id": "R05",
    "issue": "Unlabeled input field",
    "component_id": "c_002",
    "class": "android.widget.EditText",
    "bounds": [32, 120, 400, 168],
    "guideline": "G05 — Unlabeled input field",
    "severity": "High",
    "recommendation": "Add android:hint or a programmatic label linked via labelFor.",
}

COMPONENT_C001 = {
    "component_id": "c_001",
    "class": "android.widget.ImageButton",
    "text": "",
    "content_desc": "",
    "resource_id": "com.app:id/back",
    "clickable": True,
    "enabled": True,
    "focusable": True,
    "bounds": [32, 50, 80, 98],
}

COMPONENT_C002 = {
    "component_id": "c_002",
    "class": "android.widget.EditText",
    "text": "",
    "content_desc": "",
    "resource_id": "com.app:id/username",
    "clickable": True,
    "enabled": True,
    "focusable": True,
    "bounds": [32, 120, 400, 168],
}


# --- build_components_by_id ----------------------------------------------------


def test_build_components_by_id():
    lookup = build_components_by_id(_components_json([COMPONENT_C001, COMPONENT_C002]))
    assert lookup == {"c_001": COMPONENT_C001, "c_002": COMPONENT_C002}


# --- _extract_json_object --------------------------------------------------------


def test_extract_json_object_plain():
    assert _extract_json_object('{"recommendations": []}') == {"recommendations": []}


def test_extract_json_object_strips_markdown_fence():
    text = '```json\n{"recommendations": []}\n```'
    assert _extract_json_object(text) == {"recommendations": []}


def test_extract_json_object_strips_surrounding_prose():
    text = 'Here is the JSON:\n{"recommendations": []}\nHope that helps!'
    assert _extract_json_object(text) == {"recommendations": []}


def test_extract_json_object_returns_none_for_garbage():
    assert _extract_json_object("not json at all") is None


def test_extract_json_object_returns_none_for_json_array():
    # top-level must be an object, not a bare array
    assert _extract_json_object('[{"rule_id": "R01"}]') is None


# --- _validate_and_match: the anti-hallucination guard --------------------------


def _case(rule_id: str, component_id: str, index: int = 0) -> dict:
    return {
        "case_index": index,
        "rule_id": rule_id,
        "component_id": component_id,
        "issue": "",
        "severity": "",
        "detection_logic": "",
        "guidelines": [{"id": gid} for gid in guideline_ids_for_rule(rule_id)],
        "component": {},
    }


def test_validate_and_match_accepts_matching_item():
    cases = [_case("R02", "c_001")]
    raw_items = [
        {
            "case_index": 0,
            "rule_id": "R02",
            "component_id": "c_001",
            "explanation": "explains it",
            "user_impact": "affects blind users",
            "fix": "add contentDescription",
        }
    ]
    result = _validate_and_match(cases, raw_items, "screen_001")
    assert len(result) == 1
    assert result[0]["rule_id"] == "R02"
    assert result[0]["component_id"] == "c_001"
    assert result[0]["guideline_ids"] == guideline_ids_for_rule("R02")


def test_validate_and_match_accepts_repeated_rule_and_component_as_distinct_cases():
    """Pair-based rules (R03/R08/R17) can produce multiple distinct violations
    anchored on the SAME component (e.g. it overlaps two different other
    elements) - each must still get its own recommendation, matched by
    case_index rather than collapsed by (rule_id, component_id)."""
    cases = [_case("R08", "c_044", index=0), _case("R08", "c_044", index=1)]
    raw_items = [
        {
            "case_index": 0,
            "rule_id": "R08",
            "component_id": "c_044",
            "explanation": "overlaps element A",
            "user_impact": "u",
            "fix": "f",
        },
        {
            "case_index": 1,
            "rule_id": "R08",
            "component_id": "c_044",
            "explanation": "overlaps element B",
            "user_impact": "u",
            "fix": "f",
        },
    ]
    result = _validate_and_match(cases, raw_items, "screen_001")
    assert len(result) == 2
    explanations = {r["explanation"] for r in result}
    assert explanations == {"overlaps element A", "overlaps element B"}


def test_validate_and_match_drops_invented_extra_issue():
    """The LLM must not be able to add a violation that wasn't in the batch."""
    cases = [_case("R02", "c_001")]
    raw_items = [
        {
            "case_index": 0,
            "rule_id": "R02",
            "component_id": "c_001",
            "explanation": "explains it",
            "user_impact": "affects blind users",
            "fix": "add contentDescription",
        },
        {
            # Invented: not in the input batch at all.
            "case_index": 1,
            "rule_id": "R09",
            "component_id": "c_999",
            "explanation": "invented low contrast issue",
            "user_impact": "invented",
            "fix": "invented",
        },
    ]
    result = _validate_and_match(cases, raw_items, "screen_001")
    assert len(result) == 1
    assert result[0]["component_id"] == "c_001"
    assert all(r["component_id"] != "c_999" for r in result)


def test_validate_and_match_drops_wrong_rule_id_for_known_case_index():
    """A case_index that matches, but whose echoed rule_id/component_id
    disagrees with that case, is dropped too - content must match the index."""
    cases = [_case("R02", "c_001")]
    raw_items = [
        {
            "case_index": 0,
            "rule_id": "R30",  # wrong rule_id for this case_index
            "component_id": "c_001",
            "explanation": "x",
            "user_impact": "x",
            "fix": "x",
        }
    ]
    result = _validate_and_match(cases, raw_items, "screen_001")
    assert result == []


def test_validate_and_match_drops_unknown_case_index():
    cases = [_case("R02", "c_001")]
    raw_items = [
        {"case_index": 7, "rule_id": "R02", "component_id": "c_001", "explanation": "x", "user_impact": "x", "fix": "x"}
    ]
    result = _validate_and_match(cases, raw_items, "screen_001")
    assert result == []


def test_validate_and_match_drops_duplicate():
    cases = [_case("R02", "c_001")]
    raw_items = [
        {"case_index": 0, "rule_id": "R02", "component_id": "c_001", "explanation": "a", "user_impact": "a", "fix": "a"},
        {"case_index": 0, "rule_id": "R02", "component_id": "c_001", "explanation": "b", "user_impact": "b", "fix": "b"},
    ]
    result = _validate_and_match(cases, raw_items, "screen_001")
    assert len(result) == 1  # only the first match is kept; the duplicate is dropped


def test_validate_and_match_drops_missing_fields():
    cases = [_case("R02", "c_001")]
    raw_items = [
        {"case_index": 0, "rule_id": "R02", "component_id": "c_001", "explanation": "", "user_impact": "x", "fix": "x"}
    ]
    result = _validate_and_match(cases, raw_items, "screen_001")
    assert result == []


def test_validate_and_match_drops_non_object_items():
    cases = [_case("R02", "c_001")]
    result = _validate_and_match(cases, ["not a dict", 42, None], "screen_001")
    assert result == []


def test_validate_and_match_reports_missing_recommendation(caplog):
    """If the LLM returns fewer recommendations than violations sent, that's
    logged (count mismatch), not silently ignored."""
    cases = [_case("R02", "c_001", index=0), _case("R05", "c_002", index=1)]
    raw_items = [
        {"case_index": 0, "rule_id": "R02", "component_id": "c_001", "explanation": "a", "user_impact": "a", "fix": "a"},
    ]
    with caplog.at_level("WARNING"):
        result = _validate_and_match(cases, raw_items, "screen_001")
    assert len(result) == 1
    assert any("missing" in message.lower() for message in caplog.messages)


# --- explain_violations: end-to-end with a mocked LLM ---------------------------


def test_explain_violations_end_to_end(monkeypatch):
    components_by_id = build_components_by_id(_components_json([COMPONENT_C001, COMPONENT_C002]))
    violations_doc = _violations_doc([VIOLATION_R02, VIOLATION_R05])

    def fake_call_llm(system, user, *, max_tokens=4096):
        cases = json.loads(user.split("\n\n", 1)[1])["cases"]
        return json.dumps(
            {
                "recommendations": [
                    {
                        "case_index": case["case_index"],
                        "rule_id": case["rule_id"],
                        "component_id": case["component_id"],
                        "explanation": f"explanation for {case['rule_id']}",
                        "user_impact": f"impact for {case['rule_id']}",
                        "fix": f"fix for {case['rule_id']}",
                    }
                    for case in cases
                ]
            }
        )

    monkeypatch.setattr(explainer, "call_llm", fake_call_llm)

    result = explain_violations(violations_doc, components_by_id)

    assert result["screen_id"] == "screen_001"
    assert result["total_violations"] == 2
    assert result["total_recommendations"] == 2
    by_rule = {r["rule_id"]: r for r in result["recommendations"]}
    assert by_rule["R02"]["component_id"] == "c_001"
    assert by_rule["R02"]["guideline_ids"] == guideline_ids_for_rule("R02")
    assert by_rule["R05"]["guideline_ids"] == guideline_ids_for_rule("R05")


def test_explain_violations_drops_llm_invented_issue(monkeypatch):
    """Even if the LLM adds an issue beyond the input violations, it must not
    appear in the final output."""
    components_by_id = build_components_by_id(_components_json([COMPONENT_C001]))
    violations_doc = _violations_doc([VIOLATION_R02])

    def fake_call_llm(system, user, *, max_tokens=4096):
        return json.dumps(
            {
                "recommendations": [
                    {
                        "case_index": 0,
                        "rule_id": "R02",
                        "component_id": "c_001",
                        "explanation": "e",
                        "user_impact": "u",
                        "fix": "f",
                    },
                    {
                        "case_index": 1,  # invented - not in violations_doc at all
                        "rule_id": "R09",
                        "component_id": "c_001",
                        "explanation": "invented low-contrast finding",
                        "user_impact": "invented",
                        "fix": "invented",
                    },
                ]
            }
        )

    monkeypatch.setattr(explainer, "call_llm", fake_call_llm)

    result = explain_violations(violations_doc, components_by_id)

    assert result["total_recommendations"] == 1
    assert [r["rule_id"] for r in result["recommendations"]] == ["R02"]


def test_explain_violations_no_violations_skips_llm_call(monkeypatch):
    def fail_if_called(*args, **kwargs):
        raise AssertionError("call_llm should not be invoked when there are no violations")

    monkeypatch.setattr(explainer, "call_llm", fail_if_called)

    result = explain_violations(_violations_doc([]), {})
    assert result["total_violations"] == 0
    assert result["total_recommendations"] == 0
    assert result["recommendations"] == []


def test_explain_violations_batch_failure_is_skipped_not_raised(monkeypatch):
    """A batch that fails every retry is logged and skipped, not raised - one
    bad batch must not crash the whole run."""
    components_by_id = build_components_by_id(_components_json([COMPONENT_C001]))
    violations_doc = _violations_doc([VIOLATION_R02])

    def always_fails(system, user, *, max_tokens=4096):
        raise LLMError("simulated provider outage")

    monkeypatch.setattr(explainer, "call_llm", always_fails)
    monkeypatch.setattr(explainer.time, "sleep", lambda seconds: None)

    result = explain_violations(violations_doc, components_by_id)

    assert result["total_violations"] == 1
    assert result["total_recommendations"] == 0
    assert result["recommendations"] == []


def test_explain_violations_handles_repeated_rule_and_component_pairs(monkeypatch):
    """Regression test: R08 (layout overlap) can flag the same anchor component
    against two different overlapping elements, producing two violations that
    share (rule_id, component_id). Both must be explained - not collapsed into
    one recommendation, and not duplicated across batches."""
    violation_a = {
        "rule_id": "R08",
        "issue": "Possible layout overlap",
        "component_id": "c_044",
        "class": "android.widget.Button",
        "bounds": [0, 0, 50, 50],
        "guideline": "G08 — Possible layout overlap",
        "severity": "Medium",
        "recommendation": "Reposition or resize overlapping controls.",
        "related_component": "c_010",
    }
    violation_b = {**violation_a, "related_component": "c_020"}
    components_by_id = build_components_by_id(_components_json([COMPONENT_C001]))
    violations_doc = _violations_doc([violation_a, violation_b])

    def fake_call_llm(system, user, *, max_tokens=4096):
        cases = json.loads(user.split("\n\n", 1)[1])["cases"]
        return json.dumps(
            {
                "recommendations": [
                    {
                        "case_index": case["case_index"],
                        "rule_id": case["rule_id"],
                        "component_id": case["component_id"],
                        "explanation": f"overlap case {case['case_index']}",
                        "user_impact": "u",
                        "fix": "f",
                    }
                    for case in cases
                ]
            }
        )

    monkeypatch.setattr(explainer, "call_llm", fake_call_llm)

    result = explain_violations(violations_doc, components_by_id)

    assert result["total_violations"] == 2
    assert result["total_recommendations"] == 2
    explanations = sorted(r["explanation"] for r in result["recommendations"])
    assert explanations == ["overlap case 0", "overlap case 1"]


def test_explain_violations_batches_large_violation_lists(monkeypatch):
    """More violations than BATCH_SIZE must be split into multiple LLM calls."""
    n = explainer.BATCH_SIZE + 3
    violations = [
        {**VIOLATION_R02, "component_id": f"c_{i:03d}"} for i in range(n)
    ]
    components = [{**COMPONENT_C001, "component_id": f"c_{i:03d}"} for i in range(n)]
    components_by_id = build_components_by_id(_components_json(components))
    violations_doc = _violations_doc(violations)

    call_count = {"n": 0}

    def fake_call_llm(system, user, *, max_tokens=4096):
        call_count["n"] += 1
        cases = json.loads(user.split("\n\n", 1)[1])["cases"]
        assert len(cases) <= explainer.BATCH_SIZE
        return json.dumps(
            {
                "recommendations": [
                    {
                        "case_index": case["case_index"],
                        "rule_id": case["rule_id"],
                        "component_id": case["component_id"],
                        "explanation": "e",
                        "user_impact": "u",
                        "fix": "f",
                    }
                    for case in cases
                ]
            }
        )

    monkeypatch.setattr(explainer, "call_llm", fake_call_llm)

    result = explain_violations(violations_doc, components_by_id)

    assert call_count["n"] == 2  # BATCH_SIZE+3 violations -> 2 batches
    assert result["total_recommendations"] == n
