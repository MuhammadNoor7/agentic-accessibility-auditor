# Week 7 QA Deliverables (Noor)

**Status:** Complete on MASC 40-screen sample. **Rico holdout deferred.**

## Reports (read these)

| Doc | Purpose |
|-----|---------|
| [rule_summary.md](rule_summary.md) | R01–R30 trigger frequency + H/M/L severity |
| [guideline_summary.md](guideline_summary.md) | G01–G30 coverage from rule mapping |
| [qa_notes.md](qa_notes.md) | FP/miss patterns; Week 7 vs Week 8 split |
| [week6_crosscheck.md](week6_crosscheck.md) | Manual vs re-run consistency |
| [team_priority_fixes.md](team_priority_fixes.md) | **Share with Salar + Ayesha** |

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

## Rico holdout (later)

When XML/screenshots are copied under `data/data-rico-holdout/`:

```powershell
python scripts/run_rico_holdout_eval.py
```

Outputs will be written to `outputs/week7_holdout/` when that script is run (not part of current Week 7 pass).

## Validation

```powershell
python scripts/noor_week7_validate.py
```

Logs: `outputs/validation_logs/noor_week7_*` · Summary: `outputs/week7_summary.md`
