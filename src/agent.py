"""Stage 3 agent layer: enrich rule violations with explanations for report.json.

Uses src/explainer.py (live LLM) when an API key is configured; otherwise falls
back to template enrichment (SRS FR-AG.6). See docs/examples/report.json.
"""

from __future__ import annotations

from copy import deepcopy

from src.explainer import build_components_by_id, explain_violations
from src.llm_providers import llm_configured
from src.schema_documents import SCHEMA_VERSION

# SDS §8.2 — TBD-02 resolved (Week 3, Noor)
SEVERITY_PENALTIES = {
    "Critical": 20,
    "High": 10,
    "Medium": 5,
    "Low": 2,
}


def compute_accessibility_score(violations: list[dict]) -> int:
    """Return a 0–100 accessibility score from violation severities.

    Input: violations - list of violation dicts with a `severity` field.
    Output: integer score clamped to [0, 100].
    """
    score = 100
    for violation in violations:
        penalty = SEVERITY_PENALTIES.get(violation.get("severity", "Medium"), 5)
        score -= penalty
    return max(0, min(100, score))


def _severity_counts(violations: list[dict]) -> dict[str, int]:
    """Count violations per severity level (critical/high/medium/low)."""
    counts = {"critical": 0, "high": 0, "medium": 0, "low": 0}
    for violation in violations:
        key = violation.get("severity", "Medium").lower()
        if key in counts:
            counts[key] += 1
    return counts


def _template_enrichment(violation: dict, component: dict | None) -> dict:
    """Build agent fields from rule output when no LLM is configured."""
    issue = violation.get("issue", "Accessibility issue")
    recommendation = violation.get("recommendation", "Review this component.")
    class_name = violation.get("class") or (component or {}).get("class", "UI element")
    return {
        "agent_explanation": (
            f"The {class_name} triggered {violation.get('rule_id', 'R??')}: {issue}."
        ),
        "agent_why_it_matters": (
            "Users who rely on screen readers, motor assistance, or high contrast "
            "may be unable to perceive or operate this control correctly."
        ),
        "agent_developer_fix": recommendation,
    }


def _recommendation_lookup(recommendations_doc: dict) -> dict[tuple[str, str], dict]:
    """Map (rule_id, component_id) -> first matching LLM recommendation."""
    lookup: dict[tuple[str, str], dict] = {}
    for rec in recommendations_doc.get("recommendations", []):
        key = (rec.get("rule_id", ""), rec.get("component_id", ""))
        lookup.setdefault(key, rec)
    return lookup


def build_audit_report(
    violations_doc: dict,
    components_doc: dict | None = None,
    *,
    use_llm: bool | None = None,
) -> dict:
    """Build report.json: score, summary, and agent fields on each violation.

    Input: violations_doc - Stage 2 output; components_doc - optional Stage 1
        output; use_llm - True forces LLM, False forces templates, None auto
        (LLM when llm_configured(), else templates per FR-AG.6).
    Output: dict matching docs/examples/report.json plus accessibility_score and
        enrichment_mode ("llm" | "template").
    """
    components_by_id = build_components_by_id(components_doc) if components_doc else {}
    violations = deepcopy(violations_doc.get("violations", []))

    if use_llm is None:
        use_llm = llm_configured()

    rec_lookup: dict[tuple[str, str], dict] = {}
    enrichment_mode = "template"
    if use_llm and violations:
        recommendations_doc = explain_violations(violations_doc, components_by_id)
        rec_lookup = _recommendation_lookup(recommendations_doc)
        if recommendations_doc.get("total_recommendations", 0) > 0:
            enrichment_mode = "llm"

    enriched_violations: list[dict] = []
    for violation in violations:
        component = components_by_id.get(violation.get("component_id"))
        key = (violation.get("rule_id", ""), violation.get("component_id", ""))
        rec = rec_lookup.get(key)
        if rec:
            agent_fields = {
                "agent_explanation": rec["explanation"],
                "agent_why_it_matters": rec["user_impact"],
                "agent_developer_fix": rec["fix"],
            }
        else:
            agent_fields = _template_enrichment(violation, component)
        enriched_violations.append({**violation, **agent_fields})

    summary_counts = _severity_counts(enriched_violations)
    return {
        "schema_version": violations_doc.get("schema_version", SCHEMA_VERSION),
        "screen_id": violations_doc.get("screen_id", ""),
        "image_path": violations_doc.get("image_path", ""),
        "xml_path": violations_doc.get("xml_path", ""),
        "accessibility_score": compute_accessibility_score(enriched_violations),
        "enrichment_mode": enrichment_mode,
        "summary": {
            "total_issues": len(enriched_violations),
            **summary_counts,
        },
        "violations": enriched_violations,
    }

class AgenticEnricher:
    """Enrich violations.json into report.json (SRS FR-AG.1–FR-AG.8)."""

    def __init__(self, *, use_llm: bool | None = None) -> None:
        """use_llm=None auto-detects from LLM_PROVIDER env config; True/False forces it."""
        self.use_llm = use_llm

    def enrich(self, violations_doc: dict, components_doc: dict | None = None) -> dict:
        """Add summary + agent fields to each violation."""
        return build_audit_report(
            violations_doc,
            components_doc,
            use_llm=self.use_llm,
        )
