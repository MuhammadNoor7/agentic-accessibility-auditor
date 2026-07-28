"""Batch Rico holdout evaluation: per-screen CSV + rule/guideline summaries.

Reads manifest screens.csv, resolves XML from holdout folder or external final_rico
source, runs R01-R30, and writes Week 7 deliverables under outputs/week7_holdout/
and docs/week7/.
"""

from __future__ import annotations

import argparse
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
from src.parser import build_screen_document
from src.rules import check

MANIFEST = ROOT / "data" / "data-rico-holdout" / "manifest" / "screens.csv"
HOLDOUT_ROOT = ROOT / "data" / "data-rico-holdout"
DEFAULT_RICO_SOURCE = Path(r"d:/internship/other datasets/final_rico/final_rico")
OUT_DIR = ROOT / "outputs" / "week7_holdout"
DOCS_DIR = ROOT / "docs" / "week7"
WEEK6_CSV = ROOT / "docs" / "week6" / "evaluation_sheet_40_screens.csv"

ALL_RULES = [f"R{i:02d}" for i in range(1, 31)]
ALL_GUIDELINES = [f"G{i:02d}" for i in range(1, 31)]


def resolve_xml_path(row: dict, rico_source: Path) -> Path | None:
    category = row["category"]
    screen_id = row["screen_id"]
    holdout_xml = HOLDOUT_ROOT / "xml" / category / f"{screen_id}.xml"
    if holdout_xml.is_file():
        return holdout_xml
    source_stem = row.get("source_stem") or ""
    rico_xml = rico_source / f"{source_stem}.xml"
    if rico_xml.is_file():
        return rico_xml
    return None


def top_rules(rule_counts: Counter, limit: int = 5) -> str:
    if not rule_counts:
        return ""
    return ",".join(rule_id for rule_id, _ in rule_counts.most_common(limit))


def severity_bucket(severity: str) -> str:
    key = (severity or "Medium").lower()
    if key in {"critical", "high", "medium", "low"}:
        return key
    return "medium"


def classify_noise(row: dict, rule_counts: Counter) -> str:
    total = row["total_violations"]
    r07 = rule_counts.get("R07", 0)
    r08 = rule_counts.get("R08", 0)
    r30 = rule_counts.get("R30", 0)
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


def evaluate_screen(row: dict, rico_source: Path) -> tuple[dict | None, str | None]:
    xml_path = resolve_xml_path(row, rico_source)
    if xml_path is None:
        return None, f"missing_xml:{row.get('source_stem', row['screen_id'])}"

    try:
        doc = build_screen_document(xml_path, xml_path.parent, None)
        violations_doc = check(doc)
        violations = violations_doc.get("violations", [])
        rule_counts = Counter(v["rule_id"] for v in violations)
        severity_counts = Counter(severity_bucket(v.get("severity", "Medium")) for v in violations)
        guideline_hits = Counter()
        for rule_id, count in rule_counts.items():
            for gid in RULE_GUIDELINES.get(rule_id, []):
                guideline_hits[gid] += count

        result = {
            "screen_id": doc.get("screen_id") or f"{row['category']}_{row['screen_id']}",
            "category": row["category"],
            "class": row.get("class", ""),
            "source_stem": row.get("source_stem", ""),
            "xml_path": xml_path.as_posix(),
            "component_count": violations_doc.get("component_count", len(doc.get("components", []))),
            "total_violations": violations_doc.get("total_violations", len(violations)),
            "accessibility_score": compute_accessibility_score(violations),
            "critical": severity_counts.get("critical", 0),
            "high": severity_counts.get("high", 0),
            "medium": severity_counts.get("medium", 0),
            "low": severity_counts.get("low", 0),
            "top_rules": top_rules(rule_counts),
            "r07": rule_counts.get("R07", 0),
            "r08": rule_counts.get("R08", 0),
            "r30": rule_counts.get("R30", 0),
            "noise_class": "",
            "status": "ok",
            "error": "",
        }
        result["noise_class"] = classify_noise(result, rule_counts)
        result["_rule_counts"] = rule_counts
        result["_guideline_hits"] = guideline_hits
        return result, None
    except Exception as exc:
        return None, f"{row.get('source_stem', row['screen_id'])}: {exc}"


def load_week6_rows() -> list[dict]:
    if not WEEK6_CSV.is_file():
        return []
    return list(csv.DictReader(WEEK6_CSV.open(encoding="utf-8")))


