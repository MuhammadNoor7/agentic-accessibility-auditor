# Agentic Accessibility Auditor (Axion)

Automated accessibility auditing for **Android mobile UIs**.  
Feed the pipeline a **screenshot + UIAutomator XML** → get schema-compliant `components.json`, rule-based `violations.json`, LLM-enriched explanations, and HTML/PDF reports mapped to **G01–G30** guidelines and **R01–R30** detection rules.

**Current integration branch:** [`noor`](https://github.com/MuhammadNoor7/agentic-accessibility-auditor/tree/noor) — Weeks 1–6 complete: parser + **R01–R30**, agent + HTML/PDF export, Axion UI (Upload/Dashboard/Report/Records), **JWT + OTP/SMTP + Google OAuth**, 40-screen Week 6 eval, **146 pytest** collected (16 Jul 2026, `995f6d31`+).

---

## Team & branches

| Intern | Branch | Focus |
|--------|--------|-------|
| **Salar** | [`salar`](https://github.com/MuhammadNoor7/agentic-accessibility-auditor/tree/salar) | MASC data, parser, **rules** (with Noor + Ayesha), JWT/records base, Docker, tests |
| **Ayesha** | [`ayesha`](https://github.com/MuhammadNoor7/agentic-accessibility-auditor/tree/ayesha) | Rico holdout, Figma, React frontend, SRS co-author, rules (with Salar + Noor) |
| **Noor (Lead)** | [`noor`](https://github.com/MuhammadNoor7/agentic-accessibility-auditor/tree/noor) | Backend API, OTP/SMTP/OAuth, JSON schemas, SDS, agent, report template, Week 6 eval, docs, QA |

---

## Project documentation

| Document | Path |
|----------|------|
| **SRS v2.5** | [`srs/SRS_Agentic_Accessibility_Auditor_v2.0.md`](srs/SRS_Agentic_Accessibility_Auditor_v2.0.md) · [`.docx`](srs/SRS_Agentic_Accessibility_Auditor_v2.0.docx) |
| **SDS v2.9** | [`sds/SDS_Agentic_Accessibility_Auditor_v2.0.md`](sds/SDS_Agentic_Accessibility_Auditor_v2.0.md) · [`.docx`](sds/SDS_Agentic_Accessibility_Auditor_v2.0.docx) |
| **8-week plan** | [`updated_plan.md`](updated_plan.md) · [`docs/updated_plan_v2.0.docx`](docs/updated_plan_v2.0.docx) |
| **Progress report** | [`docs/progress/Supplementary_Progress_Report_v1.0.md`](docs/progress/Supplementary_Progress_Report_v1.0.md) · [`.docx`](docs/progress/Supplementary_Progress_Report_v1.0.docx) |
| **Week 6 eval** | [`docs/week6/evaluation_sheet.md`](docs/week6/evaluation_sheet.md) · CSV · R26–R30 design DOCX |
| **SMTP + Google setup (free)** | [`docs/auth_smtp_google_setup.md`](docs/auth_smtp_google_setup.md) |
| **Figma screenshots** | `docs/assets/figma/` (also mirrored under `docs/progress/assets/figma/` for the progress DOCX) |
| **Week 6 validation** | `outputs/validation_logs/noor_week6_summary.md` · `noor_week6_validation_log.txt` |

Regenerate Word exports: `python scripts/md_to_docx.py <input.md> -o <output.docx>`.

---

## Pipeline status (`noor`, 16 Jul 2026)

```
Screenshot + XML  →  Parser  →  Rule checker  →  Agent  →  Report
                      │              │              │          │
               components.json  violations.json  report.json  HTML/PDF
                                    ↑
                         Auth (/auth) + Records (/records)
```

| Stage | Owner | Output | Status |
|-------|-------|--------|--------|
| 1 — Parser | Salar / Noor | `components.json` | **Done** — 7,068 MASC screens |
| 2 — Rules | Salar + Noor + Ayesha | `violations.json` | **R01–R30** |
| 3 — Agent | Noor | enriched `report.json` | **Done** — `GET /api/v1/audit/{id}/report` |
| 4 — Report | Noor | HTML/PDF | **Done** — download API; screenshot/XML persist + autoescape |
| UI — Axion | Ayesha / Noor | React app | **Done (Week 6 MVP)** — Upload/Dashboard/Report/Records + Sign Up/Log In/Forgot/OTP/Reset + Google |
| Auth / Records | Salar + Noor | JWT + history | **Done** — `/auth/*`, `/records/*`; SMTP OTP; Google OAuth |
| Week 6 eval | Noor | 40-screen sheet | **Done** — stratified seed `20260715`; 40/40 assisted FP/miss notes |

**API mounts:** audit under `/api/v1/audit/*`; auth under `/auth/*`; records under `/records/*`.

**Demo path:** signup/login → upload screenshot+XML pair → dashboard/report (score + HTML/PDF) → Records (names + score).

---

## Project layout

```
agentic-accessibility-auditor/
├── app.py                  # Streamlit: upload XML + violations preview
├── test_run.py             # CLI: single XML, batch dataset, or --fixtures
├── requirements.txt
├── .env.example            # JWT, GOOGLE_CLIENT_ID, SMTP_*, LLM keys (no secrets)
├── updated_plan.md         # 8-week team plan
├── conftest.py
│
├── src/                    # Stages 1–4 Python core
│   ├── parser.py
│   ├── rules.py            # R01–R30
│   ├── agent.py
│   ├── report.py           # Jinja2 HTML + Playwright PDF
│   ├── templates/audit_report.html.j2
│   ├── explainer.py
│   ├── guidelines.py
│   ├── llm_providers.py
│   └── schema_documents.py
│
├── backend/                # FastAPI gateway
│   ├── main.py             # load_dotenv(override=True)
│   ├── auth.py             # JWT helpers
│   ├── otp_store.py        # OTP TTL store
│   ├── email_service.py    # Gmail SMTP OTP mail
│   ├── routers/
│   │   ├── audit.py        # /api/v1/audit/*
│   │   ├── auth_router.py  # /auth/* (register, login, OTP, Google)
│   │   └── records_router.py
│   ├── tests/test_auth.py  # 22 auth tests
│   └── data/               # local users/records/otp JSON (gitignored)
│
├── frontend/               # Axion React (Vite + React 19 + Tailwind)
│   └── src/
│       ├── api.js
│       ├── utils/auth.js, googleAuth.js, validation.js, api.js
│       ├── components/ui/UserAvatar.jsx
│       └── pages/          # Upload, Dashboard, Report, Records, auth/*
│
├── tests/                  # ~146 pytest collected
│   ├── test_parser.py
│   ├── test_rules.py
│   ├── test_agent.py
│   ├── test_audit.py
│   ├── test_report.py
│   ├── test_explainer.py
│   └── fixtures/rules/     # 57 controlled XML screens
│
├── scripts/
│   ├── md_to_docx.py
│   ├── noor_week3_validate.py … noor_week6_validate.py
│   ├── fill_week6_manual_eval.py
│   ├── masc_parse_signoff.py
│   ├── validate_output.py
│   └── dev/                # optional local SMTP/auth smoke helpers
│
├── docs/
│   ├── week6/              # eval sheet CSV/MD/DOCX + R26–R30 design
│   ├── progress/           # supplementary report + assets/ (figma + logs)
│   ├── assets/figma/       # Figma PNG references
│   └── …                   # schemas, guidelines, QA plan
│
├── srs/                    # Software Requirements Spec
├── sds/                    # Software Design Spec
│
├── data/
│   ├── data-masc/          # parsed/ tracked; raw xml/screenshots local
│   └── data-rico-holdout/
│
└── outputs/
    ├── validation_logs/    # noor_week1–6 summaries + logs (tracked)
    ├── violations/samples/
    └── reports/samples/
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
| Rico | Widget tags + space-separated bounds |
| Generic upload | Any element with `class` / widget tag + bounds |

**R13–R20 extended fields:** `focus_order`, `parent_id`, `long_clickable`, `scrollable`, `selected`, `checked`, `password`, `text_all_caps`, `input_type`, `important_for_accessibility`, `media_type`, `is_dialog`, `label_for`.

Formal contract: [`docs/json_schemas.md`](docs/json_schemas.md) · [`docs/schemas/auditor_schema.json`](docs/schemas/auditor_schema.json)

---

## Rule checker (Stage 2)

`src/rules.py` — `check(components_json)` runs **R01–R30** and returns `violations.json`.

```bash
python test_run.py path/to/screen.xml
python test_run.py --fixtures
python test_run.py --dataset masc
```

---

## Quick start

### 1. Install

```bash
python -m venv venv
venv\Scripts\activate        # Windows
pip install -r requirements.txt
pip install -r backend/requirements.txt
```

### 2. Configure `.env`

Copy `.env.example` → `.env` and set:

| Variable | Purpose |
|----------|---------|
| `JWT_SECRET` | JWT signing |
| `GOOGLE_CLIENT_ID` | Google Sign-In Web client ID |
| `SMTP_*` | Gmail App Password for OTP mail (sender Gmail; recipients any domain) |
| `AUTH_DEV_SHOW_OTP` | `0` when real SMTP works |
| `VITE_API_BASE` | Frontend → API (e.g. `http://127.0.0.1:8000`) |
| LLM provider keys | Optional live explanations |

**Never commit** `.env` or App Passwords.

### 3. Parse + rules

```bash
python test_run.py --dataset masc
python test_run.py data/data-masc/xml/chat/49879.xml
python scripts/validate_output.py
```

### 4. Tests & Week 6 validation

```bash
python -m pytest tests/ backend/tests/ -q
python scripts/noor_week6_validate.py
```

Logs: `outputs/validation_logs/noor_week6_summary.md`

### 5. FastAPI + Axion UI

```bash
# Terminal 1 — API
python -m uvicorn backend.main:app --reload --host 0.0.0.0 --port 8000

# Terminal 2 — UI
cd frontend
npm ci
npm run dev
# http://localhost:5173
```

Auth: `POST /auth/register`, `/auth/login`, forgot/OTP/reset, `/auth/google`  
Audit: `POST /api/v1/audit` (screenshot + XML) → report / download  
Records: `GET /records` (JWT)

### 6. Docker (backend + auditor)

```bash
docker-compose up --build
# Frontend still via Vite locally
```

### 7. Streamlit (optional)

```bash
streamlit run app.py
```

---

## Datasets

| Dataset | Path | Purpose |
|---------|------|---------|
| **MASC** | `data/data-masc/` | Development & tuning (70/15/15 splits) |
| **Rico holdout** | `data/data-rico-holdout/` | Final unseen evaluation (Week 8) |
| **Uploads** | `data/xml/` + `data/screenshots/` | Ad-hoc screens |

---

## Scripts

| Script | Purpose |
|--------|---------|
| [`md_to_docx.py`](scripts/md_to_docx.py) | Markdown → formatted Word |
| [`noor_week6_validate.py`](scripts/noor_week6_validate.py) | Auth/records + eval sheet QA |
| [`fill_week6_manual_eval.py`](scripts/fill_week6_manual_eval.py) | Assisted FP/miss fill for 40-screen CSV |
| [`noor_week3_validate.py`](scripts/noor_week3_validate.py) … `week5` | Earlier week QA pipelines |
| [`masc_parse_signoff.py`](scripts/masc_parse_signoff.py) | MASC parse sign-off |
| [`validate_output.py`](scripts/validate_output.py) | JSON Schema validation |
| `scripts/dev/*` | Optional local SMTP/auth smoke helpers |

---

## Git: what to commit

**Always commit:** source, `docs/`, `srs/`, `sds/`, `scripts/`, `tests/`, `frontend/`, `requirements.txt`, tracked validation logs / samples

**Never commit:** `.venv/`, `.env`, `backend/data/*.db.json` (local user/OTP DBs), raw bulk `outputs/violations/chat_*`, App Passwords

**Tracked on `noor`:** `data/data-masc/parsed/`, splits, holdout manifests, `outputs/validation_logs/`, `outputs/*/samples/`, `docs/week6/`, progress assets

---

## Troubleshooting

| Problem | Fix |
|---------|-----|
| OTP not emailed | Check `SMTP_*` in `.env`; restart uvicorn (`load_dotenv(override=True)`); set `AUTH_DEV_SHOW_OTP=0` when mail works |
| Google Sign-In fails | Confirm `GOOGLE_CLIENT_ID` matches GIS meta / Cloud Console Web client |
| HTML/PDF missing screenshot | Ensure upload pair persisted under `outputs/runs/{id}/input/` (Week 6 fix) |
| Pair rejected | Screenshot + XML stems/IDs must match (`filesMatch` + API) |
| Schema validation fails | `python scripts/validate_output.py` |

---

## License & attribution

Internship project — **Agentic Accessibility Auditor (Axion)**.  
Datasets: [MASC](https://drive.google.com/file/d/1kx8qRbOtdQbbewZgfBTeCIj7lNvabFTF/view?usp=sharing), Rico (see `docs/rico_holdout_dataset.md`).
