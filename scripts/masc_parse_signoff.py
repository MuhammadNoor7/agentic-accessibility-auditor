"""Full MASC XML parsing sign-off across train, val, and test splits."""

from __future__ import annotations

import csv
import json
import sys
from collections import defaultdict
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(PROJECT_ROOT))

from src.parser import parse_ui_xml
from src.schema_documents import build_components_document

REQUIRED_COMP = {
    "component_id",
    "class",
    "text",
    "content_desc",
    "resource_id",
    "clickable",
    "enabled",
    "focusable",
    "bounds",
}


def check_split(split_name: str) -> dict:
    csv_path = PROJECT_ROOT / "data" / "data-masc" / "splits" / f"{split_name}.csv"
    stats: dict[str, dict[str, int]] = defaultdict(
        lambda: {"ok": 0, "empty": 0, "parse_error": 0, "missing": 0, "schema": 0}
    )
    errors: list[dict[str, str]] = []

    with csv_path.open(newline="", encoding="utf-8") as handle:
        rows = list(csv.DictReader(handle))

    for row in rows:
        category = row["category"]
        xml_path = PROJECT_ROOT / row["xml_path"]
        if not xml_path.is_file():
            stats[category]["missing"] += 1
            continue
        try:
            components = parse_ui_xml(xml_path)
            if not components:
                stats[category]["empty"] += 1
                continue
            build_components_document(
                screen_id=f"screen_{row['screen_id']}",
                image_path=row["image_path"],
                xml_path=row["xml_path"],
                components=components,
            )
            if REQUIRED_COMP - set(components[0].keys()):
                stats[category]["schema"] += 1
            else:
                stats[category]["ok"] += 1
        except Exception as exc:
            stats[category]["parse_error"] += 1
            if len(errors) < 20:
                errors.append(
                    {
                        "screen_id": row["screen_id"],
                        "category": category,
                        "xml_path": row["xml_path"],
                        "error": str(exc),
                    }
                )

    totals = {"ok": 0, "empty": 0, "parse_error": 0, "missing": 0, "schema": 0}
    for category in sorted(stats.keys()):
        cat_stats = stats[category]
        for key in totals:
            totals[key] += cat_stats[key]

    print(f"\n=== MASC {split_name} split ({len(rows)} screens) ===")
    for category in sorted(stats.keys()):
        cat_stats = stats[category]
        print(
            f"  {category:10s} ok={cat_stats['ok']:4d} "
            f"empty={cat_stats['empty']:3d} errors={cat_stats['parse_error']:3d} "
            f"missing={cat_stats['missing']:3d} schema={cat_stats['schema']:3d}"
        )
    print(
        f"  {'TOTAL':10s} ok={totals['ok']:4d} empty={totals['empty']:3d} "
        f"errors={totals['parse_error']:3d} missing={totals['missing']:3d} "
        f"schema={totals['schema']:3d}"
    )

    return {
        "split": split_name,
        "total_screens": len(rows),
        "totals": totals,
        "by_category": dict(stats),
        "errors": errors,
    }


def main() -> int:
    print("=== MASC XML parsing sign-off (all splits, all categories) ===")
    split_reports = [check_split(name) for name in ("train", "val", "test")]

    all_totals = {"ok": 0, "empty": 0, "parse_error": 0, "missing": 0, "schema": 0}
    for report in split_reports:
        for key in all_totals:
            all_totals[key] += report["totals"][key]

    passed = not (
        all_totals["parse_error"] or all_totals["missing"] or all_totals["schema"]
    )

    signoff = {
        "sign_off": "PASS" if passed else "ISSUES",
        "dataset": "MASC",
        "total_screens": sum(r["total_screens"] for r in split_reports),
        "categories": 10,
        "category_names": sorted(
            {cat for r in split_reports for cat in r["by_category"].keys()}
        ),
        "aggregate_totals": all_totals,
        "splits": {r["split"]: r for r in split_reports},
    }

    report_path = PROJECT_ROOT / "data" / "data-masc" / "parsed" / "masc_parse_signoff_report.json"
    report_path.parent.mkdir(parents=True, exist_ok=True)
    report_path.write_text(json.dumps(signoff, indent=2), encoding="utf-8")

    print("\n--- Aggregate ---")
    print(
        f"  TOTAL      ok={all_totals['ok']:4d} empty={all_totals['empty']:3d} "
        f"errors={all_totals['parse_error']:3d} missing={all_totals['missing']:3d} "
        f"schema={all_totals['schema']:3d}"
    )
    print(f"\nSign-off report: {report_path.relative_to(PROJECT_ROOT)}")
    print("Overall:", signoff["sign_off"])
    return 0 if passed else 1


if __name__ == "__main__":
    raise SystemExit(main())
