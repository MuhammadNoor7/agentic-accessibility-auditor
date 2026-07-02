"""Stage 2 rule checker: evaluates parsed UI components against accessibility rules R01-R10.

Consumes a components.json-shaped dict (see docs/json_schemas.md) and produces a
violations.json-shaped dict validated by docs/schemas/auditor_schema.json.
"""

from __future__ import annotations

from collections import defaultdict

from src.schema_documents import SCHEMA_VERSION

# --- Tunable thresholds -------------------------------------------------------

MIN_TOUCH_TARGET_DP = 48
# TBD-03: no density metadata is available from the parser, so this MVP assumes
# a baseline of 160dpi, at which 1px == 1dp.
ASSUMED_DENSITY_DPI = 160
TEXT_OVERFLOW_CHARS_PER_PX2 = 0.15
CONTRAST_RATIO_THRESHOLD = 4.5


# --- Helpers -------------------------------------------------------------------

def _px_to_dp(px: float, dpi: int = ASSUMED_DENSITY_DPI) -> float:
    """Convert a pixel measurement to dp for a given screen density.

    Input: px - length in pixels; dpi - screen density (default 160, see TBD-03).
    Output: float dp value (equals px when dpi == 160).
    """
    return px / (dpi / 160)


def _bounds_wh(bounds: list[int]) -> tuple[int, int]:
    """Compute pixel width/height from a [left, top, right, bottom] bounds list.

    Input: bounds - four-int list [left, top, right, bottom].
    Output: (width, height) tuple; may be zero or negative for invalid rects.
    """
    left, top, right, bottom = bounds
    return right - left, bottom - top


def _overlap_area(bounds_a: list[int], bounds_b: list[int]) -> int:
    """Compute the pixel area where two bounds rectangles intersect.

    Input: bounds_a, bounds_b - four-int [left, top, right, bottom] lists.
    Output: non-negative overlap area in px^2 (0 if they do not intersect).
    """
    left = max(bounds_a[0], bounds_b[0])
    top = max(bounds_a[1], bounds_b[1])
    right = min(bounds_a[2], bounds_b[2])
    bottom = min(bounds_a[3], bounds_b[3])
    if right <= left or bottom <= top:
        return 0
    return (right - left) * (bottom - top)


def _make_violation(
    rule_id: str,
    issue: str,
    component: dict,
    guideline: str,
    severity: str,
    recommendation: str,
    related_component: str | None = None,
) -> dict:
    """Build a violation dict matching the `violation` definition in auditor_schema.json.

    Input: rule_id/issue/guideline/severity/recommendation strings, the offending
        component dict, and an optional related_component id for pair-based rules.
    Output: violation dict with denormalized class/bounds, ready to append to violations[].
    """
    violation = {
        "rule_id": rule_id,
        "issue": issue,
        "component_id": component["component_id"],
        "class": component["class"],
        "bounds": component["bounds"],
        "guideline": guideline,
        "severity": severity,
        "recommendation": recommendation,
    }
    if related_component is not None:
        violation["related_component"] = related_component
    return violation


# --- R01-R05: high priority rules ----------------------------------------------

def check_missing_label(components: list[dict]) -> list[dict]:
    """R01: flag clickable elements with empty text AND empty content_desc.

    Input: components - parsed component dicts.
    Output: list of R01 violation dicts.
    """
    violations = []
    for component in components:
        if not component.get("clickable"):
            continue
        if component.get("text") or component.get("content_desc"):
            continue
        violations.append(
            _make_violation(
                rule_id="R01",
                issue="Missing accessible label",
                component=component,
                guideline="G01 — Missing accessible label",
                severity="High",
                recommendation=(
                    "Add a visible text label or android:contentDescription so "
                    "screen readers can announce this control."
                ),
            )
        )
    return violations


def check_image_button_without_description(components: list[dict]) -> list[dict]:
    """R02: flag clickable ImageButton/ImageView elements with empty content_desc.

    Input: components - parsed component dicts.
    Output: list of R02 violation dicts.
    """
    violations = []
    for component in components:
        class_name = component.get("class", "")
        if "ImageButton" not in class_name and "ImageView" not in class_name:
            continue
        if not component.get("clickable"):
            continue
        if component.get("content_desc"):
            continue
        violations.append(
            _make_violation(
                rule_id="R02",
                issue="Image button without description",
                component=component,
                guideline="G02 — Image button without description",
                severity="High",
                recommendation="Add android:contentDescription with the action name, such as Back.",
            )
        )
    return violations


