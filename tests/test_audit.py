"""Tests for backend audit API — parse + rules + agent report."""

from __future__ import annotations

import io
from pathlib import Path

import pytest
from fastapi.testclient import TestClient
from PIL import Image

from backend.main import app
from src.agent import build_audit_report, compute_accessibility_score
from src.parser import load_xml_root, parse_xml_tree
from src.rules import check
from src.schema_documents import build_components_document

FIXTURES_DIR = Path(__file__).resolve().parent / "fixtures" / "rules"
R01_FIXTURE = FIXTURES_DIR / "r01_missing_label_fail.xml"
R01_SCREENSHOT_NAME = "r01_missing_label_fail.png"
R08_FIXTURE = FIXTURES_DIR / "r08_layout_overlap_fail.xml"
R08_SCREENSHOT_NAME = "r08_layout_overlap_fail.png"

MINIMAL_PNG = (
    b"\x89PNG\r\n\x1a\n\x00\x00\x00\rIHDR\x00\x00\x00\x01\x00\x00\x00\x01"
    b"\x08\x02\x00\x00\x00\x90wS\xde\x00\x00\x00\x0cIDATx\x9cc\xf8\xcf"
    b"\xc0\x00\x00\x00\x03\x00\x01\x00\x05\xfe\xd4\xef\x00\x00\x00\x00IEND\xaeB`\x82"
)


def _real_png(size: tuple[int, int] = (300, 300)) -> bytes:
    """A genuinely decodable PNG (unlike MINIMAL_PNG, which passes Image.open()'s
    header check but fails on .load() - fine for tests that only need the file
    to exist, not for anything that actually crops/decodes pixels)."""
    buf = io.BytesIO()
    Image.new("RGB", size, color=(200, 200, 200)).save(buf, format="PNG")
    return buf.getvalue()


def _post_audit(client: TestClient, *, use_llm: bool | None = None) -> object:
    query = f"?use_llm={'false' if use_llm is False else 'true'}" if use_llm is not None else ""
    with R01_FIXTURE.open("rb") as handle:
        return client.post(
            f"/api/v1/audit{query}",
            files={
                "screenshot": (R01_SCREENSHOT_NAME, MINIMAL_PNG, "image/png"),
                "xml": (R01_FIXTURE.name, handle, "application/xml"),
            },
        )


def _expected_violations_for_fixture(xml_path: Path) -> dict:
    """Same path as test_rules: parse fixture XML and run check()."""
    components = parse_xml_tree(load_xml_root(xml_path))
    components_json = build_components_document(
        screen_id=xml_path.stem,
        image_path="",
        xml_path=str(xml_path),
        components=components,
    )
    return check(components_json)


@pytest.fixture
def client() -> TestClient:
    return TestClient(app)


def test_audit_pipeline_r01_fixture(client: TestClient) -> None:
    """POST fixture XML → GET violations matches test_rules R01 expectations."""
    expected = _expected_violations_for_fixture(R01_FIXTURE)

    response = _post_audit(client)

    assert response.status_code == 202
    body = response.json()
    audit_id = body["audit_id"]
    assert body["status"] == "complete"

    status_response = client.get(f"/api/v1/audit/{audit_id}/status")
    assert status_response.status_code == 200
    assert status_response.json()["status"] == "complete"

    violations_response = client.get(f"/api/v1/audit/{audit_id}/violations")
    assert violations_response.status_code == 200
    violations_doc = violations_response.json()

    assert violations_doc["total_violations"] == expected["total_violations"]
    assert violations_doc["total_violations"] >= 1
    rule_ids = {v["rule_id"] for v in violations_doc["violations"]}
    assert "R01" in rule_ids

    for key in ("schema_version", "screen_id", "image_path", "xml_path", "total_violations", "violations"):
        assert key in violations_doc
    assert violations_doc["total_violations"] == len(violations_doc["violations"])


def test_audit_pipeline_attaches_cv_confidence_to_r08(client: TestClient) -> None:
    """R08 (a CV-confirmable rule) gets a cv_confidence field from the crop
    classifier; the field is a real float in [0, 1], not always None, which
    proves the model is actually being called during the pipeline run."""
    with R08_FIXTURE.open("rb") as handle:
        response = client.post(
            "/api/v1/audit",
            files={
                "screenshot": (R08_SCREENSHOT_NAME, _real_png(), "image/png"),
                "xml": (R08_FIXTURE.name, handle, "application/xml"),
            },
        )

    assert response.status_code == 202
    audit_id = response.json()["audit_id"]
    assert response.json()["status"] == "complete"

    violations_doc = client.get(f"/api/v1/audit/{audit_id}/violations").json()
    r08_violations = [v for v in violations_doc["violations"] if v["rule_id"] == "R08"]
    assert len(r08_violations) == 1

    cv_confidence = r08_violations[0]["cv_confidence"]
    assert cv_confidence is not None, "classify_crop() was not actually called"
    assert 0 <= cv_confidence <= 1


def test_audit_falls_back_to_yolo_when_xml_omitted(client: TestClient) -> None:
    """No xml part at all -> the pipeline uses the screenshot-only YOLO
    detector (FR-CV.4) instead of 422ing or erroring."""
    from backend.routers.audit import _AUDIT_JOBS

    response = client.post(
        "/api/v1/audit",
        files={"screenshot": ("no_xml_screen.png", _real_png(), "image/png")},
    )

    assert response.status_code == 202
    audit_id = response.json()["audit_id"]
    assert response.json()["status"] == "complete"

    violations_doc = client.get(f"/api/v1/audit/{audit_id}/violations").json()
    assert violations_doc["xml_path"] == ""

    components = _AUDIT_JOBS[audit_id]["components"]["components"]
    assert all(c["inferred"] is True for c in components)


