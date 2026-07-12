# Agentic Accessibility Auditor — Updated 8-Week Plan

**Project:** Agentic Accessibility Auditor (Axion)  
**Duration:** 8 weeks (Summer 2026)  
**Last updated:** 12 July 2026  
**Status:** End of Week 5 — HTML/PDF report export shipped on `noor` (`4ce430feb`); entering Week 6 (auth + records)

---

## Team (named roles)

| Role | Name | GitHub branch | Primary focus |
|------|------|---------------|---------------|
| **Intern 1** | **Salar** | `azeem` → rename to `salar` | MASC data (with Noor); parser (with Noor); **rules implementation**; `components.json`; Docker; **tests** (with Noor) |
| **Intern 2** | **Ayesha** | `ayesha` | **Rico holdout**; Figma + React frontend; **SRS co-author** (with Salar); rules **review** (with Noor) |
| **Intern 3 (Lead)** | **Muhammad Noor** | `noor` | **Backend API**; **JSON schemas**; **SDS**; **SRS review**; agent + **report template**; `violations.json` (with Salar); MASC data; parser extensions; **tests**; QA/coordination |

**Repository:** [github.com/MuhammadNoor7/agentic-accessibility-auditor](https://github.com/MuhammadNoor7/agentic-accessibility-auditor)  
**Default branch on GitHub:** `ayesha`

---

## Canonical documents (read these first)

| Document | Path | Purpose |
|----------|------|---------|
| **SRS v2.0** | `d:\internship\srs\SRS_Agentic_Accessibility_Auditor_v2.0.md` | What the system must do |
| **SDS v2.0** | `d:\internship\sds\SDS_Agentic_Accessibility_Auditor_v2.0.md` | How to implement it |
| **Progress report** | `d:\internship\reports\Supplementary_Progress_Report_v1.0.md` | What is actually done |
| **This plan** | `d:\internship\updated_plan.md` | Weekly schedule + folder map |

Formatted Word/PDF versions of SRS and SDS are in the `srs\` and `sds\` folders.

---

## Workspace folder map (July 2026)

Use this layout — the project was reorganized in late June:

```
d:\internship\
│
├── agentic-accessibility-auditor\     ★ MAIN REPO — all code changes go here
│   ├── src\
│   │   ├── parser.py                  ✅ Done
│   │   ├── schema_documents.py        ✅ Done
│   │   ├── rules.py                   ✅ Done (R01–R30)
│   │   ├── agent.py                   ✅ Done (Week 4)
│   │   ├── report.py                  ✅ Done (Week 5 — Jinja2 + Playwright PDF)
│   │   ├── templates/audit_report.html.j2  ✅ Week 5
│   │   ├── explainer.py               ✅ Done (Week 4)
│   │   └── llm_providers.py           ✅ Done (Week 4)
│   ├── backend\
│   │   ├── main.py                    ✅ Audit API v0.4.0 (violations + report + download)
│   │   └── routers/audit.py           ✅ POST /audit, GET …/report/download
│   ├── frontend\                      ✅ Partial — Upload/Dashboard/Report wired; Records mock
│   ├── tests/fixtures/rules/          ✅ 57 XML fixtures (R01–R30 pass/fail)
│   ├── scripts\                       ✅ 12+ dataset/QA utilities (+ noor_week5_validate.py)
│   ├── docs\                          ✅ Schemas, guidelines, QA plan, progress report v1.7
│   ├── data\
│   │   ├── data-masc\                 ✅ 7,068 screens + parsed outputs
│   │   ├── data-rico-holdout\        ✅ 1,698 holdout
│   │   ├── xml\                       Generic uploads
│   │   └── screenshots\
│   ├── outputs\
│   │   ├── violations\                Stage 2 output (generated locally)
│   │   ├── reports\                   Stage 3–4: JSON + HTML/PDF
│   │   └── validation_logs\           noor_week1–5 logs
│   ├── docker-compose.yml             ⚠️ Deferred on `noor` (Salar branch)
│   ├── test_run.py                    ✅ Batch + single + --fixtures
│   └── app.py                         ✅ Streamlit dev tool
│
├── project-folder-salar\              Salar's local copy + git clone
├── srs\                               SRS v2.0 markdown + formatted docx/pdf
├── sds\                               SDS v2.0 markdown + formatted docx/pdf
├── reports\                           Progress reports (this folder)
├── basic scripts\                       md_to_docx.py, docx_to_pdf.py
├── masc-data collection\                Original MASC download
├── other datasets\                      Rico, OneExample archives
└── updated_plan.md                      ← You are here
```

**Do not use** deprecated `intern1` folders — see `intern1_folder_review.md` for why.

---

## Pipeline (what we are building)

```
Screenshot + UIAutomator XML
    → Parser (Salar lead; Noor + Ayesha support)          → components.json     ✅ DONE
    → Rule engine (Team: Salar + Ayesha + Noor)           → violations.json     ✅ R01–R30
    → Agent/model layer (Noor + Ayesha; Salar support)    → report.json         ✅ Week 4
    → Report generator (Noor lead; team support)          → HTML / PDF          ✅ Week 5 (Noor)
    → Axion UI (Ayesha lead; Noor + Salar support)        → upload / dashboard  ✅ Partial (Records Week 6)
    → Auth + Records (team)    → per-user history    ⬜ Week 6–7
```

---

## Rule & guideline collaboration matrix (mandatory)

All 30 rules and 30 guidelines are a **team responsibility**. Ownership below means implementation lead, not solo ownership.

| Block | Rule lead | Guideline validation lead | Required reviewers |
|------|-----------|---------------------------|--------------------|
| **R01–R10 / G01–G10** | Salar | Noor | Ayesha + Noor |
| **R11–R20 / G11–G20** | Ayesha | Salar | Noor + Salar |
| **R21–R30 / G21–G30** | Noor | Ayesha | Salar + Ayesha |

Minimum policy:
- Every rule PR must include at least one reviewer from the other two interns.
- Every rule must reference mapped guideline IDs (Gxx) in output/recommendation docs.
- No rule/guideline block is considered complete unless all three have contributed code/tests/review.

---

## Progress snapshot (1 July 2026)

| Milestone | Target week | Actual status |
|-----------|-------------|---------------|
| MASC dataset local + splits | Week 1–2 | ✅ 7,068 screens, 70/15/15 split |
| Hybrid XML parser | Week 2 | ✅ 7,068/7,068 PASS sign-off |
| Rico holdout (unseen eval) | Week 2 | ✅ 1,698 disjoint screens built |
| JSON schemas + examples | Week 1–2 | ✅ `auditor_schema.json` + docs |
| SRS + SDS v2.0 | Week 2 | ✅ Written with Figma screenshots |
| Docker skeleton | Week 1–2 | ⚠️ Partial (no frontend service) |
| Rule engine R01–R30 | Week 3–8 | 🟡 In progress (R01–R10 implemented; R11–R30 pending) |
| React Axion UI | Week 3–6 | ❌ Not started |
| Rule engine R01–R30 | Week 3–4 | ✅ Done + 57 XML fixtures |
| Agent + report API | Week 4 | ✅ `GET …/report` |
| HTML/PDF report export | Week 5 | ✅ `src/report.py` + download API |
| Axion UI (core pages) | Week 4–5 | ✅ Upload/Dashboard/Report wired |
| Auth + Records | Week 6–7 | ❌ Spec only (SRS §4.9) |
| Final evaluation (Rico holdout) | Week 8 | ❌ Not started |

---

## Revised 8-week schedule

### Phase 1 — Foundation (Weeks 1–2) ✅ Mostly complete

#### Week 1 — Setup, data, schemas

| Person | Planned | **Actual outcome** |
|--------|---------|-------------------|
| **Salar** | Docker setup, data collection | Docker Compose created; MASC dataset integrated |
| **Ayesha** | JSON schemas, Figma, GitHub | `auditor_schema.json`, `json_schemas.md`, Figma screens in SRS |
| **Noor** | QA plan, project board, schema review | `qa_test_plan.md`, guidelines report, repo coordination |

#### Week 2 — Parser + documentation

| Person | Planned | **Actual outcome** |
|--------|---------|-------------------|
| **Salar** | XML parser → `components.json` | **Done** — hybrid parser; 7,068 MASC parses PASS |
| **Ayesha** | React dashboard (basic) | **Deferred** — Figma + schemas done; React not started |
| **Noor** | Report library research, Docker wiring | Rico holdout built; SRS/SDS v2.0 merged |

**Week 2 carry-over into Week 3:** React scaffold (Ayesha), rules engine (Salar).

---

### Phase 2 — Core logic (Weeks 3–4) ✅ Complete

#### Week 3 — Rule engine + UI foundation (completed Jul 2026)

| Person | Planned | **Actual outcome** |
|--------|---------|-------------------|
| **Salar** | R01–R05 + validation | R01–R30 in `check()`; MASC full scan |
| **Ayesha** | UI scaffold + R11/R12 stubs | Figma + schemas; React deferred to Week 4 |
| **Noor** | Agent scaffold + R13–R20 | Parser extensions; `noor_week3_validate.py` |

#### Week 4 — Full rules + agent prompts (completed 9–11 Jul 2026)

| Person | Planned | **Actual outcome** |
|--------|---------|-------------------|
| **Salar** | R13–R15 + explainer layer | `explainer.py`, `llm_providers.py`, visibility filter |
| **Ayesha** | Dashboard + R11–R15 tests | Frontend ↔ API wiring; TBD-01 Groq default |
| **Noor** | Agent API + R21–R30 | `GET …/report`; 94→120 pytest after Week 5 |

---

### Phase 3 — Integration (Weeks 5–6) ← **CURRENT**

#### Week 5 — Reports + pipeline wiring (completed 12 Jul 2026, `4ce430feb`)

| Person | Planned | **Actual outcome** |
|--------|---------|-------------------|
| **Salar** | FastAPI orchestration | Rules R16–R20 covered by new XML fixtures + tests |
| **Ayesha** | Report page + download modal | `Report.jsx` + `downloadAuditReport()` wired |
| **Noor** | `src/report.py` HTML/PDF | Jinja2 + Playwright PDF; download API; 21 new R09–R20 fixtures; `noor_week5_validate.py` |

**Week 5 demo goal:** Upload XML → dashboard → downloadable HTML/PDF report. **Met.**

#### Week 6 — Auth, Records, big audit run

| Person | Tasks | Deliverable |
|--------|-------|-------------|
| **Salar** | Auth backend (JWT); records persistence; contribute to R21–R25 implementation | Auth + Records API + R21–R25 code support |
| **Ayesha** | Auth screens + records page; contribute to R21–R25 tests; continue model experiments | Full Axion auth flow + R21–R25 tests |
| **Noor** | Run pipeline on 25–40 screens; manual validation; lead R26–R30 design and review | Evaluation sheet + R26–R30 design doc |

---

### Phase 4 — Polish & delivery (Weeks 7–8)

#### Week 7 — QA, benchmark, bug fixes

| Person | Tasks | Deliverable |
|--------|-------|-------------|
| **Salar** | Fix rule false positives; complete assigned R-block gaps | Stable rule engine across all 30 rules |
| **Ayesha** | UI polish; finalize model/prompt comparison notes; close R-block test gaps | Production-quality Axion + model comparison |
| **Noor** | Rico holdout evaluation; compile rule-wise and guideline-wise summary | Holdout results + G01–G30 coverage report |

#### Week 8 — Final deliverables

| Person | Tasks | Deliverable |
|--------|-------|-------------|
| **Salar** | Rule + Docker documentation; rename branch to `salar` | Rule-engine handoff docs |
| **Ayesha** | Figma + React UI + model experiment documentation | UI + agentic/model handoff doc |
| **Noor** | Final internship report; 5–7 min demo; coordinate presentation | Final report + demo with 30/30 coverage |

---

## Priority tiers (from SRS v2.0)

| Tier | Scope |
|------|-------|
| **Must Have** | Parser ✅ · R01–R10 rules · LLM explanations · HTML/PDF report · Axion Upload/Dashboard/Report · Auth + Records · Docker · 25–40 screen eval |
| **Should Have** | R11–R20 · batch API · annotated screenshot regions in UI · Ayesha model/prompt experiments integrated |
| **Stretch** | R21–R30 · R09 contrast (CV) · CNN classifier / lightweight model training · click-to-highlight in HTML report · benchmark dataset export |

---

## Git workflow

| Rule | Detail |
|------|--------|
| Branch per intern | `salar` (was `azeem`), `ayesha`, `noor` |
| Push frequency | ≥ 3× per week (SRS BR-3) |
| Weekly demo | Mandatory — show working increment |
| Do not commit | `.venv/`, `.env`, raw dataset binaries, large parsed trees (follow `.gitignore`) |
| Merge target | Coordinate through Noor before merging to shared branches |

---

## Module ownership (quick reference)

| Module / artifact | Owner | SRS section | SDS section |
|-------------------|-------|-------------|-------------|
| Data collection | All | §6 | §4 |
| MASC dataset + parse | Salar + Noor | §6 | §4 |
| Rico holdout | Ayesha | §6 | §4 |
| Parser → `components.json` | Salar / Noor | §4.2 | §3.1 |
| Rule engine → `violations.json` | Salar (review: Ayesha + Noor) | §4.3, §7 | §3.2 |
| Agent → `report.json` | Noor | §4.5 | §3.3 |
| Report HTML/PDF template | Noor | §4.6 | §3.4 |
| JSON schemas + `json_schemas.md` | Noor | §8 | §4 |
| Backend / FastAPI API | Noor | §9 | §3.5 |
| Axion UI | Ayesha | §3.1, Appendix F | §9 |
| SRS v2.0 | Ayesha + Salar (review: Noor) | — | — |
| SDS v2.2 | Noor | — | — |
| pytest suite | Salar + Noor | §10 | §13 |
| Auth + Records | Ayesha + Salar | §4.9 | §10 |
| Docker | Salar | Appendix E | §11 |
| Evaluation | Noor | §11 | §13 |

---

## Open decisions (resolve in Week 3)

| ID | Decision | Owner | Status | Resolution |
|----|----------|-------|--------|------------|
| TBD-01 | LLM/model choice (+ training strategy) | Noor + Ayesha | Resolved | Groq (llama-3.3-70b-versatile) chosen as default — only free, testable provider. Anthropic/OpenAI require paid credits; Gemini blocked by a quota bug. See `docs/TBD-01-decision.md` |
| TBD-02 | Score formula | Noor | Resolved | SDS formula: 100 − weighted penalties |
| TBD-03 | dp/density for R04 | Salar | Open | Assume 160 dpi; bounds as px for MVP |
| TBD-05 | Severity UI mapping | All | Open | High → Critical/Serious; Medium → Moderate; Low → Minor |
| TBD-06 | Auth in MVP | — | Resolved | Must Have (SRS §4.9) |
| — | Branch rename: `azeem` → `salar` | Salar | Done | — |

---

## Weekly demo checklist (use every Friday)

- [ ] Each intern pushed to their branch this week  
- [ ] Demo shows one new working feature (not slides only)  
- [ ] JSON outputs pass `scripts/validate_output.py`  
- [ ] Progress note added (optional: `docs/progress/weekN.md`)  
- [ ] Blockers escalated to Noor before weekend  

---

## How this plan differs from the original `updated_plan.pdf`

| Original (June 17 PDF) | This update (July 1) |
|------------------------|----------------------|
| Generic "Intern 1/2/3" | Named: **Salar, Ayesha, Noor** |
| 900–1000 Kaggle screens target | **MASC 7,068** + **Rico holdout 1,698** |
| React UI in Week 2 | Deferred to Week 3 (parser took priority) |
| Rules split across interns | **All three share R01–R30 and G01–G30 by defined blocks** |
| No Auth/Records | **Must Have** per SRS v2.0 |
| No SRS/SDS v2.0 | Complete specs in `srs/` and `sds/` |
| Assumes all stretch goals | Stretch goals marked; MVP scope clarified |

---

## Contact & escalation

| Issue | Escalate to |
|-------|-------------|
| Schema / API contract disagreement | Noor (Lead) |
| Parser or rule logic | Salar |
| UI / Figma mismatch | Ayesha |
| Schedule / scope | Noor → Supervisor |

---

**— End of Updated 8-Week Plan —**
