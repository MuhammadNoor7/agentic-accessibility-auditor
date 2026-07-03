# Supplementary Progress Report

## Agentic Accessibility Auditor (Axion)

**Practical work completed — Weeks 1–2 (baseline 1 July 2026)**  
**Living document — see §15 for team updates; §12–§13 for literature + rule ownership**

| Field | Value |
|-------|-------|
| Report type | Empirical / progress (not theoretical SRS/SDS) |
| Prepared by | Muhammad Noor (Lead) |
| Team | Salar (Parser/Rules/Docker), Ayesha (UI/Schemas/Figma), Noor (Agent/Reports/QA) |
| Repository | [MuhammadNoor7/agentic-accessibility-auditor](https://github.com/MuhammadNoor7/agentic-accessibility-auditor) |
| Canonical specs | In repo: `srs/` · `sds/` · `updated_plan.md` |

---

## 1. Purpose of this report

This document gathers what has actually been built, run, and produced so far. It is intentionally different from the SRS and SDS, which describe what the system **must do** and **how it should be designed**. Here we record:

- Real file outputs and counts
- Sign-off test results
- Dataset preparation numbers
- Repository and folder structure as it exists today
- Gaps between plan and implementation

---

## 2. Executive summary

> **Note:** Baseline below is as of **1 July 2026**. For current status after team pushes, see **§15 Team weekly updates**.

| Area | Result (1 Jul baseline) |
|------|-------------------------|
| Parser (Stage 1) | **Complete** — hybrid XML parser; 7,068 / 7,068 MASC screens parsed with PASS sign-off |
| Rule engine (Stage 2) | **In progress** — R01–R10 done; R11–R12 stubs |
| Agent layer (Stage 3) | **Scaffolded** — `src/agent.py` template enrichment |
| Report generator (Stage 4) | Not started |
| Axion React UI | **On `noor` branch** — Ayesha `frontend/` synced (auth + Upload/Dashboard/Report/Records); backend not wired yet |
| Auth + Records | Specified in SRS v2.0; not implemented in code |
| Docker | Partial — `docker-compose.yml` runs backend + batch auditor |
| Documentation | SRS v2.0 (cleaned §9/TBD-06), SDS v2.0, progress report v1.1 |

**Bottom line (1 Jul):** The data and parsing foundation is strong. The team was ready to begin Week 3 (rule engine).

---

## 3. Pipeline status (actual vs planned)

| Stage | Owner | Output artefact | Status (1 Jul) | Evidence |
|-------|-------|-----------------|----------------|----------|
| 1 — Parser | Salar | `*_components.json` | **Done** | `data/data-masc/parsed/` (7,068 files) |
| 2 — Rules | Salar | `violations.json` | Planned at baseline | See §15 |
| 3 — Agent | Noor | enriched `report.json` | Planned | No `src/agent.py` |
| 4 — Report | Noor | HTML/PDF | Planned | No `src/report.py` |
| UI — Axion | Ayesha | React dashboard | Planned | No `frontend/` folder |
| API | Salar / Noor | FastAPI routes | Partial | `backend/main.py` — health only |
| Auth/Records | Ayesha / Salar | JWT + per-user history | Planned | SRS §4.9 only |

---

## 4. Project folder structure (repository root)

> **As of 3 July 2026** on branch `noor` — canonical repo: [agentic-accessibility-auditor](https://github.com/MuhammadNoor7/agentic-accessibility-auditor)

```
agentic-accessibility-auditor/          ← repo root (clone / _noor_push locally)
│
├── src/                                ← Stage 1–3 Python core
│   ├── parser.py                       ← XML → components.json (Stage 1)
│   ├── rules.py                        ← R01–R12 rule checker (Stage 2)
│   ├── agent.py                        ← Agent scaffold / score formula (Stage 3, not API-wired)
│   └── schema_documents.py             ← JSON envelope builders
│
├── backend/                            ← FastAPI gateway
│   ├── main.py                         ← App entry + CORS + routers
│   ├── Dockerfile
│   ├── requirements.txt
│   ├── models/
│   │   └── audit.py                    ← Pydantic audit response models
│   └── routers/
│       └── audit.py                    ← POST /api/v1/audit, GET …/violations (Week 3)
│
├── frontend/                           ← Axion React UI (Ayesha, synced to noor)
│   ├── package.json                    ← Vite 8 + React 19 + Tailwind 4
│   ├── vite.config.js
│   ├── public/                         ← favicon, icons
│   └── src/
│       ├── App.jsx                     ← Routes (auth + Upload/Dashboard/Report/Records)
│       ├── main.jsx, index.css
│       ├── assets/                     ← Axion logo, etc.
│       ├── components/
│       │   ├── Sidebar.jsx
│       │   ├── layout/                 ← AuthLayout, MainLayout
│       │   └── ui/                     ← Button, TextField, OtpInput, FileDropzone, …
│       └── pages/
│           ├── auth/                   ← Login, SignUp, ForgotPassword, VerifyCode, …
│           ├── Upload.jsx, Dashboard.jsx, Report.jsx, Records.jsx
│           └── main/Placeholder.jsx
│
├── tests/                              ← pytest suite
│   ├── test_rules.py                   ← 23 tests (R01–R12)
│   ├── test_agent.py                   ← 2 tests (agent scaffold)
│   ├── test_audit.py                   ← 2 tests (FastAPI violations API)
│   └── fixtures/rules/                 ← XML fixtures per rule (16 files)
│
├── data/                               ← datasets + local uploads
│   ├── data-masc/
│   │   ├── parsed/                     ← 7,068 MASC components.json (10 categories)
│   │   └── splits/                     ← train / val / test split JSON
│   ├── data-rico-holdout/              ← 1,698-screen holdout + manifest
│   ├── xml/                            ← generic upload XML drops
│   ├── parsed/                         ← generic parsed output
│   └── screenshots/                    ← optional screenshot uploads
│
├── outputs/                            ← pipeline artefacts (violations gitignored except logs)
│   ├── violations/                     ← *_violations.json (~70 files after Week 3)
│   └── validation_logs/
│       ├── week3_summary.md            ← Salar Week 3 validation summary
│       ├── week3_validation_log.txt    ← Salar full terminal log
│       ├── noor_week3_summary.md       ← Noor Week 3 validation summary
│       └── noor_week3_validation_log.txt
│
├── docs/                               ← project documentation
│   ├── progress/
│   │   └── Supplementary_Progress_Report_v1.0.md   ← this report
│   ├── schemas/auditor_schema.json
│   ├── examples/                       ← sample components / violations / report JSON
│   ├── assets/                         ← Figma exports (SRS Appendix F)
│   ├── r11_r12_design.md
│   ├── qa_test_plan.md
│   └── updated_plan_v2.0.docx
│
├── scripts/                            ← batch + validation utilities
│   ├── validate_output.py              ← JSON schema checker
│   ├── noor_week3_validate.py          ← Noor Week 3 re-runnable validation
│   ├── masc_parse_signoff.py
│   ├── split_masc_dataset.py
│   └── build_rico_holdout.py
│
├── srs/                                ← SRS v2.0 (md + docx)
├── sds/                                ← SDS v2.0 (md + docx)
│
├── app.py                              ← Streamlit dev UI (parse + violations preview)
├── test_run.py                         ← CLI batch / single-file parser + rules
├── docker-compose.yml                  ← backend + auditor services
├── Dockerfile                          ← root batch auditor image
├── requirements.txt                    ← root Python deps
├── updated_plan.md                     ← 8-week team plan
├── conftest.py
└── README.md
```

### Key paths by pipeline stage

| Stage | Primary code | Output location |
|-------|--------------|-----------------|
| 1 — Parser | `src/parser.py`, `test_run.py`, `app.py` | `data/**/parsed/*_components.json` |
| 2 — Rules | `src/rules.py` | `outputs/violations/*_violations.json` |
| 3 — Agent | `src/agent.py` (scaffold) | `report.json` — Week 4+ |
| 4 — Report | `src/report.py` (planned) | `outputs/reports/` — not started |
| API | `backend/routers/audit.py` | in-memory job → violations JSON |
| UI | `frontend/` | browser at `:5173` (not wired to API yet) |

### Local workspace (optional clones)

Team members may keep additional working copies beside the canonical clone:

```
d:\internship\
├── agentic-accessibility-auditor\   ← main local copy
├── _noor_push\                      ← Noor's push branch working copy
├── _salar_pull\                     ← Salar sync copy
└── updated_plan.md                  ← local plan copy (also in repo root)
```

**Important:** Treat the GitHub repo root layout above as the single source of truth for code and folder conventions.

---

## 5. Parser deliverables (Salar)

### 5.1 Sign-off result

| Metric | Value |
|--------|-------|
| Dataset | MASC |
| Total screens | 7,068 |
| Categories | 10 |
| Parse OK | 7,068 |
| Parse errors | 0 |
| Sign-off | **PASS** |

Source: `data/data-masc/parsed/masc_parse_signoff_report.json`  
Script: `scripts/masc_parse_signoff.py` (29 June 2026)

### 5.2 MASC train / val / test split

| Split | Screens | Ratio |
|-------|---------|-------|
| Train | 4,943 | 70% |
| Val | 1,056 | 15% |
| Test | 1,069 | 15% |
| **Total** | **7,068** | 100% |

Config: `data/data-masc/splits/split_summary.json`

### 5.3 Supported XML formats

`src/parser.py` handles UIAutomator, MASC, Rico, and generic upload formats.

---

## 6. Dataset work

### 6.1 MASC (primary development corpus)

- **Screens:** 7,068 paired screenshot + XML
- **Parsed output:** `data/data-masc/parsed/{category}/{id}_components.json`
- **Splits:** `data/data-masc/splits/`

### 6.2 Rico holdout (unseen final evaluation)

- **Selected screens:** 1,698 (after removing 302 MASC-overlapping screens)
- **Overlap verification:** 0 hash collisions
- **Manifest:** `data/data-rico-holdout/manifest/selection_report.json`
- **Parsed at baseline:** 4 screens (holdout batch not yet run at scale)

---

## 7. Code and infrastructure delivered (baseline 1 Jul)

| Path | Purpose | Owner |
|------|---------|-------|
| `src/parser.py` | Hybrid XML → `components.json` | Salar |
| `src/schema_documents.py` | JSON envelope builders | Salar |
| `test_run.py` | CLI batch / single-file parser | Salar |
| `app.py` | Streamlit dev UI | Salar |
| `backend/main.py` | FastAPI health endpoints | Salar |
| `scripts/validate_output.py` | JSON schema validation | Salar |
| `docker-compose.yml` | Backend + auditor services | Salar |

---

## 8. Documentation delivered

| Document | Status |
|----------|--------|
| SRS v2.0 | Complete |
| SDS v2.0 | Complete |
| JSON schemas + `auditor_schema.json` | Complete |
| Accessibility guidelines (G01–G30, R01–R30) | Complete |
| QA test plan (TC-01–TC-06) | Complete |
| Figma UI specs (SRS Appendix F) | Documented |
| Updated 8-week plan | Complete |

---

## 9. Per-person contribution summary (baseline 1 Jul)

### Salar — Parser, rules, Docker, datasets

**Done:** Hybrid parser, 7,068 MASC parses, MASC splits, Rico holdout build, Docker Compose, validate script  
**Pending at baseline:** `src/rules.py`, full audit API, Auth backend, branch rename `azeem` → `salar`

### Ayesha — Schemas, Figma, React UI

**Done:** `auditor_schema.json`, `json_schemas.md`, Figma designs (8 screen groups in SRS)  
**Pending:** React + Vite + Tailwind project, all Axion screens, API integration

### Noor (Lead) — Agent, reports, QA, coordination

**Done:** QA test plan, Rico holdout strategy, SRS/SDS v2.0, supplementary report, updated plan  
**Pending:** `src/agent.py`, `src/report.py`, evaluation, weekly demos

---

## 10. Week 2 completion checklist (baseline)

| Task | Done? |
|------|-------|
| MASC dataset integrated locally | Yes |
| Parser handles MASC/Rico/UIAutomator formats | Yes |
| 7,068 `components.json` files generated | Yes |
| Parser sign-off PASS | Yes |
| Train/val/test split created | Yes |
| Rico holdout built (1,698 disjoint screens) | Yes |
| JSON schemas documented + validated | Yes |
| SRS + SDS v2.0 written | Yes |
| Docker backend runs (health only) | Yes |
| Rule engine R01–R10 | No (at baseline) |
| React UI started | No |

**Week 2 status:** ~75% complete at baseline.

---

## 11. Key output file locations

| What | Where |
|------|-------|
| Parsed MASC components | `data/data-masc/parsed/` |
| Parser sign-off report | `data/data-masc/parsed/masc_parse_signoff_report.json` |
| Split summary | `data/data-masc/splits/split_summary.json` |
| Rico holdout manifest | `data/data-rico-holdout/manifest/selection_report.json` |
| JSON schema | `docs/schemas/auditor_schema.json` |
| Example outputs | `docs/examples/components.json`, `violations.json`, `report.json` |

---

## 12. Literature insights (Chen et al., IEEE TSE 2021)

**Paper:** *Accessible or Not? An Empirical Investigation of Android App Accessibility* (Chen et al., 2021, DOI [10.1109/TSE.2021.3108162](https://doi.org/10.1109/TSE.2021.3108162))

**Why it matters for Axion:** The paper studies **86,767 issue-level findings** from **2,270 Android apps** using automated exploration (tool: **Xbot**). This validates our approach of rule-based, violation-level auditing rather than only screen-level pass/fail.

### Top real-world issue types (literature + our Week 3 validation)

| Rank | Issue type (literature) | Our rule(s) | Week 3 evidence |
|------|-------------------------|-------------|-----------------|
| 1 | Small touch target | **R04**, R17 | 3 hits on 20 MASC screens (Salar validation) |
| 2 | Missing label / content description | **R01**, R02, R30 | 261 R01 + 28 R02 on 20 MASC screens |
| 3 | Low contrast | **R09** | Placeholder — needs screenshot CV (Stretch) |
| 4 | Unlabeled input | **R05**, R20 | 9 R05 hits on validation sample |
| 5 | Image/icon without text alternative | **R02**, R30 | Covered by R02 |

### Findings we apply directly

1. **Prioritize R01–R05** in MVP — highest frequency in literature and in our MASC sample.
2. **Investigate R07 dominance** — 65% of violations in Salar's 20-screen run; may include parser `[0,0,0,0]` bounds fallback (follow-up needed).
3. **Issue-level JSON** (`violations.json` → `report.json`) matches research direction — enables severity stats and guideline mapping.
4. **Fixing gap** — Chen et al. report many apps do not improve accessibility across versions; our agent layer should produce actionable developer fixes, not just detection counts.

**Source for our validation counts:** `outputs/validation_logs/week3_summary.md` (Salar, `salar` branch).

---

## 13. Rule & guideline ownership checklist (R01–R30)

> All 30 rules and 30 guidelines are **team-owned**. "Lead" implements; "Reviewers" must approve PRs. Canonical G↔R mapping: `docs/accessibility_guidelines_report.md` §3–§4.

### Block leads (from `updated_plan.md`)

| Block | Rule lead | Guideline validation | Reviewers |
|-------|-----------|----------------------|-----------|
| R01–R10 / G01–G10 | **Salar** | **Noor** | Ayesha |
| R11–R20 / G11–G20 | **Ayesha** | **Salar** | Noor |
| R21–R30 / G21–G30 | **Noor** | **Ayesha** | Salar |

### Per-rule tracker

| Rule | Guideline(s) | Lead | Status | Notes |
|------|--------------|------|--------|-------|
| R01 | G01, G02, G30 | Salar | ✅ Done | High frequency in validation |
| R02 | G02, G30 | Salar | ✅ Done | |
| R03 | G03 | Salar | ✅ Done | |
| R04 | G04, G17 | Salar | ✅ Done | DPI-aware (Week 3 fix) |
| R05 | G05, G20 | Salar | ✅ Done | `hint` field + INPUT_CLASSES |
| R06 | G06, G26 | Salar | ✅ Done | |
| R07 | G07, G25 | Salar | ✅ Done | Review false-positive rate |
| R08 | G08, G15 | Salar | ✅ Done | Zero-area guard added |
| R09 | G09, G11 | Salar | 🟡 Stub | Needs screenshot contrast |
| R10 | G10, G28, G29 | Salar | ✅ Done | |
| R11 | G11 | Ayesha | 🟡 Stub | `docs/r11_r12_design.md` |
| R12 | G12 | Ayesha | 🟡 Stub | Flags VideoView only |
| R13 | G13 | Ayesha | ⬜ Week 4+ | |
| R14 | G14 | Ayesha | ⬜ Week 4+ | |
| R15 | G15, G16 | Ayesha | ⬜ Week 4+ | |
| R16 | G16 | Ayesha | ⬜ Week 4+ | |
| R17 | G17 | Ayesha | ⬜ Week 4+ | Pairs with R04 |
| R18 | G18 | Ayesha | ⬜ Week 4+ | |
| R19 | G19 | Ayesha | ⬜ Week 4+ | |
| R20 | G05, G20 | Ayesha | ⬜ Week 4+ | |
| R21 | G21 | Noor | ⬜ Week 4+ | |
| R22 | G22 | Noor | ⬜ Week 4+ | |
| R23 | G01, G23 | Noor | ⬜ Week 5+ | |
| R24 | G24 | Noor | ⬜ Week 5+ | |
| R25 | G25 | Noor | ⬜ Week 5+ | |
| R26 | G06, G26 | Noor | ⬜ Week 5+ | |
| R27 | G27 | Noor | ⬜ Week 6+ | |
| R28 | G10, G28 | Noor | ⬜ Week 6+ | |
| R29 | G29 | Noor | ⬜ Week 6+ | |
| R30 | G01, G30 | Noor | ⬜ Week 6+ | |

**Legend:** ✅ implemented + tests · 🟡 stub/partial · ⬜ not started

---

## 14. Recommended next steps (updated Week 3)

1. **Salar:** Tune R07 false positives; begin R13–R15 with team
2. **Ayesha:** Push `frontend/`; refine R11/R12 stubs; connect to audit API
3. **Noor:** Wire LLM into `src/agent.py`; add `src/report.py`; Rico holdout eval design
4. **All:** Demo — XML upload → API → violations → report.json on one screen

---

## 15. Team weekly updates

> **Instructions:** Each intern adds a dated entry after pushing work. Newest week at the top. Keep entries factual — file names, test counts, branch commits.

### Week 3 — Salar (`salar` branch, commits `c46b4da` → `712dbd8`)

**Pushed by:** Muhammad Salar Khan  
**Latest:** `712dbd8` — violations outputs + Week 3 validation logs

**Completed:**
- R01–R10 rule checker + **23 pytest tests**
- R04/R05/R08 fixes (real DPI, `hint`, overlap zero-area guard)
- `app.py` wired to Stage 2 (violations table + download)
- `outputs/violations/` — 69 files (MASC + fixtures)
- `outputs/validation_logs/week3_summary.md` — 20/20 schema pass
- `docs/r11_r12_design.md` shared with Ayesha

**Blockers:** None

---

### Week 3 — Ayesha (`ayesha` branch)
Pushed by: Ayesha Naveed

Completed:
* Set up React frontend project (Vite + Tailwind CSS) under `frontend/`
* Built folder structure: `pages/`, `components/`, layout wrapper, reusable UI components (Button, Input, Divider, Logo)
* Implemented 6 auth screens matching Figma designs: Sign Up, Log In, Forgot Password, Verify Code, Set Password, Password Reset Success
* Corrected route paths to match SDS §9.3 (`/verify-otp`, `/reset-password`, `/dashboard/:auditId`, `/report/:auditId`, added `/records`)
* Pulled `src/rules.py` from `salar` branch; added R11 (Color-Only Info) and R12 (Missing Captions) detection stub functions
* Opened PR #3 "Add R11/R12 detection stubs"
* Updated `frontend/` folder — synced onto `noor` branch by Noor (3 Jul, 38 files)

Pending:

* Agent/model prompt experiment session with Noor — not yet scheduled
* Wire frontend pages to FastAPI (`POST /api/v1/audit`, violations fetch) — Week 4
* Making necessary changes to frontend (Ayesha)

Blockers:None

### Week 3 — Noor (`noor` branch)

**Pushed by:** Muhammad Noor  
**Date:** 3 July 2026

**Completed:**
- Synced Salar Week 3 code + violations to `noor` branch (`fd6036b`)
- Added **§12 Literature insights** and **§13 Rule ownership checklist** (this report)
- Scaffolded **`src/agent.py`** — score formula (TBD-02), template enrichment (unit tests; not API-wired yet)
- Added **`backend/routers/audit.py`** — violations-only API (`POST /api/v1/audit` → parse → rules → `GET .../violations`)
- Added **`tests/test_agent.py`** (2 tests), **`tests/test_audit.py`** (2 tests)
- **Frontend sync (Ayesha → `noor`):** pulled `frontend/` from `ayesha` branch (`7a591b0`) — **38 files**
  - Stack: React 19, Vite 8, Tailwind 4, React Router 7
  - Auth: SignUp, Login, ForgotPassword, VerifyCode, SetPassword, ResetSuccess
  - App pages: Upload, Dashboard, Report, Records (+ shared Sidebar, layouts, UI kit)
  - Run: `cd frontend && npm ci && npm run dev` → http://localhost:5173
  - Status: UI scaffold only — no live calls to FastAPI yet
- **Validation logs (Noor Week 3):** same pattern as Salar's `week3_summary.md` / `week3_validation_log.txt`
  - `outputs/validation_logs/noor_week3_summary.md` — scope, 27 pytest pass, CLI↔API parity, schema pass
  - `outputs/validation_logs/noor_week3_validation_log.txt` — full terminal log (8 steps)
  - Re-run: `python scripts/noor_week3_validate.py`
- **SRS cleanup:** auth endpoints in §9 table; TBD-06 marked resolved; §1.4.2 auth moved to Must Have

**Pending:**
- Wire live LLM into agent (Week 4)
- Connect frontend to FastAPI
- `src/report.py` HTML/PDF generation
- Auth + Records API implementation

**Blockers:** None

---

## 16. Document history

| Version | Date | Author | Changes |
|---------|------|--------|---------|
| 1.0 | 1 Jul 2026 | Noor | Initial empirical report (Weeks 1–2 baseline) |
| 1.0.1 | Jul 2026 | Noor | Added to repo `docs/progress/`; team update template |
| 1.1 | 3 Jul 2026 | Noor | Literature insights, R01–R30 ownership table, Noor Week 3 deliverables |
| 1.2 | 3 Jul 2026 | Noor | Frontend sync on `noor`, Noor validation logs, violations-only API push |
| 1.3 | 3 Jul 2026 | Noor | §4 project folder structure updated for Week 3 repo layout |

---

**— End of Supplementary Progress Report —**
