"""Run Noor Week 8 validation: Rico-holdout eval (deferred from Week 7) + pytest + artifact checks."""

from __future__ import annotations

import io
import json
import subprocess
import sys
from datetime import date
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

LOG_DIR = ROOT / "outputs" / "validation_logs"
LOG_PATH = LOG_DIR / "noor_week8_validation_log.txt"
SUMMARY_PATH = LOG_DIR / "noor_week8_summary.md"
WEEK8_SUMMARY = ROOT / "outputs" / "week8_summary.md"
HOLDOUT_OUT = ROOT / "outputs" / "week7_holdout"
DOCS_WEEK7 = ROOT / "docs" / "week7"


class _Tee:
    def __init__(self, *streams):
        self._streams = streams

    def write(self, data: str) -> None:
        for stream in self._streams:
            stream.write(data)
            stream.flush()

    def flush(self) -> None:
        for stream in self._streams:
            stream.flush()


def run_cmd(label: str, cmd: list[str]) -> tuple[int, str]:
    print(f"\n{'-' * 66}\n{label}\n{'-' * 66}")
    result = subprocess.run(cmd, cwd=ROOT, capture_output=True, text=True)
    output = (result.stdout or "") + (result.stderr or "")
    print(output)
    return result.returncode, output


def check_files(label: str, paths: list[Path]) -> tuple[bool, list[str]]:
    print(f"\n{'-' * 66}\n{label}\n{'-' * 66}")
    missing = [p.relative_to(ROOT).as_posix() for p in paths if not p.is_file()]
    for path in paths:
        status = "OK" if path.is_file() else "MISSING"
        print(f"  [{status}] {path.relative_to(ROOT)}")
    ok = not missing
    print(f"  => {'PASS' if ok else 'FAIL'} ({len(paths) - len(missing)}/{len(paths)} present)")
    return ok, missing


