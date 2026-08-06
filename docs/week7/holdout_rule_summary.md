# Rico Holdout — Rule-wise Summary (R01–R30)

**Generated:** 2026-08-05 17:26 UTC  
**Screens evaluated:** 1698 / 1698  
**Failures:** 0  
**XML source:** D:/internship/_noor_push/data/data-rico-holdout

## Aggregate screen health

| Metric | Value |
|--------|------:|
| Mean violations / screen | 31.7 |
| Median violations / screen | 14 |
| Mean accessibility score | 32.0 |
| Screens with 0 violations | 87 |
| over_flagging (heuristic) | 251 |
| mixed_r30_noise | 129 |
| mostly_agree | 1231 |
| clean | 87 |

## Rule trigger frequency (sorted by violation count)

| Rule | Screens triggered | % screens | Violations | Avg/screen when triggered |
|------|------------------:|----------:|-----------:|--------------------------:|
| R07 | 1078 | 63.5% | 18143 | 16.8 |
| R01 | 1449 | 85.3% | 13970 | 9.6 |
| R08 | 467 | 27.5% | 7238 | 15.5 |
| R18 | 798 | 47.0% | 3191 | 4.0 |
| R02 | 645 | 38.0% | 2492 | 3.9 |
| R30 | 649 | 38.2% | 2307 | 3.6 |
| R17 | 428 | 25.2% | 1929 | 4.5 |
| R03 | 212 | 12.5% | 835 | 3.9 |
| R11 | 201 | 11.8% | 709 | 3.5 |
| R15 | 656 | 38.6% | 656 | 1.0 |
| R05 | 210 | 12.4% | 496 | 2.4 |
| R16 | 353 | 20.8% | 392 | 1.1 |
| R06 | 189 | 11.1% | 326 | 1.7 |
| R04 | 143 | 8.4% | 289 | 2.0 |
| R14 | 113 | 6.7% | 267 | 2.4 |
| R24 | 143 | 8.4% | 143 | 1.0 |
| R19 | 81 | 4.8% | 125 | 1.5 |
| R23 | 81 | 4.8% | 124 | 1.5 |
| R13 | 33 | 1.9% | 75 | 2.3 |
| R12 | 31 | 1.8% | 37 | 1.2 |
| R21 | 11 | 0.6% | 26 | 2.4 |
| R26 | 6 | 0.4% | 12 | 2.0 |
| R27 | 3 | 0.2% | 3 | 1.0 |
| R09 | 0 | 0.0% | 0 | 0.0 |
| R10 | 0 | 0.0% | 0 | 0.0 |
| R20 | 0 | 0.0% | 0 | 0.0 |
| R22 | 0 | 0.0% | 0 | 0.0 |
| R25 | 0 | 0.0% | 0 | 0.0 |
| R28 | 0 | 0.0% | 0 | 0.0 |
| R29 | 0 | 0.0% | 0 | 0.0 |

## Obvious noise clusters (Week 6 themes confirmed on holdout)

1. **R07/R08 nesting** — R07 triggered on 1078 screens (63.5%), R08 on 467 (27.5%). 279 screens show R07+R08 dominating (>=45% of violations, total>=40) — same pattern as Week 6 MASC chat/list FP notes.
2. **R30 density** — triggered on 649 screens; 129 screens classified `mixed_r30_noise` (R30>=5, total<120).
3. **R01/R02 label gaps** — remain top volume rules on holdout; many are real missing labels but some are decorative ImageViews (Week 6 partial FP theme).

## Severity distribution by rule (violation-level totals)

See `outputs/week7_holdout/rule_summary.csv` for machine-readable export.

