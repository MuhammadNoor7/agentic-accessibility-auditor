"""Validate components.json and violations.json files against auditor_schema.json."""

from __future__ import annotations

import json
import sys
from pathlib import Path

try:
    import jsonschema
except ImportError:
    print("Install jsonschema: pip install jsonschema")
    raise SystemExit(1)

PROJECT_ROOT = Path(__file__).resolve().parents[1]
SCHEMA_PATH = PROJECT_ROOT / "docs" / "schemas" / "auditor_schema.json"


def load_schema() -> dict:
    return json.loads(SCHEMA_PATH.read_text(encoding="utf-8"))


def infer_schema_title(doc: dict) -> str:
    if "summary" in doc:
        return "report.json"
    if "total_violations" in doc:
        return "violations.json"
    return "components.json"


def validate_file(path: Path, schema: dict) -> tuple[bool, str, list[str]]:
    doc = json.loads(path.read_text(encoding="utf-8"))
    title = infer_schema_title(doc)
    validator = jsonschema.Draft202012Validator(schema)
    errors = [e.message for e in validator.iter_errors(doc)]
    return len(errors) == 0, title, errors


def main() -> int:
    targets: list[Path] = []
    parsed_roots = [
        PROJECT_ROOT / "data" / "data-masc" / "parsed",
        PROJECT_ROOT / "data" / "data-rico-holdout" / "parsed",
        PROJECT_ROOT / "data" / "parsed",
    ]
    violations = PROJECT_ROOT / "outputs" / "violations"

    for parsed in parsed_roots:
        if parsed.exists():
            targets.extend(sorted(parsed.rglob("*_components.json"))[:5])
    if violations.exists():
        targets.extend(sorted(violations.glob("*_violations.json"))[:5])

    if not targets:
        print("No output files found. Run test_run.py first.")
        return 1

    schema = load_schema()
    ok_count = 0
    for path in targets:
        ok, doc_type, errors = validate_file(path, schema)
        status = "PASS" if ok else "FAIL"
        print(f"{status} [{doc_type}] {path.name}")
        if errors:
            for err in errors[:3]:
                print(f"  - {err}")
        else:
            ok_count += 1

    print(f"\nValidated {len(targets)} file(s); {ok_count} passed schema checks.")
    return 0 if ok_count == len(targets) else 1


if __name__ == "__main__":
    raise SystemExit(main())