def check_duplicate_labels(components: list[dict]) -> list[dict]:
    """R03: flag clickable elements that share an identical non-empty text or content_desc.

    Input: components - parsed component dicts.
    Output: list of R03 violation dicts. Every duplicate beyond the first
        occurrence in its group links back to that first element via
        related_component.
    """
    by_text: dict[str, list[dict]] = defaultdict(list)
    by_desc: dict[str, list[dict]] = defaultdict(list)
    for component in components:
        if not component.get("clickable"):
            continue
        text = component.get("text", "")
        desc = component.get("content_desc", "")
        if text:
            by_text[text].append(component)
        if desc:
            by_desc[desc].append(component)

    violations = []
    for group in list(by_text.values()) + list(by_desc.values()):
        if len(group) < 2:
            continue
        anchor = group[0]
        for duplicate in group[1:]:
            violations.append(
                _make_violation(
                    rule_id="R03",
                    issue="Duplicate labels",
                    component=duplicate,
                    guideline="G03 — Duplicate labels",
                    severity="Medium",
                    recommendation=(
                        "Give each control a unique, specific label (e.g., include the "
                        "item name) so screen reader users can tell them apart."
                    ),
                    related_component=anchor["component_id"],
                )
            )
    return violations


def check_small_touch_target(components: list[dict]) -> list[dict]:
    """R04: flag clickable elements whose width or height in dp is below 48dp.

    Input: components - parsed component dicts (bounds are pixels; per TBD-03
        this MVP assumes 160dpi so dp == px).
    Output: list of R04 violation dicts.
    """
    violations = []
    for component in components:
        if not component.get("clickable"):
            continue
        width_px, height_px = _bounds_wh(component["bounds"])
        if width_px <= 0 or height_px <= 0:
            continue  # zero/invalid bounds are R07's concern, not R04's
        width_dp = _px_to_dp(width_px)
        height_dp = _px_to_dp(height_px)
        if width_dp >= MIN_TOUCH_TARGET_DP and height_dp >= MIN_TOUCH_TARGET_DP:
            continue
        violations.append(
            _make_violation(
                rule_id="R04",
                issue="Small touch target",
                component=component,
                guideline="G04 — Small touch target",
                severity="High",
                recommendation=(
                    f"Increase the touch target to at least {MIN_TOUCH_TARGET_DP}x"
                    f"{MIN_TOUCH_TARGET_DP}dp (e.g., add padding or minWidth/minHeight)."
                ),
            )
        )
    return violations


def check_unlabeled_input(components: list[dict]) -> list[dict]:
    """R05: flag EditText elements with empty hint (if present), text, and content_desc.

    Input: components - parsed component dicts. `hint` is read defensively
        since the current parser schema does not emit a hint field.
    Output: list of R05 violation dicts.
    """
    violations = []
    for component in components:
        if "EditText" not in component.get("class", ""):
            continue
        if component.get("hint") or component.get("text") or component.get("content_desc"):
            continue
        violations.append(
            _make_violation(
                rule_id="R05",
                issue="Unlabeled input field",
                component=component,
                guideline="G05 — Unlabeled input field",
                severity="High",
                recommendation="Add android:hint or a programmatic label linked via labelFor.",
            )
        )
    return violations


# --- R06-R10: secondary rules ---------------------------------------------------

def check_disabled_control(components: list[dict]) -> list[dict]:
    """R06: flag clickable elements that are disabled.

    Input: components - parsed component dicts.
    Output: list of R06 violation dicts.
    """
    violations = []
    for component in components:
        if component.get("clickable") and not component.get("enabled", True):
            violations.append(
                _make_violation(
                    rule_id="R06",
                    issue="Disabled important control",
                    component=component,
                    guideline="G06 — Disabled important control",
                    severity="Medium",
                    recommendation=(
                        "Explain why the control is disabled (e.g., helper text) or "
                        "re-enable it once its prerequisites are met."
                    ),
                )
            )
    return violations


def check_zero_size(components: list[dict]) -> list[dict]:
    """R07: flag elements whose bounds width or height is zero (or otherwise invalid).

    Input: components - parsed component dicts.
    Output: list of R07 violation dicts.
    """
    violations = []
    for component in components:
        width_px, height_px = _bounds_wh(component["bounds"])
        if width_px <= 0 or height_px <= 0:
            violations.append(
                _make_violation(
                    rule_id="R07",
                    issue="Invisible or zero-size component",
                    component=component,
                    guideline="G07 — Invisible or zero-size component",
                    severity="Medium",
                    recommendation=(
                        "Remove this element from the accessibility/focus tree, or give "
                        "it valid, non-zero bounds if it should be visible."
                    ),
                )
            )
    return violations


