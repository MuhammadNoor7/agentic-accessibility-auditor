"""Before/after comparison for the hidden-component filtering fix in
src.rules.check(). Not part of the shipped pipeline — a one-off diagnostic
to quantify how much of the previously-reported violation volume was on
elements Android itself marks as visibility="gone" / visible-to-user="False".

"Before" replicates check()'s exact rule-calling sequence over the
UNFILTERED component list (no rule logic is touched or duplicated in
meaning, only re-invoked); "after" is the real, current check().

Usage: python scripts/compare_visibility_filter_impact.py [--per-category N]
"""

from __future__ import annotations

import argparse
import sys
from collections import Counter
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(REPO_ROOT))

from src import rules as rules_mod  # noqa: E402
from src.parser import build_screen_document, load_xml_root, parse_xml_tree  # noqa: E402

ALL_RULES = [f"R{i:02d}" for i in range(1, 31)]


def _run_all_rules_unfiltered(components: list[dict], device_info: dict) -> list[dict]:
    """Mirror check()'s rule-calling sequence exactly, but skip the
    visibility filter — reproduces pre-fix behavior without duplicating or
    modifying any rule's own logic."""
    dpi = device_info.get("dpi", rules_mod.ASSUMED_DENSITY_DPI)
    height_px = device_info.get("height_px", 0)
    violations: list[dict] = []
    violations.extend(rules_mod.check_missing_label(components))
    violations.extend(rules_mod.check_image_button_without_description(components))
    violations.extend(rules_mod.check_duplicate_labels(components))
    violations.extend(rules_mod.check_small_touch_target(components, dpi=dpi))
    violations.extend(rules_mod.check_unlabeled_input(components))
    violations.extend(rules_mod.check_disabled_control(components))
    violations.extend(rules_mod.check_zero_size(components))
    violations.extend(rules_mod.check_layout_overlap(components))
    violations.extend(rules_mod.check_low_contrast(components))
    violations.extend(rules_mod.check_text_overflow(components))
    violations.extend(rules_mod.check_color_only_info(components))
    violations.extend(rules_mod.check_missing_captions(components))
    violations.extend(rules_mod.check_audio_without_transcript(components))
    violations.extend(rules_mod.check_audio_only_notification(components))
    violations.extend(rules_mod.check_bad_focus_order(components))
    violations.extend(rules_mod.check_decorative_in_focus_tree(components))
    violations.extend(rules_mod.check_insufficient_spacing(components, dpi=dpi))
    violations.extend(rules_mod.check_multi_gesture_only(components))
    violations.extend(rules_mod.check_destructive_without_confirmation(components))
    violations.extend(rules_mod.check_hint_only_label(components))
    violations.extend(rules_mod.check_vague_error_message(components))
    violations.extend(rules_mod.check_no_password_toggle(components))
    violations.extend(rules_mod.check_unlabeled_nav_control(components))
    violations.extend(rules_mod.check_missing_screen_title(components, height_px=height_px))
    violations.extend(rules_mod.check_uncontrolled_animation(components))
    violations.extend(rules_mod.check_no_timeout_warning(components))
    violations.extend(rules_mod.check_complex_label_language(components))
    violations.extend(rules_mod.check_font_scale_overflow(components, dpi=dpi))
    violations.extend(rules_mod.check_all_caps_body_text(components))
    violations.extend(rules_mod.check_icon_only_no_label(components))
    return violations


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--per-category", type=int, default=50, help="Files sampled per category (default 50)")
    args = parser.parse_args()

    xml_root = REPO_ROOT / "data" / "data-masc" / "xml"
    per_category: dict[str, list[Path]] = {}
    for f in sorted(xml_root.rglob("*.xml")):
        per_category.setdefault(f.parent.name, []).append(f)

    sample: list[Path] = []
    for category, files in sorted(per_category.items()):
        sample.extend(sorted(files)[: args.per_category])

    print(f"Sampling {args.per_category} files per category, {len(sample)} total.\n")

    rule_before: Counter[str] = Counter()
    rule_after: Counter[str] = Counter()
    total_components = total_hidden = 0

    for xml_path in sample:
        root = load_xml_root(xml_path)
        components = parse_xml_tree(root)
        from src.parser import _extract_device_info  # local import, private helper

        device_info = _extract_device_info(root, components)
        total_components += len(components)
        total_hidden += sum(1 for c in components if not c.get("visible", True))

        before = _run_all_rules_unfiltered(components, device_info)
        rule_before.update(v["rule_id"] for v in before)

        doc = {"components": components, "device_info": device_info, "screen_id": xml_path.stem}
        after_result = rules_mod.check(doc)
        rule_after.update(v["rule_id"] for v in after_result["violations"])

    total_before = sum(rule_before.values())
    total_after = sum(rule_after.values())
    reduction = 100 * (1 - total_after / total_before) if total_before else 0.0

    print(f"Components scanned: {total_components:,} ({total_hidden:,} hidden, "
          f"{100 * total_hidden / total_components:.1f}%)\n")
    print(f"{'Rule':<6}{'Before':>10}{'After':>10}{'Reduction':>12}")
    print("-" * 38)
    for rule_id in ALL_RULES:
        b, a = rule_before.get(rule_id, 0), rule_after.get(rule_id, 0)
        if b == 0 and a == 0:
            continue
        pct = f"{100 * (1 - a / b):.1f}%" if b else "-"
        print(f"{rule_id:<6}{b:>10,}{a:>10,}{pct:>12}")
    print("-" * 38)
    print(f"{'TOTAL':<6}{total_before:>10,}{total_after:>10,}{f'{reduction:.1f}%':>12}")


if __name__ == "__main__":
    main()
