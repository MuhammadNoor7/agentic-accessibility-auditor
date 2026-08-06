# Week 6 MASC (n=40) vs Rico Holdout Cross-check

**Generated:** 2026-08-05 17:26 UTC  
**Week 6 sample:** stratified MASC 40 screens (seed 20260715) with assisted FP/miss notes.  
**Holdout:** 1698 Rico screens (MASC-disjoint).

## Verdict distribution comparison

| Label | Week 6 (MASC 40) | Holdout (heuristic) |
|-------|-----------------:|--------------------:|
| clean | 3 | 87 |
| agree_clean | 3 | 0 |
| mostly_agree | 32 | 1231 |
| over_flagging | 2 | 251 |
| mixed_r30_noise | 3 | 129 |

## Top rules — consistent themes

| Rule | Week 6 trigger rate (40) | Holdout trigger rate | Consistent? |
|------|-------------------------:|---------------------:|:-----------:|
| R01 | 0% | 85% | Review |
| R02 | 0% | 38% | Review |
| R07 | 0% | 63% | Review |
| R08 | 0% | 28% | Yes |
| R17 | 0% | 25% | Yes |
| R18 | 0% | 47% | Review |
| R30 | 57% | 38% | Yes |

## Week 6 FP themes — holdout confirmation

- **R07/R08 nesting:** Present on holdout at scale; assign Salar Week 7 tuning.
- **R30 density:** Holdout chat/list categories show same mixed_r30_noise pattern.
- **R01 secondary chrome:** Still appears but lower relative volume than R07/R08 on holdout.

## Week 6 miss themes — still not covered by rules

- Live announcements, error association, selected nav state — unchanged; document as limitations.
