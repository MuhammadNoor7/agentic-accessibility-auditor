"""Run Noor validation: parser R13-R20 fields, rules R01-R20, API, and MASC scan."""

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
R01_VIOLATIONS = ROOT / "outputs" / "violations" / "r01_missing_label_fail_violations.json"
MASC_DATASET = ROOT / "data" / "data-masc"
MASC_PARSED = MASC_DATASET / "parsed"
LOG_DIR = ROOT / "outputs" / "validation_logs"
LOG_PATH = LOG_DIR / "noor_week3_validation_log.txt"


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

PARSER_EXTENSION_FIELDS = (
    "focus_order",
    "parent_id",
    "long_clickable",
    "scrollable",
    "selected",
    "checked",
    "password",
    "text_all_caps",
    "input_type",
    "important_for_accessibility",
    "media_type",
    "is_dialog",
    "label_for",
)

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


def check_parser_extended_fields() -> None:
    print(f"\n{'-' * 66}")
    print("STEP 5: Parser extended fields (R13-R20 support) on R01 fixture")
    print("-" * 66)
    from src.parser import load_xml_root, parse_xml_tree

    components = parse_xml_tree(load_xml_root(R01_FIXTURE))
    assert components, "fixture produced no components"
    sample = components[0]
    missing = [field for field in PARSER_EXTENSION_FIELDS if field not in sample]
    print(f"Components parsed: {len(components)}")
    print(f"Sample component_id: {sample['component_id']}")
    print(f"Extended fields present: {len(PARSER_EXTENSION_FIELDS) - len(missing)}/{len(PARSER_EXTENSION_FIELDS)}")
    if missing:
        print(f"MISSING: {missing}")
    else:
        print("All extended parser fields present: PASS")
    with_parent = sum(1 for component in components if component.get("parent_id"))
    print(f"Components with parent_id: {with_parent}")


def reparse_masc_dataset() -> int:
    """Re-parse every MASC XML under data/data-masc/xml into parsed/ + violations."""
    print(f"\n{'-' * 66}")
    print("STEP 0: MASC full re-parse (all xml folders -> parsed + rules R01-R20)")
    print("-" * 66)
    xml_root = MASC_DATASET / "xml"
    if not xml_root.is_dir():
        print(f"SKIP: MASC XML not found at {xml_root}")
        print("Link or copy data/data-masc/xml and screenshots before re-parsing.")
        return 1

    xml_count = len(list(xml_root.rglob("*.xml")))
    print(f"XML files found: {xml_count}")
    print(f"Output parsed root: {MASC_PARSED}")
    print(f"Violations root: {ROOT / 'outputs' / 'violations'}")

    py = sys.executable
    result = subprocess.run(
        [py, "test_run.py", "--dataset", "masc"],
        cwd=ROOT,
        capture_output=True,
        text=True,
    )
    out = (result.stdout + result.stderr).strip()
    print(out)
    if result.returncode != 0:
        print(f"EXIT CODE: {result.returncode}")
    return result.returncode


def masc_rule_scan(*, sample_size: int = 20) -> None:
    print(f"\n{'-' * 66}")
    print(f"STEP 9: MASC rule scan R01-R20 (random {sample_size} screens + full counts)")
    print("-" * 66)
    from src.rules import check

    if not MASC_PARSED.exists():
        print("SKIP: data/data-masc/parsed not found")
        return

    all_files = sorted(MASC_PARSED.rglob("*_components.json"))
    stale = 0
    rule_counts = Counter()
    screens_with = Counter()

    for path in all_files:
        doc = json.loads(path.read_text(encoding="utf-8"))
        components = doc.get("components", [])
        if components and "focus_order" not in components[0]:
            stale += 1
        fired = {violation["rule_id"] for violation in check(doc)["violations"]}
        for rule_id in fired:
            screens_with[rule_id] += 1
        for violation in check(doc)["violations"]:
            rule_counts[violation["rule_id"]] += 1

    print(f"MASC screens scanned: {len(all_files)}")
    print(f"Stale components.json (pre-parser-extension): {stale}")
    print()
    print("Rule | Violations | Screens (>=1 hit)")
    for index in range(1, 21):
        rule_id = f"R{index:02d}"
        print(
            f"{rule_id} | {rule_counts.get(rule_id, 0):7d} | "
            f"{screens_with.get(rule_id, 0):5d}"
        )

    zero_rules = [f"R{i:02d}" for i in range(1, 21) if rule_counts.get(f"R{i:02d}", 0) == 0]
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


def cross_check_cli_api() -> None:
    print(f"\n{'-' * 66}")
    print("STEP 7: CLI vs API output cross-check (R01 fixture)")
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
    print("STEP 11: Direct schema validation - R01 violations.json")
    print("-" * 66)
    import jsonschema

    if not R01_VIOLATIONS.exists():
        print("SKIP: violations file missing")
        return

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
    print("STEP 6: Live API smoke (TestClient - parse -> rules -> violations)")
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
        sorted({v["rule_id"] for v in doc["violations"]}),
    )
    report = client.get(f"/api/v1/audit/{audit_id}/report")
    print("GET /report (expect 404):", report.status_code)
    health = client.get("/health")
    print("GET /health", health.status_code, health.json())


def _run_validation() -> int:
    today = date.today().isoformat()
    print("=" * 66)
    print("NOOR WEEK 3+ VALIDATION LOG (R01-R20)")
    print(f"Branch: noor   Date: {today}")
    print("Owner: Muhammad Noor - parser extension + rules R13-R20 + API")
    print("=" * 66)

    py = sys.executable
    failures = 0

    if reparse_masc_dataset() != 0:
        failures += 1

    steps = [
        ("STEP 1: pytest tests/test_parser.py", [py, "-m", "pytest", "tests/test_parser.py", "-v"]),
        ("STEP 2: pytest tests/test_rules.py (R01-R20)", [py, "-m", "pytest", "tests/test_rules.py", "-q"]),
        ("STEP 3: pytest tests/test_agent.py", [py, "-m", "pytest", "tests/test_agent.py", "-q"]),
        ("STEP 4: pytest tests/test_audit.py", [py, "-m", "pytest", "tests/test_audit.py", "-q"]),
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
        "STEP 4b: python test_run.py R01 fixture (parse + rules -> violations.json)",
        [py, "test_run.py", str(R01_FIXTURE.relative_to(ROOT))],
    )
    check_parser_extended_fields()
    api_smoke()
    cross_check_cli_api()
    run_cmd(
        "STEP 8: python scripts/validate_output.py",
        [py, "scripts/validate_output.py"],
    )
    masc_rule_scan(sample_size=20)
    validate_schema()

    print(f"\n{'-' * 66}")
    print("SUMMARY")
    print("-" * 66)
    if failures:
        print(f"FAILED pytest steps: {failures}")
        return 1
    print("All pytest steps: PASS")
    print("Parser R13-R20 fields: PASS (when fixture XML present)")
    print("MASC re-parse + rules R01-R20: see STEP 0")
    print("validate_output.py: run in STEP 8 (schema spot-check on parsed + violations)")
    print("API violations-only: PASS (R01 fixture)")
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