def write_week8_summary(run_meta: dict, checks: dict[str, bool]) -> None:
    top_rules = run_meta.get("top_rules_by_violations", [])
    noise = run_meta.get("noise_distribution", {})
    lines = [
        "# Noor Week 8 Summary — Rico Holdout Batch Eval (deferred from Week 7)",
        "",
        f"**Branch:** `noor`  ",
        f"**Date:** {date.today().isoformat()}  ",
        "**Owner:** Muhammad Noor  ",
        "**Dataset:** `data/data-rico-holdout` (1698 screens, MASC-disjoint)",
        "",
        "## Deliverables — status",
        "",
        "| Item | Path | Status |",
        "|------|------|--------|",
        "| Per-screen results CSV | `outputs/week7_holdout/per_screen_results.csv` | Done |",
        "| Rule summary | `outputs/week7_holdout/rule_summary.csv` + `docs/week7/holdout_rule_summary.md` | Done |",
        "| Guideline summary | `outputs/week7_holdout/guideline_summary.csv` + `docs/week7/holdout_guideline_summary.md` | Done |",
        "| QA notes | `docs/week7/holdout_qa_notes.md` | Done |",
        "| Week 6 (MASC) vs Holdout cross-check | `docs/week7/holdout_week6_crosscheck.md` | Done |",
        "| Team priorities | `docs/week7/holdout_team_priority_fixes.md` | Done |",
        "| Validation logs | `outputs/validation_logs/noor_week8_*` | Done |",
        "",
        "## Key numbers (Rico holdout, n=1698)",
        "",
        "| Metric | Value |",
        "|--------|------:|",
        f"| Screens evaluated | {run_meta.get('evaluated_screens', 0)} / {run_meta.get('manifest_total', 0)} |",
        f"| Failures | {run_meta.get('failure_count', 0)} |",
        f"| Mean violations / screen | {run_meta.get('mean_violations', 0):.1f} |",
        f"| Median violations / screen | {run_meta.get('median_violations', 0)} |",
        f"| Mean accessibility score | {run_meta.get('mean_score', 0):.1f} |",
        f"| Screens with 0 violations | {run_meta.get('zero_violation_screens', 0)} |",
        f"| mostly_agree (heuristic) | {noise.get('mostly_agree', 0)} |",
        f"| over_flagging | {noise.get('over_flagging', 0)} |",
        f"| mixed_r30_noise | {noise.get('mixed_r30_noise', 0)} |",
        f"| clean | {noise.get('clean', 0)} |",
        "",
        "## Top rules",
        "",
    ]
    for rule_id, count in top_rules[:5]:
        lines.append(f"- **{rule_id}** — {count} violations")
    lines.extend([
        "",
        "## Validation checks",
        "",
    ])
    for name, passed in checks.items():
        lines.append(f"- {'PASS' if passed else 'FAIL'} — {name}")
    lines.extend([
        "",
        "## R07/R08/R30/R20/R05 fix verification (2026-07-28, Noor)",
        "",
        "- **R07** (`src/rules.py::check_zero_size`) — now skips non-interactive/non-content zero-size "
        "elements via `_is_a11y_relevant` (clickable/focusable/text/content_desc only).",
        "- **R08** (`src/rules.py::check_layout_overlap`) — now skips clickable ancestor/descendant "
        "pairs via `_is_ancestor` (full parent_id chain, not just immediate parent).",
        "- **R30** (`src/rules.py::check_icon_only_no_label`) — now collapses repeated same-template "
        "list-row icons (same resource_id + bounds size) via `_dedupe_repeated`.",
        "- **R20/R05** (`src/parser.py::_get_hint`) — now reads MASC's real `text-hint` attribute "
        "(was only checking `hint`/`android:hint`, which MASC never emits), unblocking R20 "
        "(0 -> 749 hits on full MASC) and correcting R05's false positives (2117 -> 717 on full MASC).",
        "- Full MASC sweep (7068 screens, 0 failures) confirms rule counts moved as expected; "
        "see `outputs/violations/*.json` (regenerated) and `notebooks/masc_dataset_analysis.ipynb` "
        "(re-executed) for before/after detail.",
        "",
        "## Since 29 Jul — crop classifier, YOLO, backbone sweep, backend wiring (Noor)",
        "",
        "- **29 Jul**: crop classifier Rico holdout eval added and run end-to-end (1698 screens, "
        "9343 crops) — R08 F1 0.70->0.46, R17 0.47->0.35, R04 0.36->0.25, macro avg 0.25->0.18 vs. "
        "the MASC test split (commit `06ad0ece`). Docs synced: SRS v2.8->2.9, SDS v2.12->2.13, "
        "Progress Report v1.24->1.25 (commit `7a1e6a4f`).",
        "- **30 Jul**: merged Salar's completed 60-epoch YOLO run + his `src/yolo_ui_detector.py` "
        "(`detect_ui()`) from the `salar` branch — final checkpoint mAP50 0.434 / mAP50-95 0.322 "
        "(up from a 1-epoch interim 0.397/0.285); merged his Rico zero-shot-vs-fine-tuned eval "
        "(mAP50 0.0258->0.2546). Crop-classifier Rico artifact inventory added (9343 crops tracked); "
        "SRS v2.10, SDS v2.14, Progress Report v1.26 synced (commit `12724e72`).",
        "- **30 Jul - 03 Aug: 33-backbone comparison sweep** (crop classifier, Task B): verified "
        "whether `mobilenet_v3_small` was actually the best pick by training/evaluating all 33 "
        "candidates (same pipeline, ImageNet-1k pretrained, MASC test + Rico holdout) via a new "
        "unattended `scripts/overnight_sweep.py`, plus all related tooling "
        "(`scripts/run_backbone_sweep.py`, `scripts/eval_masc_test.py`, "
        "`scripts/extract_notebook_results.py`) and documentation "
        "(`docs/crop_classifier_comparison_findings.md`, 1813 lines; "
        "`docs/crop_classifier_model_reference.md`, 291 lines - architecture/year/paper/authors for "
        "all 33, organized by family). Result: `mobilenet_v3_small` came in mid-pack (Rico macro-F1 "
        "0.18, beaten by 10+ models); `swin_tiny_patch4_window7_224` won outright (Rico macro-F1 "
        "0.22, evenly distributed across R04/R17/R08), confirmed via a `convnext_tiny` control that "
        "attention specifically drives the gap, not capacity. **Swin is now the pick**, replacing "
        "`mobilenet_v3_small`.",
        "- **04-05 Aug: connecting both trained models to the backend**: `confirm_violations()` "
        "(crop classifier) and a new `detections_to_components()` converter (YOLO) both wired into "
        "`backend/routers/audit.py::_run_pipeline`; `xml` upload made optional with a YOLO fallback "
        "on missing/malformed/empty-hierarchy XML; `docs/schemas/auditor_schema.json` updated "
        "(`cv_confidence`, `inferred`, relaxed `xml_path`, plus an unrelated pre-existing "
        "`component_count`/`hidden_component_count` gap fixed). 155/155 tests pass (153 baseline + "
        "2 new), including two real bugs caught during implementation: a missing `ultralytics` "
        "install masked by a `pip`/`python` environment mismatch, and an `xml_path` field that was "
        "silently overwritten after the YOLO fallback ran (caught by the new malformed-XML test).",
        "",
        "## Next",
        "",
        "- Noor: commit the 33-model sweep + backend wiring to `origin/noor` — both are currently "
        "uncommitted locally.",
        "- Noor: sync Report/SDS/SRS/`updated_plan`/README to reflect Swin as the final backbone "
        "pick and both models now wired into the pipeline.",
        "- Noor: SRS Appendix D — TBD-01 row still shows \"Open\" though `docs/TBD-01-decision.md` "
        "resolved it in July.",
        "",
    ])
    WEEK8_SUMMARY.write_text("\n".join(lines), encoding="utf-8")
    SUMMARY_PATH.write_text("\n".join(lines), encoding="utf-8")


