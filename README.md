# Agentic Accessibility Auditor

An automated accessibility auditing tool for Android mobile UIs.  
Accepts a **screenshot + UIAutomator XML**, parses UI components, detects violations (R01–R30), maps them to guidelines (G01–G30), explains issues via an LLM, and generates HTML/PDF reports.

---

## Team

| Intern | Responsibilities |
|--------|------------------|
| **Intern 1** | Data collection, XML parsing, rule checker, Docker |
| **Intern 2** | JSON schemas, Figma design, React UI dashboard |
| **Intern 3 (Lead)** | Project lead, LLM agent layer, CNN (optional), report generation |

---

## Project Structure

All teammates should use **these paths** so pipeline outputs line up.

```
agentic-accessibility-auditor/
├── app.py                      # Streamlit demo (upload → parse → components.json)
├── requirements.txt
├── Dockerfile
├── docker-compose.yml
├── test_run.py                 # Parser smoke test
│
├── data/
│   ├── screenshots/            # Single-screen uploads & ADB captures (runtime)
│   ├── xml/                    # Matching UIAutomator XML per screen (runtime)
│   ├── parsed/                 # Stage 1 output: {screen}_components.json
│   │
│   ├── data-masc/              # Full MASC dataset (7,068 pairs) — local only, not in Git
│   │   ├── screenshots/{category}/
│   │   ├── xml/{category}/
│   │   ├── json/{category}/
│   │   ├── parsed/             # Batch parser output for MASC screens
│   │   └── splits/             # train.csv, val.csv, test.csv (70/15/15)
│   │
│   ├── final_rico/             # Raw Rico source (2,000 screens) — local only, not in Git
│   │   └── final_rico/         # Category_ID.jpg / .xml / .json (flat layout)
│   │
│   └── data-rico-holdout/      # MASC-disjoint Rico holdout (1,698 pairs) — unseen final testing
│       ├── screenshots/{category}/
│       ├── xml/{category}/
│       ├── json/{category}/
│       └── manifest/           # screens.csv, selection_report.json, sheet import CSV
│
├── outputs/
│   ├── violations/             # Stage 2 output: {screen}_violations.json
│   └── reports/                # Stage 4 output: audit_report.html / .pdf
│
├── src/
│   ├── schema_documents.py     # Build schema-compliant JSON envelopes
│   ├── report_generator.py     # HTML/PDF report (planned wiring)
│   └── templates/
│       └── report.html
│
├── scripts/                    # Dataset & utility scripts (see below)
│
└── docs/
    ├── accessibility_guidelines_report.md
    ├── json_schemas.md
    ├── qa_test_plan.md
    ├── schemas/auditor_schema.json
    ├── examples/               # Sample components.json, violations.json, report.json
    └── progress/               # Weekly notes per intern (merge at end of internship)
```

### Pipeline → folder mapping

| Stage | Producer | Output path | File pattern |
|-------|----------|-------------|--------------|
| Input | ADB / upload | `data/screenshots/`, `data/xml/` | `screen_001.png`, `window_001.xml` |
| 1 — Parser | Intern 1 | `data/parsed/` | `{name}_components.json` |
| 2 — Rule checker | Intern 1 | `outputs/violations/` | `{name}_violations.json` |
| 3 — Agent | Intern 3 | (enriches violations) | fields in final `report.json` |
| 4 — Report | Intern 3 | `outputs/reports/` | `audit_report.html`, `.pdf` |

**Naming rule:** Screenshot and XML for the same screen share the same base name (e.g. `screen_001.png` + `window_001.xml`).

---

## Dataset

