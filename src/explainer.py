"""Stage 3 agentic explanation layer: turns Stage 2 rule-checker violations
into plain-language, developer-facing recommendations.

Consumes a violations.json-shaped dict (see src/rules.py::check()) and a
components.json-shaped lookup, and produces a recommendations.json-shaped
dict with one entry per violation:

    {
      "rule_id": "R01",
      "component_id": "c_001",
      "guideline_ids": ["G01"],
      "explanation": "...",
      "user_impact": "...",
      "fix": "...",
    }

Anti-hallucination contract:
  - The LLM only ever sees the specific violations sent to it (rule_id,
    detection logic, matched guideline text, and that one component's own
    attributes) - never the full screen - so it has nothing to invent
    additional issues from.
  - guideline_ids in the output are computed locally from src/guidelines.py,
    never trusted from the LLM response.
  - Every recommendation returned by the LLM is matched back to an exact case
    from the input batch (by an internal case_index, cross-checked against
    that case's own rule_id/component_id) before being kept; any
    unmatched/invented item is dropped and logged as a warning rather than
    silently included. See _validate_and_match().
    NOTE: (rule_id, component_id) alone is NOT a unique key - pair-based rules
    (R03/R08/R17) can produce multiple distinct violations anchored on the
    same component (e.g. one component overlapping two different others), so
    matching must use case_index, not just rule_id/component_id.

Does not modify src/parser.py or src/rules.py.
"""

from __future__ import annotations

import json
import logging
import time

from src.guidelines import GUIDELINES, RULE_DETECTION_LOGIC, guideline_ids_for_rule
from src.llm_providers import LLMError, call_llm

logger = logging.getLogger(__name__)

# --- Tunables -----------------------------------------------------------------

BATCH_SIZE = 12  # violations per LLM call - keeps prompts small and batches cheap
MAX_RETRIES = 3  # retry attempts per batch on a transient LLM/network failure
BACKOFF_BASE_SECONDS = 2.0
MAX_TOKENS_PER_ITEM = 350  # rough output-token budget per violation in a batch
MIN_MAX_TOKENS = 1024

# Fields from components.json worth showing the LLM - kept narrow on purpose so
# it sees only what's needed to explain *this* violation, not a free-form view
# of the whole screen it could use to "find" other issues.
COMPONENT_FIELDS = (
    "class", "text", "content_desc", "hint", "resource_id",
    "bounds", "clickable", "enabled", "focusable", "password",
)

SYSTEM_PROMPT = """You are an accessibility engineer writing developer-facing \
explanations for accessibility issues that have ALREADY been detected by a \
deterministic rule checker. You are not auditing the screen yourself, and you \
must not look for, mention, or invent any accessibility issue beyond the \
exact ones given to you in the input list.

For each case in the input, write:
  - "explanation": 1-2 plain-language sentences on WHY this specific case \
fails accessibility, referencing the component's actual attributes (its \
text/content-desc/class/etc.) rather than generic advice.
  - "user_impact": 1-2 sentences on WHO is affected and HOW, based on the \
guideline's stated user group.
  - "fix": a concrete, developer-facing fix. Where the issue is code-fixable \
(e.g. a missing attribute, an undersized touch target), include a short, \
literal code snippet (e.g. android:contentDescription="..." or a \
minWidth/minHeight value) using the component's own resource_id or text \
where relevant. Do not give vague advice like "improve accessibility here".

Tone: plain-language, for a developer fixing the bug - not academic WCAG \
language, not a research report.

Each input case has a "case_index" integer. Some cases may look similar (the \
same component can appear in more than one case, e.g. it overlaps two \
different other elements) - they are still separate cases and each one needs \
its own entry in your response, matched by case_index.

Respond with ONLY a single JSON object, no markdown fences, no prose before \
or after it, matching exactly this shape:

{"recommendations": [
  {"case_index": 0, "rule_id": "...", "component_id": "...", "explanation": "...", "user_impact": "...", "fix": "..."}
]}

Rules:
  - Return exactly one entry per case in the input, in any order.
  - Every "case_index", "rule_id", and "component_id" in your response MUST \
be copied verbatim from the input case it corresponds to. Never invent a \
case_index, rule_id, component_id, or an issue not present in the input.
  - Do not add any extra keys, extra entries, or commentary outside the JSON \
object."""


def build_components_by_id(components_json: dict) -> dict[str, dict]:
    """Build a component_id -> component dict lookup from a components.json doc.

    Input: components_json - dict matching the components.json schema (see
        src/schema_documents.py), typically the parser's output for the same
        screen as the violations being explained.
    Output: dict mapping component_id to its full component dict.
    """
    return {
        component["component_id"]: component
        for component in components_json.get("components", [])
    }


