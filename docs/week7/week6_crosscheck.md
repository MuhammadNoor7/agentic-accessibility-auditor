# Week 6 Manual Review vs Re-run Cross-check

**Generated:** 2026-08-05 17:42 UTC  
**Method:** Re-ran `check()` on 40 components.json files; compared auto heuristics to Week 6 `manual_verdict`.

## Verdict distribution

| Label | Manual (Week 6) | Auto (re-run) |
|-------|----------------:|--------------:|
| agree_clean / clean | 3 | 1 |
| mostly_agree | 32 | 33 |
| over_flagging | 2 | 3 |
| mixed_r30_noise | 3 | 3 |

**Verdict alignment:** yes=37, partial=0, no=3

## Score consistency (CSV auto_score vs re-run)

| screen_id | CSV score | Re-run score | Delta |
|-----------|----------:|-------------:|------:|
| chat_19617 | 0 | 45 | +45 |
| chat_69291 | 0 | 50 | +50 |
| home_28353 | 0 | 30 | +30 |
| home_26401 | 80 | 95 | +15 |
| home_7030 | 0 | 75 | +75 |
| list_24905 | 0 | 90 | +90 |
| list_20652 | 0 | 90 | +90 |
| list_30302 | 0 | 5 | +5 |
| login_34202 | 0 | 50 | +50 |
| login_56516 | 0 | 60 | +60 |
| maps_40613 | 0 | 0 | +0 |
| maps_9916 | 0 | 55 | +55 |
| menu_16322 | 0 | 10 | +10 |
| profile_62448 | 0 | 20 | +20 |
| profile_62959 | 0 | 10 | +10 |
| profile_47000 | 20 | 60 | +40 |
| search_957 | 0 | 0 | +0 |
| search_9295 | 0 | 75 | +75 |
| search_33575 | 0 | 40 | +40 |
| settings_65638 | 0 | 60 | +60 |
| settings_14091 | 0 | 80 | +80 |
| welcome_33915 | 0 | 0 | +0 |
| welcome_17362 | 85 | 90 | +5 |
| welcome_37280 | 85 | 100 | +15 |
| welcome_63932 | 0 | 95 | +95 |

## Thematic consistency

- Week 6 FP themes (R07/R08/R30) appear in the same categories on re-run.
- Week 6 miss themes unchanged — static XML limits still apply.
- Assisted manual notes remain valid; re-run confirms rule counts stable on `noor` branch.
