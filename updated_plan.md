# Agentic Accessibility Auditor — Updated 8-Week Plan

**Project:** Agentic Accessibility Auditor (Axion)  
**Duration:** 8 weeks (Summer 2026)  
**Last updated:** 15 July 2026  
**Status:** Week 6 largely complete on `noor` (`92702a71`) — JWT auth + records synced; 40-screen stratified-random eval sheet; Weeks 1–5 done; manual eval fill + Friday demo remaining

---

## Team (named roles)

| Role | Name | GitHub branch | Primary focus |
|------|------|---------------|---------------|
| **Intern 1** | **Salar** | `azeem` → rename to `salar` | MASC data (with Noor); parser (with Noor); **rules** (with Noor + Ayesha); `components.json`; Docker; **tests** (with Noor) |
| **Intern 2** | **Ayesha** | `ayesha` | **Rico holdout**; Figma + React frontend; **SRS co-author** (with Salar); **rules** (with Salar + Noor) |
| **Intern 3 (Lead)** | **Muhammad Noor** | `noor` | **Backend API**; **JSON schemas**; **SDS**; **SRS review**; agent + **report template**; **rules** (with Salar + Ayesha); MASC data; parser extensions; **tests**; QA/coordination |

**Repository:** [github.com/MuhammadNoor7/agentic-accessibility-auditor](https://github.com/MuhammadNoor7/agentic-accessibility-auditor)  
**Default branch on GitHub:** `ayesha`

---

## Canonical documents (read these first)

| Document | Path | Purpose |
|----------|------|---------|
| **SRS v2.3** | `srs/SRS_Agentic_Accessibility_Auditor_v2.0.md` (+ `.docx`) | What the system must do |
| **SDS v2.7** | `sds/SDS_Agentic_Accessibility_Auditor_v2.0.md` (+ `.docx`) | How to implement it |
| **Progress report** | `docs/progress/Supplementary_Progress_Report_v1.0.md` (+ `.docx`) v1.11 | What is actually done |
| **This plan** | `updated_plan.md` (+ `docs/updated_plan_v2.0.docx`) | Weekly schedule + folder map |

Word exports: `scripts/md_to_docx.py` · Figma assets: `docs/assets/figma/`

---

## Workspace folder map (July 2026)

Use this layout — the project was reorganized in late June:

```
agentic-accessibility-auditor/          ★ MAIN REPO (branch: noor)
│   ├── src/                            parser, rules, agent, report, explainer
│   ├── backend/                        audit + JWT auth + records routers
│   ├── frontend/                       Upload/Dashboard/Report/Records/Login wired
│   ├── tests/ + backend/tests/         rules/audit/report + auth suite
│   ├── tests/fixtures/rules/           57 XML fixtures (R01–R30 pass/fail)
│   ├── scripts/                        week1–6 validate + md_to_docx + utilities
│   ├── docs/                           schemas, progress, week6/, figma/, plan DOCX
│   ├── srs/ · sds/                     SRS v2.3 / SDS v2.7 markdown + DOCX
│   ├── data/
│   │   ├── data-masc/                  7,068 screens + parsed outputs + splits
│   │   └── data-rico-holdout/          1,698 holdout
│   ├── outputs/
│   │   ├── violations/samples/         ✅ 56 fixture JSON samples (R01–R30, no R28)
│   │   ├── reports/samples/            ✅ Example JSON/HTML/PDF report
│   │   └── validation_logs/            noor_week1–6 logs + summaries
│   ├── docker-compose.yml              ✅ Synced from Salar (Week 6)
│   └── test_run.py                     batch + single + --fixtures
```

---

## Pipeline (what we are building)

```
Screenshot + UIAutomator XML
    → Parser (Salar lead; Noor + Ayesha support)          → components.json     ✅ DONE
    → Rule engine (Team: Salar + Ayesha + Noor)           → violations.json     ✅ R01–R30
    → Agent/model layer (Noor + Ayesha; Salar support)    → report.json         ✅ Week 4
    → Report generator (Noor lead; team support)          → HTML / PDF          ✅ Week 5 (Noor)
    → Axion UI (Ayesha lead; Noor + Salar support)        → upload / dashboard / records  ✅ Week 6
    → Auth + Records (Salar + Ayesha; Noor sync)          → JWT + per-user history        ✅ Week 6 on `noor`
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

## Progress snapshot (15 July 2026)

| Milestone | Target week | Actual status |
|-----------|-------------|---------------|
| MASC dataset local + splits | Week 1–2 | ✅ 7,068 screens, 70/15/15 split |
| Hybrid XML parser | Week 2 | ✅ 7,068/7,068 PASS sign-off |
| Rico holdout (unseen eval) | Week 2 | ✅ 1,698 disjoint screens built |
| JSON schemas + examples | Week 1–2 | ✅ `auditor_schema.json` + docs |
| SRS + SDS | Week 2+ | ✅ SRS v2.3 / SDS v2.7 + DOCX (Figma embedded) |
| Docker skeleton | Week 1–2 | ✅ Synced to `noor` (Salar Week 6) |
| Rule engine R01–R30 | Week 3–4 | ✅ Done + 57 XML fixtures + 56 sample JSON in repo |
| Agent + report API | Week 4 | ✅ `GET …/report` |
| HTML/PDF report export | Week 5 | ✅ `src/report.py` + download API |
| Axion UI (core pages) | Week 4–5 | ✅ Upload/Dashboard/Report wired (+ pair validation) |
| Auth + Records | Week 6 | ✅ JWT + `/records` on `noor` (Salar); Login/Records UI live |
| 25–40 screen manual eval | Week 6 | 🟡 Sheet ready (40 stratified-random); **manual fill ≥25 pending** |
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

### Phase 3 — Integration (Weeks 5–6) ✅ Mostly complete

#### Week 5 — Reports + pipeline wiring (completed 12 Jul 2026, `4ce430feb`)

| Person | Planned | **Actual outcome** |
|--------|---------|-------------------|
| **Salar** | FastAPI orchestration | Rules R16–R20 covered by new XML fixtures + tests |
| **Ayesha** | Report page + download modal | `Report.jsx` + `downloadAuditReport()` wired |
| **Noor** | `src/report.py` HTML/PDF | Jinja2 + Playwright PDF; download API; 21 new R09–R20 fixtures; `noor_week5_validate.py` |

**Week 5 demo goal:** Upload XML → dashboard → downloadable HTML/PDF report. **Met.**

#### Week 6 — Auth, Records, evaluation batch (updated 15 Jul 2026, `92702a71`)

| Person | Planned | **Actual outcome** |
|--------|---------|-------------------|
| **Salar** | Auth backend (JWT); records persistence | ✅ Done — `backend/auth.py`, `auth_router.py`, `records_router.py`, `test_auth.py`; synced into `noor` |
| **Ayesha** | Auth screens + Records page; prompt experiments | ✅ Login/SignUp wired to JWT; Records on live API; prompt experiments expanded (`3d4fa82`); Dashboard re-run popup |
| **Noor** | 25–40 screen eval; R26–R30 design; sync + docs | ✅ Sync Salar+Ayesha; score/filename on Records; stratified-random 40-screen CSV (`docs/week6/`); R26–R30 design DOCX; `noor_week6_validate.py` + logs; SRS/SDS/progress updated |

**Week 6 remaining (this week):**
- Fill ≥25 **manual** rows on `docs/week6/evaluation_sheet_40_screens.csv` (auto scores already filled; FP/miss notes blank)
- Friday demo: signup/login → upload screenshot+XML pair → dashboard → report HTML/PDF → Records list with score
- OTP / forgot-password backend still **stretch** (UI screens exist)

**Week 6 demo goal:** Auth + upload pair + report download + Records. **Ready to demo** (manual eval fill ongoing).

---

### Phase 4 — Polish & delivery (Weeks 7–8) ← **NEXT**

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
| **Must Have** | Parser ✅ · R01–R30 rules ✅ · LLM explanations ✅ · HTML/PDF ✅ · Upload/Dashboard/Report ✅ · Auth + Records ✅ · Docker ✅ · 25–40 screen eval 🟡 (sheet done; manual fill pending) |
| **Should Have** | Batch API · annotated screenshot regions in UI · deeper prompt comparison notes |
| **Stretch** | OTP auth · R09 contrast (CV) · CNN / lightweight training on MASC train→val→test · click-to-highlight in HTML · Rico holdout batch (Week 8) |

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
| Rule engine → `violations.json` | Salar + Noor + Ayesha (reviewed by all) | §4.3, §7 | §3.2 |
| Agent → `report.json` | Noor | §4.5 | §3.3 |
| Report HTML/PDF template | Noor | §4.6 | §3.4 |
| JSON schemas + `json_schemas.md` | Noor | §8 | §4 |
| Backend / FastAPI audit API | Noor | §9 | §3.5 |
| Auth (JWT) + Records API | Salar (synced by Noor) | §4.9 | §10 |
| Axion UI | Ayesha (+ Salar auth wiring) | §3.1, Appendix F | §9 |
| SRS v2.3 | Ayesha + Salar (updates: Noor) | — | — |
| SDS v2.7 | Noor | — | — |
| pytest suite | Salar + Noor | §10 | §13 |
| Docker | Salar | Appendix E | §11 |
| Evaluation (40-screen sheet) | Noor | §11 | §13 |

---

## Open decisions (resolve in Week 3)

| ID | Decision | Owner | Status | Resolution |
|----|----------|-------|--------|------------|
| TBD-01 | LLM/model choice (+ training strategy) | Noor + Ayesha | Resolved | Groq (llama-3.3-70b-versatile) chosen as default — only free, testable provider. Anthropic/OpenAI require paid credits; Gemini blocked by a quota bug. See `docs/TBD-01-decision.md` |
| TBD-02 | Score formula | Noor | Resolved | `compute_accessibility_score`: start 100; Critical−20, High−10, Medium−5, Low−2; clamp [0,100] |
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