def _component_snapshot(component: dict | None) -> dict:
    """Narrow a full component dict to the fields relevant to explaining a violation.

    Input: component - a components.json component dict, or None if the
        component_id wasn't found in components_by_id.
    Output: dict with only COMPONENT_FIELDS present (missing fields omitted);
        {} if component is None.
    """
    if component is None:
        return {}
    return {field: component[field] for field in COMPONENT_FIELDS if field in component}


def _build_case(
    violation: dict, index: int, components_by_id: dict[str, dict], guidelines_map: dict
) -> dict:
    """Build one self-contained case block for the LLM prompt.

    Input: violation - one entry from violations_doc["violations"]; index -
        this violation's position among the screen's violations, used as an
        internal join key (see module docstring - rule_id/component_id alone
        can repeat across distinct violations for pair-based rules);
        components_by_id - component_id -> component dict lookup;
        guidelines_map - guideline_id -> {description, user_group, wcag}.
    Output: dict with a case_index, the rule_id/issue/severity, matched
        guideline text, the rule's detection logic, and a narrowed component
        snapshot - nothing else from the source screen is included.
    """
    rule_id = violation["rule_id"]
    component_id = violation["component_id"]
    guidelines = [
        {"id": gid, **guidelines_map[gid]}
        for gid in guideline_ids_for_rule(rule_id)
        if gid in guidelines_map
    ]
    return {
        "case_index": index,
        "rule_id": rule_id,
        "component_id": component_id,
        "issue": violation.get("issue", ""),
        "severity": violation.get("severity", ""),
        "detection_logic": RULE_DETECTION_LOGIC.get(rule_id, ""),
        "guidelines": guidelines,
        "component": _component_snapshot(components_by_id.get(component_id)),
    }


def _build_user_prompt(cases: list[dict]) -> str:
    return (
        "Explain each of the following already-detected accessibility "
        "violations. Do not add any case not listed here.\n\n"
        + json.dumps({"cases": cases}, indent=2)
    )


def _extract_json_object(text: str) -> dict | None:
    """Parse an LLM response as a JSON object, tolerating markdown code fences.

    Input: text - raw LLM response text.
    Output: parsed dict, or None if no valid JSON object could be recovered.
    """
    text = text.strip()
    if text.startswith("```"):
        text = text.strip("`")
        if text.lower().startswith("json"):
            text = text[4:]
        text = text.strip()
    try:
        parsed = json.loads(text)
        return parsed if isinstance(parsed, dict) else None
    except json.JSONDecodeError:
        pass
    start, end = text.find("{"), text.rfind("}")
    if start == -1 or end == -1 or end <= start:
        return None
    try:
        parsed = json.loads(text[start : end + 1])
        return parsed if isinstance(parsed, dict) else None
    except json.JSONDecodeError:
        return None


def _validate_and_match(cases: list[dict], raw_items: list, screen_id: str) -> list[dict]:
    """Anti-hallucination guard: keep only LLM items that match an input case.

    Matches on case_index (a batch-local join key assigned when the case was
    built), not on (rule_id, component_id) alone - pair-based rules
    (R03/R08/R17) can produce multiple distinct violations anchored on the
    same component, so rule_id/component_id can legitimately repeat across
    different cases. As a second check, an item's rule_id/component_id must
    also match the case found at that case_index, or it's dropped too - a
    correct case_index paired with mismatched content is itself suspicious.

    Input: cases - the exact case blocks sent to the LLM for this batch;
        raw_items - the "recommendations" list parsed from the LLM response
        (may be malformed, missing entries, or contain invented ones);
        screen_id - for logging context.
    Output: validated recommendation dicts (rule_id, component_id,
        guideline_ids, explanation, user_impact, fix), at most one per input
        case. Invented/duplicate/malformed items are dropped and logged as
        warnings rather than silently included; a response with fewer
        recommendations than cases sent is also logged.
    """
    pending = {case["case_index"]: case for case in cases}
    validated: list[dict] = []

    for item in raw_items:
        if not isinstance(item, dict):
            logger.warning("[%s] Dropping non-object recommendation item: %r", screen_id, item)
            continue
        case_index = item.get("case_index")
        case = pending.get(case_index)
        if case is None:
            logger.warning(
                "[%s] Dropping recommendation with case_index=%r: not in the batch sent to the "
                "LLM (invented, or a duplicate response for an already-matched case).",
                screen_id, case_index,
            )
            continue
        if (item.get("rule_id"), item.get("component_id")) != (case["rule_id"], case["component_id"]):
            logger.warning(
                "[%s] Dropping recommendation for case_index=%s: rule_id/component_id (%s, %s) "
                "does not match the case sent to the LLM (%s, %s).",
                screen_id, case_index, item.get("rule_id"), item.get("component_id"),
                case["rule_id"], case["component_id"],
            )
            continue
        explanation = str(item.get("explanation", "")).strip()
        user_impact = str(item.get("user_impact", "")).strip()
        fix = str(item.get("fix", "")).strip()
        if not (explanation and user_impact and fix):
            logger.warning(
                "[%s] Dropping recommendation for case_index=%s: missing "
                "explanation/user_impact/fix.",
                screen_id, case_index,
            )
            continue
        del pending[case_index]
        validated.append(
            {
                "rule_id": case["rule_id"],
                "component_id": case["component_id"],
                "guideline_ids": [g["id"] for g in case["guidelines"]],
                "explanation": explanation,
                "user_impact": user_impact,
                "fix": fix,
            }
        )

    if pending:
        missing = ", ".join(f"{c['rule_id']}/{c['component_id']} (case {idx})" for idx, c in pending.items())
        logger.warning(
            "[%s] LLM response missing %d of %d expected recommendations: %s",
            screen_id, len(pending), len(cases), missing,
        )

    return validated


