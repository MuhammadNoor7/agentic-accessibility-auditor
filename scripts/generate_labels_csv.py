import os
from pathlib import Path
import csv

# ----------------------------------------------------------------------
# Configuration – adjust only if folder layout changes
# ----------------------------------------------------------------------
PROJECT_ROOT = r"d:/internship/agentic-accessibility-auditor"

# Folder containing the screenshot sub‑categories
SCREENSHOT_ROOT = os.path.join(PROJECT_ROOT, "data", "screenshots")

# Mapping from lower‑case sub‑folder name to the original category name (class)
CATEGORY_MAP = {
    "chat": "Chat",
    "home": "Home",
    "list": "List",
    "login": "Login",
    "maps": "Map",
    "menu": "Menu",
    "profile": "Profile",
    "settings": "Setting",
    "welcome": "Welcome",
    "search": "Search",
}

# Output CSV file (placed alongside the screenshots folder)
OUTPUT_CSV = Path(SCREENSHOT_ROOT) / "labels.csv"

def collect_labels():
    rows = []
    for subfolder, class_name in CATEGORY_MAP.items():
        folder_path = Path(SCREENSHOT_ROOT) / subfolder
        if not folder_path.is_dir():
            continue
        for img_file in folder_path.iterdir():
            if img_file.is_file() and img_file.suffix.lower() in {".jpg", ".png", ".jpeg"}:
                screen_id = img_file.stem  # filename without extension
                rows.append((screen_id, class_name))
    return rows

def main():
    rows = collect_labels()
    # Sort by screen id (numeric if possible) for a tidy CSV
    try:
        rows.sort(key=lambda r: int(r[0]))
    except ValueError:
        rows.sort(key=lambda r: r[0])

    with OUTPUT_CSV.open("w", newline="", encoding="utf-8") as csvfile:
        writer = csv.writer(csvfile)
        writer.writerow(["Screen Id", "class"])  # header
        writer.writerows(rows)

    print(f"[INFO] Labels CSV written to {OUTPUT_CSV}")
    print(f"[INFO] Total screenshots labelled: {len(rows)}")

if __name__ == "__main__":
    main()
