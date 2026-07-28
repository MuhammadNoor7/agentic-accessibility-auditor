# Noor Week 8 Summary — Rico Holdout Batch Eval (deferred from Week 7)

**Branch:** `noor`  
**Date:** 2026-07-28  
**Owner:** Muhammad Noor  
**Dataset:** `data/data-rico-holdout` (1698 screens, MASC-disjoint)

## Deliverables — status

| Item | Path | Status |
|------|------|--------|
| Per-screen results CSV | `outputs/week7_holdout/per_screen_results.csv` | Done |
| Rule summary | `outputs/week7_holdout/rule_summary.csv` + `docs/week7/holdout_rule_summary.md` | Done |
| Guideline summary | `outputs/week7_holdout/guideline_summary.csv` + `docs/week7/holdout_guideline_summary.md` | Done |
| QA notes | `docs/week7/holdout_qa_notes.md` | Done |
| Week 6 (MASC) vs Holdout cross-check | `docs/week7/holdout_week6_crosscheck.md` | Done |
| Team priorities | `docs/week7/holdout_team_priority_fixes.md` | Done |
| Validation logs | `outputs/validation_logs/noor_week8_*` | Done |

## Key numbers (Rico holdout, n=1698)

| Metric | Value |
|--------|------:|
| Screens evaluated | 1698 / 1698 |
| Failures | 0 |
| Mean violations / screen | 51.7 |
| Median violations / screen | 21 |
| Mean accessibility score | 26.3 |
| Screens with 0 violations | 60 |
| mostly_agree (heuristic) | 1007 |
| over_flagging | 513 |
| mixed_r30_noise | 118 |
| clean | 60 |

## Top rules

- **R07** — 46367 violations
- **R01** — 13970 violations
- **R08** — 12738 violations
- **R18** — 3191 violations
- **R30** — 2514 violations

## Validation checks

- PASS — rico_holdout_eval
- PASS — pytest_rules
- PASS — pytest_auth
- PASS — pytest_audit
- PASS — week8_holdout_outputs
- PASS — week8_holdout_docs

## Next

- Salar: use holdout R07/R08/R30 numbers to validate FP fixes at scale (see `holdout_team_priority_fixes.md`).
- Noor: re-run this script after Salar's fixes land to quantify the FP-rate delta vs this baseline.
