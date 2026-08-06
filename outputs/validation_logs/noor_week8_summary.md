# Noor Week 8 Summary — Rico Holdout Batch Eval (deferred from Week 7)

**Branch:** `noor`  
**Date:** 2026-08-05  
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

## Since 29 Jul — crop classifier, YOLO, backbone sweep, backend wiring (Noor)

- **29 Jul**: crop classifier Rico holdout eval added and run end-to-end (1698 screens, 9343 crops) — R08 F1 0.70->0.46, R17 0.47->0.35, R04 0.36->0.25, macro avg 0.25->0.18 vs. the MASC test split (commit `06ad0ece`). Docs synced: SRS v2.8->2.9, SDS v2.12->2.13, Progress Report v1.24->1.25 (commit `7a1e6a4f`).
- **30 Jul**: merged Salar's completed 60-epoch YOLO run + his `src/yolo_ui_detector.py` (`detect_ui()`) from the `salar` branch — final checkpoint mAP50 0.434 / mAP50-95 0.322 (up from a 1-epoch interim 0.397/0.285); merged his Rico zero-shot-vs-fine-tuned eval (mAP50 0.0258->0.2546). Crop-classifier Rico artifact inventory added (9343 crops tracked); SRS v2.10, SDS v2.14, Progress Report v1.26 synced (commit `12724e72`).
- **30 Jul - 03 Aug: 33-backbone comparison sweep** (crop classifier, Task B): verified whether `mobilenet_v3_small` was actually the best pick by training/evaluating all 33 candidates (same pipeline, ImageNet-1k pretrained, MASC test + Rico holdout) via a new unattended `scripts/overnight_sweep.py`, plus all related tooling (`scripts/run_backbone_sweep.py`, `scripts/eval_masc_test.py`, `scripts/extract_notebook_results.py`) and documentation (`docs/crop_classifier_comparison_findings.md`, 1813 lines; `docs/crop_classifier_model_reference.md`, 291 lines - architecture/year/paper/authors for all 33, organized by family). Result: `mobilenet_v3_small` came in mid-pack (Rico macro-F1 0.18, beaten by 10+ models); `swin_tiny_patch4_window7_224` won outright (Rico macro-F1 0.22, evenly distributed across R04/R17/R08), confirmed via a `convnext_tiny` control that attention specifically drives the gap, not capacity. **Swin is now the pick**, replacing `mobilenet_v3_small`.
- **04-05 Aug: connecting both trained models to the backend**: `confirm_violations()` (crop classifier) and a new `detections_to_components()` converter (YOLO) both wired into `backend/routers/audit.py::_run_pipeline`; `xml` upload made optional with a YOLO fallback on missing/malformed/empty-hierarchy XML; `docs/schemas/auditor_schema.json` updated (`cv_confidence`, `inferred`, relaxed `xml_path`, plus an unrelated pre-existing `component_count`/`hidden_component_count` gap fixed). 155/155 tests pass (153 baseline + 2 new), including two real bugs caught during implementation: a missing `ultralytics` install masked by a `pip`/`python` environment mismatch, and an `xml_path` field that was silently overwritten after the YOLO fallback ran (caught by the new malformed-XML test).

## Next

- Noor: commit the 33-model sweep + backend wiring to `origin/noor` — both are currently uncommitted locally.
- Noor: sync Report/SDS/SRS/`updated_plan`/README to reflect Swin as the final backbone pick and both models now wired into the pipeline.
- Noor: SRS Appendix D — TBD-01 row still shows "Open" though `docs/TBD-01-decision.md` resolved it in July.
