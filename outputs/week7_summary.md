# Noor Week 7 Summary — QA Analysis (MASC 40-screen)

**Branch:** `noor`  
**Date:** 2026-07-20  
**Owner:** Muhammad Noor  
**Rico holdout:** deferred

## Deliverables — status

| Item | Path | Status |
|------|------|--------|
| Per-screen results CSV | `outputs/week7_eval/per_screen_results.csv` | Done |
| Rule summary | `outputs/week7_eval/rule_summary.csv` + `docs/week7/rule_summary.md` | Done |
| Guideline summary | `outputs/week7_eval/guideline_summary.csv` + `docs/week7/guideline_summary.md` | Done |
| QA notes | `docs/week7/qa_notes.md` | Done |
| Week 6 cross-check | `docs/week7/week6_crosscheck.md` | Done |
| Team priorities | `docs/week7/team_priority_fixes.md` | Done |
| Validation logs | `outputs/validation_logs/noor_week7_*` | Done |

## Key numbers (MASC n=40, seed `20260715`)

| Metric | Value |
|--------|------:|
| Screens evaluated | 40 |
| Failures | 0 |
| Mean violations / screen | 64.3 |
| Mean accessibility score | 6.8 |
| mostly_agree (manual) | 32 |
| agree_clean | 3 |
| over_flagging | 2 |
| mixed_r30_noise | 3 |

## Top rules

- **R07** — 1127 violations
- **R08** — 629 violations
- **R01** — 324 violations
- **R18** — 102 violations
- **R02** — 89 violations

## Validation checks

- PASS — week7_eval_analysis
- PASS — pytest_rules
- PASS — pytest_auth
- PASS — pytest_audit
- PASS — week7_eval_outputs
- PASS — week7_docs

## Next

- Salar: R07/R08/R30 FP tuning
- Ayesha: UI polish + prompt doc finalize
- Noor: Rico holdout batch (`scripts/run_rico_holdout_eval.py`) when dataset ready
