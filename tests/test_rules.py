"""Tests for src/rules.py: run each controlled fixture through the parser and rule checker.

Fixtures live in tests/fixtures/rules/ and map to TC-02 (R01), TC-03 (R04), and
TC-04 (R05) in docs/qa_test_plan.md, plus additional coverage for R02, R03,
R06, R07, R08, R10, and a negative/regression case.
"""

from __future__ import annotations

from pathlib import Path

import pytest

from src.parser import load_xml_root, parse_xml_tree
from src.rules import check, check_color_only_info, check_missing_captions, check_small_touch_target
from src.schema_documents import build_components_document

FIXTURES_DIR = Path(__file__).resolve().parent / "fixtures" / "rules"


def _violations_for(filename: str) -> dict:
    """Parse a fixture XML and run the rule checker on it.

    Input: filename - name of an XML file under tests/fixtures/rules/.
    Output: violations.json-shaped dict returned by src.rules.check().
    """
    xml_path = FIXTURES_DIR / filename
    components = parse_xml_tree(load_xml_root(xml_path))
    components_json = build_components_document(
        screen_id=xml_path.stem,
        image_path="",
        xml_path=str(xml_path),
        components=components,
    )
    return check(components_json)


@pytest.mark.parametrize(
    "filename,expected_rule",
    [
        ("r01_missing_label_fail.xml", "R01"),
        ("r02_image_button_fail.xml", "R02"),
        ("r03_duplicate_labels_fail.xml", "R03"),
        ("r04_small_target_fail.xml", "R04"),
        ("r05_unlabeled_input_fail.xml", "R05"),
        ("r06_disabled_control_fail.xml", "R06"),
        ("r07_zero_size_fail.xml", "R07"),
        ("r08_layout_overlap_fail.xml", "R08"),
        ("r10_text_overflow_fail.xml", "R10"),
    ],
)
def test_rule_triggers_on_fail_fixture(filename: str, expected_rule: str) -> None:
    """Each *_fail.xml fixture must produce a violation for its target rule."""
    result = _violations_for(filename)
    rule_ids = {violation["rule_id"] for violation in result["violations"]}
    assert expected_rule in rule_ids


@pytest.mark.parametrize(
    "filename,absent_rule",
    [
        ("r01_missing_label_pass.xml", "R01"),
        ("r02_image_button_pass.xml", "R02"),
        ("r04_small_target_pass.xml", "R04"),
        ("r05_unlabeled_input_pass.xml", "R05"),
        ("r05_unlabeled_input_hint_pass.xml", "R05"),
    ],
)
def test_rule_does_not_trigger_on_pass_fixture(filename: str, absent_rule: str) -> None:
    """Each *_pass.xml fixture must NOT produce a violation for the rule it targets."""
    result = _violations_for(filename)
    rule_ids = {violation["rule_id"] for violation in result["violations"]}
    assert absent_rule not in rule_ids


def test_clean_fixture_has_zero_violations() -> None:
    """The regression fixture with no injected issues must produce zero violations."""
    result = _violations_for("clean_no_violations.xml")
    assert result["violations"] == []
    assert result["total_violations"] == 0


def test_check_output_matches_violations_json_shape() -> None:
    """check() output must carry every field required by violations.json."""
    result = _violations_for("r02_image_button_fail.xml")
    for key in ("schema_version", "screen_id", "image_path", "xml_path", "total_violations", "violations"):
        assert key in result
    assert result["total_violations"] == len(result["violations"])
    for violation in result["violations"]:
        for key in ("rule_id", "issue", "component_id", "class", "bounds", "guideline", "severity", "recommendation"):
            assert key in violation


def test_duplicate_labels_reference_related_component() -> None:
    """R03 violations must link the duplicate back to the first occurrence."""
    result = _violations_for("r03_duplicate_labels_fail.xml")
    duplicate = next(v for v in result["violations"] if v["rule_id"] == "R03")
    assert "related_component" in duplicate


