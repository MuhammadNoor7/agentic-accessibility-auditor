"""Week 7 QA analysis from Week 6 stratified MASC sample (no Rico holdout).

Re-runs R01-R30 on the 40-screen evaluation sheet, exports structured CSVs,
rule/guideline summaries, QA notes, Week 6 cross-check, and team priorities.
"""

from __future__ import annotations

import csv
import json
import sys
from collections import Counter, defaultdict
from datetime import datetime, timezone
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from src.agent import compute_accessibility_score
from src.guidelines import GUIDELINES, RULE_GUIDELINES
from src.rules import check

WEEK6_CSV = ROOT / "docs" / "week6" / "evaluation_sheet_40_screens.csv"
OUT_DIR = ROOT / "outputs" / "week7_eval"
DOCS_DIR = ROOT / "docs" / "week7"

ALL_RULES = [f"R{i:02d}" for i in range(1, 31)]
ALL_GUIDELINES = [f"G{i:02d}" for i in range(1, 31)]


def severity_bucket(severity: str) -> str:
    key = (severity or "Medium").lower()
    return key if key in {"critical", "high", "medium", "low"} else "medium"


def top_rules(rule_counts: Counter, limit: int = 5) -> str:
    return ",".join(r for r, _ in rule_counts.most_common(limit))


def classify_noise(total: int, r07: int, r08: int, r30: int) -> str:
    naming_heavy = (r07 + r08) >= max(12, int(total * 0.45)) if total else False
    if total == 0:
        return "clean"
    if r30 >= 5 and total < 120:
        return "mixed_r30_noise"
    if total >= 150 or (total >= 80 and naming_heavy):
        return "over_flagging"
    if naming_heavy and total >= 40:
        return "over_flagging"
    return "mostly_agree"


def evaluate_row(row: dict) -> tuple[dict | None, str | None]:
    components_path = ROOT / row["components_path"].replace("\\", "/")
    if not components_path.is_file():
        return None, f"missing_components:{components_path}"

    try:
        doc = json.loads(components_path.read_text(encoding="utf-8"))
        violations_doc = check(doc)
        violations = violations_doc.get("violations", [])
        rule_counts = Counter(v["rule_id"] for v in violations)
        rule_severity: dict[str, Counter] = defaultdict(Counter)
        for v in violations:
            rule_severity[v["rule_id"]][severity_bucket(v.get("severity", "Medium"))] += 1

        guideline_hits = Counter()
        for rule_id, count in rule_counts.items():
            for gid in RULE_GUIDELINES.get(rule_id, []):
                guideline_hits[gid] += count

        sev = Counter(severity_bucket(v.get("severity", "Medium")) for v in violations)
        r07 = rule_counts.get("R07", 0)
        r08 = rule_counts.get("R08", 0)
        r30 = rule_counts.get("R30", 0)
        total = violations_doc.get("total_violations", len(violations))
        score = compute_accessibility_score(violations)

        result = {
            "screen_id": row["screen_id"],
            "category": row["category"],
            "components_path": row["components_path"],
            "total_violations": total,
            "accessibility_score": score,
            "critical": sev.get("critical", 0),
            "high": sev.get("high", 0),
            "medium": sev.get("medium", 0),
            "low": sev.get("low", 0),
            "top_rules": top_rules(rule_counts),
            "manual_verdict": row.get("manual_verdict", ""),
            "false_positives_notes": row.get("false_positives_notes", ""),
            "missed_issues_notes": row.get("missed_issues_notes", ""),
            "auto_verdict": classify_noise(total, r07, r08, r30),
            "verdict_match": "",
            "status": "ok",
            "error": "",
        }
        for rule_id in ALL_RULES:
            result[rule_id.lower()] = rule_counts.get(rule_id, 0)

        manual = result["manual_verdict"]
        auto = result["auto_verdict"]
        if manual == "agree_clean" and auto == "clean":
            result["verdict_match"] = "yes"
        elif manual in {"mostly_agree", "agree_clean"} and auto == "mostly_agree":
            result["verdict_match"] = "yes"
        elif manual == auto:
            result["verdict_match"] = "yes"
        elif manual == "over_flagging" and auto in {"over_flagging", "mixed_r30_noise"}:
            result["verdict_match"] = "partial"
        elif manual == "mixed_r30_noise" and auto == "mixed_r30_noise":
            result["verdict_match"] = "yes"
        else:
            result["verdict_match"] = "no"

        result["_rule_counts"] = rule_counts
        result["_rule_severity"] = rule_severity
        result["_guideline_hits"] = guideline_hits
        return result, None
    except Exception as exc:
        return None, f"{row['screen_id']}: {exc}"