**MASC (Mobile App Screenshots Corpus)** — training & development  
[Google Drive — MASC dataset](https://drive.google.com/file/d/1kx8qRbOtdQbbewZgfBTeCIj7lNvabFTF/view?usp=sharing)

**Rico holdout** — final unseen evaluation (filtered from `final_rico`, zero overlap with MASC)  
See [`docs/rico_holdout_dataset.md`](docs/rico_holdout_dataset.md) and (https://drive.google.com/file/d/1DmFb4vAanD8dnzv2HAg38YpGk7ReTwfv/view?usp=sharing) for the full filtering process.

| Dataset | Location | Split | Use |
|---------|----------|-------|-----|
| **MASC** | `data/data-masc/` | Train 70% / Val 15% / Test 15% | Development & tuning |
| **Rico holdout** | `data/data-rico-holdout/` | No split (100% held out) | **Final unseen evaluation only** |
| **final_rico** | `data/final_rico/final_rico/` | Source only (not for direct eval) | Raw Rico corpus; 302/2000 screens overlap MASC |

### How Rico holdout was filtered from `final_rico`

1. Hash every `.jpg`, `.xml`, and `.json` in both `data-masc` and `final_rico`.
2. **Reject** any `final_rico` screen if **any** of its three files matches a MASC file by MD5 (same bytes).
3. Keep only screens with a complete jpg + xml + json triplet.
4. Stratify across the same 10 categories as MASC; include all 1,698 remaining unique screens.

Verified: **0 byte-level collisions** with MASC across 5,094 holdout files.

Regenerate MASC splits:
```bash
python scripts/split_masc_dataset.py
```

Build Rico holdout from `final_rico`:
```bash
python scripts/build_rico_holdout.py
python scripts/build_rico_holdout_sheet.py
```

---

## Scripts (`scripts/`)

| Script | Purpose |
|--------|---------|
| `split_masc_dataset.py` | Create train/val/test CSVs for MASC |
| `build_rico_holdout.py` | Build MASC-disjoint holdout from `final_rico` |
| `build_rico_holdout_sheet.py` | Build Google Sheet import xlsx/csv for Rico holdout |
| `compare_datasets.py` | Compare MASC vs `final_rico` for content overlap |
| `convert_json-to-xml.py` | Convert MASC JSON hierarchies to XML |
| `generate_labels_csv.py` | Generate screenshot labels CSV |
| `copy_matched_jsons.py` | Copy matched JSON files into dataset folders |

---

## Local Setup

```bash
python -m venv venv
venv\Scripts\activate          # Windows
pip install -r requirements.txt
set GEMINI_API_KEY=your_key
streamlit run app.py
```

## Docker

```bash
docker-compose up --build
# http://localhost:8501
# Mounts ./data and ./outputs into the container
```

---

## Architecture

| Stage | Module | Output |
|-------|--------|--------|
| 1 | XML parser | `components.json` |
| 2 | Rule checker (R01–R30) | `violations.json` |
| 3 | Agent explanation layer | enriched `report.json` |
| 4 | Report generator | `audit_report.html` / PDF |

**Week 2 status:** Schema, guidelines, and parsing flow documented. Rule checker, agent, and full report pipeline are planned for later weeks.

---

## Documentation

| Doc | Description |
|-----|-------------|
| [`docs/windows_setup.md`](docs/windows_setup.md) | Windows install & onboarding (Linux → Windows) |
| [`docs/accessibility_guidelines_report.md`](docs/accessibility_guidelines_report.md) | G01–G30 guidelines, R01–R30 rules |
| [`docs/json_schemas.md`](docs/json_schemas.md) | JSON schemas between modules |
| [`docs/schemas/auditor_schema.json`](docs/schemas/auditor_schema.json) | Formal JSON Schema v1.0 |
| [`docs/qa_test_plan.md`](docs/qa_test_plan.md) | QA test cases & sign-off criteria |
| [`docs/rico_holdout_dataset.md`](docs/rico_holdout_dataset.md) | Rico holdout filtering, layout, and regeneration |
| [`docs/rico_holdout_dataset.md`](docs/rico_holdout_dataset.md) | Rico holdout filtering, layout, and regeneration |
| [`docs/examples/`](docs/examples/) | Sample JSON for all pipeline stages |
