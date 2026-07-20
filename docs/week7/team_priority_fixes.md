# Week 7 — Team Priority Fixes (share with Salar + Ayesha)

**Date:** 2026-07-20 10:46 UTC  
**Owner:** Muhammad Noor  
**Basis:** MASC 40-screen Week 6 eval (Rico holdout deferred)

## Interim numbers for standup

- Sample: **40/40** stratified MASC screens (seed `20260715`)
- Mean violations/screen: **64.3**; mean score: **6.8**
- Manual verdicts: mostly_agree **32**, agree_clean **3**, over_flagging **2**, mixed_r30_noise **3**
- Top violation rules: R07 (1127), R08 (629), R01 (324), R18 (102), R02 (89)

## Priority queue

1. **P0 Salar** — R07/R08 nesting FP fix
2. **P0 Salar** — R30 overlap tolerance (list/chat/map/search)
3. **P1 Salar** — R01 decorative-node filter
4. **P1 Ayesha** — UI polish for Friday demo path
5. **P2 Ayesha** — Finalize `docs/agent_prompt_experiments.md`
6. **P2 Noor** — Rico holdout batch when dataset copied locally

## Rico holdout

Not included in this pass. When ready: `python scripts/run_rico_holdout_eval.py`
(requires `data/data-rico-holdout/xml/` or external `final_rico` path).
