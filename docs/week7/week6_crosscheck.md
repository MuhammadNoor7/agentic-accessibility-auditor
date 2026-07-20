# Week 6 Manual Review vs Re-run Cross-check

**Generated:** 2026-07-20 10:46 UTC  
**Method:** Re-ran `check()` on 40 components.json files; compared auto heuristics to Week 6 `manual_verdict`.

## Verdict distribution

| Label | Manual (Week 6) | Auto (re-run) |
|-------|----------------:|--------------:|
| agree_clean / clean | 3 | 0 |
| mostly_agree | 32 | 19 |
| over_flagging | 2 | 18 |
| mixed_r30_noise | 3 | 3 |

**Verdict alignment:** yes=24, partial=0, no=16

## Score consistency (CSV auto_score vs re-run)

| screen_id | CSV score | Re-run score | Delta |
|-----------|----------:|-------------:|------:|
| chat_32469 | 0 | 0 | +0 |
| chat_19617 | 0 | 0 | +0 |
| chat_69291 | 0 | 0 | +0 |
| list_30302 | 0 | 0 | +0 |
| list_11742 | 0 | 0 | +0 |
| login_18858 | 0 | 0 | +0 |
| maps_40613 | 0 | 0 | +0 |
| maps_9916 | 0 | 0 | +0 |
| maps_15184 | 0 | 0 | +0 |
| menu_17147 | 0 | 0 | +0 |
| profile_62448 | 0 | 0 | +0 |
| search_33575 | 0 | 0 | +0 |
| settings_14091 | 0 | 0 | +0 |
| settings_24654 | 0 | 0 | +0 |
| settings_35321 | 0 | 0 | +0 |
| welcome_63932 | 0 | 0 | +0 |
| *(all 40 match)* | | | 0 |

## Thematic consistency

- Week 6 FP themes (R07/R08/R30) appear in the same categories on re-run.
- Week 6 miss themes unchanged — static XML limits still apply.
- Assisted manual notes remain valid; re-run confirms rule counts stable on `noor` branch.