def check_layout_overlap(components: list[dict]) -> list[dict]:
    """R08: flag pairs of clickable elements whose bounds overlap by more than
    50% of the smaller element's area.

    Input: components - parsed component dicts. Restricted to clickable
        elements only, to avoid flagging expected container/child nesting.
    Output: list of R08 violation dicts, one per overlapping pair, anchored on
        the smaller element with related_component pointing at the larger one.
    """
    clickable = [component for component in components if component.get("clickable")]
    violations = []
    for i, first in enumerate(clickable):
        width1, height1 = _bounds_wh(first["bounds"])
        area1 = width1 * height1
        if area1 <= 0:
            continue
        for second in clickable[i + 1:]:
            width2, height2 = _bounds_wh(second["bounds"])
            area2 = width2 * height2
            if area2 <= 0:
                continue
            overlap_area = _overlap_area(first["bounds"], second["bounds"])
            smaller_area = min(area1, area2)
            if overlap_area <= 0.5 * smaller_area:
                continue
            smaller, larger = (first, second) if area1 <= area2 else (second, first)
            violations.append(
                _make_violation(
                    rule_id="R08",
                    issue="Possible layout overlap",
                    component=smaller,
                    guideline="G08 — Possible layout overlap",
                    severity="Medium",
                    recommendation=(
                        "Reposition or resize overlapping controls so neither hides the "
                        "other and the focus order stays predictable."
                    ),
                    related_component=larger["component_id"],
                )
            )
    return violations


def check_low_contrast(components: list[dict]) -> list[dict]:
    """R09: optional low-contrast check (MVP placeholder, see G09 in docs).

    Input: components - parsed component dicts.
    Output: list of R09 violation dicts. Real contrast analysis needs
        screenshot pixel data, which this XML-only rule checker does not have,
        so this only fires if some future pipeline stage attaches a
        `contrast_score` field to a component.
    """
    # TODO: implement real screenshot-based contrast scoring once a screenshot
    # analysis stage exists; R09/G09 is documented as optional for the MVP.
    violations = []
    for component in components:
        contrast_score = component.get("contrast_score")
        if contrast_score is None or contrast_score >= CONTRAST_RATIO_THRESHOLD:
            continue
        violations.append(
            _make_violation(
                rule_id="R09",
                issue="Low contrast",
                component=component,
                guideline="G09 — Low contrast",
                severity="Medium",
                recommendation=(
                    f"Increase contrast to at least {CONTRAST_RATIO_THRESHOLD}:1 between "
                    "text/icon and background."
                ),
            )
        )
    return violations


def check_text_overflow(components: list[dict]) -> list[dict]:
    """R10: flag TextView elements whose text length is disproportionate to their bounds area.

    Input: components - parsed component dicts.
    Output: list of R10 violation dicts, using a chars-per-px^2 density heuristic.
    """
    violations = []
    for component in components:
        if "TextView" not in component.get("class", ""):
            continue
        text = component.get("text", "")
        if not text:
            continue
        width_px, height_px = _bounds_wh(component["bounds"])
        area = width_px * height_px
        if area <= 0:
            continue
        density = len(text) / area
        if density <= TEXT_OVERFLOW_CHARS_PER_PX2:
            continue
        violations.append(
            _make_violation(
                rule_id="R10",
                issue="Text overflow",
                component=component,
                guideline="G10 — Text overflow",
                severity="Low",
                recommendation=(
                    "Shrink the text, wrap it across multiple lines, or enlarge the "
                    "container so the full string is visible."
                ),
            )
        )
    return violations


# --- Entry point -----------------------------------------------------------------

RULES = (
    check_missing_label,
    check_image_button_without_description,
    check_duplicate_labels,
    check_small_touch_target,
    check_unlabeled_input,
    check_disabled_control,
    check_zero_size,
    check_layout_overlap,
    check_low_contrast,
    check_text_overflow,
)


def check(components_json: dict) -> dict:
    """Run all R01-R10 rules over a components.json document and build violations.json.

    Input: components_json - dict matching the components.json schema
        (schema_version, screen_id, image_path, xml_path, components[]).
    Output: dict matching the violations.json schema (schema_version,
        screen_id, image_path, xml_path, total_violations, violations[]).
    """
    components = components_json.get("components", [])
    violations: list[dict] = []
    for rule in RULES:
        violations.extend(rule(components))

    return {
        "schema_version": components_json.get("schema_version", SCHEMA_VERSION),
        "screen_id": components_json.get("screen_id", ""),
        "image_path": components_json.get("image_path", ""),
        "xml_path": components_json.get("xml_path", ""),
        "total_violations": len(violations),
        "violations": violations,
    }