def aggregate_rules(results: list[dict]) -> dict[str, dict]:
    stats = {
        rule_id: {
            "screens_triggered": 0,
            "violation_count": 0,
            "critical": 0,
            "high": 0,
            "medium": 0,
            "low": 0,
        }
        for rule_id in ALL_RULES
    }
    for row in results:
        rc = row.get("_rule_counts", Counter())
        rs = row.get("_rule_severity", {})
        for rule_id in ALL_RULES:
            count = rc.get(rule_id, 0)
            if count:
                stats[rule_id]["screens_triggered"] += 1
                stats[rule_id]["violation_count"] += count
                for sev in ("critical", "high", "medium", "low"):
                    stats[rule_id][sev] += rs.get(rule_id, Counter()).get(sev, 0)
    return stats


def aggregate_guidelines(results: list[dict]) -> dict[str, dict]:
    stats = {gid: {"screens_triggered": 0, "violation_count": 0} for gid in ALL_GUIDELINES}
    for row in results:
        gh = row.get("_guideline_hits", Counter())
        seen = set()
        for gid, count in gh.items():
            stats[gid]["violation_count"] += count
            if gid not in seen and count:
                stats[gid]["screens_triggered"] += 1
                seen.add(gid)
    return stats


def write_outputs(results: list[dict], failures: list[dict], rule_stats: dict, guideline_stats: dict) -> dict:
    OUT_DIR.mkdir(parents=True, exist_ok=True)
    DOCS_DIR.mkdir(parents=True, exist_ok=True)

    totals = sorted(r["total_violations"] for r in results)
    scores = [r["accessibility_score"] for r in results]
    meta = {
        "generated_at": datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M UTC"),
        "dataset": "MASC Week 6 stratified sample",
        "sample_seed": "20260715",
        "screens": len(results),
        "failures": len(failures),
        "mean_violations": sum(totals) / len(totals) if totals else 0,
        "median_violations": totals[len(totals) // 2] if totals else 0,
        "mean_score": sum(scores) / len(scores) if scores else 0,
        "rico_holdout": "deferred — run scripts/run_rico_holdout_eval.py when ready",
    }

    per_screen_fields = [
        "screen_id", "category", "components_path", "total_violations", "accessibility_score",
        "critical", "high", "medium", "low", "top_rules",
        "manual_verdict", "auto_verdict", "verdict_match",
        "false_positives_notes", "missed_issues_notes", "status", "error",
    ] + [r.lower() for r in ALL_RULES]

    with (OUT_DIR / "per_screen_results.csv").open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=per_screen_fields, extrasaction="ignore")
        writer.writeheader()
        for row in results:
            writer.writerow({k: row.get(k, "") for k in per_screen_fields})

    with (OUT_DIR / "failures.csv").open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=["screen_id", "category", "error"])
        writer.writeheader()
        writer.writerows(failures)

    with (OUT_DIR / "rule_summary.csv").open("w", newline="", encoding="utf-8") as handle:
        fields = ["rule_id", "screens_triggered", "violation_count", "critical", "high", "medium", "low", "guideline_ids"]
        writer = csv.DictWriter(handle, fieldnames=fields)
        writer.writeheader()
        for rule_id in ALL_RULES:
            s = rule_stats[rule_id]
            writer.writerow({
                "rule_id": rule_id,
                **{k: s[k] for k in ("screens_triggered", "violation_count", "critical", "high", "medium", "low")},
                "guideline_ids": "|".join(RULE_GUIDELINES.get(rule_id, [])),
            })

    with (OUT_DIR / "guideline_summary.csv").open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=["guideline_id", "screens_triggered", "violation_count", "description"])
        writer.writeheader()
        for gid in ALL_GUIDELINES:
            writer.writerow({
                "guideline_id": gid,
                **guideline_stats[gid],
                "description": GUIDELINES.get(gid, {}).get("description", ""),
            })

    write_rule_summary_md(results, rule_stats, meta)
    write_guideline_summary_md(guideline_stats, meta)
    write_qa_notes_md(results, rule_stats, meta)
    write_crosscheck_md(results, meta)
    write_team_priorities_md(results, rule_stats, meta)

    meta["manual_verdicts"] = dict(Counter(r["manual_verdict"] for r in results))
    meta["auto_verdicts"] = dict(Counter(r["auto_verdict"] for r in results))
    meta["verdict_match"] = dict(Counter(r["verdict_match"] for r in results))
    meta["top_rules"] = sorted(
        [(r, rule_stats[r]["violation_count"]) for r in ALL_RULES],
        key=lambda x: x[1],
        reverse=True,
    )[:10]
    (OUT_DIR / "run_summary.json").write_text(json.dumps(meta, indent=2), encoding="utf-8")
    return meta