def _call_llm_batch(cases: list[dict], screen_id: str) -> list[dict]:
    """Call the LLM for one batch of cases, with retry/backoff, then validate.

    Input: cases - case blocks built by _build_case() for one batch;
        screen_id - for logging context.
    Output: validated recommendation dicts for this batch (see
        _validate_and_match()). Returns [] (logged as an error, not raised) if
        the LLM call fails after MAX_RETRIES attempts, so one bad batch/screen
        doesn't crash a larger run.
    """
    user_prompt = _build_user_prompt(cases)
    max_tokens = max(MIN_MAX_TOKENS, len(cases) * MAX_TOKENS_PER_ITEM)

    last_error: Exception | None = None
    for attempt in range(1, MAX_RETRIES + 1):
        try:
            raw_text = call_llm(SYSTEM_PROMPT, user_prompt, max_tokens=max_tokens)
            parsed = _extract_json_object(raw_text)
            if parsed is None:
                raise LLMError("Response was not valid JSON.")
            raw_items = parsed.get("recommendations")
            if not isinstance(raw_items, list):
                raise LLMError('Response JSON is missing a "recommendations" array.')
            return _validate_and_match(cases, raw_items, screen_id)
        except LLMError as exc:
            last_error = exc
            logger.warning(
                "[%s] LLM batch call failed (attempt %d/%d): %s",
                screen_id, attempt, MAX_RETRIES, exc,
            )
            if attempt < MAX_RETRIES:
                time.sleep(BACKOFF_BASE_SECONDS * (2 ** (attempt - 1)))

    logger.error(
        "[%s] Giving up on a batch of %d violation(s) after %d attempt(s): %s",
        screen_id, len(cases), MAX_RETRIES, last_error,
    )
    return []


def explain_violations(
    violations_doc: dict,
    components_by_id: dict[str, dict],
    guidelines_map: dict | None = None,
) -> dict:
    """Generate developer-facing recommendations for one screen's violations.

    Input: violations_doc - violations.json-shaped dict for one screen (see
        src/rules.py::check()); components_by_id - component_id -> component
        dict lookup for the SAME screen (see build_components_by_id()), used
        to give the LLM each violation's actual attributes; guidelines_map -
        optional guideline_id -> {description, user_group, wcag} map,
        defaults to src.guidelines.GUIDELINES.
    Output: recommendations.json-shaped dict: schema_version, screen_id,
        image_path, xml_path, total_violations, total_recommendations,
        recommendations[] (each: rule_id, component_id, guideline_ids,
        explanation, user_impact, fix). Violations whose batch failed every
        retry, or whose LLM item was dropped by the anti-hallucination guard,
        are simply absent from recommendations[] - never filled in with an
        invented recommendation - and are logged as warnings/errors.
    """
    guidelines_map = guidelines_map if guidelines_map is not None else GUIDELINES
    screen_id = violations_doc.get("screen_id", "")
    violations = violations_doc.get("violations", [])

    recommendations: list[dict] = []
    if violations:
        cases = [
            _build_case(v, i, components_by_id, guidelines_map) for i, v in enumerate(violations)
        ]
        for batch_start in range(0, len(cases), BATCH_SIZE):
            batch = cases[batch_start : batch_start + BATCH_SIZE]
            recommendations.extend(_call_llm_batch(batch, screen_id))

    return {
        "schema_version": violations_doc.get("schema_version", "1.0"),
        "screen_id": screen_id,
        "image_path": violations_doc.get("image_path", ""),
        "xml_path": violations_doc.get("xml_path", ""),
        "total_violations": len(violations),
        "total_recommendations": len(recommendations),
        "recommendations": recommendations,
    }