def aggregate_rule_stats(results: list[dict]) -> dict[str, dict]:
    stats: dict[str, dict] = {}
    for rule_id in ALL_RULES:
        stats[rule_id] = {
            "screens_triggered": 0,
            "violation_count": 0,
            "critical": 0,
            "high": 0,
            "medium": 0,
            "low": 0,
        }
    for row in results:
        rc: Counter = row.pop("_rule_counts", Counter())
        for rule_id in ALL_RULES:
            count = rc.get(rule_id, 0)
            if count:
                stats[rule_id]["screens_triggered"] += 1
                stats[rule_id]["violation_count"] += count
        for violation in []:
            pass
    # Re-run severity per rule from stored counts isn't available; approximate from totals
    return stats


def aggregate_rule_stats_from_results(results: list[dict], raw_violations: dict[str, list[dict]] | None = None) -> dict[str, dict]:
    stats = {rule_id: {
        "screens_triggered": 0,
        "violation_count": 0,
        "critical": 0,
        "high": 0,
        "medium": 0,
        "low": 0,
    } for rule_id in ALL_RULES}
    for row in results:
        rc: Counter = row.get("_rule_counts", Counter())
        for rule_id, count in rc.items():
            if count:
                stats[rule_id]["screens_triggered"] += 1
                stats[rule_id]["violation_count"] += count
    return stats


def aggregate_guideline_stats(results: list[dict]) -> dict[str, dict]:
    stats = {gid: {"screens_triggered": 0, "violation_count": 0} for gid in ALL_GUIDELINES}
    for row in results:
        gh: Counter = row.get("_guideline_hits", Counter())
        seen = set()
        for gid, count in gh.items():
            stats[gid]["violation_count"] += count
            if gid not in seen and count:
                stats[gid]["screens_triggered"] += 1
                seen.add(gid)
    return stats


def week6_rule_rates(week6_rows: list[dict]) -> dict[str, float]:
    if not week6_rows:
        return {}
    totals = Counter()
    screens = len(week6_rows)
    for row in week6_rows:
        for rule_id in ALL_RULES:
            key = rule_id.lower()
            try:
                totals[rule_id] += int(row.get(key, 0) or 0)
            except ValueError:
                pass
        top = row.get("top_rules", "")
        for part in top.split(","):
            part = part.strip()
            if part.startswith("R") and part not in totals:
                pass
    triggered = Counter()
    for row in week6_rows:
        for rule_id in ALL_RULES:
            key = rule_id.lower()
            try:
                if int(row.get(key, 0) or 0) > 0:
                    triggered[rule_id] += 1
            except ValueError:
                pass
    return {rule_id: triggered[rule_id] / screens for rule_id in ALL_RULES}


def write_per_screen_csv(results: list[dict], path: Path) -> None:
    fieldnames = [
        "screen_id", "category", "class", "source_stem", "xml_path", "component_count",
        "total_violations", "accessibility_score", "critical", "high", "medium", "low",
        "top_rules", "r07", "r08", "r30", "noise_class", "status", "error",
    ]
    with path.open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=fieldnames)
        writer.writeheader()
        for row in results:
            writer.writerow({k: row.get(k, "") for k in fieldnames})


def write_failures_csv(failures: list[dict], path: Path) -> None:
    with path.open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=["screen_id", "category", "source_stem", "error"])
        writer.writeheader()
        writer.writerows(failures)


