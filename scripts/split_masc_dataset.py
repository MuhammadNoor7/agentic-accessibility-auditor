"""
Create stratified train / val / test splits for the full MASC dataset (7,068 screens).

Use MASC splits for development and internal regression only.
OneExample (data/data-oneexample/, 266 screens) is held out for unseen final evaluation.

Pairs each screenshot (data/data-masc/screenshots/<category>/<id>.jpg)
with its XML (data/data-masc/xml/<category>/<id>.xml) using labels.csv.

Outputs:
  data/data-masc/splits/train.csv
  data/data-masc/splits/val.csv
  data/data-masc/splits/test.csv
  data/data-masc/splits/split_summary.json
"""

from __future__ import annotations

import argparse
import csv
import json
import random
from collections import Counter, defaultdict
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parents[1]
DATA_ROOT = PROJECT_ROOT / "data" / "data-masc"
SCREENSHOT_ROOT = DATA_ROOT / "screenshots"
XML_ROOT = DATA_ROOT / "xml"
LABELS_CSV = SCREENSHOT_ROOT / "labels.csv"
OUT_DIR = DATA_ROOT / "splits"

CATEGORY_DIRS = [
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


def collect_pairs() -> list[dict[str, str]]:
    """Collect every screenshot/XML pair on disk (7068 total).

    Some screen IDs appear in more than one category folder, so we key by
    (category, screen_id) rather than screen_id alone.
    """
    pairs: list[dict[str, str]] = []
    missing_xml: list[str] = []

    for category in CATEGORY_DIRS:
        screen_class = DIR_TO_CLASS[category]
        screenshot_dir = SCREENSHOT_ROOT / category
        if not screenshot_dir.is_dir():
            continue

        for image_path in sorted(screenshot_dir.glob("*.jpg")):
            screen_id = image_path.stem
            xml_path = XML_ROOT / category / f"{screen_id}.xml"
            if not xml_path.is_file():
                missing_xml.append(str(xml_path))
                continue

            pairs.append(
                {
                    "screen_id": screen_id,
                    "class": screen_class,
                    "category": category,
                    "image_path": image_path.relative_to(PROJECT_ROOT).as_posix(),
                    "xml_path": xml_path.relative_to(PROJECT_ROOT).as_posix(),
                }
            )

    if missing_xml:
        raise FileNotFoundError(f"Missing {len(missing_xml)} XML files. Example: {missing_xml[0]}")

    return pairs


def stratified_split(
    pairs: list[dict[str, str]],
    train_ratio: float,
    val_ratio: float,
    test_ratio: float,
    seed: int,
) -> tuple[list[dict[str, str]], list[dict[str, str]], list[dict[str, str]]]:
    total = train_ratio + val_ratio + test_ratio
    if abs(total - 1.0) > 1e-6:
        raise ValueError("train_ratio + val_ratio + test_ratio must equal 1.0")

    by_class: dict[str, list[dict[str, str]]] = defaultdict(list)
    for pair in pairs:
        by_class[pair["class"]].append(pair)

    rng = random.Random(seed)
    train: list[dict[str, str]] = []
    val: list[dict[str, str]] = []
    test: list[dict[str, str]] = []

    for screen_class in sorted(by_class):
        items = by_class[screen_class][:]
        rng.shuffle(items)
        n = len(items)
        n_train = int(n * train_ratio)
        n_val = int(n * val_ratio)
        n_test = n - n_train - n_val

        train.extend(items[:n_train])
        val.extend(items[n_train : n_train + n_val])
        test.extend(items[n_train + n_val :])

        if n_test < 0:
            raise RuntimeError(f"Invalid split sizes for class {screen_class}")

    for bucket in (train, val, test):
        bucket.sort(key=lambda row: (row["class"], int(row["screen_id"])))

    return train, val, test


def write_csv(path: Path, rows: list[dict[str, str]]) -> None:
    fieldnames = ["screen_id", "class", "category", "image_path", "xml_path"]
    with path.open("w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(rows)


def summarize(rows: list[dict[str, str]]) -> dict[str, int]:
    return dict(sorted(Counter(row["class"] for row in rows).items()))


def main() -> None:
    parser = argparse.ArgumentParser(description="Split MASC dataset into train/val/test.")
    parser.add_argument("--train", type=float, default=0.70, help="Train ratio (default: 0.70)")
    parser.add_argument("--val", type=float, default=0.15, help="Validation ratio (default: 0.15)")
    parser.add_argument("--test", type=float, default=0.15, help="Test ratio (default: 0.15)")
    parser.add_argument("--seed", type=int, default=42, help="Random seed (default: 42)")
    args = parser.parse_args()

    pairs = collect_pairs()
    train, val, test = stratified_split(pairs, args.train, args.val, args.test, args.seed)

    OUT_DIR.mkdir(parents=True, exist_ok=True)
    write_csv(OUT_DIR / "train.csv", train)
    write_csv(OUT_DIR / "val.csv", val)
    write_csv(OUT_DIR / "test.csv", test)

    summary = {
        "total_pairs": len(pairs),
        "ratios": {"train": args.train, "val": args.val, "test": args.test},
        "seed": args.seed,
        "counts": {
            "train": len(train),
            "val": len(val),
            "test": len(test),
        },
        "class_counts": {
            "train": summarize(train),
            "val": summarize(val),
            "test": summarize(test),
        },
    }
    (OUT_DIR / "split_summary.json").write_text(json.dumps(summary, indent=2), encoding="utf-8")

    print(f"Total pairs: {len(pairs)}")
    print(f"Train: {len(train)}  Val: {len(val)}  Test: {len(test)}")
    print(f"Wrote splits to {OUT_DIR}")


if __name__ == "__main__":
    main()
