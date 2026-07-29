# Rico Holdout — QA Notes (FP / Miss / Week 7 vs Week 8)

**Generated:** 2026-07-28 18:43 UTC  
**Method:** Automated batch on Rico holdout XML (unseen vs MASC). Heuristic noise classes mirror Week 6 assisted review labels.

## False-positive patterns (likely noisy flags)

1. **R07 + R08 on container rows** — clickable/focusable parents flagged when child TextView already names the action; dense chat/list/home layouts.
2. **R30 overlap on scroll siblings** — icon-only targets in RecyclerView/ListView chrome; bounding-box overlap without user-facing ambiguity.
3. **R01 on decorative ImageViews** — empty content-desc on non-actionable icons that are layout chrome.
4. **R08 high volume globally** — overlap rule fires on many screen pairs; tolerance may be too aggressive for nested Android hierarchies.
5. **R18 multi-touch heuristic** — may flag scroll/pager containers that have single-touch alternatives in practice.

## Probable missed-issue patterns (rules under-trigger)

1. **Live regions / dynamic announcements** — chat unread counts, typing indicators, badge updates (not in static XML dump).
2. **Field–error association** — login/signup error text not linked to inputs (R21 partial; no aria-describedby equivalent).
3. **Selected tab / bottom-nav state** — missing checked/selected semantics when XML lacks state attrs.
4. **G09/G11 contrast from pixels** — R09 only uses declared colors; screenshot CV not in MVP.
5. **R12–R14 media/accessibility** — rare on holdout sample; video/audio/alert patterns seldom present in Rico static dumps.

## Week 7 fixes (assign now)

| Owner | Fix | Rationale |
|-------|-----|-----------|
| **Salar** | R07/R08 nesting suppression when child provides name | Top FP cluster on holdout + Week 6 |
| **Salar** | R30 overlap tolerance / scroll-container exclusion | mixed_r30_noise screens |
| **Salar** | R09 declared-color edge cases | Partial rule; reduce borderline FPs |
| **Ayesha** | UI polish + empty/error states on Upload/Records | Demo quality |
| **Ayesha** | Finalize prompt comparison doc (Groq default) | Week 7 deliverable |
| **Noor** | Holdout summary + cross-check (this doc) | Week 7 deliverable |

## Week 8 stretch (defer)

- G09/G11 screenshot contrast (CV model on MASC train→val).
- Gold-label spot check on 40-screen MASC sample (upgrade from assisted heuristics).
- Rico holdout re-run after Salar FP fixes to measure delta.
- TalkBack / agentic task audit comparison (literature gap).

## Rules rarely triggered on holdout

**Zero screens:** R09, R10, R20, R22, R25, R28, R29

**<=5 screens:** R27 (3)
