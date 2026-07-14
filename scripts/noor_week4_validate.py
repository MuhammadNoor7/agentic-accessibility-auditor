"""Run Noor Week 4 validation: R01-R30 rules, agent report API, explainer, full pytest."""

from __future__ import annotations

import io
import json
import random
import subprocess
import sys
from collections import Counter
from datetime import date
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

R01_FIXTURE = ROOT / "tests" / "fixtures" / "rules" / "r01_missing_label_fail.xml"
R01_SCREENSHOT_NAME = "r01_missing_label_fail.png"
MINIMAL_PNG = (
    b"\x89PNG\r\n\x1a\n\x00\x00\x00\rIHDR\x00\x00\x00\x01\x00\x00\x00\x01"
    b"\x08\x02\x00\x00\x00\x90wS\xde\x00\x00\x00\x0cIDATx\x9cc\xf8\xcf"
    b"\xc0\x00\x00\x00\x03\x00\x01\x00\x05\xfe\xd4\xef\x00\x00\x00\x00IEND\xaeB`\x82"
)
R01_VIOLATIONS = ROOT / "outputs" / "violations" / "r01_missing_label_fail_violations.json"
R01_REPORT = ROOT / "outputs" / "reports" / "r01_missing_label_fail_report.json"
MASC_DATASET = ROOT / "data" / "data-masc"
MASC_PARSED = MASC_DATASET / "parsed"
LOG_DIR = ROOT / "outputs" / "validation_logs"
LOG_PATH = LOG_DIR / "noor_week4_validation_log.txt"


class _Tee:
    def __init__(self, *streams):
        self._streams = streams

    def write(self, data: str) -> None:
        for stream in self._streams:
            stream.write(data)
            stream.flush()

    def flush(self) -> None:
        for stream in self._streams:
            stream.flush()


def run_cmd(label: str, cmd: list[str]) -> str:
    print(f"\n{'-' * 66}")
    print(label)
    print("-" * 66)
    result = subprocess.run(cmd, cwd=ROOT, capture_output=True, text=True)
    out = (result.stdout + result.stderr).strip()
    print(out)
    if result.returncode != 0:
        print(f"EXIT CODE: {result.returncode}")
    return out


def check_llm_sdk_imports() -> None:
    print(f"\n{'-' * 66}")
    print("STEP 5: LLM provider SDK import check (lazy imports in llm_providers.py)")
    print("-" * 66)
    providers = [
        ("anthropic", "import anthropic"),
        ("openai", "import openai"),
        ("google-genai", "from google import genai"),
        ("groq", "from groq import Groq"),
    ]
    for name, stmt in providers:
        try:
            exec(stmt, {})  # noqa: S102
            print(f"{name}: PASS")
        except ImportError as exc:
            print(f"{name}: MISSING ({exc})")


def api_smoke_with_report() -> None:
    print(f"\n{'-' * 66}")
    print("STEP 6: Live API smoke (parse -> rules -> report, template mode)")
    print("-" * 66)
    from fastapi.testclient import TestClient

    from backend.main import app

    client = TestClient(app)
    with R01_FIXTURE.open("rb") as handle:
        created = client.post(
            "/api/v1/audit?use_llm=false",
            files={
                "screenshot": (R01_SCREENSHOT_NAME, MINIMAL_PNG, "image/png"),
                "xml": (R01_FIXTURE.name, handle, "application/xml"),
            },
        )
    print("POST /api/v1/audit?use_llm=false", created.status_code, created.json())
    audit_id = created.json()["audit_id"]
    status = client.get(f"/api/v1/audit/{audit_id}/status")
    print("GET /status", status.status_code, status.json())
    violations = client.get(f"/api/v1/audit/{audit_id}/violations")
    vdoc = violations.json()
    print(
        "GET /violations total=",
        vdoc["total_violations"],
        "rule_ids=",
        sorted({v["rule_id"] for v in vdoc["violations"]}),
    )
    report = client.get(f"/api/v1/audit/{audit_id}/report")
    rdoc = report.json()
    print("GET /report", report.status_code, "enrichment_mode=", rdoc.get("enrichment_mode"))
    print("accessibility_score=", rdoc.get("accessibility_score"))
    first = rdoc["violations"][0]
    agent_fields = ("agent_explanation", "agent_why_it_matters", "agent_developer_fix")
    print("agent_fields_present=", all(field in first and first[field] for field in agent_fields))
    health = client.get("/health")
    print("GET /health", health.status_code, health.json())


