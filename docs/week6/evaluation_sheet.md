# Week 6 evaluation sheet (40 screens)

**Owner:** Muhammad Noor  
**Branch:** `noor`  
**CSV:** `docs/week6/evaluation_sheet_40_screens.csv`

## Sampling method

- **Stratified random** — 4 screens randomly chosen from each of 10 MASC categories (`chat`, `home`, `list`, `login`, `maps`, `menu`, `profile`, `search`, `settings`, `welcome`).
- **Not** every-Nth / sorted fixed picks (that was the earlier draft).
- **Reproducible seed:** `20260715` (column `sample_seed` in the CSV). Re-run:

```powershell
python scripts/noor_week6_validate.py
```

## Columns

| Column | Meaning |
|--------|---------|
| `auto_score` | Rule-engine score via `compute_accessibility_score` (not manual) |
| `top_rules` | Highest-frequency rule IDs on that screen |
| `r26`–`r30` | Hit counts for Week 6 stretch rules |
| `manual_verdict` / FP / missed | **Fill by hand** (≥25 screens target) |
| `reviewer` | Default `Noor` |

## Related

- Design notes: `docs/week6/r26_r30_design.docx`
- Validation: `outputs/validation_logs/noor_week6_summary.md`
