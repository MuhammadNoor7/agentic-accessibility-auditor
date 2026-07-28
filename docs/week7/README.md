# Week 7 QA Deliverables (Noor)

**Status:** Complete on MASC 40-screen sample. **Rico holdout: run in Week 8** (see below).

## Reports (read these)

| Doc | Purpose |
|-----|---------|
| [rule_summary.md](rule_summary.md) | R01–R30 trigger frequency + H/M/L severity (MASC 40) |
| [guideline_summary.md](guideline_summary.md) | G01–G30 coverage from rule mapping (MASC 40) |
| [qa_notes.md](qa_notes.md) | FP/miss patterns; Week 7 vs Week 8 split (MASC 40) |
| [week6_crosscheck.md](week6_crosscheck.md) | Manual vs re-run consistency (MASC 40) |
| [team_priority_fixes.md](team_priority_fixes.md) | **Share with Salar + Ayesha** (MASC 40) |

## Machine-readable outputs

| File | Purpose |
|------|---------|
| `outputs/week7_eval/per_screen_results.csv` | Per-screen violations, score, all R01–R30 counts, manual notes |
| `outputs/week7_eval/failures.csv` | Parse/rule errors (empty if all ok) |
| `outputs/week7_eval/rule_summary.csv` | Rule aggregates |
| `outputs/week7_eval/guideline_summary.csv` | Guideline aggregates |
| `outputs/week7_eval/run_summary.json` | Top-level stats |

## Regenerate

```powershell
python scripts/run_week7_eval_analysis.py
```

## Rico holdout (run in Week 8, 2026-07-28)

`data/data-rico-holdout/` now has all 1698 screenshots+XML, so the deferred holdout batch ran:

```powershell
python scripts/run_rico_holdout_eval.py --rico-source data/data-rico-holdout
```

Outputs live in `outputs/week7_holdout/` (per-screen CSV, rule/guideline summaries, `run_summary.json`).
Docs use a `holdout_` prefix to avoid clobbering the MASC-40 reports above:

| Doc | Purpose |
|-----|---------|
| [holdout_rule_summary.md](holdout_rule_summary.md) | R01–R30 trigger frequency on 1698 Rico-holdout screens |
| [holdout_guideline_summary.md](holdout_guideline_summary.md) | G01–G30 coverage on holdout |
| [holdout_qa_notes.md](holdout_qa_notes.md) | FP/miss patterns on holdout |
| [holdout_week6_crosscheck.md](holdout_week6_crosscheck.md) | MASC-40 (manual) vs Rico-holdout (heuristic) verdict/rate comparison |
| [holdout_team_priority_fixes.md](holdout_team_priority_fixes.md) | Priority queue from holdout numbers |

The Week 8 validation wrapper (`scripts/noor_week8_validate.py`) re-runs this and checks all of the above are present — see `outputs/validation_logs/noor_week8_*` and `outputs/week8_summary.md`.

## Validation

```powershell
python scripts/noor_week7_validate.py
```

Logs: `outputs/validation_logs/noor_week7_*` · Summary: `outputs/week7_summary.md`
