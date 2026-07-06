"""Full MASC XML parsing sign-off across train, val, and test splits."""

from __future__ import annotations

import csv
import json
import sys
from collections import Counter, defaultdict
from datetime import datetime, timezone
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(PROJECT_ROOT))

from src.parser import parse_ui_xml
from src.rules import check as check_rules
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

EXTENDED_PARSER_FIELDS = (
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

PARSED_ROOT = PROJECT_ROOT / "data" / "data-masc" / "parsed"
SIGNOFF_REPORT = PARSED_ROOT / "masc_parse_signoff_report.json"
FULL_LOG = PARSED_ROOT / "batch_parse_masc_full.log"


def check_split(split_name: str) -> dict:
    csv_path = PROJECT_ROOT / "data" / "data-masc" / "splits" / f"{split_name}.csv"
    stats: dict[str, dict[str, int]] = defaultdict(
        lambda: {
            "ok": 0,
            "empty": 0,
            "parse_error": 0,
            "missing": 0,
            "schema": 0,
            "extended_missing": 0,
        }
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
            elif any(field not in components[0] for field in EXTENDED_PARSER_FIELDS):
                stats[category]["extended_missing"] += 1
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

    totals = {
        "ok": 0,
        "empty": 0,
        "parse_error": 0,
        "missing": 0,
        "schema": 0,
        "extended_missing": 0,
    }
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
            f"missing={cat_stats['missing']:3d} schema={cat_stats['schema']:3d} "
            f"ext_missing={cat_stats['extended_missing']:3d}"
        )
    print(
        f"  {'TOTAL':10s} ok={totals['ok']:4d} empty={totals['empty']:3d} "
        f"errors={totals['parse_error']:3d} missing={totals['missing']:3d} "
        f"schema={totals['schema']:3d} ext_missing={totals['extended_missing']:3d}"
    )

    return {
        "split": split_name,
        "total_screens": len(rows),
        "totals": totals,
        "by_category": dict(stats),
        "errors": errors,
    }


def summarize_rules_on_parsed() -> dict:
    """Count R01-R20 rule hits across written components.json files."""
    if not PARSED_ROOT.is_dir():
        return {"error": "parsed root missing"}

    rule_counts: Counter[str] = Counter()
    screens_with: Counter[str] = Counter()
    stale = 0
    files = sorted(PARSED_ROOT.rglob("*_components.json"))
    for path in files:
        doc = json.loads(path.read_text(encoding="utf-8"))
        components = doc.get("components", [])
        if components and "focus_order" not in components[0]:
            stale += 1
        fired: set[str] = set()
        for violation in check_rules(doc)["violations"]:
            rule_counts[violation["rule_id"]] += 1
            fired.add(violation["rule_id"])
        for rule_id in fired:
            screens_with[rule_id] += 1

    r13_r20 = {
        f"R{index:02d}": {
            "violations": rule_counts.get(f"R{index:02d}", 0),
            "screens": screens_with.get(f"R{index:02d}", 0),
        }
        for index in range(13, 21)
    }
    return {
        "parsed_files": len(files),
        "stale_without_extended_fields": stale,
        "rules_r01_r20": {
            f"R{index:02d}": {
                "violations": rule_counts.get(f"R{index:02d}", 0),
                "screens": screens_with.get(f"R{index:02d}", 0),
            }
            for index in range(1, 21)
        },
        "rules_r13_r20": r13_r20,
        "zero_hit_rules": [
            f"R{index:02d}"
            for index in range(1, 21)
            if rule_counts.get(f"R{index:02d}", 0) == 0
        ],
    }


def main() -> int:
    print("=== MASC XML parsing sign-off (all splits, all categories) ===")
    split_reports = [check_split(name) for name in ("train", "val", "test")]

    all_totals = {
        "ok": 0,
        "empty": 0,
        "parse_error": 0,
        "missing": 0,
        "schema": 0,
        "extended_missing": 0,
    }
    for report in split_reports:
        for key in all_totals:
            all_totals[key] += report["totals"][key]

    rules_summary = summarize_rules_on_parsed()

    passed = not (
        all_totals["parse_error"]
        or all_totals["missing"]
        or all_totals["schema"]
        or all_totals["extended_missing"]
    )

    signoff = {
        "sign_off": "PASS" if passed else "ISSUES",
        "generated_at": datetime.now(timezone.utc).isoformat(),
        "dataset": "MASC",
        "parser_extension": "R13-R20 fields required on every component",
        "extended_parser_fields": list(EXTENDED_PARSER_FIELDS),
        "total_screens": sum(r["total_screens"] for r in split_reports),
        "categories": 10,
        "category_names": sorted(
            {cat for r in split_reports for cat in r["by_category"].keys()}
        ),
        "aggregate_totals": all_totals,
        "splits": {r["split"]: r for r in split_reports},
        "rules_on_parsed_json": rules_summary,
    }

    report_path = SIGNOFF_REPORT
    report_path.parent.mkdir(parents=True, exist_ok=True)
    report_path.write_text(json.dumps(signoff, indent=2), encoding="utf-8")

    print("\n--- Aggregate ---")
    print(
        f"  TOTAL      ok={all_totals['ok']:4d} empty={all_totals['empty']:3d} "
        f"errors={all_totals['parse_error']:3d} missing={all_totals['missing']:3d} "
        f"schema={all_totals['schema']:3d} ext_missing={all_totals['extended_missing']:3d}"
    )
    print("\n--- Rules R13-R20 on parsed JSON ---")
    for rule_id, counts in rules_summary.get("rules_r13_r20", {}).items():
        print(f"  {rule_id}: violations={counts['violations']:5d} screens={counts['screens']:4d}")
    print(f"\nSign-off report: {report_path.relative_to(PROJECT_ROOT)}")
    print(f"Full batch log:  {FULL_LOG.relative_to(PROJECT_ROOT)}")
    print("Overall:", signoff["sign_off"])
    return 0 if passed else 1


if __name__ == "__main__":
    raise SystemExit(main())
