# Agentic Accessibility Auditor (Axion)

Automated accessibility auditing for **Android mobile UIs**.  
Feed the pipeline a **screenshot + UIAutomator XML** → get schema-compliant `components.json`, rule-based `violations.json`, LLM-enriched explanations, and HTML/PDF reports mapped to **G01–G30** guidelines and **R01–R30** detection rules.

**Current integration branch:** [`noor`](https://github.com/MuhammadNoor7/agentic-accessibility-auditor/tree/noor) — Weeks 1–7 complete + **post–Week 7 YOLO UI-element detector** track + **Week 8 rule-accuracy fixes (29 Jul)**: three confirmed false-positive rules (R07, R08, R30) and one parser bug blocking R20/R05 fixed and verified against the full 7,068-screen MASC set and the 1,698-screen Rico holdout — not just fixtures.

---

## Team & branches

| Intern | Branch | Focus |
|--------|--------|-------|
| **Salar** | [`salar`](https://github.com/MuhammadNoor7/agentic-accessibility-auditor/tree/salar) | MASC data, parser, **rules** (with Noor + Ayesha), JWT/records base, Docker, tests |
| **Ayesha** | [`ayesha`](https://github.com/MuhammadNoor7/agentic-accessibility-auditor/tree/ayesha) | Rico holdout, Figma, React frontend, SRS co-author, rules (with Salar + Noor) |
| **Noor (Lead)** | [`noor`](https://github.com/MuhammadNoor7/agentic-accessibility-auditor/tree/noor) | Backend API, OTP/SMTP/OAuth, JSON schemas, SDS, agent, report template, Week 7 QA eval, **Week 8 rule-accuracy fixes**, docs, coordination |

---

## Project documentation

| Document | Path |
|----------|------|
| **SRS v2.8** | [`srs/SRS_Agentic_Accessibility_Auditor_v2.8.md`](srs/SRS_Agentic_Accessibility_Auditor_v2.8.md) · [`.docx`](srs/SRS_Agentic_Accessibility_Auditor_v2.8.docx) |
| **SDS v2.12** | [`sds/SDS_Agentic_Accessibility_Auditor_v2.12.md`](sds/SDS_Agentic_Accessibility_Auditor_v2.12.md) · [`.docx`](sds/SDS_Agentic_Accessibility_Auditor_v2.12.docx) |
| **8-week plan** | [`updated_plan.md`](updated_plan.md) · [`docs/updated_plan_v2.0.docx`](docs/updated_plan_v2.0.docx) |
| **Progress report v1.24** | [`docs/progress/Supplementary_Progress_Report_v1.24.md`](docs/progress/Supplementary_Progress_Report_v1.24.md) · [`.docx`](docs/progress/Supplementary_Progress_Report_v1.24.docx) — §16 Document history through 29 Jul: R07/R08/R30 false-positive fixes + R20/R05 parser fix, full-dataset verification, crop-classifier retrain |
| **Week 6 eval** | [`docs/week6/evaluation_sheet.md`](docs/week6/evaluation_sheet.md) · CSV · R26–R30 design DOCX |
| **Week 7 QA** | [`docs/week7/README.md`](docs/week7/README.md) · rule/guideline summaries (MASC sample + Rico holdout variants) · team priorities |
| **YOLO UI detector (post–Week 7)** | `notebooks/train_yolo_ui_detector.ipynb` · `runs/runs/yolo_ui_detector/` (config, metrics, plots, exported `best.pt`) — not yet pipeline-wired into `src/` |
| **Crop-violation classifier (Week 8)** | `notebooks/train_crop_violation_classifier.ipynb` · `src/crop_violation_classifier.py` (inference) · `models/crop_violation_classifier_best.pt` — pixel-level confirmation for R09/R04/R17/R10/R28/R08 |
| **SMTP + Google setup (free)** | [`docs/auth_smtp_google_setup.md`](docs/auth_smtp_google_setup.md) |
| **Figma screenshots** | `docs/assets/figma/` (also mirrored under `docs/progress/assets/figma/` for the progress DOCX) |
| **Validation logs** | `outputs/validation_logs/` — `noor_week1`…`noor_week8_{summary.md,validation_log.txt}` (append-only, one dated block per run) |

Regenerate Word exports: `python scripts/md_to_docx.py <input.md> -o <output.docx>`.

---

## Pipeline status (`noor`, 29 Jul 2026)

```
Screenshot + XML  →  Parser  →  Rule checker  →  Agent  →  Report
                      │              │              │          │
               components.json  violations.json  report.json  HTML/PDF
                                    ↑
                         Auth (/auth) + Records (/records)
```

| Stage | Owner | Output | Status |
|-------|-------|--------|--------|
| 1 — Parser | Salar / Noor | `components.json` | **Done** — 7,068 MASC + 1,698 Rico holdout screens |
| 2 — Rules | Salar + Noor + Ayesha | `violations.json` | **R01–R30**; R07/R08/R30 false-positive fixes + R20/R05 parser fix verified 29 Jul |
| 3 — Agent | Noor | enriched `report.json` | **Done** — `GET /api/v1/audit/{id}/report` |
| 4 — Report | Noor | HTML/PDF | **Done** — download API; screenshot/XML persist + autoescape |
| UI — Axion | Ayesha / Noor | React app | **Done (Week 6 MVP)** — Upload/Dashboard/Report/Records + Sign Up/Log In/Forgot/OTP/Reset + Google |
| Auth / Records | Salar + Noor | JWT + history | **Done** — `/auth/*`, `/records/*`; SMTP OTP; Google OAuth |
| Week 6 eval | Noor | 40-screen sheet | **Done** — stratified seed `20260715`; 40/40 assisted FP/miss notes |
| Week 7 QA (Noor) | Noor | Rule/guideline summaries | **Done** — MASC 40-screen sample + full Rico holdout (1,698 screens) both re-evaluated post-fix |
| YOLO UI detector (post–Week 7) | Salar (notebook) / Noor (Colab train) | `best.pt`, YOLO-format datasets | **Trained** — `runs/runs/yolo_ui_detector/`; zero-shot vs fine-tuned eval built for Rico holdout; **not pipeline-wired** (no `src/yolo_ui_detector.py` yet) |
| Crop-violation classifier (Week 8) | Noor (Colab train) | `crop_violation_classifier_best.pt` | **Trained (epoch 17, val macro-F1 0.265)** — retrained after the R08 fix since R08 is one of its 6 label classes; `src/crop_violation_classifier.py` inference wrapper wired, **not called from the main pipeline yet** |
| R01–R30 accuracy fixes (Week 8) | Noor | Fixed `src/rules.py` + `src/parser.py` | **Done, 29 Jul** — verified against full MASC (7,068) + Rico holdout (1,698), not just fixtures; see §16 v1.24 in the progress report |

**API mounts:** audit under `/api/v1/audit/*`; auth under `/auth/*`; records under `/records/*`.

**Demo path:** signup/login → upload screenshot+XML pair → dashboard/report (score + HTML/PDF) → Records (names + score).

---

## What changed in the Week 8 rule-accuracy pass (29 Jul 2026)

Three rules and one parser bug were confirmed, via direct inspection of real MASC/Rico screens (not assumption), to be producing false positives or a hard-blocked rule:

| Rule / file | Problem | Fix |
|---|---|---|
| **R07** `check_zero_size` | Flagged non-interactive structural elements (`Space`, `LinearLayout` wrappers) with zero bounds — never reachable by a screen reader regardless of size | New `_is_a11y_relevant` gate: only clickable/focusable/text/content_desc elements are eligible |
| **R08** `check_layout_overlap` | Flagged a clickable scrollable container (e.g. a `ListView`) against its own clickable rows — normal Android nesting, confirmed on a real Rico `chat` screen (8/8 rows falsely flagged) | New `_is_ancestor` helper walks the full `parent_id` chain and skips ancestor/descendant pairs. **-43.2% on the Rico holdout** (12,738 → 7,238) |
| **R30** `check_icon_only_no_label` | One violation per repeated list/grid-row icon instance, inflating counts for what's really one design decision | New `_dedupe_repeated` collapses same-`resource_id`-and-bounds repeats into one violation, count noted in the issue text |
| **R20 / R05** `parser._get_hint` | `_get_hint` only checked `hint`/`android:hint` — MASC's real attribute is `text-hint`, which was never read. R20 was structurally unable to ever fire (0 hits); R05 was flagging every hinted `EditText` as unlabeled as a side effect | Added the `text-hint` alias. **R20: 0 → 749 hits** on full MASC. **R05: 2,117 → 717** (-66%) |

Verified: full pytest suite (152 passed), full MASC re-parse + re-check (7,068 screens, 0 failures), Rico holdout re-eval (1,698 screens, 0 failures), `masc_dataset_analysis.ipynb` re-executed with a corrected §9 Findings section, `train_crop_violation_classifier.ipynb` retrained on Colab (R08 is one of its 6 label classes).

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
│   ├── parser.py           # hybrid UIAutomator/MASC/Rico/generic parser
│   ├── rules.py            # R01–R30
│   ├── agent.py            # score + template/LLM enrichment
│   ├── report.py           # Jinja2 HTML + Playwright PDF
│   ├── templates/audit_report.html.j2
│   ├── explainer.py        # Stage 3 LLM explanations
│   ├── guidelines.py
│   ├── llm_providers.py
│   ├── schema_documents.py
│   └── crop_violation_classifier.py  # MobileNetV3 crop-level classifier (R09/R04/R17/R10/R28/R08), inference only
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
├── frontend/                # Axion React (Vite + React 19 + Tailwind)
│   └── src/
│       ├── api.js
│       ├── utils/auth.js, googleAuth.js, validation.js, api.js
│       ├── components/ui/UserAvatar.jsx
│       └── pages/          # Upload, Dashboard, Report, Records, auth/*
│
├── tests/                  # 152 pytest collected (tests/ + backend/tests/)
│   ├── test_parser.py
│   ├── test_rules.py
│   ├── test_agent.py
│   ├── test_audit.py
│   ├── test_report.py
│   ├── test_explainer.py
│   └── fixtures/rules/     # 61 controlled XML screens (R01–R27, R29–R30; R28 has no fixture)
│
├── scripts/
│   ├── md_to_docx.py
│   ├── noor_week3_validate.py … noor_week8_validate.py
│   ├── run_week7_eval_analysis.py · run_rico_holdout_eval.py
│   ├── fill_week6_manual_eval.py
│   ├── masc_parse_signoff.py · check_train_parser.py
│   ├── build_rico_holdout.py · build_rico_holdout_sheet.py
│   ├── run_explainer_sample.py
│   ├── validate_output.py
│   └── dev/                # optional local SMTP/auth smoke helpers
│
├── notebooks/
│   ├── masc_dataset_analysis.ipynb          # exploratory analysis of outputs/violations/ (MASC-only, filtered)
│   ├── train_crop_violation_classifier.ipynb # Week 8: crop-level CV classifier training (Colab)
│   └── train_yolo_ui_detector.ipynb          # post–Week 7: screenshot-only UI detector training (Colab)
│
├── docs/
│   ├── week6/              # eval sheet CSV/MD/DOCX + R26–R30 design
│   ├── week7/              # rule/guideline summaries — MASC sample + `holdout_*` Rico variants
│   ├── progress/           # supplementary report + assets/ (figma + logs)
│   ├── assets/figma/       # Figma PNG references
│   └── …                   # schemas, guidelines, QA plan, technical overview
│
├── srs/                    # Software Requirements Spec (v2.8)
├── sds/                    # Software Design Spec (v2.12)
│
├── data/
│   ├── data-masc/          # parsed/ + splits/ tracked; raw xml/screenshots local only
│   ├── data-rico-holdout/  # parsed/ + manifest/ tracked; raw xml/screenshots/json local only
│   ├── xml/, screenshots/, parsed/  # generic ad-hoc single-file uploads
│   └── data-rico-holdout.zip        # 249MB raw archive — gitignored (size budget)
│
├── outputs/
│   ├── validation_logs/    # noor_week1–8 summaries + append-only logs (tracked)
│   ├── week7_eval/         # MASC 40-screen sample eval (tracked)
│   ├── week7_holdout/      # Rico holdout eval (local only — see docs/week7/holdout_*)
│   ├── violations/samples/ # curated fixture-derived violations (tracked); full MASC/Rico batch stays local
│   └── reports/samples/    # curated fixture-derived reports (tracked)
│
├── models/                 # crop_violation_classifier_best.pt (gitignored — .pt weights never committed)
│
└── runs/                   # training artifacts — everything EXCEPT .pt weights is tracked
    ├── notebooks/           # executed copies with saved outputs (masc_dataset_analysis, train_crop_violation_classifier, train_yolo_ui_detector)
    ├── crop_violation_classifier/
    │   ├── crops/           # extracted training/val/test crop images
    │   ├── manifests/       # train/val/test.csv (labels)
    │   └── export/          # crop_violation_classifier_best.pt (gitignored)
    └── runs/yolo_ui_detector/
        ├── export/          # yolo_ui_detector_best.pt (gitignored)
        ├── yolo_dataset/, rico_yolo_dataset/  # MASC train vs Rico eval-only YOLO-format datasets
        └── runs/yolo_ui_detector/             # args.yaml, results.csv, confusion matrix, curves
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
| MASC | UIAutomator nodes + `<wrapper>` numeric bounds; real hint attribute is `text-hint`, not `hint` |
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
python test_run.py --dataset rico
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
python test_run.py --dataset rico
python test_run.py data/data-masc/xml/chat/49879.xml
python scripts/validate_output.py
```

### 4. Tests & validation

```bash
python -m pytest tests/ backend/tests/ -q   # 152 passed
python scripts/noor_week8_validate.py       # Rico holdout eval + pytest (rules+parser+auth+audit) + logs
```

Logs: `outputs/validation_logs/noor_week8_summary.md` · `noor_week8_validation_log.txt`

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
| **MASC** | `data/data-masc/` | Development & tuning (70/15/15 splits) — 7,068 screens |
| **Rico holdout** | `data/data-rico-holdout/` | Final unseen evaluation — 1,698 screens, MASC-disjoint |
| **Uploads** | `data/xml/` + `data/screenshots/` | Ad-hoc screens |

---

## Scripts

| Script | Purpose |
|--------|---------|
| [`md_to_docx.py`](scripts/md_to_docx.py) | Markdown → formatted Word |
| [`noor_week8_validate.py`](scripts/noor_week8_validate.py) | Rico holdout eval + pytest (rules/parser/auth/audit) + fix-verification log |
| [`noor_week7_validate.py`](scripts/noor_week7_validate.py) | Week 7 QA analysis + pytest + logs |
| [`run_week7_eval_analysis.py`](scripts/run_week7_eval_analysis.py) | MASC 40-screen rule/guideline summaries |
| [`run_rico_holdout_eval.py`](scripts/run_rico_holdout_eval.py) | Rico holdout batch eval (1,698 screens) |
| [`fill_week6_manual_eval.py`](scripts/fill_week6_manual_eval.py) | Assisted FP/miss fill for 40-screen CSV |
| [`noor_week3_validate.py`](scripts/noor_week3_validate.py) … `week6` | Earlier week QA pipelines |
| [`masc_parse_signoff.py`](scripts/masc_parse_signoff.py) · [`check_train_parser.py`](scripts/check_train_parser.py) | MASC parse sign-off + train-split parse checks |
| [`build_rico_holdout.py`](scripts/build_rico_holdout.py) · [`build_rico_holdout_sheet.py`](scripts/build_rico_holdout_sheet.py) | Rico holdout dataset curation |
| [`run_explainer_sample.py`](scripts/run_explainer_sample.py) | Stage 3 LLM explainer sample runner |
| [`validate_output.py`](scripts/validate_output.py) | JSON Schema validation |
| `scripts/dev/*` | Optional local SMTP/auth smoke helpers |

---

## Git: what to commit

**Always commit:** source, `docs/`, `srs/`, `sds/`, `scripts/`, `tests/`, `frontend/`, `requirements.txt`, tracked validation logs / samples, `runs/` (everything except `.pt` weights)

**Never commit:** `.venv/`, `.env`, `backend/data/*.db.json` (local user/OTP DBs), `.pt` model weights anywhere (`runs/**/*.pt`, `models/*.pt`), raw dataset archives over the size budget (`data/data-rico-holdout.zip`), App Passwords

**Tracked on `noor`:** `data/data-masc/parsed/` + `splits/`, `data/data-rico-holdout/parsed/` + `manifest/`, `outputs/validation_logs/`, `outputs/week7_eval/`, `outputs/*/samples/`, `docs/week6/`, `docs/week7/`, progress assets, `runs/` (non-`.pt`)

---

## Troubleshooting

| Problem | Fix |
|---------|-----|
| OTP not emailed | Check `SMTP_*` in `.env`; restart uvicorn (`load_dotenv(override=True)`); set `AUTH_DEV_SHOW_OTP=0` when mail works |
| Google Sign-In fails | Confirm `GOOGLE_CLIENT_ID` matches GIS meta / Cloud Console Web client |
| HTML/PDF missing screenshot | Ensure upload pair persisted under `outputs/runs/{id}/input/` (Week 6 fix) |
| Pair rejected | Screenshot + XML stems/IDs must match (`filesMatch` + API) |
| Schema validation fails | `python scripts/validate_output.py` |
| `models/` folder or `.pt` file vanishes after creation | Seen once locally — likely antivirus quarantine of a freshly-downloaded `.pt` (pickle) file; check your AV's quarantine log and whitelist `models/` if it recurs |

---

## License & attribution

Internship project — **Agentic Accessibility Auditor (Axion)**.  
Datasets: [MASC](https://drive.google.com/file/d/1kx8qRbOtdQbbewZgfBTeCIj7lNvabFTF/view?usp=sharing), Rico (see `docs/rico_holdout_dataset.md`).
