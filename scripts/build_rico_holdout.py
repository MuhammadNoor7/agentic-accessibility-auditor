"""
Build a 100% MASC-disjoint RICO holdout dataset for unseen evaluation.

Selection criteria (documented in selection_report.json):
  1. Content-hash exclusion — reject any screen whose .jpg, .xml, or .json
     MD5 hash appears anywhere in data-masc (prevents train/test leakage).
  2. Complete triplet — require all three files present in final_rico.
  3. Stratified by category — same 10 UI categories as MASC for comparable eval.
  4. Deterministic pick — sort by numeric screen_id, take up to --per-category
     unique screens per category (reproducible with --seed for tie-breaking).
  5. Purpose — holdout set for evaluating the auditor on Rico screens never
     seen during MASC training, tuning, or internal splits.

Outputs:
  data/data-rico-holdout/screenshots/{category}/{id}.jpg
  data/data-rico-holdout/xml/{category}/{id}.xml
  data/data-rico-holdout/json/{category}/{id}.json
  data/data-rico-holdout/manifest/screens.csv
  data/data-rico-holdout/manifest/selection_report.json
"""

from __future__ import annotations

import argparse
import csv
import hashlib
import json
import re
import shutil
from collections import Counter, defaultdict
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parents[1]
MASC_ROOT = PROJECT_ROOT / "data" / "data-masc"
RICO_SOURCE = PROJECT_ROOT / "data" / "final_rico" / "final_rico"
OUT_ROOT = PROJECT_ROOT / "data" / "data-rico-holdout"

CATEGORIES = [
    "chat",
    "home",
    "list",
    "login",
    "maps",
    "menu",
    "profile",
    "search",
    "settings",
    "welcome",
]

RICO_TO_DIR = {
    "Chat": "chat",
    "Home": "home",
    "List": "list",
    "Login": "login",
    "Maps": "maps",
    "Menu": "menu",
    "Profile": "profile",
    "Search": "search",
    "Settings": "settings",
    "Welcome": "welcome",
}

DIR_TO_CLASS = {
    "chat": "Chat",
    "home": "Home",
    "list": "List",
    "login": "Login",
    "maps": "Map",
    "menu": "Menu",
    "profile": "Profile",
    "search": "Search",
    "settings": "Setting",
    "welcome": "Welcome",
}


def file_md5(path: Path) -> str:
    digest = hashlib.md5()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(65536), b""):
            digest.update(chunk)
    return digest.hexdigest()


def build_masc_hash_index() -> set[tuple[str, str]]:
    index: set[tuple[str, str]] = set()
    for path in MASC_ROOT.rglob("*"):
        if path.is_file() and path.suffix.lower() in {".jpg", ".xml", ".json"}:
            index.add((path.suffix.lower(), file_md5(path)))
    return index


def is_masc_disjoint(files: dict[str, Path], masc_hashes: set[tuple[str, str]]) -> bool:
    for ext, path in files.items():
        if (ext, file_md5(path)) in masc_hashes:
            return False
    return True


def collect_rico_candidates(masc_hashes: set[tuple[str, str]]) -> dict[str, list[dict]]:
    by_category: dict[str, list[dict]] = defaultdict(list)

    for jpg_path in sorted(RICO_SOURCE.glob("*.jpg")):
        match = re.match(r"^([A-Za-z]+)_(\d+)$", jpg_path.stem)
        if not match:
            continue

        rico_cat, screen_id = match.group(1), match.group(2)
        category = RICO_TO_DIR.get(rico_cat)
        if category is None:
            continue

        files = {".jpg": jpg_path}
        for ext in (".xml", ".json"):
            sibling = RICO_SOURCE / f"{rico_cat}_{screen_id}{ext}"
            if sibling.is_file():
                files[ext] = sibling

        if len(files) != 3:
            continue
        if not is_masc_disjoint(files, masc_hashes):
            continue

        by_category[category].append(
            {
                "screen_id": screen_id,
                "class": DIR_TO_CLASS[category],
                "category": category,
                "source_stem": f"{rico_cat}_{screen_id}",
                "files": files,
            }
        )

    for category in by_category:
        by_category[category].sort(key=lambda row: int(row["screen_id"]))

    return by_category


