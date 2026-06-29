# Agentic Accessibility Auditor

An automated accessibility auditing tool for Android mobile UIs.  
Accepts a **screenshot + UIAutomator XML**, parses UI components, detects violations (R01–R30), maps them to guidelines (G01–G30), explains issues via an LLM, and generates HTML/PDF reports.

**Branch `azeem` (Intern 1):** Stage 1 parser pipeline — hybrid XML parsing, batch runner, schema validation, Docker.

---

## Team

| Intern | Branch | Responsibilities |
|--------|--------|------------------|
| **Azeem (Intern 1)** | `azeem` | Data collection, XML parsing, rule checker, Docker |
| **Ayesha (Intern 2)** | `ayesha` | JSON schemas, Figma design, React UI dashboard |
| **Noor (Intern 3, Lead)** | `noor` | Project lead, LLM agent layer, CNN (optional), report generation |

---

## Project structure

All teammates should use **these paths** so pipeline outputs line up.

```
agentic-accessibility-auditor/
├── app.py                      # Streamlit demo (upload + batch parse)
├── test_run.py                 # Batch / single-file parser runner
├── requirements.txt
├── Dockerfile
├── docker-compose.yml
│
├── backend/                    # FastAPI service (Docker)
│   ├── Dockerfile
│   ├── main.py
│   └── requirements.txt
│
├── src/
│   ├── parser.py               # Hybrid Android UI XML → components.json
│   ├── schema_documents.py     # Schema constants + build_components_document()
│   └── report_generator.py     # HTML/PDF report (planned wiring)
│
├── scripts/
│   ├── validate_output.py      # Validate JSON against auditor_schema.json
│   ├── split_masc_dataset.py   # MASC train/val/test splits
│   ├── build_rico_holdout.py   # Build MASC-disjoint Rico holdout
│   └── …                       # Other dataset utilities
│
├── data/
│   ├── screenshots/            # Single-screen uploads (runtime)
│   ├── xml/                      # Uploaded UIAutomator XML (any app)
│   ├── parsed/                   # Generic upload output
│   ├── data-masc/                # MASC dataset (local raw + tracked parsed/splits)
│   ├── data-rico-holdout/        # Rico holdout (local raw + tracked parsed/manifest)
│   └── final_rico/               # Raw Rico source (local only)
│
├── outputs/
│   ├── violations/             # Stage 2: {screen}_violations.json (planned)
│   └── reports/                  # Stage 4: audit_report.html / .pdf (planned)
│
└── docs/
    ├── accessibility_guidelines_report.md
    ├── json_schemas.md
    ├── qa_test_plan.md
    ├── rico_holdout_dataset.md
    ├── windows_setup.md
    ├── schemas/auditor_schema.json
    ├── examples/
    └── progress/
```

### Pipeline → folder mapping

| Stage | Producer | Output path | File pattern |
|-------|----------|-------------|--------------|
| Input | ADB / upload | `data/screenshots/`, `data/xml/` | `{category}/{id}.jpg` + `.xml` |
| 1 — Parser | Intern 1 | `data/parsed/` or `data/data-masc/parsed/` or `data/data-rico-holdout/parsed/` | `{id}_components.json` |
| 2 — Rule checker | Intern 1 | `outputs/violations/` | `{screen}_violations.json` |
| 3 — Agent | Intern 3 | (enriches violations) | fields in final `report.json` |
| 4 — Report | Intern 3 | `outputs/reports/` | `audit_report.html`, `.pdf` |

**Naming rule:** Screenshot and XML for the same screen share the same base name (e.g. `chat/49879.jpg` + `chat/49879.xml`).

---

## Parser (Stage 1 — implemented)

`src/parser.py` is a **hybrid parser** — one pass over any Android UI XML dump:

| Format | How it is detected |
|--------|-------------------|
| **UIAutomator** | `<node class="..." bounds="[x,y][x,y]">` |
| **MASC** | UIAutomator nodes + `<wrapper>` child bounds |
| **Rico** | Layout tags (`LinearLayout`, `TextView`, …) with space-separated bounds |
| **Generic upload** | Any element with `class` or widget tag + bounds |

**Resilience:** null-byte sanitization, TC-01 missing-bounds handling, screenshot paths inferred (images not parsed).

