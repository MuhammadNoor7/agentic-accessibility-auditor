# Supplementary Progress Report

## Agentic Accessibility Auditor (Axion)

**Practical work completed — Weeks 1–4 (baseline 1 July 2026; updated 9 July 2026)**  
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

| Area | Result (9 Jul on `noor`) |
|------|--------------------------|
| Parser (Stage 1) | **Complete** — hybrid XML parser; MASC `<wrapper>` + bounds fixes; visibility field; R13–R20 extended fields |
| Rule engine (Stage 2) | **R01–R30 implemented** — visibility filter; R11 implemented; R09 needs declared colors/screenshot; **94 pytest** |
| Agent layer (Stage 3) | **Wired** — `src/explainer.py` + `src/agent.py` (`build_audit_report`); LLM or template fallback; API-wired |
| Report generator (Stage 4) | Not started — no `src/report.py` HTML/PDF yet |
| Axion React UI | **On `noor` branch** — Ayesha `frontend/` synced (latest 8 Jul); **not calling live API** (mock data) |
| FastAPI audit API | **Partial** — `POST /audit` → violations + **`GET …/report`** (score + agent fields); no auth/records/download |
| Auth + Records | Specified in SRS v2.0; not implemented in code |
| Docker | Deferred on `noor` (removed); Salar owns Docker on `salar` |
| Documentation | SRS v2.0, **SDS v2.2**, progress report **v1.6** |

**Bottom line (9 Jul):** Week 4 agent wiring is done — real API demo: XML → R01–R30 → `report.json` (template mode without live LLM). Next: Ayesha frontend↔API + prompt experiments (TBD-01); Noor `src/report.py` HTML/PDF.

---

## 3. Pipeline status (actual vs planned)

| Stage | Owner | Output artefact | Status (9 Jul) | Evidence |
|-------|-------|-----------------|----------------|----------|
| 1 — Parser | Salar / Noor | `*_components.json` | **Done** (R13–R20 fields + visibility) | `data/data-masc/parsed/` (7,068 files, sign-off PASS) |
| 2 — Rules | Salar / Noor | `violations.json` | **Done** R01–R30 | `src/rules.py`; fixtures R11 + R21–R30 |
| 3 — Agent | Noor / Salar | enriched `report.json` | **Done** (API-wired) | `src/agent.py` + `src/explainer.py`; `GET …/report` |
| 4 — Report | Noor | HTML/PDF | Planned | No `src/report.py` |
| UI — Axion | Ayesha | React dashboard | **Scaffold** | `frontend/` on `noor`; mock data only |
| API | Noor | FastAPI audit routes | **Partial** | violations + report; no auth/records/download |
| Auth/Records | Ayesha / Salar | JWT + per-user history | Planned | SRS §4.9 only |

---

## 4. Project folder structure (repository root)

