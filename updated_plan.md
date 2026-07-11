# Agentic Accessibility Auditor — Updated 8-Week Plan

**Project:** Agentic Accessibility Auditor (Axion)  
**Duration:** 8 weeks (Summer 2026)  
**Last updated:** 1 July 2026  
**Status:** End of Week 2 — parser complete; entering Week 3  

---

## Team (named roles)

| Role | Name | GitHub branch | Primary focus |
|------|------|---------------|---------------|
| **Intern 1** | **Salar** | `azeem` → rename to `salar` | Data, parser, shared rules/guidelines implementation, Docker, backend APIs |
| **Intern 2** | **Ayesha** | `ayesha` | UI + schemas + shared rules/guidelines + agentic/model experiments |
| **Intern 3 (Lead)** | **Muhammad Noor** | `noor` | Agent/report lead, shared rules/guidelines, QA/evaluation, coordination |

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
│   │   ├── rules.py                   ⬜ Week 3–8 (Team: Salar + Ayesha + Noor)
│   │   ├── agent.py                   ⬜ Week 4–8 (Team: Noor lead, Ayesha + Salar support)
│   │   └── report.py                  ⬜ Week 5 (Noor)
│   ├── backend\
│   │   └── main.py                    ⚠️ Health only — expand Week 3–6
│   ├── frontend\                      ⬜ Week 3–6 (Ayesha) — create with Vite
│   ├── scripts\                       ✅ 10 dataset/QA utilities
│   ├── docs\                          ✅ Schemas, guidelines, QA plan
│   ├── data\
│   │   ├── data-masc\                 ✅ 7,068 screens + parsed outputs
│   │   ├── data-rico-holdout\        ✅ 1,698 holdout (4 parsed so far)
│   │   ├── final_rico\                Raw Rico corpus
│   │   ├── xml\                       Generic uploads
│   │   └── screenshots\
│   ├── outputs\
│   │   ├── violations\                ⬜ Stage 2 output
│   │   └── reports\                   ⬜ Stage 4 output
│   ├── docker-compose.yml             ⚠️ backend + auditor (no frontend yet)
│   ├── test_run.py                    ✅ Batch parser CLI
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
    → Rule engine (Team: Salar + Ayesha + Noor)           → violations.json     ⬜ Week 3–8
    → Agent/model layer (Noor + Ayesha; Salar support)    → report.json         ⬜ Week 4–8
    → Report generator (Noor lead; team support)          → HTML / PDF          ⬜ Week 5–8
    → Axion UI (Ayesha lead; Noor + Salar support)        → upload / dashboard  ⬜ Week 3–7
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
| LLM agent + reports | Week 4–8 | ⬜ Team setup pending (Ayesha added to model workstream) |
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

### Phase 2 — Core logic (Weeks 3–4) ← **CURRENT**

#### Week 3 — Rule engine + UI foundation

| Person | Tasks | Deliverable |
|--------|-------|-------------|
| **Salar** | Lead R01–R05 hardening + pair with Ayesha on R11/R12 design; run `validate_output.py` on violations samples | R01–R05 stable + validation logs |
| **Ayesha** | Frontend scaffold + start R11–R12 detection stubs + join agent/model prompt experiments with Noor | UI scaffold + first R11/R12 PR + model notes |
| **Noor** | Lock score formula; scaffold `src/agent.py`; support R01–R05 review; define G01–G10 mapping checks | API/agent skeleton + mapping checklist |

**Week 3 demo goal:** One controlled XML file → `violations.json` with R01–R05 hits.

#### Week 4 — Full rules + agent prompts

| Person | Tasks | Deliverable |
|--------|-------|-------------|
| **Salar** | Co-implement R13–R15 with team; start Rico holdout batch parse with rules | R13–R15 PRs + holdout run logs |
| **Ayesha** | Dashboard page + co-implement R11–R15 tests; participate in model fine-tuning/prompt loop | Core dashboard UI + R11–R15 tests + model eval notes |
| **Noor** | LLM prompts/agent wiring + co-implement R21 starter rules; review R11–R15 | `report.json` draft + R21 starter PR |

**Week 4 demo goal:** Parse → rules → agent explanation for one screen.

---

### Phase 3 — Integration (Weeks 5–6)

#### Week 5 — Reports + pipeline wiring

| Person | Tasks | Deliverable |
|--------|-------|-------------|
| **Salar** | FastAPI audit pipeline orchestration; co-work on R16–R20 fixes | End-to-end API + R16–R20 support |
| **Ayesha** | Audit Report page + Generate Report modal; agent/model experiment branch updates | Report UI + model experiment report |
| **Noor** | `src/report.py` generation; integrate agent output with shared rule blocks | Downloadable report + integrated agent flow |

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

| Module | Owner | SRS section | SDS section |
|--------|-------|-------------|-------------|
| Parser | Salar | §4.2 | §3.1 |
| Rule engine (R01–R30) | Salar + Ayesha + Noor (split by blocks) | §4.3, §7 | §6 |
| Agent / model layer | Noor + Ayesha (Salar support) | §4.5 | §7 |
| Report generator | Noor | §4.6 | §8 |
| Axion UI | Ayesha | §3.1, Appendix F | §9 |
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
