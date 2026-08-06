# Week 7 — Rule-wise Summary (R01–R30)

**Generated:** 2026-08-05 17:42 UTC  
**Dataset:** MASC Week 6 stratified sample (n=40, seed `20260715`)  
**Rico holdout:** deferred (Noor will run later)

## Aggregate screen health

| Metric | Value |
|--------|------:|
| Mean violations / screen | 19.4 |
| Median violations / screen | 11 |
| Mean accessibility score | 32.1 |
| Manual over_flagging / mixed_r30_noise | 5 |
| Auto over_flagging / mixed_r30_noise | 6 |

## Rule trigger frequency + severity (sorted by violation count)

| Rule | Screens | % | Violations | High | Medium | Low | Avg when triggered |
|------|--------:|--:|-----------:|-----:|-------:|----:|-------------------:|
| R08 | 18 | 45% | 305 | 0 | 305 | 0 | 16.9 |
| R01 | 36 | 90% | 189 | 189 | 0 | 0 | 5.2 |
| R18 | 22 | 55% | 75 | 75 | 0 | 0 | 3.4 |
| R02 | 15 | 38% | 48 | 48 | 0 | 0 | 3.2 |
| R30 | 15 | 38% | 48 | 48 | 0 | 0 | 3.2 |
| R03 | 5 | 12% | 26 | 0 | 26 | 0 | 5.2 |
| R11 | 4 | 10% | 23 | 23 | 0 | 0 | 5.8 |
| R15 | 20 | 50% | 20 | 0 | 20 | 0 | 1.0 |
| R17 | 8 | 20% | 20 | 0 | 20 | 0 | 2.5 |
| R20 | 5 | 12% | 6 | 0 | 6 | 0 | 1.2 |
| R14 | 3 | 8% | 4 | 0 | 4 | 0 | 1.3 |
| R05 | 1 | 2% | 3 | 3 | 0 | 0 | 3.0 |
| R06 | 2 | 5% | 3 | 0 | 3 | 0 | 1.5 |
| R23 | 1 | 2% | 3 | 3 | 0 | 0 | 3.0 |
| R04 | 2 | 5% | 2 | 2 | 0 | 0 | 1.0 |
| R16 | 1 | 2% | 1 | 0 | 0 | 1 | 1.0 |
| R07 | 0 | 0% | 0 | 0 | 0 | 0 | 0.0 |
| R09 | 0 | 0% | 0 | 0 | 0 | 0 | 0.0 |
| R10 | 0 | 0% | 0 | 0 | 0 | 0 | 0.0 |
| R12 | 0 | 0% | 0 | 0 | 0 | 0 | 0.0 |
| R13 | 0 | 0% | 0 | 0 | 0 | 0 | 0.0 |
| R19 | 0 | 0% | 0 | 0 | 0 | 0 | 0.0 |
| R21 | 0 | 0% | 0 | 0 | 0 | 0 | 0.0 |
| R22 | 0 | 0% | 0 | 0 | 0 | 0 | 0.0 |
| R24 | 0 | 0% | 0 | 0 | 0 | 0 | 0.0 |
| R25 | 0 | 0% | 0 | 0 | 0 | 0 | 0.0 |
| R26 | 0 | 0% | 0 | 0 | 0 | 0 | 0.0 |
| R27 | 0 | 0% | 0 | 0 | 0 | 0 | 0.0 |
| R28 | 0 | 0% | 0 | 0 | 0 | 0 | 0.0 |
| R29 | 0 | 0% | 0 | 0 | 0 | 0 | 0.0 |

## Obvious noise clusters (Week 6 confirmed)

1. **R07 + R08 nesting** — R07 on 0/40 screens, R08 on 18/40. 3 screens show R07+R08 dominating (>=45% of violations).
2. **R30 density** — triggered on 15/40 screens; 3 manual `mixed_r30_noise` verdicts.
3. **R01/R02 label volume** — high count but mix of real missing labels and decorative ImageView FPs.

Machine-readable export: `outputs/week7_eval/rule_summary.csv`