> **As of 9 July 2026** on branch `noor` — canonical repo: [agentic-accessibility-auditor](https://github.com/MuhammadNoor7/agentic-accessibility-auditor)

```
agentic-accessibility-auditor/          ← repo root (clone / _noor_push locally)
│
├── src/                                ← Stage 1–3 Python core
│   ├── parser.py                       ← XML → components.json (Stage 1; R13–R20 fields + visibility)
│   ├── rules.py                        ← R01–R30 rule checker (Stage 2)
│   ├── agent.py                        ← Score + build_audit_report (Stage 3; API-wired)
│   ├── explainer.py                    ← Live LLM recommendations (batched; anti-hallucination)
│   ├── guidelines.py                   ← G01–G30 + R→G mapping for explainer
│   ├── llm_providers.py                ← Anthropic / OpenAI / Gemini / Groq
│   └── schema_documents.py             ← JSON envelope builders
│
├── backend/                            ← FastAPI gateway
│   ├── main.py                         ← App entry + CORS + routers
│   ├── requirements.txt
│   ├── models/
│   │   └── audit.py                    ← Pydantic audit response models
│   └── routers/
│       └── audit.py                    ← POST /audit, GET …/violations, GET …/report
│
├── frontend/                           ← Axion React UI (Ayesha, synced to noor)
│   ├── package.json                    ← Vite 8 + React 19 + Tailwind 4
│   ├── vite.config.js
│   ├── public/                         ← favicon, icons
│   └── src/
│       ├── App.jsx                     ← Routes (auth + Upload/Dashboard/Report/Records)
│       ├── main.jsx, index.css
│       ├── state/auditFiles.js         ← Local upload state (not API-wired yet)
│       ├── components/
│       │   ├── Sidebar.jsx
│       │   ├── layout/                 ← AuthLayout, MainLayout
│       │   └── ui/                     ← Button, TextField, OtpInput, FileDropzone, …
│       └── pages/
│           ├── auth/                   ← Login, SignUp, ForgotPassword, VerifyCode, …
│           ├── Upload.jsx, Dashboard.jsx, Report.jsx, Records.jsx
│           └── main/Placeholder.jsx
│
├── tests/                              ← pytest suite (**94** passed on `noor`)
│   ├── test_parser.py
│   ├── test_rules.py                   ← R01–R30 fixtures + visibility filter tests
│   ├── test_agent.py                   ← score + template report
│   ├── test_audit.py                   ← FastAPI violations + report
│   ├── test_explainer.py               ← anti-hallucination / batching (mocked LLM)
│   └── fixtures/rules/                 ← XML fixtures (R01–R12, R21–R30, …)
│
├── data/                               ← datasets + local uploads
│   ├── data-masc/
│   │   ├── parsed/                     ← 7,068 MASC components.json
│   │   │   ├── masc_parse_signoff_report.json
│   │   │   └── batch_parse_masc_full.log
│   │   └── splits/                     ← train / val / test split JSON
│   ├── data-rico-holdout/              ← 1,698-screen holdout + manifest
│   ├── xml/                            ← generic upload XML drops
│   ├── parsed/                         ← generic parsed output
│   └── screenshots/                    ← optional screenshot uploads
│
├── outputs/                            ← pipeline artefacts
│   ├── violations/                     ← *_violations.json
│   ├── reports/                        ← *_report.json (agent-enriched; Week 4)
│   └── validation_logs/
│       ├── week3_summary.md
│       ├── week3_validation_log.txt
│       ├── noor_week3_summary.md
│       ├── noor_week3_validation_log.txt
│       └── masc_reparse_log.txt
│
├── notebooks/
│   └── masc_dataset_analysis.ipynb     ← Salar MASC analysis (synced Week 4)
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
│   ├── validate_output.py
│   ├── noor_week3_validate.py
│   ├── masc_parse_signoff.py
│   ├── run_explainer_sample.py         ← Stage 3 LLM sample runner
│   ├── compare_visibility_filter_impact.py
│   ├── split_masc_dataset.py
│   └── build_rico_holdout.py
│
├── srs/                                ← SRS v2.0 (md + docx)
├── sds/                                ← SDS v2.2 (md + docx)
│
├── app.py                              ← Streamlit dev UI (parse + violations preview)
├── test_run.py                         ← CLI batch / single-file parser + rules
├── .env.example                        ← LLM_PROVIDER + API key template
├── requirements.txt                    ← root Python deps (+ anthropic/openai/groq)
├── updated_plan.md                     ← 8-week team plan
├── conftest.py
└── README.md
```

### Key paths by pipeline stage

| Stage | Primary code | Output location |
|-------|--------------|-----------------|
| 1 — Parser | `src/parser.py`, `test_run.py`, `app.py` | `data/**/parsed/*_components.json` |
| 2 — Rules | `src/rules.py` | `outputs/violations/*_violations.json` |
| 3 — Agent | `src/agent.py`, `src/explainer.py` | `outputs/reports/*_report.json` |
| 4 — Report | `src/report.py` (planned) | HTML/PDF — not started |
| API | `backend/routers/audit.py` | in-memory job → violations + report JSON |
| UI | `frontend/` | browser at `:5173` (mock data; not wired to API yet) |

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

### 5.1 Sign-off result (re-parse 6 July 2026)

| Metric | Value |
|--------|-------|
| Dataset | MASC |
| Total screens | 7,068 |
| Categories | 10 |
| Components parsed | **640,563** |
| Violations (R01–R20) | **462,542** |
| Extended parser fields | **0 missing** (all 13 R13–R20 fields) |
| Parse OK | 7,068 |
| Parse errors | 0 |
| Sign-off | **PASS** |

Source: `data/data-masc/parsed/masc_parse_signoff_report.json`  
Scripts: `python test_run.py --dataset masc` · `python scripts/masc_parse_signoff.py`  
Commit: `f7bcac9` on branch `noor`

**Parser fix (Jul 2026):** MASC widgets nest inside `<wrapper>` nodes; depth-first walk now descends into wrappers (previously ~1 component/screen).

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

### Top real-world issue types (literature + full MASC validation, Jul 2026)

| Rank | Issue type (literature) | Our rule(s) | MASC evidence (7,068 screens) |
|------|-------------------------|-------------|-------------------------------|
| 1 | Missing label / content description | **R01**, R02, R30 | R01: 60,112 violations / 6,185 screens |
| 2 | Layout / focus order issues | **R07**, R08, **R15** | R07: 266,393; R15: 3,860 screens |
| 3 | Small touch target / spacing | **R04**, **R17** | R17: 9,327 violations / 1,697 screens |
| 4 | Multi-gesture only | **R18** | R18: 13,529 violations / 3,945 screens |
| 5 | Unlabeled input | **R05**, **R20** | R05: 3,797; R20: 0 (no hint-only inputs in MASC) |
| 6 | Low contrast | **R09** | 0 — needs screenshot CV |

### Findings we apply directly

1. **Prioritize R01–R05** in MVP — highest frequency in literature and in our MASC sample.
2. **R07 remains dominant** on full MASC — review false-positive rate (bounds fallback).
3. **R13–R20 are active** on real data after parser re-parse (audio, focus order, spacing, gestures).
4. **Issue-level JSON** enables severity stats and guideline mapping per Chen et al.

**Sources:** `outputs/validation_logs/noor_week3_summary.md` · `data/data-masc/parsed/masc_parse_signoff_report.json`

---

## 13. Rule & guideline ownership checklist (R01–R30)

> All 30 rules and 30 guidelines are **team-owned**. "Lead" implements; "Reviewers" must approve PRs. Canonical G↔R mapping: `docs/accessibility_guidelines_report.md` §3–§4.

### Block leads (from `updated_plan.md`)

| Block | Rule lead | Guideline validation | Reviewers |
|-------|-----------|----------------------|-----------|
| R01–R10 / G01–G10 | **Salar** | **Noor** | Ayesha |
| R11–R12 / G11–G12 | **Ayesha** | **Salar** | Noor |
| R13–R20 / G13–G20 | **Noor** | **Salar** | Ayesha |
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
| R09 | G09, G11 | Salar | 🟡 Partial | Needs declared colors / screenshot contrast |
| R10 | G10, G28, G29 | Salar | ✅ Done | |
| R11 | G11 | Ayesha | ✅ Done | Implemented on `salar`/`noor` (checkable-state widgets); Ayesha review pending |
| R12 | G12 | Ayesha | ✅ Done | `media_type` + caption heuristics |
| R13 | G13 | Noor | ✅ Done | 1,055 violations / 118 MASC screens |
| R14 | G14 | Noor | ✅ Done | 1,873 / 667 screens |
| R15 | G15, G16 | Noor | ✅ Done | 3,860 / 3,860 screens |
| R16 | G16 | Noor | ✅ Done | 130 / 115 screens |
| R17 | G17 | Noor | ✅ Done | `related_component`; 9,327 / 1,697 |
| R18 | G18 | Noor | ✅ Done | 13,529 / 3,945 screens |
| R19 | G19 | Noor | ✅ Done | 758 / 416 screens |
| R20 | G05, G20 | Noor | ✅ Done | Unit tests pass; 0 MASC hits |
| R21 | G21 | Noor | ✅ Done | Vague error message (Salar sync Week 4) |
| R22 | G22 | Noor | ✅ Done | No password toggle |
| R23 | G01, G23 | Noor | ✅ Done | Unlabeled nav control |
| R24 | G24 | Noor | ✅ Done | Missing screen title |
| R25 | G25 | Noor | ✅ Done | Uncontrolled animation |
| R26 | G06, G26 | Noor | ✅ Done | No timeout warning |
| R27 | G27 | Noor | ✅ Done | Complex label language |
| R28 | G10, G28 | Noor | ✅ Done | Font scale overflow (needs declared text size) |
| R29 | G29 | Noor | ✅ Done | All-caps body text |
| R30 | G01, G30 | Noor | ✅ Done | Icon-only, no label |

**Legend:** ✅ implemented + tests · 🟡 stub/partial · ⬜ not started

---

## 14. Recommended next steps (updated 9 July 2026)

1. **Ayesha:** Wire `frontend/` to live audit API (`POST /audit`, `GET …/violations`, `GET …/report`); run prompt experiments (`run_explainer_sample.py`) and resolve **TBD-01** with Noor; review R11–R12
2. **Noor:** Start `src/report.py` HTML/PDF; update validation logs for R01–R30; Rico holdout batch parse
3. **Salar:** Tune R07 false positives; improve R09 when colors/screenshots available
4. **All:** Demo — XML upload → API → violations → agent-enriched report (template or live LLM)

---

## 15. Team weekly updates

> **Instructions:** Each intern adds a dated entry after pushing work. Newest week at the top. Keep entries factual — file names, test counts, branch commits.

### Week 4 — Ayesha 

**Pushed by:** Ayesha Naveed
**Date:** 11 July 2026

**Completed:**
- **R11–R12 review sign-off:** reviewed `src/rules.py` implementations of `check_color_only_info` (R11) and `check_missing_captions` (R12) against `docs/r11_r12_design.md`. Confirmed both rules moved past their original Week 3 stub design — R11 now flags checkable-state widgets (CheckBox/Switch/ToggleButton/RadioButton) with no text/content_desc; R12 now uses `parent_id` sibling adjacency plus bounds-proximity fallback, not just a blanket VideoView flag. Ran `pytest tests/test_rules.py -k "r11 or r12"` — all 5 relevant tests passed (fixture pass/fail cases, non-checkable-widget exclusion, sibling-vs-bounds-distance priority, non-media stub behavior).
- **Frontend ↔ API wiring** (Priority 1): Upload, Dashboard, and Report pages now call the live backend (`POST /api/v1/audit`, `GET /report`) instead of mock data. Tested end-to-end with a real XML fixture and Groq — confirmed full pipeline works (upload → audit → dashboard → report).
- **Agent prompt experiments (TBD-01):** ran `scripts/run_explainer_sample.py` — Groq tested successfully (15/15 violations explained, good quality, no hallucination observed). Anthropic/OpenAI blocked by paid billing requirements; Gemini blocked by a Google-side free-tier quota bug (`429`, limit 0) even after Noor's SDK fix resolved the original key-format issue. Documented in `docs/agent_prompt_experiments.md` and `docs/TBD-01-decision.md`; TBD-01 marked Resolved (Groq as default) in this doc's Open Decisions table.

**Pending:**
- Full 4-provider comparison once Anthropic/OpenAI credits are available and Gemini's quota issue is resolved
- Records/Audit History page — blocked on backend (no list endpoint, no persistence yet)
- Auth pages (login/signup/etc.) — blocked on backend (no auth router implemented yet)

**Blockers:** None on my own tasks; Records + Auth wiring blocked on backend work not yet scoped.

---

### Week 4 — Noor (`noor` branch, commits `98efd2fe0` → `0144b1af3`)

**Pushed by:** Muhammad Noor  
**Date:** 9 July 2026

**Completed:**
- **Salar sync** (`98efd2fe0`): Stage 3 LLM layer — `src/explainer.py`, `src/guidelines.py`, `src/llm_providers.py`; rules **R01–R30** + visibility filter; parser bounds/visibility fixes; R11 + R21–R30 fixtures; `scripts/run_explainer_sample.py`, `compare_visibility_filter_impact.py`; `.env.example`
- **Notebook sync** (`20c96fd07`): `notebooks/masc_dataset_analysis.ipynb`
- **Ayesha frontend sync** (`2d8356066`): Report/Sidebar/Dashboard/Records/Upload updates + `frontend/src/state/auditFiles.js`
- **Agent API wiring** (`0144b1af3`): `build_audit_report()` in `src/agent.py` merges explainer + score formula (TBD-02); `GET /api/v1/audit/{id}/report`; pipeline statuses include `explaining`; template fallback when no API key (FR-AG.6); reports → `outputs/reports/`
- **Tests:** **94 pytest** passed (parser, rules R01–R30, agent, audit, explainer)
- Week 4 demo goal met: XML upload → violations → agent-enriched `report.json` (template mode without live LLM)

**Pending:**
- Ayesha: frontend ↔ API wiring; prompt experiments + TBD-01 model choice
- `src/report.py` HTML/PDF (Week 5)
- Formal R11–R15 review sign-off documentation
- Rico holdout batch evaluation
- Auth + Records API

**Blockers:** None (API ready for Ayesha)

---

### Week 3+ — Noor (`noor` branch, commit `f7bcac9`)

**Pushed by:** Muhammad Noor  
**Date:** 6 July 2026

**Completed:**
- **Parser R13–R20 extension** — 13 new component fields (`focus_order`, `parent_id`, `media_type`, etc.)
- **MASC `<wrapper>` fix** — full widget extraction (640,563 components vs ~1/screen before)
- **Rules R13–R20** wired in `check()`; **31** rule tests + **3** parser tests (**38** total with agent/audit)
- **Full MASC re-parse** — 7,068 XML → `data/data-masc/parsed/`; **462,542** violations
- **`scripts/noor_week3_validate.py`** — re-parse + pytest + random 20-screen MASC sample + schema check
- **`scripts/masc_parse_signoff.py`** — extended-field validation + R13–R20 aggregate counts
- **SDS v2.1** — R01–R20 parser/rules design, validation artefact paths
- **`auditor_schema.json`** — optional R13–R20 component fields
- Validation logs: `noor_week3_summary.md`, `noor_week3_validation_log.txt`, `masc_reparse_log.txt`
- Sign-off: `masc_parse_signoff_report.json` → **PASS** (0 extended-field misses)

**Pending:**
- Wire live LLM into agent (Week 4)
- Connect frontend to FastAPI
- `src/report.py` HTML/PDF generation
- Auth + Records API

**Blockers:** None

---

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
| 1.4 | 6 Jul 2026 | Noor | R13–R20 parser/rules, full MASC re-parse, SDS v2.1, validation sign-off |
| 1.5 | 6 Jul 2026 | Noor | R13–R20 rule lead → Noor; DOCX regenerated |
| **1.6** | **9 Jul 2026** | **Noor** | Week 4: R01–R30, explainer + report API, 94 tests, frontend/notebook sync; next steps + §15 |

---

**— End of Supplementary Progress Report —**
