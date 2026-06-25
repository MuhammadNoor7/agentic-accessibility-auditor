"""Compare data-masc and final_rico for overlap."""
import csv
import hashlib
import re
from collections import defaultdict
from pathlib import Path

BASE = Path(__file__).resolve().parents[1] / "data"
MASC = BASE / "data-masc"
RICO = BASE / "final_rico" / "final_rico"


def file_md5(path: Path) -> str:
    h = hashlib.md5()
    with open(path, "rb") as f:
        for chunk in iter(lambda: f.read(65536), b""):
            h.update(chunk)
    return h.hexdigest()


def build_hash_index(root: Path, exts: set[str]) -> dict[tuple[str, str], list[Path]]:
    idx: dict[tuple[str, str], list[Path]] = defaultdict(list)
    for p in root.rglob("*"):
        if p.is_file() and p.suffix.lower() in exts:
            idx[(p.suffix.lower(), file_md5(p))].append(p)
    return idx


def main() -> None:
    print("Indexing MASC...")
    masc_idx = build_hash_index(MASC, {".jpg", ".xml", ".json"})

    rico_screens: dict[tuple[str, str], dict[str, Path]] = defaultdict(dict)
    for p in RICO.rglob("*"):
        if not p.is_file() or p.suffix.lower() not in {".jpg", ".xml", ".json"}:
            continue
        m = re.match(r"^([A-Za-z]+)_(\d+)$", p.stem)
        if m:
            rico_screens[(m.group(1).lower(), m.group(2))][p.suffix.lower()] = p

    results = {
        "jpg_match": 0,
        "xml_match": 0,
        "json_match": 0,
        "all_three_match": 0,
        "any_match": 0,
        "no_match": 0,
        "jpg_only": 0,
        "jpg_json": 0,
        "jpg_xml": 0,
    }

    def find_masc_match(rpath: Path) -> list[Path]:
        ext = rpath.suffix.lower()
        return masc_idx.get((ext, file_md5(rpath)), [])

    for _key, files in rico_screens.items():
        jpg_m = xml_m = json_m = False
        if ".jpg" in files:
            jpg_m = len(find_masc_match(files[".jpg"])) > 0
        if ".xml" in files:
            xml_m = len(find_masc_match(files[".xml"])) > 0
        if ".json" in files:
            json_m = len(find_masc_match(files[".json"])) > 0

        if jpg_m:
            results["jpg_match"] += 1
        if xml_m:
            results["xml_match"] += 1
        if json_m:
            results["json_match"] += 1
        if jpg_m and xml_m and json_m:
            results["all_three_match"] += 1
        if jpg_m or xml_m or json_m:
            results["any_match"] += 1
        else:
            results["no_match"] += 1
        if jpg_m and not xml_m and not json_m:
            results["jpg_only"] += 1
        if jpg_m and json_m and not xml_m:
            results["jpg_json"] += 1
        if jpg_m and xml_m and not json_m:
            results["jpg_xml"] += 1

    total = len(rico_screens)
    print(f"\nTotal RICO screens: {total}")
    print("Content overlap (RICO file exists identically somewhere in MASC):")
    for label, key in [
        ("Screenshot (.jpg)", "jpg_match"),
        ("JSON", "json_match"),
        ("XML", "xml_match"),
        ("All 3 identical", "all_three_match"),
        ("Any file matches", "any_match"),
        ("Completely unique", "no_match"),
    ]:
        n = results[key]
        print(f"  {label}: {n} ({100 * n / total:.1f}%)")
    print(f"  JPG only (no json/xml match): {results['jpg_only']}")
    print(f"  JPG+JSON (no xml): {results['jpg_json']}")
    print(f"  JPG+XML (no json): {results['jpg_xml']}")

    train_ids: set[tuple[str, str]] = set()
    val_ids: set[tuple[str, str]] = set()
    test_ids: set[tuple[str, str]] = set()
    for split, target in [
        ("train.csv", train_ids),
        ("val.csv", val_ids),
        ("test.csv", test_ids),
    ]:
        with open(MASC / "splits" / split, encoding="utf-8") as f:
            for row in csv.DictReader(f):
                target.add((row["category"].lower(), row["screen_id"]))

    rico_keys = set(rico_screens.keys())
    print("\nMASC split overlap with RICO (by category+screen_id):")
    print(f"  In train split: {len(rico_keys & train_ids)}")
    print(f"  In val split:   {len(rico_keys & val_ids)}")
    print(f"  In test split:  {len(rico_keys & test_ids)}")
    print(f"  In any MASC split: {len(rico_keys & (train_ids | val_ids | test_ids))}")


if __name__ == "__main__":
    main()
