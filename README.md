# Agentic Accessibility Auditor

Automated accessibility auditing for **Android mobile UIs**.  
Feed the pipeline a **screenshot + UIAutomator XML** → get schema-compliant `components.json`, rule-based `violations.json`, LLM-enriched explanations, and HTML/PDF reports mapped to **G01–G30** guidelines and **R01–R30** detection rules.

---

## Team & branches

| Intern | Branch | Focus |
|--------|--------|-------|
| **Azeem** | [`azeem`](https://github.com/MuhammadNoor7/agentic-accessibility-auditor/tree/azeem) | Data, hybrid XML parser, rule checker, Docker |
| **Ayesha** | [`ayesha`](https://github.com/MuhammadNoor7/agentic-accessibility-auditor/tree/ayesha) | JSON schemas, Figma, React dashboard |
| **Noor (Lead)** | [`noor`](https://github.com/MuhammadNoor7/agentic-accessibility-auditor/tree/noor) | LLM agent, reports, project coordination |

---

## Pipeline

```
Screenshot + XML  →  Parser  →  Rule checker  →  Agent  →  Report
                      │              │              │          │
               components.json  violations.json  report.json  HTML/PDF
```

| Stage | Owner | Output | Status |
|-------|-------|--------|--------|
| 1 — Parser | Intern 1 | `components.json` | **Done** |
| 2 — Rules (R01–R30) | Intern 1 | `violations.json` | Planned |
| 3 — Agent layer | Intern 3 | enriched `report.json` | Planned |
| 4 — Report | Intern 3 | `audit_report.html` / PDF | Planned |

---

## Project layout

```
agentic-accessibility-auditor/
├── app.py                  # Streamlit: upload XML + batch parse
├── test_run.py             # CLI batch / single-file parser
├── requirements.txt
├── Dockerfile
├── docker-compose.yml
│
├── backend/                # FastAPI (Docker) — health check API
├── src/
│   ├── parser.py           # Hybrid Android UI XML → components.json
│   └── schema_documents.py
│
├── scripts/                # Dataset utilities + validate_output.py
│
├── data/                   # See “Datasets” — mostly local / selective Git
│   ├── xml/                # Generic uploads (any app)
│   ├── screenshots/
│   ├── parsed/             # Generic upload parser output
│   ├── data-masc/           # MASC train/dev (7,068 screens)
│   ├── data-rico-holdout/  # Unseen final eval (1,698 screens)
│   └── final_rico/         # Raw Rico source corpus
│
├── outputs/
│   ├── violations/         # Stage 2 (planned)
│   └── reports/            # Stage 4 (planned)
│
└── docs/                   # Schemas, guidelines, QA plan, setup guide
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
| MASC | UIAutomator nodes + `<wrapper>` numeric bounds |
| Rico | Widget tags (`LinearLayout`, `TextView`, …) + space-separated bounds |
| Generic upload | Any element with `class` / widget tag + bounds |

**Built-in resilience**

- Strips null bytes before parse (e.g. corrupt `chat/49879.xml`)
- TC-01: missing bounds on UIAutomator nodes → `[0,0,0,0]` (no crash)
- Missing bounds on layout-only tags → skipped
- Screenshots referenced by path only (images are not parsed)

**Minimal output shape** (`components.json`):

```json
{
  "schema_version": "1.0",
  "screen_id": "chat_49879",
  "image_path": "data/data-masc/screenshots/chat/49879.jpg",
  "xml_path": "data/data-masc/xml/chat/49879.xml",
  "components": [
    {
      "component_id": "c_001",
      "class": "android.widget.TextView",
      "text": "Send",
      "content_desc": "",
      "resource_id": "com.example:id/send",
      "clickable": true,
      "enabled": true,
      "focusable": true,
      "bounds": [0, 120, 200, 180]
    }
  ]
}
```

Formal contract: [`docs/json_schemas.md`](docs/json_schemas.md) · [`docs/schemas/auditor_schema.json`](docs/schemas/auditor_schema.json)

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

Download datasets (not in Git — see [MASC Drive](https://drive.google.com/file/d/1kx8qRbOtdQbbewZgfBTeCIj7lNvabFTF/view?usp=sharing) and [`docs/rico_holdout_dataset.md`](docs/rico_holdout_dataset.md)):

```
data/data-masc/xml/{category}/{id}.xml
data/data-masc/screenshots/{category}/{id}.jpg
```

### 3. Parse

```bash
# MASC — full batch (default dataset)
python test_run.py

# Single screen (known edge case: null bytes in XML)
python test_run.py data/data-masc/xml/chat/49879.xml

# Rico holdout — smoke test only (do not tune on this)
python test_run.py --dataset rico --max-files 4

# Any uploaded / unknown app XML
python test_run.py --dataset upload

# Validate against JSON Schema
python scripts/validate_output.py
```

### 4. Streamlit UI

```bash
streamlit run app.py
```

Upload XML in the main panel; run dataset batch parse from the sidebar.

### 5. Docker

```bash
docker-compose up --build
# FastAPI health: http://localhost:8000/health
# Auditor service runs test_run.py on MASC by default
```

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
| [`docs/examples/`](docs/examples/) | Sample JSON for each pipeline stage |

---

## Git: what to commit

**Always commit:** source code, `docs/`, `scripts/`, Docker files, `requirements.txt`

**Never commit:** `.venv/`, `__pycache__/`, `.env`, raw `xml/` / `screenshots/` / `json/` trees, `outputs/`

**Tracked on `azeem` (parser artifacts & metadata):**

- `data/data-masc/parsed/`
- `data/data-masc/splits/`
- `data/data-rico-holdout/parsed/` (smoke samples)
- `data/data-rico-holdout/manifest/*.csv` and `*.json` only  
  (not `_sheet_thumbs/`, `category_sheets/`, `google_sheets/`, or `.xlsx`)

---

## Troubleshooting

| Problem | Fix |
|---------|-----|
| `ParseError` on XML | File may contain null bytes — current parser strips `\x00` automatically |
| 0 components parsed | Check XML has `class` + `bounds` (UIAutomator) or layout tags + bounds (Rico) |
| Screenshot path wrong | Ensure `{id}.jpg` sits under `screenshots/{category}/` mirroring `xml/{category}/` |
| `DATASET_ROOT` on Windows | Prefer `python test_run.py --dataset rico` over env vars in cmd |
| Schema validation fails | Run `python scripts/validate_output.py` and compare with [`docs/examples/components.json`](docs/examples/components.json) |

---

## License & attribution

Internship project — **Agentic Accessibility Auditor**.  
Datasets: [MASC](https://drive.google.com/file/d/1kx8qRbOtdQbbewZgfBTeCIj7lNvabFTF/view?usp=sharing), Rico (see `docs/rico_holdout_dataset.md`).
