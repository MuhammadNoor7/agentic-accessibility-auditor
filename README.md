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
├── app.py                      # Streamlit demo (parse XML → components.json)
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
│   └── schema_documents.py     # Schema constants + build_components_document()
│
├── scripts/
│   └── validate_output.py      # Validate JSON against auditor_schema.json
│
├── data/                       # Local only — not committed to Git
│   ├── screenshots/            # Single-screen uploads (runtime)
│   ├── xml/                    # Uploaded UIAutomator XML (any app)
│   ├── parsed/                 # Generic upload output
│   │
│   ├── data-masc/              # MASC dataset (7,068 pairs)
│   │   ├── screenshots/{category}/
│   │   ├── xml/{category}/
│   │   ├── json/{category}/
│   │   ├── parsed/{category}/  # {id}_components.json
│   │   └── splits/             # train.csv, val.csv, test.csv (70/15/15)
│   │
│   └── data-rico-holdout/      # Rico holdout (1,698 pairs) — unseen final eval
│       ├── screenshots/{category}/
│       ├── xml/{category}/
│       ├── json/{category}/
│       └── parsed/{category}/  # {id}_components.json
│
├── outputs/
│   ├── violations/             # Stage 2: {screen}_violations.json (planned)
│   └── reports/                # Stage 4: audit_report.html / .pdf (planned)
│
└── docs/
    ├── accessibility_guidelines_report.md
    ├── json_schemas.md
    ├── qa_test_plan.md
    ├── rico_holdout_dataset.md
    ├── windows_setup.md
    ├── schemas/auditor_schema.json
    └── examples/               # Sample components.json, violations.json, report.json
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

## Parser (Stage 1 — implemented on `azeem`)

`src/parser.py` is a **hybrid parser** — one pass over any Android UI XML dump:

| Format | How it is detected |
|--------|-------------------|
| **UIAutomator** | `<node class="..." bounds="[x,y][x,y]">` |
| **MASC** | UIAutomator nodes + `<wrapper>` child bounds |
| **Rico** | Layout tags (`LinearLayout`, `TextView`, …) with space-separated bounds |
| **Generic upload** | Any element with `class` or widget tag + bounds |

**Resilience:**

- Null bytes in XML are stripped before parse (e.g. `chat/49879.xml`).
- Missing bounds on UIAutomator nodes → `[0,0,0,0]` (TC-01, no crash).
- Missing bounds on layout elements → skipped.

Screenshots are **referenced by path only** — the parser does not read image files.

---

## Quick start

```bash
python -m venv venv
venv\Scripts\activate          # Windows
pip install -r requirements.txt
```

### Parse XML

```bash
# MASC (default dataset)
python test_run.py

# Single file
python test_run.py data/data-masc/xml/chat/49879.xml

# Rico holdout (smoke test — limit files)
python test_run.py --dataset rico --max-files 4

# Generic uploaded XML (any app — place files in data/xml/)
python test_run.py --dataset upload

# Validate outputs against JSON Schema
python scripts/validate_output.py
```

### Streamlit demo

```bash
streamlit run app.py
```

Upload an XML file or run the batch parser from the sidebar.

### Docker

```bash
docker-compose up --build
# Backend API: http://localhost:8000
# Parser batch runs via auditor service (MASC by default)
```

---

## Dataset

**MASC (Mobile App Screenshots Corpus)** — training & development  
[Google Drive — MASC dataset](https://drive.google.com/file/d/1kx8qRbOtdQbbewZgfBTeCIj7lNvabFTF/view?usp=sharing)

**Rico holdout** — final unseen evaluation (filtered from `final_rico`, zero overlap with MASC)  
See [`docs/rico_holdout_dataset.md`](docs/rico_holdout_dataset.md).

| Dataset | Location | Split | Use |
|---------|----------|-------|-----|
| **MASC** | `data/data-masc/` | Train 70% / Val 15% / Test 15% | Development & tuning |
| **Rico holdout** | `data/data-rico-holdout/` | No split (100% held out) | **Final unseen evaluation only** |
| **Uploads** | `data/xml/` + `data/screenshots/` | N/A | Any new screen / unknown app |

Download datasets locally; they are listed in `.gitignore` and are **not** pushed to GitHub.

---

## Architecture & status

| Stage | Module | Output | Status on `azeem` |
|-------|--------|--------|-------------------|
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

- `data/data-masc/`, `data/data-rico-holdout/`, `data/parsed/`
- `outputs/` (generated violations, reports)
- `.venv/`, `__pycache__/`, `.env`