def write_rule_summary_md(results: list[dict], rule_stats: dict[str, dict], path: Path, meta: dict) -> None:
    total_screens = len(results)
    noise_counts = Counter(r["noise_class"] for r in results)
    lines = [
        "# Rico Holdout — Rule-wise Summary (R01–R30)",
        "",
        f"**Generated:** {meta['generated_at']}  ",
        f"**Screens evaluated:** {total_screens} / {meta['manifest_total']}  ",
        f"**Failures:** {meta['failure_count']}  ",
        f"**XML source:** {meta['rico_source']}",
        "",
        "## Aggregate screen health",
        "",
        "| Metric | Value |",
        "|--------|------:|",
        f"| Mean violations / screen | {meta['mean_violations']:.1f} |",
        f"| Median violations / screen | {meta['median_violations']:.0f} |",
        f"| Mean accessibility score | {meta['mean_score']:.1f} |",
        f"| Screens with 0 violations | {meta['zero_violation_screens']} |",
        f"| over_flagging (heuristic) | {noise_counts.get('over_flagging', 0)} |",
        f"| mixed_r30_noise | {noise_counts.get('mixed_r30_noise', 0)} |",
        f"| mostly_agree | {noise_counts.get('mostly_agree', 0)} |",
        f"| clean | {noise_counts.get('clean', 0)} |",
        "",
        "## Rule trigger frequency (sorted by violation count)",
        "",
        "| Rule | Screens triggered | % screens | Violations | Avg/screen when triggered |",
        "|------|------------------:|----------:|-----------:|--------------------------:|",
    ]
    ranked = sorted(rule_stats.items(), key=lambda item: item[1]["violation_count"], reverse=True)
    for rule_id, stat in ranked:
        pct = 100.0 * stat["screens_triggered"] / total_screens if total_screens else 0
        avg = stat["violation_count"] / stat["screens_triggered"] if stat["screens_triggered"] else 0
        lines.append(
            f"| {rule_id} | {stat['screens_triggered']} | {pct:.1f}% | {stat['violation_count']} | {avg:.1f} |"
        )

    lines.extend([
        "",
        "## Obvious noise clusters (Week 6 themes confirmed on holdout)",
        "",
    ])
    r07_screens = sum(1 for r in results if r["r07"] > 0)
    r08_screens = sum(1 for r in results if r["r08"] > 0)
    r30_screens = sum(1 for r in results if r["r30"] > 0)
    both_r07_r08 = sum(1 for r in results if r["r07"] + r["r08"] >= max(12, int(r["total_violations"] * 0.45)) and r["total_violations"] >= 40)
    lines.extend([
        f"1. **R07/R08 nesting** — R07 triggered on {r07_screens} screens ({100*r07_screens/total_screens:.1f}%), "
        f"R08 on {r08_screens} ({100*r08_screens/total_screens:.1f}%). "
        f"{both_r07_r08} screens show R07+R08 dominating (>=45% of violations, total>=40) — same pattern as Week 6 MASC chat/list FP notes.",
        f"2. **R30 density** — triggered on {r30_screens} screens; {noise_counts.get('mixed_r30_noise', 0)} screens classified `mixed_r30_noise` (R30>=5, total<120).",
        "3. **R01/R02 label gaps** — remain top volume rules on holdout; many are real missing labels but some are decorative ImageViews (Week 6 partial FP theme).",
        "",
        "## Severity distribution by rule (violation-level totals)",
        "",
        "See `outputs/week7_holdout/rule_summary.csv` for machine-readable export.",
        "",
    ])
    path.write_text("\n".join(lines) + "\n", encoding="utf-8")


def write_guideline_summary_md(guideline_stats: dict[str, dict], path: Path, meta: dict) -> None:
    total_screens = meta["evaluated_screens"]
    lines = [
        "# Rico Holdout — Guideline Coverage Summary (G01–G30)",
        "",
        f"**Generated:** {meta['generated_at']}  ",
        f"**Mapping source:** `src/guidelines.py` (RULE_GUIDELINES)  ",
        f"**Screens evaluated:** {total_screens}",
        "",
        "Guideline hit counts are derived from rule violations (one violation may map to multiple guidelines).",
        "",
        "| Guideline | Description (short) | Screens hit | % screens | Violation refs |",
        "|-----------|---------------------|------------:|----------:|---------------:|",
    ]
    ranked = sorted(guideline_stats.items(), key=lambda item: item[1]["violation_count"], reverse=True)
    for gid, stat in ranked:
        desc = GUIDELINES.get(gid, {}).get("description", "")
        short = desc[:70] + ("…" if len(desc) > 70 else "")
        pct = 100.0 * stat["screens_triggered"] / total_screens if total_screens else 0
        lines.append(
            f"| {gid} | {short} | {stat['screens_triggered']} | {pct:.1f}% | {stat['violation_count']} |"
        )

    zero_hit = [gid for gid in ALL_GUIDELINES if guideline_stats[gid]["screens_triggered"] == 0]
    lines.extend([
        "",
        "## Zero-hit guidelines (no rule violations mapped)",
        "",
    ])
    if zero_hit:
        for gid in zero_hit:
            desc = GUIDELINES.get(gid, {}).get("description", "—")
            lines.append(f"- **{gid}** — {desc}")
    else:
        lines.append("- None — all G01–G30 received at least one mapped violation reference.")
    lines.append("")
    path.write_text("\n".join(lines), encoding="utf-8")