def test_layout_overlap_references_related_component() -> None:
    """R08 violations must link the smaller element to the one it overlaps with."""
    result = _violations_for("r08_layout_overlap_fail.xml")
    overlap = next(v for v in result["violations"] if v["rule_id"] == "R08")
    assert "related_component" in overlap


def test_layout_overlap_ignores_zero_size_elements() -> None:
    """R08 must not crash or falsely flag a pair of zero-size (0-area) elements."""
    result = _violations_for("r08_zero_size_no_crash.xml")
    rule_ids = {violation["rule_id"] for violation in result["violations"]}
    assert "R08" not in rule_ids


def test_r11_stub_returns_empty_list() -> None:
    """R11 (check_color_only_info) is a documented no-op stub; it must always return []."""
    components = [
        {
            "component_id": "c_001",
            "class": "android.widget.EditText",
            "text": "",
            "content_desc": "",
            "hint": "",
            "resource_id": "com.example.app:id/email",
            "clickable": True,
            "enabled": True,
            "focusable": True,
            "bounds": [0, 0, 400, 100],
        }
    ]
    assert check_color_only_info(components) == []


def test_r12_stub_returns_empty_list_for_non_media_components() -> None:
    """R12 (check_missing_captions) only matches VideoView/MediaPlayer classes;
    it must return [] when no such component is present."""
    components = [
        {
            "component_id": "c_001",
            "class": "android.widget.Button",
            "text": "Play",
            "content_desc": "",
            "hint": "",
            "resource_id": "com.example.app:id/play_button",
            "clickable": True,
            "enabled": True,
            "focusable": True,
            "bounds": [0, 0, 200, 100],
        }
    ]
    assert check_missing_captions(components) == []


def test_check_handles_missing_image_path_gracefully() -> None:
    """check() must not crash when image_path points to a nonexistent file;
    R09 (check_low_contrast) in particular must gracefully return [] rather
    than trying to open a screenshot that isn't there."""
    components_json = build_components_document(
        screen_id="missing_image_test",
        image_path="data/screenshots/does_not_exist.jpg",
        xml_path="tests/fixtures/rules/does_not_matter.xml",
        components=[
            {
                "component_id": "c_001",
                "class": "android.widget.Button",
                "text": "Continue",
                "content_desc": "",
                "hint": "",
                "resource_id": "com.example.app:id/continue_button",
                "clickable": True,
                "enabled": True,
                "focusable": True,
                "bounds": [0, 0, 300, 120],
            }
        ],
    )
    result = check(components_json)
    rule_ids = {violation["rule_id"] for violation in result["violations"]}
    assert "R09" not in rule_ids
    assert result["total_violations"] == 0


def test_small_touch_target_respects_dpi_parameter() -> None:
    """R04 must scale its 48dp threshold by whatever dpi is passed in, not a fixed 160."""
    component = {
        "component_id": "c_001",
        "class": "android.widget.Button",
        "text": "OK",
        "content_desc": "",
        "hint": "",
        "resource_id": "com.example.app:id/btn_ok",
        "clickable": True,
        "enabled": True,
        "focusable": True,
        "bounds": [0, 0, 100, 100],
    }
    # At the 160dpi baseline, 100px == 100dp — comfortably above the 48dp minimum.
    assert check_small_touch_target([component], dpi=160) == []
    # At 420dpi, 100px == 100 * 160/420 =~ 38dp — below the 48dp minimum.
    violations = check_small_touch_target([component], dpi=420)
    assert len(violations) == 1
    assert violations[0]["rule_id"] == "R04"


