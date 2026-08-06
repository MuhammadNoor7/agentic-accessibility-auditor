# Agentic Accessibility Auditor — Updated 8-Week Plan

**Project:** Agentic Accessibility Auditor (Axion)  
**Duration:** 8 weeks (Summer 2026)  
**Plan version:** 2.2  
**Last updated:** 05 August 2026  
**Status:** Week 6 complete · **Week 7 (Noor) QA analysis complete** on `noor` — rule/guideline summaries; Rico holdout batch **now done** (1,698 screens, 0 failures — no longer deferred) · **Post–Week 7 YOLO track:** full 60-epoch MASC-only training run completed 30 Jul (Salar, `salar` branch, merged into `noor`), checkpoint exported (51.2 MB), zero-shot-vs-fine-tuned Rico holdout eval done (mAP50 0.0258 → 0.2546) · **Week 8 rule-accuracy pass (29 Jul):** three false-positive rules (R07, R08, R30) and one parser bug blocking R20/R05 fixed and verified against full MASC (7,068) + Rico holdout (1,698) · **30 Jul–03 Aug: 33-backbone comparison sweep** — original crop-classifier pick (MobileNetV3-Small) tested against 32 alternatives; replaced with **`swin_tiny_patch4_window7_224`** (best in sweep, Rico macro-F1 0.22) · **04–05 Aug: both CV models wired into the backend pipeline** (`confirm_violations()` and `detect_ui()`/`detections_to_components()` called from `backend/routers/audit.py`; `xml` now optional on `POST /api/v1/audit`) — no longer deferred · **05 Aug Docker fixes:** `backend/requirements.txt` dependency sync + `backend/Dockerfile` system-library fix (both caused real startup crashes, found by actually running the containers) + new `frontend` Compose service · **99/99 SRS requirements Done**

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
| **SRS v2.11** | `srs/SRS_Agentic_Accessibility_Auditor_v2.11.md` (+ `.docx`) | What the system must do |
| **SDS v2.15** | `sds/SDS_Agentic_Accessibility_Auditor_v2.15.md` (+ `.docx`) | How to implement it |
| **Progress report v1.27** | `docs/progress/Supplementary_Progress_Report_v1.27.md` (+ `.docx`) | What is actually done — §16 Document history through 05 Aug: 33-backbone sweep, both CV models wired into backend, Docker fixes |
| **This plan** | `updated_plan.md` (+ `updated_plan.docx`) | Weekly schedule + folder map + remaining work |

Word exports: `scripts/md_to_docx.py` · Figma assets: `docs/assets/figma/`

---

## Workspace folder map (05 August 2026)

Use this layout — the project was reorganized in late June, and gained CV models + Docker in Aug:

```
agentic-accessibility-auditor/          ★ MAIN REPO (branch: noor)
│   ├── src/                            parser, rules, agent, report, explainer, crop_violation_classifier, yolo_ui_detector
│   ├── backend/                        audit + JWT auth + records routers; Dockerfile (torch/ultralytics + opencv system libs, 05 Aug fix)
│   ├── frontend/                       Upload/Dashboard/Report/Records/Login wired; Dockerfile (new 05 Aug, port 5173)
│   ├── tests/ + backend/tests/         rules/audit/report + auth suite — 155 collected
│   ├── tests/fixtures/rules/           61 XML fixtures (R01–R27, R29–R30 pass/fail; R28 has none)
│   ├── notebooks/                      masc_dataset_analysis, train_crop_violation_classifier, train_yolo_ui_detector
│   ├── scripts/                        week1–8 validate + md_to_docx + backbone-sweep tooling + plot_crop_classifier_curves + utilities
│   ├── docs/                           schemas, progress, week6/, week7/, figma/, crop_classifier_comparison_findings.md, crop_classifier_model_reference.md
│   ├── srs/ · sds/                     SRS v2.11 / SDS v2.15 markdown + DOCX
│   ├── data/
│   │   ├── data-masc/                  7,068 screens + parsed outputs + splits
│   │   └── data-rico-holdout/          1,698 holdout — final eval now done
│   ├── models/                         crop_violation_classifier_best.pt (swin_tiny), yolo_ui_detector_best.pt (gitignored, .pt weights)
│   ├── outputs/
│   │   ├── violations/samples/         ✅ 61 fixture JSON samples (R01–R27, R29–R30)
│   │   ├── reports/samples/            ✅ Example JSON/HTML/PDF report
│   │   ├── week7_holdout/              per_screen_results.csv, rule_summary.csv, guideline_summary.csv, run_summary.json
│   │   └── validation_logs/            noor_week1–8 logs + summaries
│   ├── runs/                           ✅ YOLO detector + crop classifier — trained, Rico-evaluated, wired into backend pipeline
│   │   ├── notebooks/                  executed copies with saved outputs (incl. 26 backbone-sweep notebooks)
│   │   ├── crop_violation_classifier/  crops/, rico_crops/, manifests/, rico_manifest/, export/, crop_classifier/ (9 plots, new 05 Aug)
│   │   └── runs/yolo_ui_detector/      args.yaml, results.csv, plots, export/best.pt
│   ├── docker-compose.yml              ✅ frontend + backend + auditor (frontend added 05 Aug; backend loads .env via env_file)
│   └── test_run.py                     batch + single + --fixtures (auditor Docker entrypoint)
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
| Auth + Records | Week 6 | ✅ JWT + `/records` on `noor`; Login/Records UI; **OTP/SMTP/Google OAuth** (Noor `995f6d31`) |
| 25–40 screen manual eval | Week 6 | ✅ 40 stratified-random + 40/40 assisted FP/miss notes (`docs/week6/`) |
| Final evaluation (Rico holdout) | Week 8 | ✅ Batch eval done — 1,698 screens, 0 failures, re-run post rule-fix 29 Jul (`docs/week7/holdout_*`) |

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

#### Week 6 — Auth, Records, evaluation batch (updated **16 Jul 2026**, `995f6d31`)

| Person | Planned | **Actual outcome** |
|--------|---------|-------------------|
| **Salar** | Auth backend (JWT); records persistence | ✅ Done — `backend/auth.py`, `auth_router.py`, `records_router.py`, `test_auth.py`; synced into `noor` |
| **Ayesha** | Auth screens + Records page; prompt experiments | ✅ Login/SignUp wired to JWT; Records on live API; prompt experiments expanded; Dashboard re-run popup |
| **Noor** | 25–40 screen eval; R26–R30 design; sync + docs; auth stretch | ✅ Sync Salar+Ayesha; score/filename on Records; **40/40** stratified eval (`docs/week6/`); R26–R30 design DOCX; validation logs; **OTP + SMTP + Google OAuth**; Forgot /OTP /RESET UI ; HTML/PDF export fix; profile initials; SRS/SDS/progress/plan updated |

### Noor Week 6 detail — signup / login / reset / forgot / SMTP / OTP / OAuth

| Deliverable | Detail |
|-------------|--------|
| **Sign Up / Log In** | Register + login JWT; password ≥8 with letter+number; **any valid email domain** (Yahoo, Outlook, education/university, etc.) |
| **Forgot → OTP → Reset** | Forgot password sends 6-digit OTP; verify; set new password; success path matches Figma |
| **SMTP mail** | Gmail SMTP (`smtp.gmail.com:587` TLS) with App Password; `SMTP_USER` / `SMTP_FROM` = project Gmail; recipients can be non-Gmail |
| **OTP store** | `backend/otp_store.py` + `email_service.py`; purposes: email verify + password reset; resend supported |
| **Google OAuth** | GIS button + `POST /auth/google`; env `GOOGLE_CLIENT_ID` (Web client ID from Google Cloud Console) |
| **Credentials / env** | `.env` / `.env.example`: `JWT_SECRET`, `GOOGLE_CLIENT_ID`, `SMTP_*`, `AUTH_DEV_SHOW_OTP` (0 when real mail works), `VITE_API_BASE` |
| **Profile UI** | `UserAvatar` initials from logged-in name/email (not hardcoded “AN”) |
| **Report export** | Persist screenshot+XML under run folder; HTML/PDF include media + violations (`123fbde4`) |
| **Eval research** | 40-screen stratified sheet (seed `20260715`) + assisted FP/miss notes on **all 40** rows |
| **Tests (16 Jul)** | Auth **22** passed · Audit **9** passed · R26–R30 **8** passed |

**Week 6 remaining (optional):**
- Friday demo walkthrough: signup/login → upload screenshot+XML pair → dashboard → report HTML/PDF → Records list with score

**Week 6 demo goal:** Auth + upload pair + report download + Records. **Ready to demo.**

**Secrets policy:** App Passwords and `JWT_SECRET` stay in local `.env` only (gitignored). Document env **names** in `.env.example`; never commit live SMTP passwords.

---

### Phase 4 — Polish & delivery (Weeks 7–8) ← **NEXT**

#### Week 7 — QA, benchmark, bug fixes

| Person | Tasks | Deliverable |
|--------|-------|-------------|
| **Salar** | Fix rule false positives; complete assigned R-block gaps | Stable rule engine across all 30 rules |
| **Ayesha** | UI polish; finalize model/prompt comparison notes; close R-block test gaps | Production-quality Axion + model comparison |
| **Noor** | Rico holdout evaluation; compile rule-wise and guideline-wise summary | Holdout results + G01–G30 coverage report |

**Week 7 Noor status (20 Jul):** MASC 40-screen QA complete — `docs/week7/`, `outputs/week7_eval/`, validation logs. Rico holdout batch deferred to later in Week 7/8.

**Post–Week 7 status (updated 30 Jul):** YOLO UI-element detector track — MASC-only training run, **full 60/60 epochs completed** by Salar on the `salar` branch, merged into `noor` (final precision 0.535, recall 0.447, mAP50 0.434, mAP50-95 0.322 — supersedes the earlier 1-epoch interim figures of 0.471/0.420/0.397/0.285); best checkpoint exported (`runs/runs/yolo_ui_detector/export/yolo_ui_detector_best.pt`, `models/yolo_ui_detector_best.pt`, both 51.2 MB); zero-shot-vs-fine-tuned Rico holdout comparison run: mAP50 0.0258 (zero-shot) → 0.2546 (fine-tuned). `src/yolo_ui_detector.py` **now exists** (ported from Salar's branch 30 Jul, correcting the 29 Jul "does not exist" claim) and, as of 05 Aug, is **wired into the backend** — `detect_ui()` + a new `detections_to_components()` converter, called from `backend/routers/audit.py` as a fallback when XML is missing/malformed/empty. Full training results: Progress Report §15C/§15C.7/§15C.9; wiring detail: §15J.

**Week 8 status (29 Jul):** rule-accuracy pass — fixed and verified R07/R08/R30 false positives + the R20/R05 parser bug (see "What changed" in `README.md`) against the full 7,068-screen MASC set and the 1,698-screen Rico holdout, not just fixtures. Also retrained the crop-violation classifier (`notebooks/train_crop_violation_classifier.ipynb`) since R08 is one of its 6 label classes.

**30 Jul–03 Aug status:** a 33-backbone comparison sweep tested the original crop-classifier pick (`mobilenet_v3_small`) against 32 alternatives — found mid-pack (Rico macro-F1 0.18). Replaced with **`swin_tiny_patch4_window7_224`**, the sweep's best result (Rico macro-F1 0.22). Full results: `docs/crop_classifier_comparison_findings.md`, `docs/crop_classifier_model_reference.md`.

**04–05 Aug status:** both CV models wired into the backend pipeline — `confirm_violations()` (crop classifier) and `detect_ui()`/`detections_to_components()` (YOLO) both called from `backend/routers/audit.py`; `xml` now optional on `POST /api/v1/audit`. Two real bugs found and fixed along the way (wrong-Python `ultralytics` install; an `xml_path`-overwrite logic bug caught by a new test). Two real Docker bugs also found by actually building/running the containers and fixed (missing torch/ultralytics dependency; missing opencv system libraries). Full detail: Progress Report §15J.

### Remaining work — verified against SDS v2.15 (05 Aug 2026)

Cross-checked every "in progress" / "stretch" / "stub" claim in SDS §1.4 and §6 against what's actually in the repo right now (grepped for the files, not assumed from the docs — several SDS claims turned out to be stale):

| Item | SDS says | Actually verified | Remaining work |
|------|----------|--------------------|-----------------|
| **YOLO UI-element detector integration** | §1.4: "In progress... not yet wired into pipeline" (pre-05 Aug) | **Done, 05 Aug.** `detect_ui()` + new `detections_to_components()` wired into `backend/routers/audit.py`; `xml` optional on `POST /api/v1/audit`; falls back on missing/malformed/empty-hierarchy XML | Done — no remaining action |
| **Crop-violation classifier integration** | Now in SDS §3.7 | **Done, 05 Aug.** `confirm_violations()` wired into `backend/routers/audit.py`, called after `check_rules()`; attaches `cv_confidence` to R08/R17/R04. Backbone also changed to `swin_tiny_patch4_window7_224` after the 33-model sweep | Done — no remaining action |
| **R09 — Low contrast** | §6.10: "Screenshot crop + WCAG contrast ratio; requires `src/contrast.py`" | `src/contrast.py` **does not exist**. Current `check_low_contrast` is a pure declared-attribute check (`text_color`/`background_color` XML attrs) — correctly implemented, but reports 0 hits on MASC/Rico since neither dataset ever declares those attributes (confirmed: 0 occurrences across all 7,068 MASC files) | Build real screenshot-pixel contrast sampling (or route through the crop-classifier above, which already includes R09 as a label) if this rule needs to fire on real data |
| **R28 — Font-scale overflow** | Same category as R09 (declared-size only) | `check_font_scale_overflow` reads `text_size_sp`, which MASC/Rico never declare (0 occurrences) — correct code, no signal in current datasets | Same as R09 — needs a screenshot/CV signal, or accept it as XML-only and out of scope for these datasets |
| **R22 / R29 (password toggle / all-caps)** | Not flagged as gaps in SDS | Genuine **data-coverage gaps**, not code gaps: 0 password fields and 0 `textAllCaps` attributes anywhere in the 7,068-file MASC corpus (verified directly) | Nothing to fix in code; would need a differently-curated sample (e.g. deliberately including login/password screens) to ever exercise these rules for real |
| **SDS §6 rule-design prose is stale in places** | §6.12: "R11 — Color-only information (stub)" | `check_color_only_info` is **fully implemented** (checkable-state widgets with no text/content_desc), not a stub — confirmed by reading the current function | Update SDS §6.10–6.12 prose to match actual implementation (separate from this plan; noted here so it isn't lost) |
| **TBD-03 — dp/density for R04** | Open decision, owner Salar | Still assumes 160 dpi flat; no per-device density lookup | Resolve or explicitly accept 160dpi-flat as final for MVP |
| **TBD-05 — Severity UI mapping** | Open decision, owner: All | Not resolved | Decide High→Critical/Serious, Medium→Moderate, Low→Minor mapping and wire into frontend severity badges |
| **Final internship report + demo** | Week 8 (Noor) | Not started | 5–7 min demo + final report covering 30/30 rule coverage, per Week 8 deliverable below |

#### Week 8 — Final deliverables

| Person | Tasks | Deliverable |
|--------|-------|-------------|
| **Salar** | 5–7 min demo ; rename branch to `salar` | Rule-engine handoff docs |
| **Ayesha** | Figma + React UI + model experiment documentation | UI + agentic/model handoff doc |
| **Noor** | Final internship report ; Rule + Docker documentation ; coordinate presentation | Final report + demo with 30/30 coverage |

---

## Priority tiers (from SRS v2.11)

| Tier | Scope |
|------|-------|
| **Must Have** | Parser ✅ · R01–R30 rules ✅ (R07/R08/R30 false positives + R20/R05 parser bug fixed 29 Jul) · LLM explanations ✅ · HTML/PDF ✅ · Upload/Dashboard/Report ✅ · Auth + Records ✅ · Docker ✅ · 25–40 screen eval ✅ (40/40 assisted notes) · OTP/forgot/reset + SMTP ✅ · Google OAuth ✅ · Rico holdout final eval ✅ |
| **Should Have** | Batch API · annotated screenshot regions in UI · deeper prompt comparison notes |
| **Stretch** | R09/R28 real CV signal (contrast + font-scale — currently correct code, no data signal) · **YOLO UI-element detector** trained, Rico-evaluated, **wired into backend pipeline** ✅ (05 Aug) · **Crop-violation classifier** trained, Rico-evaluated, **wired into backend pipeline** ✅ (05 Aug; backbone `swin_tiny_patch4_window7_224` after 33-model sweep) · click-to-highlight in HTML (not implemented) |

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
| Rico holdout | Ayesha + Noor | §6 | §4 |
| Parser → `components.json` | Salar / Noor | §4.2 | §3.1 |
| Rule engine → `violations.json` | Salar + Noor + Ayesha (reviewed by all) | §4.3, §7 | §3.2 |
| Agent → `report.json` | Noor | §4.5 | §3.3 |
| Report HTML/PDF template | Noor | §4.6 | §3.4 |
| JSON schemas + `json_schemas.md` | Noor | §8 | §4 |
| Backend / FastAPI audit API | Noor | §9 | §3.5 |
| Auth (JWT) + Records API | Salar (synced by Noor) | §4.9 | §10 |
| Axion UI | Ayesha (+ Salar auth wiring) | §3.1, Appendix F | §9 |
| SRS v2.11 | Ayesha + Salar (updates: Noor) | — | — |
| SDS v2.15 | Noor | — | — |
| pytest suite | Salar + Ayesha + Noor | §10 | §13 |
| Docker | Salar + Noor | Appendix E | §11 |
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