---

## Quick start

```bash
python -m venv venv
venv\Scripts\activate          # Windows
pip install -r requirements.txt
```

### Parse XML

```bash
python test_run.py                                          # MASC batch
python test_run.py data/data-masc/xml/chat/49879.xml        # single file
python test_run.py --dataset rico --max-files 4             # Rico smoke test
python test_run.py --dataset upload                         # generic uploads in data/xml/
python scripts/validate_output.py                           # schema check
```

### Streamlit demo

```bash
streamlit run app.py
```

Upload XML in the main panel, or run batch parse from the sidebar.

### Docker

```bash
docker-compose up --build
# Backend API: http://localhost:8000
```

---

## Dataset

**MASC** — [Google Drive](https://drive.google.com/file/d/1kx8qRbOtdQbbewZgfBTeCIj7lNvabFTF/view?usp=sharing)  
**Rico holdout** — see [`docs/rico_holdout_dataset.md`](docs/rico_holdout_dataset.md)

| Dataset | Location | Use |
|---------|----------|-----|
| **MASC** | `data/data-masc/` | Development & tuning (70/15/15 split in `splits/`) |
| **Rico holdout** | `data/data-rico-holdout/` | Final unseen evaluation only |
| **final_rico** | `data/final_rico/` | Raw source corpus (not for direct eval) |
| **Uploads** | `data/xml/` + `data/screenshots/` | Any new app / unknown screen |

Regenerate splits / holdout:

```bash
python scripts/split_masc_dataset.py
python scripts/build_rico_holdout.py
python scripts/build_rico_holdout_sheet.py
```

---

## Scripts (`scripts/`)

| Script | Purpose |
|--------|---------|
| `validate_output.py` | Validate `components.json` against JSON Schema |
| `split_masc_dataset.py` | Create train/val/test CSVs for MASC |
| `build_rico_holdout.py` | Build MASC-disjoint holdout from `final_rico` |
| `build_rico_holdout_sheet.py` | Google Sheet import for Rico holdout |
| `compare_datasets.py` | Compare MASC vs `final_rico` overlap |
| `check_train_parser.py` | Sample MASC train screens & validate parser output |
| `convert_json-to-xml.py` | Convert MASC JSON hierarchies to XML |
| `generate_labels_csv.py` | Generate screenshot labels CSV |
| `copy_matched_jsons.py` | Copy matched JSON files into dataset folders |

---

## Architecture & status

| Stage | Module | Output | Status |
|-------|--------|--------|--------|
| 1 | XML parser | `components.json` | **Done** |
| 2 | Rule checker (R01–R30) | `violations.json` | Planned |
| 3 | Agent explanation layer | enriched `report.json` | Planned (Intern 3) |
| 4 | Report generator | `audit_report.html` / PDF | Planned (Intern 3) |

---

## Documentation

| Doc | Description |
|-----|-------------|
| [`docs/windows_setup.md`](docs/windows_setup.md) | Windows install & onboarding |
| [`docs/accessibility_guidelines_report.md`](docs/accessibility_guidelines_report.md) | G01–G30 guidelines, R01–R30 rules |
| [`docs/json_schemas.md`](docs/json_schemas.md) | JSON schemas between modules |
| [`docs/schemas/auditor_schema.json`](docs/schemas/auditor_schema.json) | Formal JSON Schema v1.0 |
| [`docs/qa_test_plan.md`](docs/qa_test_plan.md) | QA test cases & sign-off criteria |
| [`docs/rico_holdout_dataset.md`](docs/rico_holdout_dataset.md) | Rico holdout filtering & layout |
| [`docs/examples/`](docs/examples/) | Sample JSON for all pipeline stages |

---

## What not to commit

- Raw datasets: `data/data-masc/xml|screenshots|json/`, `data/data-rico-holdout/xml|screenshots|json/`, `data/final_rico/`
- Runtime uploads: `data/parsed/`, `data/xml/`, `data/screenshots/`
- Generated: `outputs/`, `.venv/`, `__pycache__/`, `.env`

**Tracked on `azeem` branch:** `data/data-masc/parsed/`, `data/data-masc/splits/`, `data/data-rico-holdout/parsed/`, `data/data-rico-holdout/manifest/*.csv` + `*.json`
