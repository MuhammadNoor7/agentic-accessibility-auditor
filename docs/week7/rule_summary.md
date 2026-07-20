# Week 7 — Rule-wise Summary (R01–R30)

**Generated:** 2026-07-20 10:46 UTC  
**Dataset:** MASC Week 6 stratified sample (n=40, seed `20260715`)  
**Rico holdout:** deferred (Noor will run later)

## Aggregate screen health

| Metric | Value |
|--------|------:|
| Mean violations / screen | 64.3 |
| Median violations / screen | 42 |
| Mean accessibility score | 6.8 |
| Manual over_flagging / mixed_r30_noise | 5 |
| Auto over_flagging / mixed_r30_noise | 21 |

## Rule trigger frequency + severity (sorted by violation count)

| Rule | Screens | % | Violations | High | Medium | Low | Avg when triggered |
|------|--------:|--:|-----------:|-----:|-------:|----:|-------------------:|
| R07 | 40 | 100% | 1127 | 0 | 1127 | 0 | 28.2 |
| R08 | 24 | 60% | 629 | 0 | 629 | 0 | 26.2 |
| R01 | 37 | 92% | 324 | 324 | 0 | 0 | 8.8 |
| R18 | 25 | 62% | 102 | 102 | 0 | 0 | 4.1 |
| R02 | 23 | 58% | 89 | 89 | 0 | 0 | 3.9 |
| R30 | 23 | 58% | 89 | 89 | 0 | 0 | 3.9 |
| R03 | 10 | 25% | 66 | 0 | 66 | 0 | 6.6 |
| R17 | 13 | 32% | 44 | 0 | 44 | 0 | 3.4 |
| R11 | 6 | 15% | 25 | 25 | 0 | 0 | 4.2 |
| R15 | 21 | 52% | 21 | 0 | 21 | 0 | 1.0 |
| R05 | 11 | 28% | 17 | 17 | 0 | 0 | 1.5 |
| R19 | 4 | 10% | 13 | 0 | 13 | 0 | 3.2 |
| R24 | 6 | 15% | 6 | 0 | 6 | 0 | 1.0 |
| R06 | 3 | 8% | 5 | 0 | 5 | 0 | 1.7 |
| R14 | 4 | 10% | 5 | 0 | 5 | 0 | 1.2 |
| R23 | 1 | 2% | 5 | 5 | 0 | 0 | 5.0 |
| R04 | 2 | 5% | 2 | 2 | 0 | 0 | 1.0 |
| R16 | 1 | 2% | 2 | 0 | 0 | 2 | 2.0 |
| R21 | 1 | 2% | 1 | 1 | 0 | 0 | 1.0 |
| R09 | 0 | 0% | 0 | 0 | 0 | 0 | 0.0 |
| R10 | 0 | 0% | 0 | 0 | 0 | 0 | 0.0 |
| R12 | 0 | 0% | 0 | 0 | 0 | 0 | 0.0 |
| R13 | 0 | 0% | 0 | 0 | 0 | 0 | 0.0 |
| R20 | 0 | 0% | 0 | 0 | 0 | 0 | 0.0 |
| R22 | 0 | 0% | 0 | 0 | 0 | 0 | 0.0 |
| R25 | 0 | 0% | 0 | 0 | 0 | 0 | 0.0 |
| R26 | 0 | 0% | 0 | 0 | 0 | 0 | 0.0 |
| R27 | 0 | 0% | 0 | 0 | 0 | 0 | 0.0 |
| R28 | 0 | 0% | 0 | 0 | 0 | 0 | 0.0 |
| R29 | 0 | 0% | 0 | 0 | 0 | 0 | 0.0 |

## Obvious noise clusters (Week 6 confirmed)

1. **R07 + R08 nesting** — R07 on 40/40 screens, R08 on 24/40. 19 screens show R07+R08 dominating (>=45% of violations).
2. **R30 density** — triggered on 23/40 screens; 3 manual `mixed_r30_noise` verdicts.
3. **R01/R02 label volume** — high count but mix of real missing labels and decorative ImageView FPs.

Machine-readable export: `outputs/week7_eval/rule_summary.csv`