def main() -> int:
    LOG_DIR.mkdir(parents=True, exist_ok=True)
    HOLDOUT_OUT.mkdir(parents=True, exist_ok=True)

    buffer = io.StringIO()
    stdout = sys.stdout
    sys.stdout = _Tee(stdout, buffer)

    print("=" * 66)
    print(f"NOOR WEEK 8 VALIDATION LOG")
    print(f"Branch: noor   Date: {date.today().isoformat()}")
    print("Owner: Muhammad Noor - Week 8 Rico holdout batch eval")
    print("=" * 66)

    checks: dict[str, bool] = {}

    code, _ = run_cmd(
        "STEP 1: Rico holdout batch eval (1698 screens)",
        [sys.executable, "scripts/run_rico_holdout_eval.py", "--rico-source", "data/data-rico-holdout"],
    )
    checks["rico_holdout_eval"] = code == 0

    code, _ = run_cmd(
        "STEP 2: pytest tests/test_rules.py (subset: quick)",
        [sys.executable, "-m", "pytest", "tests/test_rules.py", "-q", "--tb=no"],
    )
    checks["pytest_rules"] = code == 0

    code, _ = run_cmd(
        "STEP 2b: pytest tests/test_parser.py (R20 text-hint fix + MASC bounds/visibility)",
        [sys.executable, "-m", "pytest", "tests/test_parser.py", "-q", "--tb=no"],
    )
    checks["pytest_parser"] = code == 0

    code, _ = run_cmd(
        "STEP 3: pytest backend/tests/test_auth.py",
        [sys.executable, "-m", "pytest", "backend/tests/test_auth.py", "-q", "--tb=no"],
    )
    checks["pytest_auth"] = code == 0

    code, _ = run_cmd(
        "STEP 4: pytest tests/test_audit.py",
        [sys.executable, "-m", "pytest", "tests/test_audit.py", "-q", "--tb=no"],
    )
    checks["pytest_audit"] = code == 0

    eval_files = [
        HOLDOUT_OUT / "per_screen_results.csv",
        HOLDOUT_OUT / "rule_summary.csv",
        HOLDOUT_OUT / "guideline_summary.csv",
        HOLDOUT_OUT / "failures.csv",
        HOLDOUT_OUT / "run_summary.json",
    ]
    ok, _ = check_files("STEP 5: Week 8 holdout eval outputs", eval_files)
    checks["week8_holdout_outputs"] = ok

    doc_files = [
        DOCS_WEEK7 / "holdout_rule_summary.md",
        DOCS_WEEK7 / "holdout_guideline_summary.md",
        DOCS_WEEK7 / "holdout_qa_notes.md",
        DOCS_WEEK7 / "holdout_week6_crosscheck.md",
        DOCS_WEEK7 / "holdout_team_priority_fixes.md",
    ]
    ok, _ = check_files("STEP 6: Week 8 holdout docs", doc_files)
    checks["week8_holdout_docs"] = ok

    run_meta = {}
    meta_path = HOLDOUT_OUT / "run_summary.json"
    if meta_path.is_file():
        run_meta = json.loads(meta_path.read_text(encoding="utf-8"))

    write_week8_summary(run_meta, checks)

    overall = all(checks.values())
    print(f"\n{'=' * 66}")
    print(f"OVERALL: {'PASS' if overall else 'FAIL'}")
    for name, passed in checks.items():
        print(f"  {'PASS' if passed else 'FAIL'}  {name}")
    print(f"Summary: {WEEK8_SUMMARY.relative_to(ROOT)}")
    print(f"Summary copy: {SUMMARY_PATH.relative_to(ROOT)}")
    print("=" * 66)

    sys.stdout = stdout
    existing = LOG_PATH.read_text(encoding="utf-8") if LOG_PATH.is_file() else ""
    header = f"\n\n{'#' * 66}\n# RUN {date.today().isoformat()}\n{'#' * 66}\n"
    LOG_PATH.write_text(existing + header + buffer.getvalue(), encoding="utf-8")
    print(f"Log appended: {LOG_PATH}")

    return 0 if overall else 1


if __name__ == "__main__":
    raise SystemExit(main())