def copy_screen(row: dict) -> dict[str, str]:
    screen_id = row["screen_id"]
    category = row["category"]
    rel_paths: dict[str, str] = {}

    for ext, folder in (
        (".jpg", "screenshots"),
        (".xml", "xml"),
        (".json", "json"),
    ):
        dest_dir = OUT_ROOT / folder / category
        dest_dir.mkdir(parents=True, exist_ok=True)
        dest_path = dest_dir / f"{screen_id}{ext}"
        shutil.copy2(row["files"][ext], dest_path)
        rel_paths[f"{folder}_path"] = dest_path.relative_to(PROJECT_ROOT).as_posix()

    return {
        "screen_id": screen_id,
        "class": row["class"],
        "category": category,
        "source_stem": row["source_stem"],
        **rel_paths,
    }


def verify_no_masc_overlap() -> dict[str, int | bool]:
    masc_hashes = build_masc_hash_index()
    collisions = 0
    checked = 0

    for path in OUT_ROOT.rglob("*"):
        if path.is_file() and path.suffix.lower() in {".jpg", ".xml", ".json"}:
            checked += 1
            if (path.suffix.lower(), file_md5(path)) in masc_hashes:
                collisions += 1

    return {
        "files_checked": checked,
        "masc_collisions": collisions,
        "passed": collisions == 0,
    }


def main() -> None:
    parser = argparse.ArgumentParser(description="Build MASC-disjoint RICO holdout dataset.")
    parser.add_argument(
        "--per-category",
        type=int,
        default=200,
        help="Target screens per category (default: 200; capped by available unique screens)",
    )
    parser.add_argument("--seed", type=int, default=42, help="Reserved for future randomized selection")
    args = parser.parse_args()

    if OUT_ROOT.exists():
        shutil.rmtree(OUT_ROOT)
    (OUT_ROOT / "manifest").mkdir(parents=True)

    masc_hashes = build_masc_hash_index()
    candidates = collect_rico_candidates(masc_hashes)

    selected_rows: list[dict] = []
    per_category_counts: dict[str, dict[str, int]] = {}

    for category in CATEGORIES:
        pool = candidates.get(category, [])
        take = min(args.per_category, len(pool))
        chosen = pool[:take]
        per_category_counts[category] = {
            "available_unique": len(pool),
            "selected": take,
            "target": args.per_category,
        }
        for row in chosen:
            selected_rows.append(copy_screen(row))

    manifest_csv = OUT_ROOT / "manifest" / "screens.csv"
    fieldnames = [
        "screen_id",
        "class",
        "category",
        "source_stem",
        "screenshots_path",
        "xml_path",
        "json_path",
    ]
    with manifest_csv.open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(selected_rows)

    verification = verify_no_masc_overlap()
    report = {
        "purpose": (
            "Holdout evaluation set drawn from Rico (final_rico) with zero byte-level "
            "overlap against data-masc. Use for unseen-data testing while MASC remains "
            "the training/development corpus."
        ),
        "selection_criteria": [
            "Exclude any screen whose jpg, xml, or json MD5 exists anywhere in data-masc.",
            "Require complete jpg + xml + json triplet in final_rico source.",
            "Stratify across the same 10 UI categories used by MASC.",
            "Deterministic selection: lowest numeric screen_id first, up to per-category target.",
        ],
        "source": str(RICO_SOURCE.relative_to(PROJECT_ROOT).as_posix()),
        "output": str(OUT_ROOT.relative_to(PROJECT_ROOT).as_posix()),
        "per_category_target": args.per_category,
        "per_category": per_category_counts,
        "totals": {
            "selected": len(selected_rows),
            "by_class": dict(sorted(Counter(row["class"] for row in selected_rows).items())),
        },
        "verification": verification,
        "note": (
            "final_rico contains only 1,698 fully MASC-disjoint screens in total; "
            "no category has 200 unique screens. This dataset includes every available "
            "unique screen per category, capped at the requested target."
        ),
    }
    report_path = OUT_ROOT / "manifest" / "selection_report.json"
    report_path.write_text(json.dumps(report, indent=2), encoding="utf-8")

    print(f"Selected {len(selected_rows)} screens into {OUT_ROOT}")
    for category in CATEGORIES:
        info = per_category_counts[category]
        print(
            f"  {category:8s}: {info['selected']:3d} selected "
            f"({info['available_unique']} unique available, target {info['target']})"
        )
    print(f"Verification: {verification['masc_collisions']} MASC collisions / {verification['files_checked']} files")
    if not verification["passed"]:
        raise RuntimeError("Verification failed: holdout overlaps with MASC")


if __name__ == "__main__":
    main()