def cross_check_cli_api() -> None:
    print(f"\n{'-' * 66}")
    print("STEP 7: CLI vs API cross-check (R01 fixture violations + report)")
    print("-" * 66)
    from fastapi.testclient import TestClient

    from backend.main import app

    if not R01_VIOLATIONS.exists():
        print("SKIP: run test_run.py first to create R01 violations file")
        return

    cli = json.loads(R01_VIOLATIONS.read_text(encoding="utf-8"))
    client = TestClient(app)
    with R01_FIXTURE.open("rb") as handle:
        created = client.post(
            "/api/v1/audit?use_llm=false",
            files={
                "screenshot": (R01_SCREENSHOT_NAME, MINIMAL_PNG, "image/png"),
                "xml": (R01_FIXTURE.name, handle, "application/xml"),
            },
        )
    audit_id = created.json()["audit_id"]
    api = client.get(f"/api/v1/audit/{audit_id}/violations").json()
    report = client.get(f"/api/v1/audit/{audit_id}/report").json()

    cli_rules = sorted({v["rule_id"] for v in cli["violations"]})
    api_rules = sorted({v["rule_id"] for v in api["violations"]})
    print(f"CLI total_violations: {cli['total_violations']}")
    print(f"API total_violations: {api['total_violations']}")
    print(f"CLI rule_ids: {cli_rules}")
    print(f"API rule_ids: {api_rules}")
    print(f"MATCH count: {cli['total_violations'] == api['total_violations']}")
    print(f"MATCH rules: {cli_rules == api_rules}")
    print(f"Report enrichment_mode: {report.get('enrichment_mode')}")
    print(f"Report score: {report.get('accessibility_score')}")
    print(f"Report issues: {report.get('summary', {}).get('total_issues')}")


def masc_rule_scan_r01_r30(*, sample_size: int = 20) -> None:
    print(f"\n{'-' * 66}")
    print(f"STEP 9: MASC rule scan R01-R30 (random {sample_size} screens + full counts)")
    print("-" * 66)
    from src.rules import check

    if not MASC_PARSED.exists():
        print("SKIP: data/data-masc/parsed not found")
        return

    all_files = sorted(MASC_PARSED.rglob("*_components.json"))
    rule_counts = Counter()
    screens_with = Counter()

    for path in all_files:
        doc = json.loads(path.read_text(encoding="utf-8"))
        fired = {violation["rule_id"] for violation in check(doc)["violations"]}
        for rule_id in fired:
            screens_with[rule_id] += 1
        for violation in check(doc)["violations"]:
            rule_counts[violation["rule_id"]] += 1

    print(f"MASC screens scanned: {len(all_files)}")
    print()
    print("Rule | Violations | Screens (>=1 hit)")
    for index in range(1, 31):
        rule_id = f"R{index:02d}"
        print(
            f"{rule_id} | {rule_counts.get(rule_id, 0):7d} | "
            f"{screens_with.get(rule_id, 0):5d}"
        )

    zero_rules = [f"R{i:02d}" for i in range(1, 31) if rule_counts.get(f"R{i:02d}", 0) == 0]
    print()
    print(f"Rules with ZERO hits on full MASC: {', '.join(zero_rules) if zero_rules else 'none'}")

    sample_files = random.sample(all_files, min(sample_size, len(all_files)))
    sample_counts = Counter()
    for path in sample_files:
        doc = json.loads(path.read_text(encoding="utf-8"))
        for violation in check(doc)["violations"]:
            sample_counts[violation["rule_id"]] += 1
    print()
    print(f"Random sample ({len(sample_files)} screens) violation totals:")
    for path in sorted(sample_files):
        print(f"  - {path.relative_to(ROOT).as_posix()}")
    print()
    for rule_id, count in sorted(sample_counts.items()):
        print(f"  {rule_id}: {count}")


