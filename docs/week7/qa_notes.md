# Week 7 — QA Notes (FP / Miss / Priorities)

**Generated:** 2026-07-20 10:46 UTC  
**Basis:** Week 6 MASC 40-screen stratified sample with assisted FP/miss notes.

## False-positive patterns

1. **R07/R08 container nesting** — parent clickable flagged when child TextView names the action (chat/list/home).
2. **R30 scroll-sibling overlap** — dense list/chat/map/search layouts; 5 screens with explicit R30 FP notes.
3. **R01 on decorative ImageViews** — empty content-desc on non-actionable layout chrome.
4. **R08 volume** — overlap pairs inflate totals on complex hierarchies (maps_15184: 147 violations, mostly R07/R08).
5. **Volume-only over_flagging** — search_70760 (349 violations) flagged over_flagging without single-rule cluster.

## Probable missed-issue patterns

1. **Live regions / dynamic text** — chat unread, typing indicators (category template on all chat rows).
2. **Error–field association** — login forms; R21 partial, no described-by equivalent.
3. **Selected nav/tab state** — home bottom-nav badges and selected item (home category template).
4. **Switch/checkbox state** — profile/settings when `checked` attr missing in XML.
5. **Pixel contrast (G09/G11)** — R09 needs declared colors; screenshot CV not in MVP.

## Week 7 fixes (assign now)

| Owner | Task | Evidence |
|-------|------|----------|
| **Salar** | R07/R08 nesting suppression | Top rules on 38/40 screens; FP notes on chat/home/list |
| **Salar** | R30 overlap tolerance | 3 mixed_r30_noise + R30 called out in FP notes |
| **Salar** | R09 declared-color edge cases | Partial rule; G09 zero/low in sample |
| **Ayesha** | UI polish Upload/Report/Records | Demo readiness |
| **Ayesha** | Finalize prompt comparison doc | TBD-01 closed; Groq default |
| **Noor** | Rico holdout batch (later) | Deferred from this Week 7 pass |

## Week 8 stretch (defer)

- G09/G11 CV contrast on MASC train→val.
- Gold-label spot check replacing assisted heuristics.
- Rico holdout re-run after Salar FP fixes.
- TalkBack / agentic task comparison (literature gap).

## Rules not triggered in 40-screen sample

R09, R10, R12, R13, R20, R22, R25, R26, R27, R28, R29