@pytest.mark.parametrize(
    "checker,component,rule_id",
    [
        (
            "check_audio_without_transcript",
            {
                "component_id": "c_001",
                "class": "android.media.SoundRecorder",
                "text": "",
                "content_desc": "",
                "hint": "",
                "resource_id": "com.example:id/recorder",
                "clickable": True,
                "enabled": True,
                "focusable": True,
                "bounds": [0, 0, 200, 100],
            },
            "R13",
        ),
        (
            "check_audio_only_notification",
            {
                "component_id": "c_001",
                "class": "android.widget.TextView",
                "text": "New notification received",
                "content_desc": "",
                "hint": "",
                "resource_id": "",
                "clickable": False,
                "enabled": True,
                "focusable": False,
                "bounds": [0, 0, 400, 80],
            },
            "R14",
        ),
        (
            "check_bad_focus_order",
            {
                "component_id": "c_002",
                "class": "android.widget.Button",
                "text": "Bottom",
                "content_desc": "",
                "hint": "",
                "resource_id": "",
                "clickable": True,
                "enabled": True,
                "focusable": True,
                "bounds": [0, 500, 200, 600],
            },
            "R15",
        ),
        (
            "check_decorative_in_focus_tree",
            {
                "component_id": "c_001",
                "class": "android.widget.ImageView",
                "text": "",
                "content_desc": "",
                "hint": "",
                "resource_id": "",
                "clickable": False,
                "enabled": True,
                "focusable": True,
                "bounds": [0, 0, 100, 100],
            },
            "R16",
        ),
        (
            "check_multi_gesture_only",
            {
                "component_id": "c_001",
                "class": "android.widget.TextView",
                "text": "Pinch to zoom the map",
                "content_desc": "",
                "hint": "",
                "resource_id": "",
                "clickable": False,
                "enabled": True,
                "focusable": False,
                "bounds": [0, 0, 300, 80],
            },
            "R18",
        ),
        (
            "check_destructive_without_confirmation",
            {
                "component_id": "c_001",
                "class": "android.widget.Button",
                "text": "Delete chat",
                "content_desc": "",
                "hint": "",
                "resource_id": "",
                "clickable": True,
                "enabled": True,
                "focusable": True,
                "bounds": [0, 0, 200, 100],
            },
            "R19",
        ),
        (
            "check_hint_only_label",
            {
                "component_id": "c_001",
                "class": "android.widget.EditText",
                "text": "",
                "content_desc": "",
                "hint": "Email address",
                "resource_id": "",
                "clickable": True,
                "enabled": True,
                "focusable": True,
                "bounds": [0, 200, 400, 280],
            },
            "R20",
        ),
    ],
)
def test_r13_to_r20_trigger_on_controlled_components(checker: str, component: dict, rule_id: str) -> None:
    from src import rules as rules_module

    checker_fn = getattr(rules_module, checker)
    if rule_id == "R15":
        components = [
            {**component, "focus_order": 1},
            {
                "component_id": "c_001",
                "class": "android.widget.Button",
                "text": "Top",
                "content_desc": "",
                "hint": "",
                "resource_id": "",
                "clickable": True,
                "enabled": True,
                "focusable": True,
                "bounds": [0, 0, 200, 100],
                "focus_order": 2,
            },
        ]
    else:
        components = [component]

    violations = checker_fn(components)
    assert any(violation["rule_id"] == rule_id for violation in violations)


def test_r17_insufficient_spacing() -> None:
    from src.rules import check_insufficient_spacing

    components = [
        {
            "component_id": "c_001",
            "class": "android.widget.Button",
            "text": "A",
            "content_desc": "",
            "hint": "",
            "resource_id": "",
            "clickable": True,
            "enabled": True,
            "focusable": True,
            "bounds": [0, 0, 200, 100],
        },
        {
            "component_id": "c_002",
            "class": "android.widget.Button",
            "text": "B",
            "content_desc": "",
            "hint": "",
            "resource_id": "",
            "clickable": True,
            "enabled": True,
            "focusable": True,
            "bounds": [205, 0, 405, 100],
        },
    ]
    violations = check_insufficient_spacing(components, dpi=160)
    assert any(violation["rule_id"] == "R17" for violation in violations)
