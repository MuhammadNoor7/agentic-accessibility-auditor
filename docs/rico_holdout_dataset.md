# Rico Holdout Dataset (`data/data-rico-holdout`)

**Purpose:** Unseen evaluation set for final testing. MASC (`data/data-masc/`) is used for development, tuning, and internal train/val/test splits. Rico holdout must never overlap MASC at the file-content level.

**Source:** `data/final_rico/final_rico` (2,000 Rico screens: 200 per category × 10 categories)  
**Output:** `data/data-rico-holdout/` (1,698 screens after overlap removal)

---

## Why we built a holdout from `final_rico`

`final_rico` was derived from the Rico corpus for evaluation, but **302 of its 2,000 screens share screenshot and/or JSON content with `data-masc`**. Using `final_rico` as-is would leak training data into evaluation.

We filtered `final_rico` → `data-rico-holdout` so only **MASC-disjoint** screens remain.

---

## How overlap was detected

Script: `scripts/compare_datasets.py`

For every file in both datasets, we compute an MD5 hash of the raw bytes and compare:

| File type | Overlap in `final_rico` vs MASC |
|-----------|----------------------------------|
| `.jpg` (screenshot) | 302 / 2,000 |
| `.json` | 301 / 2,000 |
| `.xml` | 0 / 2,000 |

A screen is **rejected** if **any** of its three files (jpg, xml, or json) has a matching hash anywhere in `data-masc`, regardless of filename or category folder.

**Result:** 1,698 screens pass (zero hash collisions verified across 5,094 files).

---

## How `data-rico-holdout` was built

Script: `scripts/build_rico_holdout.py`

### Selection criteria

1. **Content-hash exclusion** — reject any screen whose `.jpg`, `.xml`, or `.json` MD5 exists anywhere in `data-masc`.
2. **Complete triplet** — require all three files present in `final_rico`.
3. **Stratified by category** — same 10 UI categories as MASC (Chat, Home, List, Login, Map, Menu, Profile, Search, Setting, Welcome).
4. **Deterministic pick** — sort by numeric `screen_id`, take lowest IDs first (reproducible).

### Per-category counts (all unique screens included)

| Category | Selected |
|----------|----------|
| Menu | 181 |
| Login | 161 |
| Home | 188 |
| Setting | 164 |
| Search | 178 |
| List | 172 |
| Map | 155 |
| Chat | 167 |
| Welcome | 167 |
| Profile | 165 |
| **Total** | **1,698** |

`final_rico` does not contain 200 MASC-disjoint screens per category, so every available unique screen was included.

### Output layout

```
data/data-rico-holdout/
├── screenshots/{category}/{id}.jpg
├── xml/{category}/{id}.xml
├── json/{category}/{id}.json
└── manifest/
    ├── screens.csv
    ├── selection_report.json
    └── rico_holdout_dataset_import.csv
```

### Regenerate

```bash
python scripts/build_rico_holdout.py
python scripts/build_rico_holdout_sheet.py
```

---

## Google Sheet import

Script: `scripts/build_rico_holdout_sheet.py`

Generates a 3-column import file: **Category | Screenshot | Xml**

- Import per-category xlsx from `manifest/category_sheets/` into Google Sheets (images visible).
- Do **not** import the full 32 MB combined xlsx or the `.csv` into Google Sheets if you need embedded screenshots.

---

## Train vs eval split (team reference)

| Dataset | Use |
|---------|-----|
| `data/data-masc/` (train 70% / val 15% / test 15%) | Development, tuning, internal regression |
| `data/data-rico-holdout/` (no split, 100% held out) | **Final unseen evaluation only** |
| `data/final_rico/` | Source corpus only — do not use directly for eval without filtering |