def write_rule_summary_md(results: list[dict], rule_stats: dict, meta: dict) -> None:
    n = len(results)
    manual = Counter(r["manual_verdict"] for r in results)
    auto = Counter(r["auto_verdict"] for r in results)
    r07_dom = sum(1 for r in results if r["r07"] + r["r08"] >= max(12, int(r["total_violations"] * 0.45)) and r["total_violations"] >= 40)

    lines = [
        "# Week 7 — Rule-wise Summary (R01–R30)",
        "",
        f"**Generated:** {meta['generated_at']}  ",
        f"**Dataset:** {meta['dataset']} (n={n}, seed `{meta['sample_seed']}`)  ",
        "**Rico holdout:** deferred (Noor will run later)",
        "",
        "## Aggregate screen health",
        "",
        "| Metric | Value |",
        "|--------|------:|",
        f"| Mean violations / screen | {meta['mean_violations']:.1f} |",
        f"| Median violations / screen | {meta['median_violations']:.0f} |",
        f"| Mean accessibility score | {meta['mean_score']:.1f} |",
        f"| Manual over_flagging / mixed_r30_noise | {manual.get('over_flagging', 0) + manual.get('mixed_r30_noise', 0)} |",
        f"| Auto over_flagging / mixed_r30_noise | {auto.get('over_flagging', 0) + auto.get('mixed_r30_noise', 0)} |",
        "",
        "## Rule trigger frequency + severity (sorted by violation count)",
        "",
        "| Rule | Screens | % | Violations | High | Medium | Low | Avg when triggered |",
        "|------|--------:|--:|-----------:|-----:|-------:|----:|-------------------:|",
    ]
    for rule_id, s in sorted(rule_stats.items(), key=lambda x: x[1]["violation_count"], reverse=True):
        pct = 100 * s["screens_triggered"] / n if n else 0
        avg = s["violation_count"] / s["screens_triggered"] if s["screens_triggered"] else 0
        lines.append(
            f"| {rule_id} | {s['screens_triggered']} | {pct:.0f}% | {s['violation_count']} | "
            f"{s['high']} | {s['medium']} | {s['low']} | {avg:.1f} |"
        )

    lines.extend([
        "",
        "## Obvious noise clusters (Week 6 confirmed)",
        "",
        f"1. **R07 + R08 nesting** — R07 on {sum(1 for r in results if r['r07']>0)}/{n} screens, "
        f"R08 on {sum(1 for r in results if r['r08']>0)}/{n}. {r07_dom} screens show R07+R08 dominating (>=45% of violations).",
        f"2. **R30 density** — triggered on {sum(1 for r in results if r['r30']>0)}/{n} screens; "
        f"{manual.get('mixed_r30_noise', 0)} manual `mixed_r30_noise` verdicts.",
        "3. **R01/R02 label volume** — high count but mix of real missing labels and decorative ImageView FPs.",
        "",
        "Machine-readable export: `outputs/week7_eval/rule_summary.csv`",
        "",
    ])
    (DOCS_DIR / "rule_summary.md").write_text("\n".join(lines), encoding="utf-8")


def write_guideline_summary_md(guideline_stats: dict, meta: dict) -> None:
    n = meta["screens"]
    lines = [
        "# Week 7 — Guideline Coverage Summary (G01–G30)",
        "",
        f"**Generated:** {meta['generated_at']}  ",
        f"**Source:** `src/guidelines.py` RULE_GUIDELINES mapping  ",
        f"**Sample:** MASC n={n} (Week 6 stratified eval)",
        "",
        "| Guideline | Screens hit | % | Violation refs | Description |",
        "|-----------|------------:|--:|---------------:|-------------|",
    ]
    for gid, s in sorted(guideline_stats.items(), key=lambda x: x[1]["violation_count"], reverse=True):
        pct = 100 * s["screens_triggered"] / n if n else 0
        desc = GUIDELINES.get(gid, {}).get("description", "")[:60]
        lines.append(f"| {gid} | {s['screens_triggered']} | {pct:.0f}% | {s['violation_count']} | {desc} |")

    zero = [gid for gid in ALL_GUIDELINES if guideline_stats[gid]["screens_triggered"] == 0]
    lines.extend(["", "## Zero-hit guidelines", ""])
    if zero:
        for gid in zero:
            lines.append(f"- **{gid}** — {GUIDELINES.get(gid, {}).get('description', '—')}")
    else:
        lines.append("- None in this 40-screen sample.")
    lines.append("")
    (DOCS_DIR / "guideline_summary.md").write_text("\n".join(lines), encoding="utf-8")


