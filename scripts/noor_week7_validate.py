"""Run Noor Week 7 validation: MASC eval analysis + pytest + artifact checks."""

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
LOG_PATH = LOG_DIR / "noor_week7_validation_log.txt"
SUMMARY_PATH = LOG_DIR / "noor_week7_summary.md"
WEEK7_SUMMARY = ROOT / "outputs" / "week7_summary.md"
EVAL_OUT = ROOT / "outputs" / "week7_eval"
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


def write_week7_summary(run_meta: dict, checks: dict[str, bool]) -> None:
    top_rules = run_meta.get("top_rules", [])
    manual = run_meta.get("manual_verdicts", {})
    lines = [
        "# Noor Week 7 Summary — QA Analysis (MASC 40-screen)",
        "",
        f"**Branch:** `noor`  ",
        f"**Date:** {date.today().isoformat()}  ",
        "**Owner:** Muhammad Noor  ",
        "**Rico holdout:** deferred",
        "",
        "## Deliverables — status",
        "",
        "| Item | Path | Status |",
        "|------|------|--------|",
        "| Per-screen results CSV | `outputs/week7_eval/per_screen_results.csv` | Done |",
        "| Rule summary | `outputs/week7_eval/rule_summary.csv` + `docs/week7/rule_summary.md` | Done |",
        "| Guideline summary | `outputs/week7_eval/guideline_summary.csv` + `docs/week7/guideline_summary.md` | Done |",
        "| QA notes | `docs/week7/qa_notes.md` | Done |",
        "| Week 6 cross-check | `docs/week7/week6_crosscheck.md` | Done |",
        "| Team priorities | `docs/week7/team_priority_fixes.md` | Done |",
        "| Validation logs | `outputs/validation_logs/noor_week7_*` | Done |",
        "",
        "## Key numbers (MASC n=40, seed `20260715`)",
        "",
        f"| Metric | Value |",
        f"|--------|------:|",
        f"| Screens evaluated | {run_meta.get('screens', 0)} |",
        f"| Failures | {run_meta.get('failures', 0)} |",
        f"| Mean violations / screen | {run_meta.get('mean_violations', 0):.1f} |",
        f"| Mean accessibility score | {run_meta.get('mean_score', 0):.1f} |",
        f"| mostly_agree (manual) | {manual.get('mostly_agree', 0)} |",
        f"| agree_clean | {manual.get('agree_clean', 0)} |",
        f"| over_flagging | {manual.get('over_flagging', 0)} |",
        f"| mixed_r30_noise | {manual.get('mixed_r30_noise', 0)} |",
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
        "## Next",
        "",
        "- Salar: R07/R08/R30 FP tuning",
        "- Ayesha: UI polish + prompt doc finalize",
        "- Noor: Rico holdout batch (`scripts/run_rico_holdout_eval.py`) when dataset ready",
        "",
    ])
    WEEK7_SUMMARY.write_text("\n".join(lines), encoding="utf-8")
    SUMMARY_PATH.write_text("\n".join(lines), encoding="utf-8")


def main() -> int:
    LOG_DIR.mkdir(parents=True, exist_ok=True)
    EVAL_OUT.mkdir(parents=True, exist_ok=True)

    buffer = io.StringIO()
    stdout = sys.stdout
    sys.stdout = _Tee(stdout, buffer)

    print("=" * 66)
    print(f"NOOR WEEK 7 VALIDATION LOG")
    print(f"Branch: noor   Date: {date.today().isoformat()}")
    print("Owner: Muhammad Noor - Week 7 QA analysis")
    print("=" * 66)

    checks: dict[str, bool] = {}

    code, _ = run_cmd(
        "STEP 1: Week 7 eval analysis (MASC 40-screen)",
        [sys.executable, "scripts/run_week7_eval_analysis.py"],
    )
    checks["week7_eval_analysis"] = code == 0

    code, _ = run_cmd(
        "STEP 2: pytest tests/test_rules.py (subset: quick)",
        [sys.executable, "-m", "pytest", "tests/test_rules.py", "-q", "--tb=no"],
    )
    checks["pytest_rules"] = code == 0

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
        EVAL_OUT / "per_screen_results.csv",
        EVAL_OUT / "rule_summary.csv",
        EVAL_OUT / "guideline_summary.csv",
        EVAL_OUT / "failures.csv",
        EVAL_OUT / "run_summary.json",
    ]
    ok, _ = check_files("STEP 5: Week 7 eval outputs", eval_files)
    checks["week7_eval_outputs"] = ok

    doc_files = [
        DOCS_WEEK7 / "rule_summary.md",
        DOCS_WEEK7 / "guideline_summary.md",
        DOCS_WEEK7 / "qa_notes.md",
        DOCS_WEEK7 / "week6_crosscheck.md",
        DOCS_WEEK7 / "team_priority_fixes.md",
        DOCS_WEEK7 / "README.md",
    ]
    ok, _ = check_files("STEP 6: Week 7 docs", doc_files)
    checks["week7_docs"] = ok

    run_meta = {}
    meta_path = EVAL_OUT / "run_summary.json"
    if meta_path.is_file():
        run_meta = json.loads(meta_path.read_text(encoding="utf-8"))

    write_week7_summary(run_meta, checks)

    overall = all(checks.values())
    print(f"\n{'=' * 66}")
    print(f"OVERALL: {'PASS' if overall else 'FAIL'}")
    for name, passed in checks.items():
        print(f"  {'PASS' if passed else 'FAIL'}  {name}")
    print(f"Summary: {WEEK7_SUMMARY.relative_to(ROOT)}")
    print(f"Summary copy: {SUMMARY_PATH.relative_to(ROOT)}")
    print("=" * 66)

    sys.stdout = stdout
    existing = LOG_PATH.read_text(encoding="utf-8") if LOG_PATH.is_file() else ""
    header = f"\n\n{'#' * 66}\n# RE-RUN {date.today().isoformat()}\n{'#' * 66}\n"
    LOG_PATH.write_text(existing + header + buffer.getvalue(), encoding="utf-8")
    print(f"Log appended: {LOG_PATH}")

    return 0 if overall else 1


if __name__ == "__main__":
    raise SystemExit(main())