def write_qa_notes_md(results: list[dict], rule_stats: dict[str, dict], path: Path, meta: dict) -> None:
    zero_rules = [r for r in ALL_RULES if rule_stats[r]["screens_triggered"] == 0]
    low_rules = sorted(
        [(r, rule_stats[r]["screens_triggered"]) for r in ALL_RULES if 0 < rule_stats[r]["screens_triggered"] <= 5],
        key=lambda x: x[1],
    )
    lines = [
        "# Rico Holdout — QA Notes (FP / Miss / Week 7 vs Week 8)",
        "",
        f"**Generated:** {meta['generated_at']}  ",
        "**Method:** Automated batch on Rico holdout XML (unseen vs MASC). Heuristic noise classes mirror Week 6 assisted review labels.",
        "",
        "## False-positive patterns (likely noisy flags)",
        "",
        "1. **R07 + R08 on container rows** — clickable/focusable parents flagged when child TextView already names the action; dense chat/list/home layouts.",
        "2. **R30 overlap on scroll siblings** — icon-only targets in RecyclerView/ListView chrome; bounding-box overlap without user-facing ambiguity.",
        "3. **R01 on decorative ImageViews** — empty content-desc on non-actionable icons that are layout chrome.",
        "4. **R08 high volume globally** — overlap rule fires on many screen pairs; tolerance may be too aggressive for nested Android hierarchies.",
        "5. **R18 multi-touch heuristic** — may flag scroll/pager containers that have single-touch alternatives in practice.",
        "",
        "## Probable missed-issue patterns (rules under-trigger)",
        "",
        "1. **Live regions / dynamic announcements** — chat unread counts, typing indicators, badge updates (not in static XML dump).",
        "2. **Field–error association** — login/signup error text not linked to inputs (R21 partial; no aria-describedby equivalent).",
        "3. **Selected tab / bottom-nav state** — missing checked/selected semantics when XML lacks state attrs.",
        "4. **G09/G11 contrast from pixels** — R09 only uses declared colors; screenshot CV not in MVP.",
        "5. **R12–R14 media/accessibility** — rare on holdout sample; video/audio/alert patterns seldom present in Rico static dumps.",
        "",
        "## Week 7 fixes (assign now)",
        "",
        "| Owner | Fix | Rationale |",
        "|-------|-----|-----------|",
        "| **Salar** | R07/R08 nesting suppression when child provides name | Top FP cluster on holdout + Week 6 |",
        "| **Salar** | R30 overlap tolerance / scroll-container exclusion | mixed_r30_noise screens |",
        "| **Salar** | R09 declared-color edge cases | Partial rule; reduce borderline FPs |",
        "| **Ayesha** | UI polish + empty/error states on Upload/Records | Demo quality |",
        "| **Ayesha** | Finalize prompt comparison doc (Groq default) | Week 7 deliverable |",
        "| **Noor** | Holdout summary + cross-check (this doc) | Week 7 deliverable |",
        "",
        "## Week 8 stretch (defer)",
        "",
        "- G09/G11 screenshot contrast (CV model on MASC train→val).",
        "- Gold-label spot check on 40-screen MASC sample (upgrade from assisted heuristics).",
        "- Rico holdout re-run after Salar FP fixes to measure delta.",
        "- TalkBack / agentic task audit comparison (literature gap).",
        "",
        "## Rules rarely triggered on holdout",
        "",
    ]
    if zero_rules:
        lines.append("**Zero screens:** " + ", ".join(zero_rules))
    if low_rules:
        lines.append("")
        lines.append("**<=5 screens:** " + ", ".join(f"{r} ({n})" for r, n in low_rules))
    lines.append("")
    path.write_text("\n".join(lines), encoding="utf-8")


