"""Run Noor Week 3 validation steps and print log-friendly output."""

from __future__ import annotations

import json
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))
R01_FIXTURE = ROOT / "tests" / "fixtures" / "rules" / "r01_missing_label_fail.xml"
R01_VIOLATIONS = ROOT / "outputs" / "violations" / "r01_missing_label_fail_violations.json"


def run_cmd(label: str, cmd: list[str]) -> str:
    print(f"\n{'-' * 66}")
    print(label)
    print("-" * 66)
    result = subprocess.run(
        cmd,
        cwd=ROOT,
        capture_output=True,
        text=True,
    )
    out = (result.stdout + result.stderr).strip()
    print(out)
    return out


def cross_check_cli_api() -> None:
    print(f"\n{'-' * 66}")
    print("STEP 6: CLI vs API output cross-check (R01 fixture)")
    print("-" * 66)
    from fastapi.testclient import TestClient

    from backend.main import app

    cli = json.loads(R01_VIOLATIONS.read_text(encoding="utf-8"))
    client = TestClient(app)
    with R01_FIXTURE.open("rb") as handle:
        created = client.post(
            "/api/v1/audit",
            files={"xml": (R01_FIXTURE.name, handle, "application/xml")},
        )
    audit_id = created.json()["audit_id"]
    api = client.get(f"/api/v1/audit/{audit_id}/violations").json()

    cli_rules = sorted({v["rule_id"] for v in cli["violations"]})
    api_rules = sorted({v["rule_id"] for v in api["violations"]})
    print(f"CLI total_violations: {cli['total_violations']}")
    print(f"API total_violations: {api['total_violations']}")
    print(f"CLI rule_ids: {cli_rules}")
    print(f"API rule_ids: {api_rules}")
    print(f"MATCH count: {cli['total_violations'] == api['total_violations']}")
    print(f"MATCH rules: {cli_rules == api_rules}")


def validate_schema() -> None:
    print(f"\n{'-' * 66}")
    print("STEP 8: Direct schema validation — Noor R01 violations.json")
    print("-" * 66)
    import jsonschema

    schema = json.loads((ROOT / "docs" / "schemas" / "auditor_schema.json").read_text(encoding="utf-8"))
    doc = json.loads(R01_VIOLATIONS.read_text(encoding="utf-8"))
    errors = list(jsonschema.Draft202012Validator(schema).iter_errors(doc))
    print(f"File: {R01_VIOLATIONS.relative_to(ROOT)}")
    print(f"total_violations: {doc['total_violations']}")
    print(f"rule_ids: {[v['rule_id'] for v in doc['violations']]}")
    status = "PASS" if not errors else "FAIL"
    print(f"Schema: {status} ({len(errors)} error(s))")
    for err in errors[:5]:
        print(f" - {err.message}")


def api_smoke() -> None:
    print(f"\n{'-' * 66}")
    print("STEP 5: Live API smoke (TestClient — parse -> rules -> violations)")
    print("-" * 66)
    from fastapi.testclient import TestClient

    from backend.main import app

    client = TestClient(app)
    with R01_FIXTURE.open("rb") as handle:
        created = client.post(
            "/api/v1/audit",
            files={"xml": (R01_FIXTURE.name, handle, "application/xml")},
        )
    print("POST /api/v1/audit", created.status_code, created.json())
    audit_id = created.json()["audit_id"]
    status = client.get(f"/api/v1/audit/{audit_id}/status")
    print("GET /status", status.status_code, status.json())
    violations = client.get(f"/api/v1/audit/{audit_id}/violations")
    doc = violations.json()
    print(
        "GET /violations total=",
        doc["total_violations"],
        "rule_ids=",
        [v["rule_id"] for v in doc["violations"]],
    )
    report = client.get(f"/api/v1/audit/{audit_id}/report")
    print("GET /report (expect 404):", report.status_code)
    health = client.get("/health")
    print("GET /health", health.status_code, health.json())


def main() -> int:
    print("=" * 66)
    print("NOOR WEEK 3 VALIDATION LOG")
    print("Branch: noor   Date: 2026-07-03")
    print("Owner: Muhammad Noor (API/agent scaffold + frontend sync)")
    print("=" * 66)

    py = sys.executable
    run_cmd(
        "STEP 1: pytest tests/test_rules.py (R01-R12 rule engine)",
        [py, "-m", "pytest", "tests/test_rules.py", "-q"],
    )
    run_cmd(
        "STEP 2: pytest tests/test_agent.py (agent scaffold / score formula)",
        [py, "-m", "pytest", "tests/test_agent.py", "-v"],
    )
    run_cmd(
        "STEP 3: pytest tests/test_audit.py (FastAPI violations-only API)",
        [py, "-m", "pytest", "tests/test_audit.py", "-v"],
    )
    run_cmd(
        "STEP 4: python test_run.py tests/fixtures/rules/r01_missing_label_fail.xml",
        [py, "test_run.py", str(R01_FIXTURE.relative_to(ROOT))],
    )
    api_smoke()
    cross_check_cli_api()
    run_cmd(
        "STEP 7: python scripts/validate_output.py (schema checks)",
        [py, "scripts/validate_output.py"],
    )
    validate_schema()
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
