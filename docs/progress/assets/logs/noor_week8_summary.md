# Noor Week 8 Summary — Rico Holdout Batch Eval (deferred from Week 7)

**Branch:** `noor`  
**Date:** 2026-07-28  
**Owner:** Muhammad Noor  
**Dataset:** `data/data-rico-holdout` (1698 screens, MASC-disjoint)

## Deliverables — status

| Item | Path | Status |
|------|------|--------|
| Per-screen results CSV | `outputs/week7_holdout/per_screen_results.csv` | Done |
| Rule summary | `outputs/week7_holdout/rule_summary.csv` + `docs/week7/holdout_rule_summary.md` | Done |
| Guideline summary | `outputs/week7_holdout/guideline_summary.csv` + `docs/week7/holdout_guideline_summary.md` | Done |
| QA notes | `docs/week7/holdout_qa_notes.md` | Done |
| Week 6 (MASC) vs Holdout cross-check | `docs/week7/holdout_week6_crosscheck.md` | Done |
| Team priorities | `docs/week7/holdout_team_priority_fixes.md` | Done |
| Validation logs | `outputs/validation_logs/noor_week8_*` | Done |

## Key numbers (Rico holdout, n=1698)

| Metric | Value |
|--------|------:|
| Screens evaluated | 1698 / 1698 |
| Failures | 0 |
| Mean violations / screen | 31.7 |
| Median violations / screen | 14 |
| Mean accessibility score | 32.0 |
| Screens with 0 violations | 87 |
| mostly_agree (heuristic) | 1231 |
| over_flagging | 251 |
| mixed_r30_noise | 129 |
| clean | 87 |

## Top rules

- **R07** — 18143 violations
- **R01** — 13970 violations
- **R08** — 7238 violations
- **R18** — 3191 violations
- **R02** — 2492 violations

## Validation checks

- PASS — rico_holdout_eval
- PASS — pytest_rules
- PASS — pytest_parser
- PASS — pytest_auth
- PASS — pytest_audit
- PASS — week8_holdout_outputs
- PASS — week8_holdout_docs

## R07/R08/R30/R20/R05 fix verification (2026-07-28, Noor)

- **R07** (`src/rules.py::check_zero_size`) — now skips non-interactive/non-content zero-size elements via `_is_a11y_relevant` (clickable/focusable/text/content_desc only).
- **R08** (`src/rules.py::check_layout_overlap`) — now skips clickable ancestor/descendant pairs via `_is_ancestor` (full parent_id chain, not just immediate parent).
- **R30** (`src/rules.py::check_icon_only_no_label`) — now collapses repeated same-template list-row icons (same resource_id + bounds size) via `_dedupe_repeated`.
- **R20/R05** (`src/parser.py::_get_hint`) — now reads MASC's real `text-hint` attribute (was only checking `hint`/`android:hint`, which MASC never emits), unblocking R20 (0 -> 749 hits on full MASC) and correcting R05's false positives (2117 -> 717 on full MASC).
- Full MASC sweep (7068 screens, 0 failures) confirms rule counts moved as expected; see `outputs/violations/*.json` (regenerated) and `notebooks/masc_dataset_analysis.ipynb` (re-executed) for before/after detail.

## Next

- Salar: R07/R08/R30 FP fixes already landed (this run) — no longer blocking; revisit R30's remaining per-instance volume if further reduction is wanted (see `holdout_team_priority_fixes.md`).