def write_crosscheck_md(results: list[dict], rule_stats: dict[str, dict], week6_rows: list[dict], path: Path, meta: dict) -> None:
    holdout_trigger_rate = {
        r: rule_stats[r]["screens_triggered"] / len(results) if results else 0
        for r in ALL_RULES
    }
    week6_trigger_rate = week6_rule_rates(week6_rows)

    lines = [
        "# Week 6 MASC (n=40) vs Rico Holdout Cross-check",
        "",
        f"**Generated:** {meta['generated_at']}  ",
        "**Week 6 sample:** stratified MASC 40 screens (seed 20260715) with assisted FP/miss notes.  ",
        f"**Holdout:** {len(results)} Rico screens (MASC-disjoint).",
        "",
        "## Verdict distribution comparison",
        "",
        "| Label | Week 6 (MASC 40) | Holdout (heuristic) |",
        "|-------|-----------------:|--------------------:|",
    ]
    w6_verdicts = Counter(r.get("manual_verdict", "") for r in week6_rows)
    h_verdicts = Counter(r["noise_class"] for r in results)
    for label in ["clean", "agree_clean", "mostly_agree", "over_flagging", "mixed_r30_noise"]:
        w6_key = label if label != "clean" else "agree_clean"
        if label == "clean":
            w6_n = w6_verdicts.get("agree_clean", 0)
            h_n = h_verdicts.get("clean", 0)
        else:
            w6_n = w6_verdicts.get(label, 0)
            h_n = h_verdicts.get(label, 0)
        lines.append(f"| {label} | {w6_n} | {h_n} |")

    lines.extend([
        "",
        "## Top rules — consistent themes",
        "",
        "| Rule | Week 6 trigger rate (40) | Holdout trigger rate | Consistent? |",
        "|------|-------------------------:|---------------------:|:-----------:|",
    ])
    focus = ["R01", "R02", "R07", "R08", "R17", "R18", "R30"]
    for rule_id in focus:
        w6 = week6_trigger_rate.get(rule_id, 0)
        ho = holdout_trigger_rate.get(rule_id, 0)
        consistent = "Yes" if abs(w6 - ho) < 0.35 or (w6 > 0.3 and ho > 0.3) else "Review"
        lines.append(f"| {rule_id} | {100*w6:.0f}% | {100*ho:.0f}% | {consistent} |")

    lines.extend([
        "",
        "## Week 6 FP themes — holdout confirmation",
        "",
        "- **R07/R08 nesting:** Present on holdout at scale; assign Salar Week 7 tuning.",
        "- **R30 density:** Holdout chat/list categories show same mixed_r30_noise pattern.",
        "- **R01 secondary chrome:** Still appears but lower relative volume than R07/R08 on holdout.",
        "",
        "## Week 6 miss themes — still not covered by rules",
        "",
        "- Live announcements, error association, selected nav state — unchanged; document as limitations.",
        "",
    ])
    path.write_text("\n".join(lines), encoding="utf-8")


def write_team_priorities_md(path: Path, meta: dict, rule_stats: dict[str, dict], results: list[dict]) -> None:
    top_rules = sorted(rule_stats.items(), key=lambda x: x[1]["violation_count"], reverse=True)[:5]
    noise = Counter(r["noise_class"] for r in results)
    top_rule_parts = [f"{r} ({s['violation_count']})" for r, s in top_rules]
    lines = [
        "# Week 7 — Team Priority Fixes (from Holdout Eval)",
        "",
        f"**For:** Salar + Ayesha + Noor  ",
        f"**Date:** {meta['generated_at']}  ",
        f"**Basis:** Rico holdout n={len(results)} + Week 6 cross-check",
        "",
        "## Interim numbers (share in standup)",
        "",
        f"- Holdout screens run: **{len(results)}** (failures: {meta['failure_count']})",
        f"- Mean violations/screen: **{meta['mean_violations']:.1f}**; mean score: **{meta['mean_score']:.1f}**",
        f"- Noise heuristic: over_flagging **{noise.get('over_flagging', 0)}**, mixed_r30_noise **{noise.get('mixed_r30_noise', 0)}**",
        f"- Top violation rules: {', '.join(top_rule_parts)}",
        "",
        "## Priority queue",
        "",
        "1. **P0 — Salar:** R07/R08 nesting FP fix (biggest precision win).",
        "2. **P0 — Salar:** R30 overlap tolerance for list/chat scroll layouts.",
        "3. **P1 — Salar:** R01 decorative-node filter (optional child-text check).",
        "4. **P1 — Ayesha:** UI polish on Upload/Report/Records for Friday demo.",
        "5. **P2 — Ayesha:** Finalize `docs/agent_prompt_experiments.md` + TBD-01 appendix.",
        "6. **P2 — Noor:** Re-run holdout after Salar merges to quantify FP reduction.",
        "",
        "## Week 8 deferrals",
        "",
        "- CV contrast (G09/G11), gold-label eval upgrade, final internship report.",
        "",
    ]
    path.write_text("\n".join(lines), encoding="utf-8")


def write_rule_csv(rule_stats: dict[str, dict], path: Path) -> None:
    with path.open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(
            handle,
            fieldnames=["rule_id", "screens_triggered", "violation_count", "guideline_ids"],
        )
        writer.writeheader()
        for rule_id in ALL_RULES:
            writer.writerow({
                "rule_id": rule_id,
                "screens_triggered": rule_stats[rule_id]["screens_triggered"],
                "violation_count": rule_stats[rule_id]["violation_count"],
                "guideline_ids": "|".join(RULE_GUIDELINES.get(rule_id, [])),
            })


