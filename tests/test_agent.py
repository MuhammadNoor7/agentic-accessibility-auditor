"""Tests for src/agent.py scaffold."""

from __future__ import annotations

from src.agent import AgenticEnricher, compute_accessibility_score


def test_compute_accessibility_score_penalties() -> None:
    violations = [
        {"severity": "High"},
        {"severity": "Medium"},
    ]
    assert compute_accessibility_score(violations) == 85


def test_enrich_adds_agent_fields_and_summary() -> None:
  violations_doc = {
      "schema_version": "1.0",
      "screen_id": "test_screen",
      "image_path": "",
      "xml_path": "",
      "total_violations": 1,
      "violations": [
          {
              "rule_id": "R01",
              "issue": "Missing accessible label",
              "component_id": "c_001",
              "class": "android.widget.Button",
              "bounds": [0, 0, 10, 10],
              "guideline": "G01 — Missing accessible label",
              "severity": "High",
              "recommendation": "Add a label.",
          }
      ],
  }
  report = AgenticEnricher(use_llm=False).enrich(violations_doc)
  assert report["enrichment_mode"] == "template"
  assert report["summary"]["total_issues"] == 1
  assert report["accessibility_score"] == 90
  v = report["violations"][0]
  assert "agent_explanation" in v
  assert "agent_why_it_matters" in v
  assert "agent_developer_fix" in v
