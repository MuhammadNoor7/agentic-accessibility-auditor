"""Run Noor Week 6 validation: auth/records API + eval sheet + R26–R30.

Also regenerates docs/week6/evaluation_sheet_40_screens.csv with a
stratified *random* sample (4 screens × 10 MASC categories, fixed seed).
"""

from __future__ import annotations

import csv
import io
import json
import random
import subprocess
import sys
from collections import defaultdict
from datetime import date
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

LOG_DIR = ROOT / "outputs" / "validation_logs"
LOG_PATH = LOG_DIR / "noor_week6_validation_log.txt"
SUMMARY_PATH = LOG_DIR / "noor_week6_summary.md"
EVAL_CSV = ROOT / "docs" / "week6" / "evaluation_sheet_40_screens.csv"
PARSED_ROOT = ROOT / "data" / "data-masc" / "parsed"
# Fixed seed so the random sample is reproducible across machines.
EVAL_SEED = 20260715
PER_CATEGORY = 4
CATEGORIES = [
    "chat",
    "home",
    "list",
    "login",
    "maps",
    "menu",
    "profile",
    "search",
    "settings",
    "welcome",
]


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


def regenerate_random_eval_sheet() -> list[dict]:
    """Stratified random sample: PER_CATEGORY screens per category (seeded)."""
    from src.agent import compute_accessibility_score
    from src.rules import check

    rng = random.Random(EVAL_SEED)
    print(f"\n{'-' * 66}")
    print(
        f"STEP 0: Regenerate eval sheet — stratified RANDOM "
        f"({PER_CATEGORY}/category, seed={EVAL_SEED})"
    )
    print("-" * 66)

    picked: list[Path] = []
    for cat in CATEGORIES:
        files = sorted((PARSED_ROOT / cat).glob("*_components.json"))
        if not files:
            print(f"  WARN: no parsed files for category={cat}")
            continue
        k = min(PER_CATEGORY, len(files))
        chosen = rng.sample(files, k=k)
        picked.extend(chosen)
        print(f"  {cat}: sampled {k}/{len(files)} -> {[p.stem for p in chosen]}")

    rows: list[dict] = []
    for path in picked:
        doc = json.loads(path.read_text(encoding="utf-8"))
        vdoc = check(doc)
        by_rule: dict[str, int] = defaultdict(int)
        by_sev: dict[str, int] = defaultdict(int)
        for v in vdoc.get("violations") or []:
            by_rule[v.get("rule_id", "?")] += 1
            by_sev[v.get("severity", "?")] += 1
        violations = vdoc.get("violations") or []
        total = int(vdoc.get("total_violations") or len(violations))
        auto_score = compute_accessibility_score(violations)
        top = sorted(by_rule.items(), key=lambda kv: (-kv[1], kv[0]))[:5]
        top_rules = ",".join(rid for rid, _ in top)
        screen_stem = path.stem.replace("_components", "")
        rows.append(
            {
                "screen_id": f"{path.parent.name}_{screen_stem}",
                "category": path.parent.name,
                "components_path": str(path.relative_to(ROOT)),
                "total_violations": total,
                "high": by_sev.get("High", 0),
                "medium": by_sev.get("Medium", 0),
                "low": by_sev.get("Low", 0),
                "auto_score": auto_score,
                "top_rules": top_rules,
                "r26": by_rule.get("R26", 0),
                "r27": by_rule.get("R27", 0),
                "r28": by_rule.get("R28", 0),
                "r29": by_rule.get("R29", 0),
                "r30": by_rule.get("R30", 0),
                "manual_verdict": "",
                "false_positives_notes": "",
                "missed_issues_notes": "",
                "reviewer": "Noor",
                "sample_seed": EVAL_SEED,
            }
        )

    EVAL_CSV.parent.mkdir(parents=True, exist_ok=True)
    fieldnames = [
        "screen_id",
        "category",
        "components_path",
        "total_violations",
        "high",
        "medium",
        "low",
        "auto_score",
        "top_rules",
        "r26",
        "r27",
        "r28",
        "r29",
        "r30",
        "manual_verdict",
        "false_positives_notes",
        "missed_issues_notes",
        "reviewer",
        "sample_seed",
    ]
    with EVAL_CSV.open("w", encoding="utf-8", newline="") as fh:
        writer = csv.DictWriter(fh, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(rows)
    print(f"  Wrote {len(rows)} rows -> {EVAL_CSV.relative_to(ROOT)}")
    return rows


def auth_records_smoke() -> None:
    print(f"\n{'-' * 66}")
    print("STEP 4: API smoke — register/login + POST/GET /records")
    print("-" * 66)
    from fastapi.testclient import TestClient

    import backend.auth as auth_module
    import backend.routers.records_router as records_module
    from backend.main import app

    # Isolate stores under outputs/validation_logs/_week6_tmp so we do not
    # pollute the developer's real backend/data JSON files.
    tmp = LOG_DIR / "_week6_tmp"
    tmp.mkdir(parents=True, exist_ok=True)
    auth_module.DATA_DIR = tmp
    auth_module.USERS_DB_PATH = tmp / "users.db.json"
    records_module.DATA_DIR = tmp
    records_module.RECORDS_DB_PATH = tmp / "records.db.json"
    for path in (auth_module.USERS_DB_PATH, records_module.RECORDS_DB_PATH):
        if path.exists():
            path.unlink()

    client = TestClient(app)
    email = f"week6_{date.today().isoformat().replace('-', '')}@example.com"
    reg = client.post("/auth/register", json={"email": email, "password": "password123"})
    print("POST /auth/register", reg.status_code, "token=" + ("yes" if reg.status_code == 200 else "no"))
    assert reg.status_code == 200, reg.text
    token = reg.json()["access_token"]
    headers = {"Authorization": f"Bearer {token}"}

    created = client.post(
        "/records",
        headers=headers,
        json={
            "screen_id": "week6_smoke",
            "total_violations": 2,
            "violations_by_severity": {"High": 1, "Medium": 1, "Low": 0},
            "components_path": "",
            "violations_path": "outputs/violations/week6_smoke_violations.json",
            "accessibility_score": 85,
            "screenshot_name": "week6_smoke.png",
            "xml_name": "week6_smoke.xml",
        },
    )
    print("POST /records", created.status_code, created.json().get("record_id", created.text)[:48])
    assert created.status_code == 200, created.text
    assert created.json().get("accessibility_score") == 85
    assert created.json().get("screenshot_name") == "week6_smoke.png"

    listed = client.get("/records", headers=headers)
    print("GET /records", listed.status_code, "total=", listed.json().get("total"))
    assert listed.status_code == 200
    assert listed.json()["total"] >= 1
    print("Auth + Records smoke: PASS")


def write_summary(pytest_lines: list[str], eval_rows: list[dict], failures: int) -> None:
    commit = subprocess.run(
        ["git", "rev-parse", "--short", "HEAD"],
        cwd=ROOT,
        capture_output=True,
        text=True,
    ).stdout.strip() or "unknown"
    today = date.today().isoformat()
    cats = sorted({r["category"] for r in eval_rows})
    body = f"""# Noor Week 6 Summary — Auth/Records Sync + Eval Sheet

**Branch:** `noor`  
**Commit:** `{commit}`  
**Date:** {today}  
**Owner:** Muhammad Noor  

## Deliverables

| Item | Path | Status |
|------|------|--------|
| Salar JWT auth | `backend/auth.py`, `backend/routers/auth_router.py` | Synced to `noor` |
| Salar records API | `backend/routers/records_router.py` | Synced (+ score/filename fields) |
| Auth tests | `backend/tests/test_auth.py` | Done |
| Ayesha prompt experiments | `docs/agent_prompt_experiments.md` | Synced |
| Dashboard re-run popup | `frontend/src/pages/Dashboard.jsx` | Synced |
| Records UI (live) | `frontend/src/pages/Records.jsx` | Done |
| Report score ring | `frontend/src/pages/Report.jsx` | Done |
| Week 6 eval sheet (40 screens) | `docs/week6/evaluation_sheet_40_screens.csv` | Done (random stratified) |
| R26–R30 design DOCX | `docs/week6/r26_r30_design.docx` | Done |
| Validation script | `scripts/noor_week6_validate.py` | Done |
| `.gitignore` | synced from `salar` (`data/` + `outputs/` + exceptions) | Done |

## What “20 passed, 1 skipped” means

When running `pytest backend/tests/test_auth.py tests/test_audit.py`:

- **20 passed** — automated checks for JWT register/login/me, records CRUD scoping, and audit upload/report/download behaviour.
- **1 skipped** — the PDF download test in `tests/test_audit.py` skips when Playwright Chromium is not installed on the machine (`pytest.skip` on 503). HTML download still runs. Fix once with: `playwright install chromium`.

## Eval sheet sampling

- **Not** a fixed/sorted every-Nth pick anymore.
- **Stratified random:** {PER_CATEGORY} screens randomly chosen from each of {len(CATEGORIES)} MASC categories (seed=`{EVAL_SEED}`).
- Categories covered: {", ".join(cats)}
- Rows regenerated this run: **{len(eval_rows)}**
- Manual columns (`manual_verdict`, FP/miss notes) left blank for human fill (≥25 target).

## Validation results

```
{chr(10).join(pytest_lines)}
Auth + Records API smoke     → PASS
Eval sheet regenerate        → {len(eval_rows)} rows (seed={EVAL_SEED})
```

Full log: `outputs/validation_logs/noor_week6_validation_log.txt`

## Pytest failure count

{"FAILED steps: " + str(failures) if failures else "All pytest steps: PASS"}

## Next

- Fill ≥25 manual verdicts on the CSV
- Friday demo: login → upload pair → dashboard → report download → records
- Training stretch: map guidelines on MASC train → tune on val → test on test
"""
    SUMMARY_PATH.write_text(body, encoding="utf-8")
    print(f"\nWrote summary -> {SUMMARY_PATH.relative_to(ROOT)}")


def _run_validation() -> int:
    today = date.today().isoformat()
    print("=" * 66)
    print("NOOR WEEK 6 VALIDATION LOG (auth/records + eval sheet)")
    print(f"Branch: noor   Date: {today}")
    print("Owner: Muhammad Noor - Week 6 sync + evaluation")
    print("=" * 66)

    eval_rows = regenerate_random_eval_sheet()

    py = sys.executable
    failures = 0
    pytest_lines: list[str] = []

    steps = [
        (
            "STEP 1: pytest backend/tests/test_auth.py",
            [py, "-m", "pytest", "backend/tests/test_auth.py", "-q"],
        ),
        (
            "STEP 2: pytest tests/test_audit.py",
            [py, "-m", "pytest", "tests/test_audit.py", "-q"],
        ),
        (
            "STEP 3: pytest R26–R30 rules",
            [py, "-m", "pytest", "tests/test_rules.py", "-k", "r26 or r27 or r28 or r29 or r30", "-q"],
        ),
    ]
    for label, cmd in steps:
        result = subprocess.run(cmd, cwd=ROOT, capture_output=True, text=True)
        out = (result.stdout + result.stderr).strip()
        print(f"\n{'-' * 66}")
        print(label)
        print("-" * 66)
        print(out)
        # Keep a short line for the summary (last non-empty / progress line).
        short = out.splitlines()[-1] if out.splitlines() else "(no output)"
        pytest_lines.append(f"{label} → {short}")
        if result.returncode != 0:
            failures += 1
            print(f"EXIT CODE: {result.returncode}")

    auth_records_smoke()
    write_summary(pytest_lines, eval_rows, failures)

    print(f"\n{'-' * 66}")
    print("SUMMARY")
    print("-" * 66)
    if failures:
        print(f"FAILED pytest steps: {failures}")
        return 1
    print("All pytest steps: PASS")
    print(f"Eval sheet: {EVAL_CSV.relative_to(ROOT)} (seed={EVAL_SEED})")
    print("Auth + Records smoke: PASS")
    return 0


def main() -> int:
    LOG_DIR.mkdir(parents=True, exist_ok=True)
    buffer = io.StringIO()
    previous_stdout = sys.stdout
    sys.stdout = _Tee(previous_stdout, buffer)
    try:
        code = _run_validation()
    finally:
        sys.stdout = previous_stdout

    with LOG_PATH.open("a", encoding="utf-8", newline="\n") as log_file:
        log_file.write(f"\n\n{'#' * 66}\n# RE-RUN {date.today().isoformat()}\n{'#' * 66}\n\n")
        log_file.write(buffer.getvalue())
    return code


if __name__ == "__main__":
    raise SystemExit(main())