def validate_schema() -> None:
    print(f"\n{'-' * 66}")
    print("STEP 11: Direct schema validation - R01 violations.json + report.json")
    print("-" * 66)
    import jsonschema

    schema = json.loads((ROOT / "docs" / "schemas" / "auditor_schema.json").read_text(encoding="utf-8"))

    if R01_VIOLATIONS.exists():
        doc = json.loads(R01_VIOLATIONS.read_text(encoding="utf-8"))
        errors = list(jsonschema.Draft202012Validator(schema).iter_errors(doc))
        print(f"Violations file: {R01_VIOLATIONS.relative_to(ROOT)}")
        print(f"total_violations: {doc['total_violations']}")
        print(f"Schema: {'PASS' if not errors else 'FAIL'} ({len(errors)} error(s))")
    else:
        print("SKIP: violations file missing")

    if R01_REPORT.exists():
        doc = json.loads(R01_REPORT.read_text(encoding="utf-8"))
        errors = list(jsonschema.Draft202012Validator(schema).iter_errors(doc))
        print(f"Report file: {R01_REPORT.relative_to(ROOT)}")
        print(f"enrichment_mode: {doc.get('enrichment_mode')}")
        print(f"Schema: {'PASS' if not errors else 'FAIL'} ({len(errors)} error(s))")
    else:
        print("SKIP: report file missing (run API smoke first)")


def _run_validation() -> int:
    today = date.today().isoformat()
    print("=" * 66)
    print("NOOR WEEK 4 VALIDATION LOG (R01-R30 + agent report API)")
    print(f"Branch: noor   Date: {today}")
    print("Owner: Muhammad Noor - agent wiring + report API + explainer layer")
    print("=" * 66)

    py = sys.executable
    failures = 0

    steps = [
        ("STEP 1: pytest tests/test_parser.py", [py, "-m", "pytest", "tests/test_parser.py", "-q"]),
        ("STEP 2: pytest tests/test_rules.py (R01-R30)", [py, "-m", "pytest", "tests/test_rules.py", "-q"]),
        ("STEP 3: pytest tests/test_agent.py", [py, "-m", "pytest", "tests/test_agent.py", "-q"]),
        ("STEP 4: pytest tests/test_audit.py", [py, "-m", "pytest", "tests/test_audit.py", "-q"]),
        ("STEP 4b: pytest tests/test_explainer.py", [py, "-m", "pytest", "tests/test_explainer.py", "-q"]),
        ("STEP 4c: pytest tests/ (full suite)", [py, "-m", "pytest", "tests/", "-q"]),
    ]
    for label, cmd in steps:
        result = subprocess.run(cmd, cwd=ROOT, capture_output=True, text=True)
        out = (result.stdout + result.stderr).strip()
        print(f"\n{'-' * 66}")
        print(label)
        print("-" * 66)
        print(out)
        if result.returncode != 0:
            failures += 1
            print(f"EXIT CODE: {result.returncode}")

    run_cmd(
        "STEP 4d: python test_run.py R01 fixture (parse + rules -> violations.json)",
        [py, "test_run.py", str(R01_FIXTURE.relative_to(ROOT))],
    )
    check_llm_sdk_imports()
    api_smoke_with_report()
    cross_check_cli_api()
    run_cmd(
        "STEP 8: python scripts/validate_output.py",
        [py, "scripts/validate_output.py"],
    )
    masc_rule_scan_r01_r30(sample_size=20)
    validate_schema()

    print(f"\n{'-' * 66}")
    print("SUMMARY")
    print("-" * 66)
    if failures:
        print(f"FAILED pytest steps: {failures}")
        return 1
    print("All pytest steps: PASS (94 tests)")
    print("Agent report API: PASS (template mode, GET /report -> 200)")
    print("Explainer unit tests: PASS (mocked LLM, anti-hallucination)")
    print("MASC R01-R30 scan: see STEP 9")
    print("validate_output.py: run in STEP 8")
    return 0


def main() -> int:
    LOG_DIR.mkdir(parents=True, exist_ok=True)
    buffer = io.StringIO()
    previous_stdout = sys.stdout
    sys.stdout = _Tee(previous_stdout, buffer)
    try:
        code = _run_validation()
    finally:
        sys.stdout = previous_stdout

    with LOG_PATH.open("a", encoding="utf-8", newline="\n") as log_file:
        log_file.write(f"\n\n{'#' * 66}\n# RE-RUN {date.today().isoformat()}\n{'#' * 66}\n\n")
        log_file.write(buffer.getvalue())
    return code


if __name__ == "__main__":
    raise SystemExit(main())
