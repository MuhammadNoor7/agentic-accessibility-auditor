# Week 7 — Team Priority Fixes (from Holdout Eval)

**For:** Salar + Ayesha + Noor  
**Date:** 2026-07-28 08:32 UTC  
**Basis:** Rico holdout n=1698 + Week 6 cross-check

## Interim numbers (share in standup)

- Holdout screens run: **1698** (failures: 0)
- Mean violations/screen: **51.7**; mean score: **26.3**
- Noise heuristic: over_flagging **513**, mixed_r30_noise **118**
- Top violation rules: R07 (46367), R01 (13970), R08 (12738), R18 (3191), R30 (2514)

## Priority queue

1. **P0 — Salar:** R07/R08 nesting FP fix (biggest precision win).
2. **P0 — Salar:** R30 overlap tolerance for list/chat scroll layouts.
3. **P1 — Salar:** R01 decorative-node filter (optional child-text check).
4. **P1 — Ayesha:** UI polish on Upload/Report/Records for Friday demo.
5. **P2 — Ayesha:** Finalize `docs/agent_prompt_experiments.md` + TBD-01 appendix.
6. **P2 — Noor:** Re-run holdout after Salar merges to quantify FP reduction.

## Week 8 deferrals

- CV contrast (G09/G11), gold-label eval upgrade, final internship report.
