"""Stage 3 agent layer: enrich rule violations with explanations for report.json.

MVP uses template-based enrichment (no live LLM call). Wire OpenAI/Gemini in Week 4.
See SDS §7 and docs/examples/report.json for the target output shape.
"""

from __future__ import annotations

from copy import deepcopy

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


class AgenticEnricher:
    """Enrich violations.json into report.json (SRS FR-AG.1–FR-AG.8 scaffold)."""

    def __init__(self, *, use_llm: bool = False) -> None:
        self.use_llm = use_llm

    def enrich(self, violations_doc: dict, components_doc: dict | None = None) -> dict:
        """Add summary + agent fields to each violation.

        Input: violations_doc - Stage 2 output; components_doc - optional Stage 1
            output for extra component context.
        Output: dict matching report.json (see docs/examples/report.json).
        """
        violations = deepcopy(violations_doc.get("violations", []))
        components_by_id = {}
        if components_doc:
            components_by_id = {
                c["component_id"]: c for c in components_doc.get("components", [])
            }

        enriched_violations: list[dict] = []
        for violation in violations:
            component = components_by_id.get(violation.get("component_id"))
            if self.use_llm:
                # Week 4: replace with LLM call per SDS §7.2
                agent_fields = _template_enrichment(violation, component)
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
            "summary": {
                "total_issues": len(enriched_violations),
                **summary_counts,
            },
            "violations": enriched_violations,
        }