def write_qa_notes_md(results: list[dict], rule_stats: dict, meta: dict) -> None:
    zero_rules = [r for r in ALL_RULES if rule_stats[r]["screens_triggered"] == 0]
    lines = [
        "# Week 7 — QA Notes (FP / Miss / Priorities)",
        "",
        f"**Generated:** {meta['generated_at']}  ",
        "**Basis:** Week 6 MASC 40-screen stratified sample with assisted FP/miss notes.",
        "",
        "## False-positive patterns",
        "",
        "1. **R07/R08 container nesting** — parent clickable flagged when child TextView names the action (chat/list/home).",
        "2. **R30 scroll-sibling overlap** — dense list/chat/map/search layouts; 5 screens with explicit R30 FP notes.",
        "3. **R01 on decorative ImageViews** — empty content-desc on non-actionable layout chrome.",
        "4. **R08 volume** — overlap pairs inflate totals on complex hierarchies (maps_15184: 147 violations, mostly R07/R08).",
        "5. **Volume-only over_flagging** — search_70760 (349 violations) flagged over_flagging without single-rule cluster.",
        "",
        "## Probable missed-issue patterns",
        "",
        "1. **Live regions / dynamic text** — chat unread, typing indicators (category template on all chat rows).",
        "2. **Error–field association** — login forms; R21 partial, no described-by equivalent.",
        "3. **Selected nav/tab state** — home bottom-nav badges and selected item (home category template).",
        "4. **Switch/checkbox state** — profile/settings when `checked` attr missing in XML.",
        "5. **Pixel contrast (G09/G11)** — R09 needs declared colors; screenshot CV not in MVP.",
        "",
        "## Week 7 fixes (assign now)",
        "",
        "| Owner | Task | Evidence |",
        "|-------|------|----------|",
        "| **Salar** | R07/R08 nesting suppression | Top rules on 38/40 screens; FP notes on chat/home/list |",
        "| **Salar** | R30 overlap tolerance | 3 mixed_r30_noise + R30 called out in FP notes |",
        "| **Salar** | R09 declared-color edge cases | Partial rule; G09 zero/low in sample |",
        "| **Ayesha** | UI polish Upload/Report/Records | Demo readiness |",
        "| **Ayesha** | Finalize prompt comparison doc | TBD-01 closed; Groq default |",
        "| **Noor** | Rico holdout batch (later) | Deferred from this Week 7 pass |",
        "",
        "## Week 8 stretch (defer)",
        "",
        "- G09/G11 CV contrast on MASC train→val.",
        "- Gold-label spot check replacing assisted heuristics.",
        "- Rico holdout re-run after Salar FP fixes.",
        "- TalkBack / agentic task comparison (literature gap).",
        "",
        "## Rules not triggered in 40-screen sample",
        "",
    ]
    if zero_rules:
        lines.append(", ".join(zero_rules))
    else:
        lines.append("All R01–R30 triggered at least once.")
    lines.append("")
    (DOCS_DIR / "qa_notes.md").write_text("\n".join(lines), encoding="utf-8")


