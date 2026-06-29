"""Sample MASC train split screens per category and validate parser output."""

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

REQUIRED_SCREEN = {"schema_version", "screen_id", "image_path", "xml_path", "components"}
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


def validate_doc(doc: dict) -> list[str]:
    issues: list[str] = []
    missing = REQUIRED_SCREEN - set(doc.keys())
    if missing:
        issues.append(f"missing screen fields: {missing}")
    comps = doc.get("components", [])
    if comps:
        c0 = comps[0]
        cm = REQUIRED_COMP - set(c0.keys())
        if cm:
            issues.append(f"missing component fields: {cm}")
        bounds = c0.get("bounds")
        if not (
            isinstance(bounds, list)
            and len(bounds) == 4
            and all(isinstance(x, int) for x in bounds)
        ):
            issues.append("bounds not [int,int,int,int]")
        for field in ("text", "content_desc", "resource_id"):
            if c0.get(field) is None:
                issues.append(f"{field} is null")
    return issues


def main() -> int:
    train_csv = PROJECT_ROOT / "data" / "data-masc" / "splits" / "train.csv"
    by_cat: dict[str, list[dict[str, str]]] = defaultdict(list)
    with train_csv.open(newline="", encoding="utf-8") as handle:
        for row in csv.DictReader(handle):
            by_cat[row["category"]].append(row)

    print("=== MASC train split parser check (3 samples per category) ===")
    print(f"Train rows total: {sum(len(v) for v in by_cat.values())}")
    print(f"Categories: {sorted(by_cat.keys())}\n")

    summary: list[dict] = []
    all_ok = True

    for category in sorted(by_cat.keys()):
        rows = by_cat[category][:3]
        cat_results: list[dict] = []
        for row in rows:
            xml_path = PROJECT_ROOT / row["xml_path"]
            img_path = PROJECT_ROOT / row["image_path"]
            rec: dict = {
                "screen_id": row["screen_id"],
                "category": category,
                "xml_path": row["xml_path"],
            }
            if not xml_path.is_file():
                rec["status"] = "MISSING_XML"
                all_ok = False
            elif not img_path.is_file():
                rec["status"] = "MISSING_SCREENSHOT"
                all_ok = False
            else:
                try:
                    components = parse_ui_xml(xml_path)
                    doc = build_components_document(
                        screen_id=f"screen_{row['screen_id']}",
                        image_path=row["image_path"],
                        xml_path=row["xml_path"],
                        components=components,
                    )
                    issues = validate_doc(doc)
                    rec["status"] = "OK" if not issues else "SCHEMA_ISSUE"
                    rec["components"] = len(components)
                    rec["issues"] = issues
                    if issues:
                        all_ok = False
                except Exception as exc:
                    rec["status"] = "PARSE_ERROR"
                    rec["error"] = str(exc)
                    all_ok = False
            cat_results.append(rec)
            suffix = ""
            if rec["status"] == "OK":
                suffix = f" ({rec['components']} components)"
            elif "error" in rec:
                suffix = f" — {rec['error']}"
            elif rec.get("issues"):
                suffix = f" — {rec['issues']}"
            print(f"  [{category}] screen {row['screen_id']}: {rec['status']}{suffix}")

        summary.append(
            {"category": category, "train_count": len(by_cat[category]), "samples": cat_results}
        )

    first_cat = sorted(by_cat.keys())[0]
    first_row = by_cat[first_cat][0]
    sample_xml = PROJECT_ROOT / first_row["xml_path"]
    sample_components = parse_ui_xml(sample_xml)
    sample_doc = build_components_document(
        screen_id=f"screen_{first_row['screen_id']}",
        image_path=first_row["image_path"],
        xml_path=first_row["xml_path"],
        components=sample_components[:2],
    )
    print("\n=== Sample components.json snippet (first 2 components) ===")
    print(json.dumps(sample_doc, indent=2))

    report_path = PROJECT_ROOT / "data" / "data-masc" / "parsed" / "train_category_check.json"
    report_path.parent.mkdir(parents=True, exist_ok=True)
    report_path.write_text(json.dumps(summary, indent=2), encoding="utf-8")
    print(f"\nReport saved: {report_path.relative_to(PROJECT_ROOT)}")
    print("Overall:", "PASS" if all_ok else "ISSUES FOUND")
    return 0 if all_ok else 1


def run_full_train() -> int:
    train_csv = PROJECT_ROOT / "data" / "data-masc" / "splits" / "train.csv"
    stats: dict[str, dict[str, int]] = defaultdict(
        lambda: {"ok": 0, "empty": 0, "parse_error": 0, "missing": 0}
    )
    errors: list[dict[str, str]] = []

    with train_csv.open(newline="", encoding="utf-8") as handle:
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
            else:
                build_components_document(
                    screen_id=f"screen_{row['screen_id']}",
                    image_path=row["image_path"],
                    xml_path=row["xml_path"],
                    components=components,
                )
                stats[category]["ok"] += 1
        except Exception as exc:
            stats[category]["parse_error"] += 1
            if len(errors) < 20:
                errors.append(
                    {
                        "screen": row["screen_id"],
                        "category": category,
                        "path": row["xml_path"],
                        "error": str(exc),
                    }
                )

    print("\n=== Full MASC train split parser run ===")
    print(f"Total train screens: {len(rows)}")
    totals = {"ok": 0, "empty": 0, "parse_error": 0, "missing": 0}
    for category in sorted(stats.keys()):
        cat_stats = stats[category]
        for key in totals:
            totals[key] += cat_stats[key]
        print(
            f"  {category:10s} ok={cat_stats['ok']:4d} "
            f"empty={cat_stats['empty']:3d} errors={cat_stats['parse_error']:3d} "
            f"missing={cat_stats['missing']:3d}"
        )
    print("---")
    print(
        f"  {'TOTAL':10s} ok={totals['ok']:4d} empty={totals['empty']:3d} "
        f"errors={totals['parse_error']:3d} missing={totals['missing']:3d}"
    )
    if errors:
        print("\nSample errors:")
        for item in errors:
            print(f"  {item}")

    report_path = PROJECT_ROOT / "data" / "data-masc" / "parsed" / "train_full_parse_report.json"
    report_path.write_text(
        json.dumps({"totals": totals, "by_category": dict(stats), "errors": errors}, indent=2),
        encoding="utf-8",
    )
    print(f"\nReport saved: {report_path.relative_to(PROJECT_ROOT)}")
    return 1 if totals["parse_error"] or totals["missing"] else 0


if __name__ == "__main__":
    import argparse

    ap = argparse.ArgumentParser()
    ap.add_argument("--full", action="store_true", help="Parse all train split screens")
    args = ap.parse_args()
    raise SystemExit(run_full_train() if args.full else main())
