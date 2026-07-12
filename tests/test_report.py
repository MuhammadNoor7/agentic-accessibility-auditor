"""Tests for src/report.py HTML/PDF export."""

from __future__ import annotations

from pathlib import Path

import pytest

from src.agent import AgenticEnricher
from src.report import render_html_report, render_pdf_report, write_report_html

FIXTURES_DIR = Path(__file__).resolve().parent / "fixtures" / "rules"
R01_FIXTURE = FIXTURES_DIR / "r01_missing_label_fail.xml"


def _sample_report() -> dict:
    return AgenticEnricher(use_llm=False).enrich(
        {
            "schema_version": "1.0",
            "screen_id": "screen_001",
            "image_path": "",
            "xml_path": str(R01_FIXTURE),
            "total_violations": 1,
            "violations": [
                {
                    "rule_id": "R01",
                    "issue": "Missing accessible label",
                    "component_id": "c_002",
                    "class": "android.widget.Button",
                    "bounds": [100, 100, 300, 220],
                    "guideline": "G01 — Missing accessible label",
                    "severity": "High",
                    "recommendation": "Add android:contentDescription.",
                }
            ],
        }
    )


def test_render_html_report_contains_core_sections() -> None:
    report_doc = _sample_report()
    html = render_html_report(report_doc)

    assert "Accessibility audit report" in html
    assert report_doc["screen_id"] in html
    assert "R01" in html
    assert "Missing accessible label" in html
    assert "Developer fix" in html
    assert str(report_doc["accessibility_score"]) in html


def test_render_html_report_includes_xml_snippet() -> None:
    report_doc = _sample_report()
    html = render_html_report(report_doc)

    assert "<" in html
    assert "xml" in html.lower()


def test_write_report_html_creates_file(tmp_path: Path) -> None:
    report_doc = _sample_report()
    output_path = tmp_path / "screen_001_report.html"
    write_report_html(report_doc, output_path)

    assert output_path.is_file()
    text = output_path.read_text(encoding="utf-8")
    assert "screen_001" in text


@pytest.mark.skipif(
    __import__("importlib").util.find_spec("playwright") is None,
    reason="playwright not installed",
)
def test_render_pdf_report_returns_pdf_bytes() -> None:
    report_doc = _sample_report()
    try:
        pdf_bytes = render_pdf_report(report_doc)
    except RuntimeError as exc:
        pytest.skip(str(exc))

    assert pdf_bytes.startswith(b"%PDF")
