# Supplementary Progress Report

## Agentic Accessibility Auditor (Axion)

**Practical work completed — Weeks 1–2 (baseline 1 July 2026)**  
**Living document — see §15 for team updates after 1 July**

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
| Rule engine (Stage 2) | **Not started** at baseline — see §15 for Salar's Week 3 update |
| Agent layer (Stage 3) | Not started |
| Report generator (Stage 4) | Not started |
| Axion React UI | Not started — Figma designs captured in SRS Appendix F |
| Auth + Records | Specified in SRS v2.0; not implemented in code |
| Docker | Partial — `docker-compose.yml` runs backend + batch auditor; no frontend service yet |
| Documentation | SRS v2.0, SDS v2.0, guidelines report, JSON schemas, QA plan — all written |

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

## 4. Workspace layout

```
d:\internship\
├── agentic-accessibility-auditor\   ← MAIN CODE REPO (canonical)
├── project-folder-salar\            ← Salar's working copy
├── srs\                             ← SRS v2.0
├── sds\                             ← SDS v2.0
├── reports\                         ← Local formatted exports
├── docs\                            ← Shared assets
├── basic scripts\                   ← md_to_docx.py, docx_to_pdf.py
├── updated_plan.md                  ← Updated 8-week plan
└── ...
```

**Important:** Use `agentic-accessibility-auditor\` as the single source of truth for code.

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

## 12. Recommended next steps (baseline 1 Jul)

1. **Salar:** Implement `src/rules.py` — R01–R05 first, with 10–15 controlled XML test files
2. **Ayesha:** Scaffold `frontend/` — auth + upload pages per Figma
3. **Noor:** Scaffold `src/agent.py` + `src/report.py`; resolve TBD score formula
4. **All:** Weekly demo — one screen through parse → rules → stub report

---

## 13. Team weekly updates

> **Instructions:** Each intern adds a dated entry after pushing work. Newest week at the top. Keep entries factual — file names, test counts, branch commits.

### Week 3 — Salar (`salar` branch, commit `c46b4da`)

**Pushed by:** Salar  
**Commit:** `feat(rules): implement R01-R10 rule checker with tests and fixtures`

**Completed:**
- Added `src/rules.py` — Stage 2 rule checker for **R01–R10**
- Added `tests/test_rules.py` + **14 XML fixtures** under `tests/fixtures/rules/`
- Added `conftest.py` for pytest imports
- Updated `test_run.py` — runs rules after parse; writes `outputs/violations/{screen_id}_violations.json`; `--skip-rules` flag
- Updated `requirements.txt` — added `pytest>=8.0.0`
- **17/17 pytest tests passing** on `salar` branch

**Rules implemented:** R01 missing label, R02 image button, R03 duplicate labels, R04 small touch target, R05 unlabeled input, R06 disabled control, R07 zero size, R08 layout overlap, R09 low contrast (placeholder), R10 text overflow

**Not done yet (from Week 3 plan):**
- `validate_output.py` run documented on violations output at scale
- Rico holdout batch parse with rules (Week 4 item)
- R11–R30 (later weeks)

**Blockers:** None reported

---

Week 3 — Ayesha (`ayesha` branch)
Pushed by: Ayesha Naveed

Completed:
* Set up React frontend project (Vite + Tailwind CSS) under `frontend/`
* Built folder structure: `pages/`, `components/`, layout wrapper, reusable UI components (Button, Input, Divider, Logo)
* Implemented 6 auth screens matching Figma designs: Sign Up, Log In, Forgot Password, Verify Code, Set Password, Password Reset Success
* Corrected route paths to match SDS §9.3 (`/verify-otp`, `/reset-password`, `/dashboard/:auditId`, `/report/:auditId`, added `/records`)
* Pulled `src/rules.py` from `salar` branch; added R11 (Color-Only Info) and R12 (Missing Captions) detection stub functions
* Opened PR #3 "Add R11/R12 detection stubs"
* Updated `frontend/` folder pushed on github.

Pending:
* Agent/model prompt experiment session with Noor — not yet scheduled
* Making necessary changes to frontend

Blockers:None

### Week 3 — Noor (`noor` branch)

**Pushed by:** Muhammad Noor  
**Date:** 1 July 2026 (and ongoing)

**Completed:**
- Published supplementary progress report to `docs/progress/` on `noor` branch
- SRS v2.0, SDS v2.0, updated 8-week plan (local `d:\internship\`)

**Pending:**
- `src/agent.py` scaffold
- FastAPI `POST /api/v1/audit` stub
- Lock score formula (TBD-02)
- SRS minor cleanup (auth API table, TBD-06)

**Blockers:** None

---

## 14. Document history

| Version | Date | Author | Changes |
|---------|------|--------|---------|
| 1.0 | 1 Jul 2026 | Noor | Initial empirical report (Weeks 1–2 baseline) |
| 1.0.1 | Jul 2026 | Noor | Added to repo `docs/progress/`; §13 team update template; Salar Week 3 entry |

---

**— End of Supplementary Progress Report —**