def test_audit_falls_back_to_yolo_when_xml_malformed(client: TestClient) -> None:
    """A .xml file that isn't valid XML -> same YOLO fallback, not a 500."""
    response = client.post(
        "/api/v1/audit",
        files={
            "screenshot": ("bad_xml_screen.png", _real_png(), "image/png"),
            "xml": ("bad_xml_screen.xml", b"this is not < valid xml", "application/xml"),
        },
    )

    assert response.status_code == 202
    audit_id = response.json()["audit_id"]
    assert response.json()["status"] == "complete"

    violations_doc = client.get(f"/api/v1/audit/{audit_id}/violations").json()
    assert violations_doc["xml_path"] == ""


def test_audit_report_endpoint_returns_enriched_report(client: TestClient) -> None:
    """POST fixture XML → GET report returns report.json with agent fields."""
    response = _post_audit(client, use_llm=False)

    assert response.status_code == 202
    audit_id = response.json()["audit_id"]

    report_response = client.get(f"/api/v1/audit/{audit_id}/report")
    assert report_response.status_code == 200
    report_doc = report_response.json()

    assert report_doc["enrichment_mode"] == "template"
    assert "accessibility_score" in report_doc
    assert 0 <= report_doc["accessibility_score"] <= 100
    assert report_doc["summary"]["total_issues"] == len(report_doc["violations"])
    assert report_doc["summary"]["total_issues"] >= 1

    first = report_doc["violations"][0]
    assert first["rule_id"] == "R01"
    for field in ("agent_explanation", "agent_why_it_matters", "agent_developer_fix"):
        assert field in first
        assert first[field]


def test_audit_report_not_found(client: TestClient) -> None:
    response = client.get("/api/v1/audit/00000000-0000-0000-0000-000000000000/report")
    assert response.status_code == 404


def test_audit_report_download_html(client: TestClient) -> None:
    created = _post_audit(client, use_llm=False)
    audit_id = created.json()["audit_id"]

    report = client.get(f"/api/v1/audit/{audit_id}/report")
    assert report.status_code == 200
    report_doc = report.json()
    assert report_doc.get("image_path")
    assert "outputs/runs/" in report_doc["image_path"].replace("\\", "/")
    assert report_doc.get("xml_path")
    assert Path(report_doc["image_path"]).is_file() or (
        Path(__file__).resolve().parents[1] / report_doc["image_path"]
    ).is_file()

    response = client.get(f"/api/v1/audit/{audit_id}/report/download?format=html")
    assert response.status_code == 200
    assert "text/html" in response.headers["content-type"]
    assert "attachment" in response.headers.get("content-disposition", "")
    assert "Accessibility audit report" in response.text
    assert "r01_missing_label_fail" in response.text
    # Screenshot + XML must be embedded (not the empty placeholders).
    assert "No screenshot available" not in response.text
    assert "data:image" in response.text
    assert "XML source not available" not in response.text
    assert "<hierarchy" in response.text or "node" in response.text.lower()


def test_audit_report_download_pdf(client: TestClient) -> None:
    created = _post_audit(client, use_llm=False)
    audit_id = created.json()["audit_id"]

    response = client.get(f"/api/v1/audit/{audit_id}/report/download?format=pdf")
    if response.status_code == 503:
        pytest.skip(response.json().get("detail", "PDF unavailable"))
    assert response.status_code == 200
    assert "application/pdf" in response.headers["content-type"]
    assert response.content.startswith(b"%PDF")


def test_audit_report_download_invalid_format(client: TestClient) -> None:
    created = _post_audit(client, use_llm=False)
    audit_id = created.json()["audit_id"]

    response = client.get(f"/api/v1/audit/{audit_id}/report/download?format=docx")
    assert response.status_code == 422


def test_audit_missing_screenshot_returns_422(client: TestClient) -> None:
    with R01_FIXTURE.open("rb") as handle:
        response = client.post(
            "/api/v1/audit",
            files={"xml": (R01_FIXTURE.name, handle, "application/xml")},
        )

    assert response.status_code == 422


def test_audit_mismatched_pair_returns_400(client: TestClient) -> None:
    with R01_FIXTURE.open("rb") as handle:
        response = client.post(
            "/api/v1/audit",
            files={
                "screenshot": ("photo1.png", MINIMAL_PNG, "image/png"),
                "xml": (R01_FIXTURE.name, handle, "application/xml"),
            },
        )

    assert response.status_code == 400
    assert "match" in response.json()["detail"].lower()


def test_build_audit_report_template_mode() -> None:
    violations_doc = _expected_violations_for_fixture(R01_FIXTURE)
    components = parse_xml_tree(load_xml_root(R01_FIXTURE))
    components_doc = build_components_document(
        screen_id=R01_FIXTURE.stem,
        image_path="",
        xml_path=str(R01_FIXTURE),
        components=components,
    )
    report_doc = build_audit_report(violations_doc, components_doc, use_llm=False)

    assert report_doc["enrichment_mode"] == "template"
    assert report_doc["accessibility_score"] == compute_accessibility_score(report_doc["violations"])
