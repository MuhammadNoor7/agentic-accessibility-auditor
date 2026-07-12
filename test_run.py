"""Parser smoke test: batch-parse XML files to dataset-specific parsed folders."""

from __future__ import annotations

import argparse
import json
import os
import sys
from pathlib import Path

from src.parser import (
    infer_dataset_root_for_xml,
    parse_xml_file,
    resolve_paths,
    resolve_dataset_root,
    resolve_parsed_root,
    _parsed_output_path,
)
from src.rules import check as check_rules

ROOT = Path(__file__).resolve().parent
VIOLATIONS_OUTPUT_ROOT = ROOT / "outputs" / "violations"
FIXTURES_ROOT = ROOT / "tests" / "fixtures" / "rules"
PARSED_FIXTURES_ROOT = ROOT / "data" / "parsed" / "fixtures"

DATASET_ALIASES = {
    "masc": ROOT / "data" / "data-masc",
    "rico": ROOT / "data" / "data-rico-holdout",
    "rico-holdout": ROOT / "data" / "data-rico-holdout",
    "upload": ROOT / "data",
    "generic": ROOT / "data",
}


def resolve_dataset_arg(dataset: str | None) -> Path | None:
    if not dataset:
        dataset_env = os.environ.get("DATASET_ROOT")
        if dataset_env:
            path = Path(dataset_env)
            if not path.is_absolute():
                path = (ROOT / path).resolve()
            return path if path.exists() else path
        return resolve_dataset_root()

    key = dataset.replace("\\", "/").strip("/")
    if key in DATASET_ALIASES:
        return DATASET_ALIASES[key]

    path = Path(dataset)
    if not path.is_absolute():
        path = (ROOT / path).resolve()
    return path


def write_violations(doc: dict, output_root: Path | None = None) -> dict:
    """Run the Stage 2 rule checker on a components.json doc and write violations.json.

    Input: doc - components.json-shaped dict returned by parse_xml_file();
        output_root - directory to write into (default outputs/violations/).
    Output: the violations.json-shaped dict that was written to disk.
    """
    output_root = output_root or VIOLATIONS_OUTPUT_ROOT
    output_root.mkdir(parents=True, exist_ok=True)
    violations_doc = check_rules(doc)
    output_file = output_root / f"{doc['screen_id']}_violations.json"
    output_file.write_text(json.dumps(violations_doc, indent=2), encoding="utf-8")
    return violations_doc


def run_batch(
    dataset: str | None = None,
    max_files: int | None = None,
    skip_rules: bool = False,
) -> dict:
    dataset_root = resolve_dataset_arg(dataset)
    if dataset_root is not None and not dataset_root.exists():
        raise FileNotFoundError(f"Dataset root not found: {dataset_root}")

    xml_root, output_root, dataset_root = resolve_paths(dataset_root=dataset_root)

    if max_files is None:
        max_files = int(os.environ.get("PARSER_MAX_FILES", "0"))

    xml_files = sorted(xml_root.rglob("*.xml"))
    if max_files > 0:
        xml_files = xml_files[:max_files]

    print(f"Parsing {len(xml_files)} XML file(s)...")
    print(f"Dataset root: {dataset_root}")
    print(f"XML root:     {xml_root}")
    print(f"Output root:  {output_root}")

    errors: list[str] = []
    processed = 0
    total_components = 0
    total_violations = 0

    for xml_path in xml_files:
        try:
            doc = parse_xml_file(xml_path, output_root, xml_root, dataset_root)
            processed += 1
            total_components += len(doc.get("components", []))
            if not skip_rules:
                violations_doc = write_violations(doc)
                total_violations += violations_doc["total_violations"]
        except Exception as exc:
            errors.append(f"{xml_path.name}: {exc}")

    return {
        "processed_files": processed,
        "failed_files": len(errors),
        "total_components": total_components,
        "total_violations": None if skip_rules else total_violations,
        "source_root": xml_root.as_posix(),
        "output_root": output_root.as_posix(),
        "dataset_root": dataset_root.as_posix() if dataset_root else None,
        "errors": errors[:20],
    }


