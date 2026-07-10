# Agentic Accessibility Auditor (Axion)

Automated accessibility auditing for **Android mobile UIs**.  
Feed the pipeline a **screenshot + UIAutomator XML** → get schema-compliant `components.json`, rule-based `violations.json`, LLM-enriched explanations, and HTML/PDF reports mapped to **G01–G30** guidelines and **R01–R30** detection rules.

**Current integration branch:** [`noor`](https://github.com/MuhammadNoor7/agentic-accessibility-auditor/tree/noor) — parser + rules **R01–R30**, agent report API, React UI scaffold (mock data), **94 pytest** (9 Jul 2026).

---

## Team & branches

| Intern | Branch | Focus |
|--------|--------|-------|
| **Salar** | [`salar`](https://github.com/MuhammadNoor7/agentic-accessibility-auditor/tree/salar) | Data, hybrid XML parser, rule checker, Docker, Stage 3 explainer |
| **Ayesha** | [`ayesha`](https://github.com/MuhammadNoor7/agentic-accessibility-auditor/tree/ayesha) | JSON schemas, Figma, React dashboard (auth + app pages) |
| **Noor (Lead)** | [`noor`](https://github.com/MuhammadNoor7/agentic-accessibility-auditor/tree/noor) | Agent/API wiring, reports, QA, coordination, R13–R30 ownership |

---

## Project documentation

| Document | Path |
|----------|------|
| **SRS v2.0** | [`srs/SRS_Agentic_Accessibility_Auditor_v2.0.md`](srs/SRS_Agentic_Accessibility_Auditor_v2.0.md) |
| **SDS v2.2** | [`sds/SDS_Agentic_Accessibility_Auditor_v2.0.md`](sds/SDS_Agentic_Accessibility_Auditor_v2.0.md) |
| **8-week plan** | [`updated_plan.md`](updated_plan.md) · [`docs/updated_plan_v2.0.docx`](docs/updated_plan_v2.0.docx) |
| **Progress report** | [`docs/progress/Supplementary_Progress_Report_v1.0.md`](docs/progress/Supplementary_Progress_Report_v1.0.md) (+ formatted DOCX in same folder) |
| **Figma screenshots** | `docs/assets/figma/` |

Formatted Word exports live in `srs/`, `sds/`, and `docs/progress/`.

---

## Pipeline status (`noor`, 9 Jul 2026)

```
Screenshot + XML  →  Parser  →  Rule checker  →  Agent  →  Report
                      │              │              │          │
               components.json  violations.json  report.json  HTML/PDF
```

| Stage | Owner | Output | Status |
|-------|-------|--------|--------|
| 1 — Parser | Salar / Noor | `components.json` | **Done** — 7,068 MASC screens; R13–R20 fields + visibility |
| 2 — Rules | Salar / Noor | `violations.json` | **R01–R30** in `check()`; R09/R28 limited without colors/text-size |
| 3 — Agent | Noor / Salar | enriched `report.json` | **Done** — `GET /api/v1/audit/{id}/report` (template or live LLM) |
| 4 — Report | Noor | HTML/PDF | Planned (`src/report.py`) |
| UI — Axion | Ayesha | React dashboard | **Scaffold** — `frontend/` (mock data; not API-wired) |
| API | Noor | FastAPI | **Partial** — violations + report; no auth/records/download |

**MASC sign-off (Jul 2026):** 640,563 components · 462,542 violations (R01–R20 baseline) · 0 parse errors — see `data/data-masc/parsed/masc_parse_signoff_report.json`.

**Demo (no live LLM):** `uvicorn backend.main:app --reload --port 8000` then `POST /api/v1/audit?use_llm=false` with an XML fixture → `GET …/report`.

---

## Project layout

```
agentic-accessibility-auditor/
├── app.py                  # Streamlit: upload XML + violations preview
├── test_run.py             # CLI batch parse + rules
├── requirements.txt
├── .env.example            # LLM_PROVIDER + API keys
├── conftest.py
│
├── src/
│   ├── parser.py           # Hybrid XML → components.json
│   ├── rules.py            # R01–R30 rule checker
│   ├── agent.py            # Score + build_audit_report (API-wired)
│   ├── explainer.py        # Live LLM recommendations
│   ├── guidelines.py       # G01–G30 + R→G mapping
│   ├── llm_providers.py    # Anthropic / OpenAI / Gemini / Groq
│   └── schema_documents.py
│
├── backend/                # FastAPI gateway
│   ├── main.py
│   └── routers/audit.py    # POST /audit → GET …/violations + …/report
│
├── frontend/               # Axion React UI (Vite + React 19 + Tailwind 4; mock data)
│
├── tests/                  # 94 pytest (parser, rules, agent, audit, explainer)
│   ├── test_parser.py
│   ├── test_rules.py
│   ├── test_agent.py
│   ├── test_audit.py
│   ├── test_explainer.py
│   └── fixtures/rules/
│
├── scripts/
│   ├── validate_output.py
│   ├── noor_week3_validate.py
│   ├── masc_parse_signoff.py
│   ├── run_explainer_sample.py
│   ├── compare_visibility_filter_impact.py
│   ├── split_masc_dataset.py
│   └── build_rico_holdout.py
│
├── notebooks/
│   └── masc_dataset_analysis.ipynb
│
├── data/
│   ├── data-masc/          # 7,068 screens — parsed JSON tracked on noor
│   ├── data-rico-holdout/  # 1,698-screen unseen eval
│   ├── xml/ / screenshots/ / parsed/   # Generic uploads
│   └── final_rico/
│
├── outputs/
│   ├── violations/         # Stage 2 outputs
│   ├── reports/            # Stage 3 report.json (Week 4)
│   └── validation_logs/    # week3 + noor_week3 + masc_reparse logs
│
├── docs/                   # Schemas, guidelines, QA plan, progress report
├── srs/                    # SRS v2.0
└── sds/                    # SDS v2.2
```

### Where parser output goes

| Input | Parser output |
|-------|----------------|
| `data/xml/{screen}.xml` | `data/parsed/{screen}_components.json` |
| `data/data-masc/xml/{cat}/{id}.xml` | `data/data-masc/parsed/{cat}/{id}_components.json` |
| `data/data-rico-holdout/xml/{cat}/{id}.xml` | `data/data-rico-holdout/parsed/{cat}/{id}_components.json` |

**Naming:** screenshot and XML for the same screen share the same stem (e.g. `chat/49879.jpg` + `chat/49879.xml`).

---

## Hybrid parser (Stage 1)

`src/parser.py` handles **any Android UI hierarchy XML** in a single pass:

| Format | Recognition |
|--------|-------------|
| UIAutomator | `<node class="…" bounds="[l,t][r,b]">` |
| MASC | UIAutomator nodes + `<wrapper>` numeric bounds (depth-first into wrappers) |
| Rico | Widget tags (`LinearLayout`, `TextView`, …) + space-separated bounds |
| Generic upload | Any element with `class` / widget tag + bounds |

**R13–R20 extended fields** (Jul 2026): `focus_order`, `parent_id`, `long_clickable`, `scrollable`, `selected`, `checked`, `password`, `text_all_caps`, `input_type`, `important_for_accessibility`, `media_type`, `is_dialog`, `label_for`.

**Built-in resilience**

- Strips null bytes before parse (e.g. corrupt `chat/49879.xml`)
- TC-01: missing bounds on UIAutomator nodes → `[0,0,0,0]` (no crash)
- Missing bounds on layout-only tags → skipped
- Screenshots referenced by path only (images are not parsed)

Formal contract: [`docs/json_schemas.md`](docs/json_schemas.md) · [`docs/schemas/auditor_schema.json`](docs/schemas/auditor_schema.json)

---

## Rule checker (Stage 2)

`src/rules.py` — `check(components_json)` runs **R01–R20** and returns `violations.json`.

| Rule | Status | Notes |
|------|--------|-------|
| R01–R10 | Done | Core accessibility checks (labels, touch targets, overlap, …) |
| R11 | Stub | Color-only info — needs before/after or pixel diff |
| R12 | Done | Missing captions (`media_type` heuristics) |
| R13–R20 | Done | Audio, focus order, spacing, gestures, hint-only labels |
| R09 | Partial | Needs screenshot contrast analysis |

Run rules via CLI: `python test_run.py` (parse + rules) or import `src.rules.check`.

---

## Quick start

### 1. Install

```bash
python -m venv venv
venv\Scripts\activate        # Windows
# source venv/bin/activate   # macOS / Linux
pip install -r requirements.txt
```

### 2. Add data locally

Download datasets (raw XML/screenshots not always in Git — see [MASC Drive](https://drive.google.com/file/d/1kx8qRbOtdQbbewZgfBTeCIj7lNvabFTF/view?usp=sharing) and [`docs/rico_holdout_dataset.md`](docs/rico_holdout_dataset.md)):

```
data/data-masc/xml/{category}/{id}.xml
data/data-masc/screenshots/{category}/{id}.jpg
```

Parsed `components.json` for all 7,068 MASC screens is tracked on `noor`.

### 3. Parse + rules

```bash
# MASC — full batch (default dataset)
python test_run.py --dataset masc

# Single screen (known edge case: null bytes in XML)
python test_run.py data/data-masc/xml/chat/49879.xml

# Rico holdout — smoke test only (do not tune on this)
python test_run.py --dataset rico --max-files 4

# Any uploaded / unknown app XML
python test_run.py --dataset upload

# Validate sample outputs against JSON Schema
python scripts/validate_output.py
```

### 4. Tests & validation

```bash
# Unit tests (38 total)
python -m pytest tests/ -q

# Full Week 3+ pipeline: re-parse → pytest → schema → MASC R01–R20 scan
python scripts/noor_week3_validate.py

# MASC parse sign-off + R13–R20 aggregate counts
python scripts/masc_parse_signoff.py
```

Validation summaries: `outputs/validation_logs/noor_week3_summary.md`

### 5. Streamlit UI

```bash
streamlit run app.py
```

Upload XML in the main panel; run dataset batch parse from the sidebar.

### 6. React frontend (Axion)

```bash
cd frontend
npm ci
npm run dev
# http://localhost:5173 — UI scaffold only; not wired to FastAPI yet
```

### 7. FastAPI (local)

```bash
# From repo root
python -m uvicorn backend.main:app --reload --host 0.0.0.0 --port 8000
# Health: http://localhost:8000/health
# Audit:  POST /api/v1/audit  →  GET /api/v1/audit/{id}/violations
```

Upload XML via multipart form to `POST /api/v1/audit`. Report endpoint (`/report`) is not implemented yet.

---

## Datasets

| Dataset | Path | Split | Purpose |
|---------|------|-------|---------|
| **MASC** | `data/data-masc/` | 70% train / 15% val / 15% test (`splits/`) | Development & tuning |
| **Rico holdout** | `data/data-rico-holdout/` | 100% held out | **Final unseen evaluation** |
| **final_rico** | `data/final_rico/` | — | Source corpus only (302/2000 overlap MASC) |
| **Uploads** | `data/xml/` + `data/screenshots/` | — | New / unknown apps |

Regenerate splits or holdout:

```bash
python scripts/split_masc_dataset.py
python scripts/build_rico_holdout.py
python scripts/build_rico_holdout_sheet.py
```

---

## Scripts

| Script | Purpose |
|--------|---------|
| [`validate_output.py`](scripts/validate_output.py) | Validate `components.json` / `violations.json` against schema |
| [`noor_week3_validate.py`](scripts/noor_week3_validate.py) | Full QA: MASC re-parse, pytest, API smoke, schema, R01–R20 scan |
| [`masc_parse_signoff.py`](scripts/masc_parse_signoff.py) | MASC parse sign-off + extended-field checks + R13–R20 counts |
| [`check_train_parser.py`](scripts/check_train_parser.py) | Sample MASC train screens & check parser output |
| [`split_masc_dataset.py`](scripts/split_masc_dataset.py) | Create train / val / test CSVs |
| [`build_rico_holdout.py`](scripts/build_rico_holdout.py) | Build MASC-disjoint Rico holdout |
| [`build_rico_holdout_sheet.py`](scripts/build_rico_holdout_sheet.py) | Export holdout sheet for review |
| [`compare_datasets.py`](scripts/compare_datasets.py) | Byte-level overlap check vs MASC |
| [`convert_json-to-xml.py`](scripts/convert_json-to-xml.py) | MASC JSON → XML conversion |
| [`generate_labels_csv.py`](scripts/generate_labels_csv.py) | Screenshot label export |
| [`copy_matched_jsons.py`](scripts/copy_matched_jsons.py) | Copy matched JSON into dataset tree |

---

## Documentation

| Document | Contents |
|----------|----------|
| [`docs/windows_setup.md`](docs/windows_setup.md) | Windows install & onboarding |
| [`docs/accessibility_guidelines_report.md`](docs/accessibility_guidelines_report.md) | G01–G30 guidelines, R01–R30 rules |
| [`docs/json_schemas.md`](docs/json_schemas.md) | Inter-module JSON contracts |
| [`docs/qa_test_plan.md`](docs/qa_test_plan.md) | TC-01–TC-06 test cases |
| [`docs/rico_holdout_dataset.md`](docs/rico_holdout_dataset.md) | Holdout filtering methodology |
| [`docs/r11_r12_design.md`](docs/r11_r12_design.md) | R11/R12 stub design notes |
| [`docs/progress/`](docs/progress/) | Living supplementary progress report |
| [`docs/examples/`](docs/examples/) | Sample JSON for each pipeline stage |

---

## Git: what to commit

**Always commit:** source code, `docs/`, `scripts/`, `tests/`, `frontend/`, `requirements.txt`

**Never commit:** `.venv/`, `__pycache__/`, `.env`, raw `xml/` / `screenshots/` trees, most of `outputs/violations/`

**Tracked on `noor` (parser artifacts & metadata):**

- `data/data-masc/parsed/` (7,068 `*_components.json` + sign-off logs)
- `data/data-masc/splits/`
- `data/data-rico-holdout/parsed/` (smoke samples)
- `data/data-rico-holdout/manifest/*.csv` and `*.json` only
- `outputs/validation_logs/` (week3 + noor_week3 summaries)

---

## Troubleshooting

| Problem | Fix |
|---------|-----|
| `ParseError` on XML | File may contain null bytes — parser strips `\x00` automatically |
| ~1 component per MASC screen | Ensure parser descends into `<wrapper>` nodes (fixed Jul 2026) |
| 0 components parsed | Check XML has `class` + `bounds` (UIAutomator) or layout tags + bounds (Rico) |
| Screenshot path wrong | Ensure `{id}.jpg` sits under `screenshots/{category}/` mirroring `xml/{category}/` |
| `DATASET_ROOT` on Windows | Prefer `python test_run.py --dataset masc` over env vars in cmd |
| Schema validation fails | Run `python scripts/validate_output.py` and compare with [`docs/examples/components.json`](docs/examples/components.json) |
| R09 / R11 always 0 on MASC | Expected — R09 needs screenshots; R11 is a documented stub |

---

## License & attribution

Internship project — **Agentic Accessibility Auditor (Axion)**.  
Datasets: [MASC](https://drive.google.com/file/d/1kx8qRbOtdQbbewZgfBTeCIj7lNvabFTF/view?usp=sharing), Rico (see `docs/rico_holdout_dataset.md`).
