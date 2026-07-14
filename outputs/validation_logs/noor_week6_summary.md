# Noor Week 6 Summary — Auth/Records Sync + Eval Sheet

**Branch:** `noor`  
**Commit:** `03ffa505a`  
**Date:** 2026-07-15  
**Owner:** Muhammad Noor  

## Deliverables

| Item | Path | Status |
|------|------|--------|
| Salar JWT auth | `backend/auth.py`, `backend/routers/auth_router.py` | Synced to `noor` |
| Salar records API | `backend/routers/records_router.py` | Synced (+ score/filename fields) |
| Auth tests | `backend/tests/test_auth.py` | Done |
| Ayesha prompt experiments | `docs/agent_prompt_experiments.md` | Synced |
| Dashboard re-run popup | `frontend/src/pages/Dashboard.jsx` | Synced |
| Records UI (live) | `frontend/src/pages/Records.jsx` | Done |
| Report score ring | `frontend/src/pages/Report.jsx` | Done |
| Week 6 eval sheet (40 screens) | `docs/week6/evaluation_sheet_40_screens.csv` | Done (random stratified) |
| R26–R30 design DOCX | `docs/week6/r26_r30_design.docx` | Done |
| Validation script | `scripts/noor_week6_validate.py` | Done |
| `.gitignore` | synced from `salar` (`data/` + `outputs/` + exceptions) | Done |

## What “20 passed, 1 skipped” means

When running `pytest backend/tests/test_auth.py tests/test_audit.py`:

- **20 passed** — automated checks for JWT register/login/me, records CRUD scoping, and audit upload/report/download behaviour.
- **1 skipped** — the PDF download test in `tests/test_audit.py` skips when Playwright Chromium is not installed on the machine (`pytest.skip` on 503). HTML download still runs. Fix once with: `playwright install chromium`.

## Eval sheet sampling

- **Not** a fixed/sorted every-Nth pick anymore.
- **Stratified random:** 4 screens randomly chosen from each of 10 MASC categories (seed=`20260715`).
- Categories covered: chat, home, list, login, maps, menu, profile, search, settings, welcome
- Rows regenerated this run: **40**
- Manual columns (`manual_verdict`, FP/miss notes) left blank for human fill (≥25 target).

## Validation results

```
STEP 1: pytest backend/tests/test_auth.py → 12 passed, 2 warnings in 7.96s
STEP 2: pytest tests/test_audit.py → 8 passed, 1 skipped, 2 warnings in 2.13s
STEP 3: pytest R26–R30 rules → 8 passed, 70 deselected in 0.14s
Auth + Records API smoke     → PASS
Eval sheet regenerate        → 40 rows (seed=20260715)
```

Full log: `outputs/validation_logs/noor_week6_validation_log.txt`

## Pytest failure count

All pytest steps: PASS

## Next

- Fill ≥25 manual verdicts on the CSV
- Friday demo: login → upload pair → dashboard → report download → records
- Training stretch: map guidelines on MASC train → tune on val → test on test