def run_single(xml_arg: str, skip_rules: bool = False) -> int:
    xml_path = Path(xml_arg)
    if not xml_path.is_absolute():
        xml_path = (ROOT / xml_path).resolve()
    if not xml_path.is_file():
        print(f"Error: file not found: {xml_path}", file=sys.stderr)
        return 1

    dataset_root = infer_dataset_root_for_xml(xml_path)
    if dataset_root is not None:
        xml_root = dataset_root / "xml"
        output_root = resolve_parsed_root(dataset_root)
    else:
        xml_root = xml_path.parent
        if FIXTURES_ROOT in xml_path.parents:
            output_root = PARSED_FIXTURES_ROOT
        else:
            output_root = resolve_parsed_root(None)

    doc = parse_xml_file(xml_path, output_root, xml_root, dataset_root)
    output_file = _parsed_output_path(xml_path, output_root, dataset_root)

    print(f"Parsed {len(doc['components'])} component(s) from {xml_path.name}")
    print(f"screen_id:  {doc['screen_id']}")
    print(f"image_path: {doc['image_path']}")
    print(f"xml_path:   {doc['xml_path']}")
    print(f"written:    {output_file}")

    if not skip_rules:
        violations_doc = write_violations(doc)
        violations_file = VIOLATIONS_OUTPUT_ROOT / f"{doc['screen_id']}_violations.json"
        rule_ids = sorted({item['rule_id'] for item in violations_doc['violations']})
        print(f"violations: {violations_doc['total_violations']} found")
        if rule_ids:
            print(f"rule_ids:   {rule_ids}")
        print(f"written:    {violations_file}")
    return 0


def run_fixtures(skip_rules: bool = False) -> int:
    """Parse every tests/fixtures/rules/*.xml and write violations under outputs/violations/."""
    xml_files = sorted(FIXTURES_ROOT.glob("*.xml"))
    if not xml_files:
        print(f"Error: no fixture XML files under {FIXTURES_ROOT}", file=sys.stderr)
        return 1

    print(f"Running {len(xml_files)} rule fixture(s)...")
    failures: list[str] = []
    for xml_path in xml_files:
        print(f"\n--- {xml_path.name} ---")
        try:
            code = run_single(xml_path, skip_rules=skip_rules)
            if code != 0:
                failures.append(xml_path.name)
        except Exception as exc:
            failures.append(f"{xml_path.name}: {exc}")
            print(f"Error: {exc}", file=sys.stderr)

    print(f"\n=== Fixture batch complete ===")
    print(f"processed: {len(xml_files) - len(failures)}")
    print(f"failed:    {len(failures)}")
    if failures:
        print("failures:", failures[:20])
    return 1 if failures else 0


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description="Parse Android UI XML (UIAutomator, MASC, Rico, or generic) into components.json.",
    )
    parser.add_argument(
        "xml_file",
        nargs="?",
        help="Optional path to a single .xml file",
    )
    parser.add_argument(
        "--dataset",
        "-d",
        metavar="NAME",
        help="Dataset for batch mode: masc, rico, upload (data/xml), or a path",
    )
    parser.add_argument(
        "--max-files",
        type=int,
        default=None,
        metavar="N",
        help="Limit batch size (default: all, or PARSER_MAX_FILES env var)",
    )
    parser.add_argument(
        "--fixtures",
        action="store_true",
        help="Run all tests/fixtures/rules/*.xml and write outputs/violations/*_violations.json",
    )
    parser.add_argument(
        "--skip-rules",
        action="store_true",
        help="Skip running the Stage 2 rule checker after parsing.",
    )
    return parser


def main(argv: list[str] | None = None) -> int:
    args = build_parser().parse_args(argv)

    if args.fixtures:
        return run_fixtures(skip_rules=args.skip_rules)

    if args.xml_file:
        return run_single(args.xml_file, skip_rules=args.skip_rules)

    try:
        result = run_batch(dataset=args.dataset, max_files=args.max_files, skip_rules=args.skip_rules)
    except FileNotFoundError as exc:
        print(f"Error: {exc}", file=sys.stderr)
        return 1

    print("\n=== Parser Results ===")
    print(json.dumps(result, indent=2))
    return 1 if result["failed_files"] else 0


if __name__ == "__main__":
    raise SystemExit(main())