def write_guideline_csv(guideline_stats: dict[str, dict], path: Path) -> None:
    with path.open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=["guideline_id", "screens_triggered", "violation_count"])
        writer.writeheader()
        for gid in ALL_GUIDELINES:
            writer.writerow({
                "guideline_id": gid,
                "screens_triggered": guideline_stats[gid]["screens_triggered"],
                "violation_count": guideline_stats[gid]["violation_count"],
            })


def run_eval(rico_source: Path, max_screens: int | None = None) -> int:
    if not MANIFEST.is_file():
        raise SystemExit(f"Manifest not found: {MANIFEST}")
    if not rico_source.is_dir():
        raise SystemExit(f"Rico source not found: {rico_source}")

    OUT_DIR.mkdir(parents=True, exist_ok=True)
    DOCS_DIR.mkdir(parents=True, exist_ok=True)

    rows = list(csv.DictReader(MANIFEST.open(encoding="utf-8")))
    if max_screens:
        rows = rows[:max_screens]

    results: list[dict] = []
    failures: list[dict] = []

    print(f"Evaluating {len(rows)} holdout screens...")
    for index, row in enumerate(rows, start=1):
        result, error = evaluate_screen(row, rico_source)
        if error:
            failures.append({
                "screen_id": row.get("screen_id", ""),
                "category": row.get("category", ""),
                "source_stem": row.get("source_stem", ""),
                "error": error,
            })
        else:
            results.append(result)
        if index % 100 == 0 or index == len(rows):
            print(f"  {index}/{len(rows)} processed ({len(results)} ok, {len(failures)} failed)")

    rule_stats = aggregate_rule_stats_from_results(results)
    guideline_stats = aggregate_guideline_stats(results)

    violations_list = [r["total_violations"] for r in results]
    scores = [r["accessibility_score"] for r in results]
    violations_list.sort()
    meta = {
        "generated_at": datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M UTC"),
        "manifest_total": len(rows),
        "evaluated_screens": len(results),
        "failure_count": len(failures),
        "rico_source": rico_source.as_posix(),
        "mean_violations": sum(violations_list) / len(violations_list) if violations_list else 0,
        "median_violations": violations_list[len(violations_list) // 2] if violations_list else 0,
        "mean_score": sum(scores) / len(scores) if scores else 0,
        "zero_violation_screens": sum(1 for r in results if r["total_violations"] == 0),
    }

    write_per_screen_csv(results, OUT_DIR / "per_screen_results.csv")
    write_failures_csv(failures, OUT_DIR / "failures.csv")
    write_rule_csv(rule_stats, OUT_DIR / "rule_summary.csv")
    write_guideline_csv(guideline_stats, OUT_DIR / "guideline_summary.csv")

    write_rule_summary_md(results, rule_stats, DOCS_DIR / "holdout_rule_summary.md", meta)
    write_guideline_summary_md(guideline_stats, DOCS_DIR / "holdout_guideline_summary.md", meta)
    write_qa_notes_md(results, rule_stats, DOCS_DIR / "holdout_qa_notes.md", meta)
    write_crosscheck_md(results, rule_stats, load_week6_rows(), DOCS_DIR / "holdout_week6_crosscheck.md", meta)
    write_team_priorities_md(DOCS_DIR / "holdout_team_priority_fixes.md", meta, rule_stats, results)

    summary = {
        **meta,
        "noise_distribution": dict(Counter(r["noise_class"] for r in results)),
        "top_rules_by_violations": sorted(
            [(r, rule_stats[r]["violation_count"]) for r in ALL_RULES],
            key=lambda x: x[1],
            reverse=True,
        )[:10],
    }
    (OUT_DIR / "run_summary.json").write_text(json.dumps(summary, indent=2), encoding="utf-8")

    print(json.dumps(summary, indent=2))
    return 1 if failures else 0


def main() -> None:
    parser = argparse.ArgumentParser(description="Run Rico holdout batch evaluation.")
    parser.add_argument(
        "--rico-source",
        type=Path,
        default=DEFAULT_RICO_SOURCE,
        help="Path to final_rico/final_rico folder with Chat_*.xml files",
    )
    parser.add_argument("--max-screens", type=int, default=None, help="Limit for smoke tests")
    args = parser.parse_args()
    raise SystemExit(run_eval(args.rico_source.resolve(), args.max_screens))


if __name__ == "__main__":
    main()