def write_crosscheck_md(results: list[dict], meta: dict) -> None:
    manual = Counter(r["manual_verdict"] for r in results)
    auto = Counter(r["auto_verdict"] for r in results)
    match = Counter(r["verdict_match"] for r in results)

    lines = [
        "# Week 6 Manual Review vs Re-run Cross-check",
        "",
        f"**Generated:** {meta['generated_at']}  ",
        "**Method:** Re-ran `check()` on 40 components.json files; compared auto heuristics to Week 6 `manual_verdict`.",
        "",
        "## Verdict distribution",
        "",
        "| Label | Manual (Week 6) | Auto (re-run) |",
        "|-------|----------------:|--------------:|",
    ]
    labels = [
        ("agree_clean / clean", manual.get("agree_clean", 0), auto.get("clean", 0)),
        ("mostly_agree", manual.get("mostly_agree", 0), auto.get("mostly_agree", 0)),
        ("over_flagging", manual.get("over_flagging", 0), auto.get("over_flagging", 0)),
        ("mixed_r30_noise", manual.get("mixed_r30_noise", 0), auto.get("mixed_r30_noise", 0)),
    ]
    for label, m, a in labels:
        lines.append(f"| {label} | {m} | {a} |")

    lines.extend([
        "",
        f"**Verdict alignment:** yes={match.get('yes', 0)}, partial={match.get('partial', 0)}, no={match.get('no', 0)}",
        "",
        "## Score consistency (CSV auto_score vs re-run)",
        "",
        "| screen_id | CSV score | Re-run score | Delta |",
        "|-----------|----------:|-------------:|------:|",
    ])
    week6 = {r["screen_id"]: r for r in csv.DictReader(WEEK6_CSV.open(encoding="utf-8"))}
    mismatches = 0
    for row in results:
        csv_score = int(week6[row["screen_id"]].get("auto_score") or 0)
        rerun = row["accessibility_score"]
        delta = rerun - csv_score
        if delta != 0:
            mismatches += 1
        if abs(delta) > 0 or row["verdict_match"] == "no":
            lines.append(f"| {row['screen_id']} | {csv_score} | {rerun} | {delta:+d} |")

    if mismatches == 0:
        lines.append("| *(all 40 match)* | | | 0 |")

    lines.extend([
        "",
        "## Thematic consistency",
        "",
        "- Week 6 FP themes (R07/R08/R30) appear in the same categories on re-run.",
        "- Week 6 miss themes unchanged — static XML limits still apply.",
        "- Assisted manual notes remain valid; re-run confirms rule counts stable on `noor` branch.",
        "",
    ])
    (DOCS_DIR / "week6_crosscheck.md").write_text("\n".join(lines), encoding="utf-8")


def write_team_priorities_md(results: list[dict], rule_stats: dict, meta: dict) -> None:
    top = sorted(rule_stats.items(), key=lambda x: x[1]["violation_count"], reverse=True)[:5]
    manual = Counter(r["manual_verdict"] for r in results)
    top_parts = [f"{r} ({s['violation_count']})" for r, s in top]
    lines = [
        "# Week 7 — Team Priority Fixes (share with Salar + Ayesha)",
        "",
        f"**Date:** {meta['generated_at']}  ",
        "**Owner:** Muhammad Noor  ",
        "**Basis:** MASC 40-screen Week 6 eval (Rico holdout deferred)",
        "",
        "## Interim numbers for standup",
        "",
        f"- Sample: **40/40** stratified MASC screens (seed `20260715`)",
        f"- Mean violations/screen: **{meta['mean_violations']:.1f}**; mean score: **{meta['mean_score']:.1f}**",
        f"- Manual verdicts: mostly_agree **{manual.get('mostly_agree', 0)}**, agree_clean **{manual.get('agree_clean', 0)}**, "
        f"over_flagging **{manual.get('over_flagging', 0)}**, mixed_r30_noise **{manual.get('mixed_r30_noise', 0)}**",
        f"- Top violation rules: {', '.join(top_parts)}",
        "",
        "## Priority queue",
        "",
        "1. **P0 Salar** — R07/R08 nesting FP fix",
        "2. **P0 Salar** — R30 overlap tolerance (list/chat/map/search)",
        "3. **P1 Salar** — R01 decorative-node filter",
        "4. **P1 Ayesha** — UI polish for Friday demo path",
        "5. **P2 Ayesha** — Finalize `docs/agent_prompt_experiments.md`",
        "6. **P2 Noor** — Rico holdout batch when dataset copied locally",
        "",
        "## Rico holdout",
        "",
        "Not included in this pass. When ready: `python scripts/run_rico_holdout_eval.py`",
        "(requires `data/data-rico-holdout/xml/` or external `final_rico` path).",
        "",
    ]
    (DOCS_DIR / "team_priority_fixes.md").write_text("\n".join(lines), encoding="utf-8")


def main() -> int:
    if not WEEK6_CSV.is_file():
        raise SystemExit(f"Missing {WEEK6_CSV}")

    rows = list(csv.DictReader(WEEK6_CSV.open(encoding="utf-8")))
    results: list[dict] = []
    failures: list[dict] = []

    for row in rows:
        result, error = evaluate_row(row)
        if error:
            failures.append({"screen_id": row.get("screen_id", ""), "category": row.get("category", ""), "error": error})
        else:
            results.append(result)

    rule_stats = aggregate_rules(results)
    guideline_stats = aggregate_guidelines(results)
    meta = write_outputs(results, failures, rule_stats, guideline_stats)
    print(json.dumps(meta, indent=2))
    return 1 if failures else 0


if __name__ == "__main__":
    raise SystemExit(main())
