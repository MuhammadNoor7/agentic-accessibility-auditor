"""Sample runner for the Stage 3 explainer (src/explainer.py).

Runs the rule checker + explainer on a SMALL sample of already-parsed
components.json files (not the full ~500-screen dataset), so explanation
quality/tone can be reviewed by hand before scaling up. Writes one
recommendations.json per sampled screen to outputs/recommendations/, plus a
single sample_review.md pairing each input violation with its generated
explanation for a quick side-by-side read.

Requires an LLM_PROVIDER + matching API key to be set (see .env.example).

Usage:
    python scripts/run_explainer_sample.py
    python scripts/run_explainer_sample.py --count 10 --dataset rico
    python scripts/run_explainer_sample.py --max-violations-per-screen 5
"""

from __future__ import annotations

import argparse
import json
import logging
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))

from src.explainer import build_components_by_id, explain_violations  # noqa: E402
from src.rules import check as check_rules  # noqa: E402

RECOMMENDATIONS_OUTPUT_ROOT = ROOT / "outputs" / "recommendations"
REVIEW_FILE = RECOMMENDATIONS_OUTPUT_ROOT / "sample_review.md"

DATASET_PARSED_ROOTS = {
    "masc": ROOT / "data" / "data-masc" / "parsed",
    "rico": ROOT / "data" / "data-rico-holdout" / "parsed",
}


def _pick_sample_files(parsed_root: Path, count: int) -> list[Path]:
    """Pick up to `count` components.json files that have at least one violation.

    Input: parsed_root - directory tree of *_components.json files;
        count - how many screens to sample.
    Output: list of Paths (screens with zero violations are skipped - nothing
        to explain there), stopping once `count` are found.
    """
    candidates = sorted(parsed_root.rglob("*_components.json"))
    picked: list[Path] = []
    for path in candidates:
        components_json = json.loads(path.read_text(encoding="utf-8"))
        violations_doc = check_rules(components_json)
        if violations_doc["total_violations"] > 0:
            picked.append(path)
        if len(picked) >= count:
            break
    return picked


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--count", type=int, default=6, help="Number of sample screens to run (default: 6)")
    parser.add_argument("--dataset", choices=sorted(DATASET_PARSED_ROOTS), default="masc")
    parser.add_argument(
        "--max-violations-per-screen",
        type=int,
        default=None,
        help="Cap violations explained per screen, for a quicker/cheaper sample run",
    )
    args = parser.parse_args(argv)

    logging.basicConfig(level=logging.INFO, format="%(levelname)s %(message)s")

    parsed_root = DATASET_PARSED_ROOTS[args.dataset]
    if not parsed_root.exists():
        print(f"Error: parsed dataset root not found: {parsed_root}", file=sys.stderr)
        return 1

    sample_files = _pick_sample_files(parsed_root, args.count)
    if not sample_files:
        print(f"No screens with violations found under {parsed_root}", file=sys.stderr)
        return 1

    RECOMMENDATIONS_OUTPUT_ROOT.mkdir(parents=True, exist_ok=True)
    review_lines = ["# Explainer sample review"]

    for path in sample_files:
        components_json = json.loads(path.read_text(encoding="utf-8"))
        violations_doc = check_rules(components_json)
        if args.max_violations_per_screen:
            violations_doc = dict(violations_doc)
            violations_doc["violations"] = violations_doc["violations"][: args.max_violations_per_screen]
            violations_doc["total_violations"] = len(violations_doc["violations"])

        components_by_id = build_components_by_id(components_json)
        print(f"\n=== {violations_doc['screen_id']} ({violations_doc['total_violations']} violation(s)) ===")

        recommendations_doc = explain_violations(violations_doc, components_by_id)

        output_file = RECOMMENDATIONS_OUTPUT_ROOT / f"{violations_doc['screen_id']}_recommendations.json"
        output_file.write_text(json.dumps(recommendations_doc, indent=2), encoding="utf-8")
        print(
            f"  -> {recommendations_doc['total_recommendations']}/{recommendations_doc['total_violations']} "
            f"explained, written to {output_file}"
        )

        violations_by_key = {(v["rule_id"], v["component_id"]): v for v in violations_doc["violations"]}
        review_lines.append(f"\n## {violations_doc['screen_id']}")
        for rec in recommendations_doc["recommendations"]:
            source_violation = violations_by_key.get((rec["rule_id"], rec["component_id"]), {})
            review_lines.append(
                f"\n### {rec['rule_id']} / {rec['component_id']} ({source_violation.get('severity', '?')})"
            )
            review_lines.append(f"- **Input issue:** {source_violation.get('issue', '?')}")
            review_lines.append(f"- **Guideline IDs:** {', '.join(rec['guideline_ids'])}")
            review_lines.append(f"- **Explanation:** {rec['explanation']}")
            review_lines.append(f"- **User impact:** {rec['user_impact']}")
            review_lines.append(f"- **Fix:** {rec['fix']}")

    REVIEW_FILE.write_text("\n".join(review_lines) + "\n", encoding="utf-8")
    print(f"\nSample review written to {REVIEW_FILE}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
