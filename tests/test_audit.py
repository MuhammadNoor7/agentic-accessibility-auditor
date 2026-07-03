"""Tests for backend audit API — parse + rules only (no agent/report)."""

from __future__ import annotations

from pathlib import Path

import pytest
from fastapi.testclient import TestClient

from backend.main import app
from src.parser import load_xml_root, parse_xml_tree
from src.rules import check
from src.schema_documents import build_components_document

FIXTURES_DIR = Path(__file__).resolve().parent / "fixtures" / "rules"
R01_FIXTURE = FIXTURES_DIR / "r01_missing_label_fail.xml"


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

    with R01_FIXTURE.open("rb") as handle:
        response = client.post(
            "/api/v1/audit",
            files={"xml": (R01_FIXTURE.name, handle, "application/xml")},
        )

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


def test_audit_report_endpoint_removed(client: TestClient) -> None:
    """Report endpoint must not exist — pipeline stops at violations."""
    response = client.get("/api/v1/audit/00000000-0000-0000-0000-000000000000/report")
    assert response.status_code == 404
