"""Stage 2 rule checker: evaluates parsed UI components against accessibility rules R01-R20.

Consumes a components.json-shaped dict (see docs/json_schemas.md) and produces a
violations.json-shaped dict validated by docs/schemas/auditor_schema.json.
"""

from __future__ import annotations

import re
from collections import defaultdict

from src.schema_documents import SCHEMA_VERSION

# --- Tunable thresholds -------------------------------------------------------

MIN_TOUCH_TARGET_DP = 48
# TBD-03: fallback baseline when a screen's components.json carries no
# device_info/dpi (e.g. older output, or a screen with no density metadata in
# its source XML) — at 160dpi, 1px == 1dp.
ASSUMED_DENSITY_DPI = 160
TEXT_OVERFLOW_CHARS_PER_PX2 = 0.15
CONTRAST_RATIO_THRESHOLD = 4.5
MIN_SPACING_DP = 8
NEARBY_LABEL_PX = 250
NEARBY_TRANSCRIPT_PX = 400
NEARBY_NOTIFICATION_ICON_PX = 350
# R05: widget classes treated as text-input fields, beyond plain EditText, to
# also cover custom/cross-platform input widgets.
INPUT_CLASSES = ("EditText", "InputField", "TextField", "TextInput")

TRANSCRIPT_TOKENS = ("transcript", "subtitle", "caption", "cc", "audio_description", "audiodesc")
NOTIFICATION_TOKENS = ("notification", "notified", "incoming call", "missed call", "alert tone", "new message alert")
DESTRUCTIVE_TOKENS = (
    "delete",
    "remove",
    "clear all",
    "erase",
    "trash",
    "discard",
    "unsubscribe",
    "permanently delete",
    "delete account",
)
CONFIRM_TOKENS = (
    "confirm",
    "are you sure",
    "delete anyway",
    "yes, delete",
    "yes delete",
    "cannot be undone",
    "permanently remove",
)
GESTURE_TOKENS = (
    "pinch",
    "two finger",
    "two-finger",
    "multitouch",
    "multi-touch",
    "rotate with two",
    "spread to zoom",
    "use two fingers",
)
AUDIO_CLASS_MARKERS = ("AudioView", "SoundRecorder", "VoiceRecorder", "MediaRecorder")
AUDIO_RESOURCE_TOKENS = ("audio", "podcast", "voice_memo", "voice_message", "voicemessage", "sound_recorder")
DECORATIVE_CLASS_MARKERS = ("ImageView", "android.view.View", "FrameLayout", "Space", "ViewStub")
LABEL_CLASS_MARKERS = ("TextView", "AppCompatTextView", "FontTextView")
DIALOG_CLASS_MARKERS = ("Dialog", "AlertDialog", "BottomSheetDialog")
# R11: checkable-state widgets whose on/off appearance is conveyed almost
# entirely by a fill/track color change (plus, at most, a small glyph).
STATE_WIDGET_CLASS_MARKERS = ("CheckBox", "Switch", "ToggleButton", "RadioButton", "CompoundButton")
# R28: ~200% system font scale, per G28; standard single-line line-height
# multiplier used to estimate required box height from a declared sp size.
FONT_SCALE_TARGET = 2.0
LINE_HEIGHT_FACTOR = 1.2

# R21: resource_id/class naming that marks a TextView as an error/validation message.
ERROR_TOKENS = ("error", "err_msg", "errormessage", "validation_message", "invalid_message", "field_error")
# R22: resource_id/content_desc naming for a password show/hide toggle control.
PASSWORD_TOGGLE_TOKENS = (
    "show_password",
    "hide_password",
    "password_toggle",
    "toggle_password",
    "text_input_password_toggle",
    "show password",
    "hide password",
    "reveal password",
    "eye",
    "visibility",
)
NEARBY_PASSWORD_TOGGLE_PX = 250  # max _edge_gap px, not center distance (see check_no_password_toggle)
# R23: resource_id tokens identifying a navigation control (back/close/home/menu).
NAV_RESOURCE_TOKENS = ("back", "close", "home", "menu")
# R24: resource_id/class naming hints for a toolbar/title region, checked before
# falling back to a pure position heuristic (see _is_toolbar_candidate).
TOOLBAR_TOKENS = ("toolbar", "actionbar", "action_bar", "appbar", "app_bar", "title", "header")
# Fraction of screen height (from device_info.height_px) treated as the
# toolbar/title region when no naming hint is present.
TOOLBAR_REGION_FRACTION = 0.12
# R25: resource_id/content_desc tokens for an animation pause/stop control.
PAUSE_STOP_TOKENS = ("pause", "stop", "dismiss", "freeze")
NEARBY_ANIMATION_CONTROL_PX = 300
# R26: text/resource_id tokens marking a countdown/session-timeout message, and
# tokens/pattern for the "Extend"/"OK" control that should accompany it.
SESSION_TOKENS = (
    "session expired",
    "session timeout",
    "session is about to expire",
    "time remaining",
    "timeout",
    "expires in",
    "auto logout",
    "auto-logout",
    "signed out",
    "log out in",
)
EXTEND_SESSION_TOKENS = ("extend", "stay logged in", "keep me signed in", "continue session", "resume session")
OK_BUTTON_RE = re.compile(r"^(ok|okay)$", re.IGNORECASE)
# R27: a content_desc/hint longer than this many words, with an average word
# length above this many characters, reads as jargon rather than plain language.
COMPLEX_LABEL_MIN_WORDS = 5
COMPLEX_LABEL_AVG_WORD_CHARS = 8
# R29: textAllCaps text longer than this many words is body/instructional
# content, not a short label, and should not be all-caps.
ALL_CAPS_MIN_WORDS = 3
# R30: icon-only widget classes, broader than R02's ImageButton/ImageView match
# so it also catches custom icon widgets (e.g. IconButton, MaterialIconButton).
ICON_CLASS_MARKERS = ("ImageButton", "ImageView", "Icon")


# --- Helpers -------------------------------------------------------------------

def _px_to_dp(px: float, dpi: int = ASSUMED_DENSITY_DPI) -> float:
    """Convert a pixel measurement to dp for a given screen density.

    Input: px - length in pixels; dpi - screen density (default 160, see TBD-03).
    Output: float dp value (equals px when dpi == 160).
    """
    return px / (dpi / 160)


def _hex_to_rgb(hex_color: str) -> tuple[int, int, int] | None:
    """Parse a #RRGGBB or #AARRGGBB hex string (as produced by the parser's
    _get_color_attr) into an (r, g, b) triple, ignoring any alpha channel.

    Input: hex_color - a normalized hex string, e.g. "#FF0000" or "#80FF0000".
    Output: (r, g, b) each 0-255, or None if the string isn't a recognized length.
    """
    digits = hex_color.lstrip("#")
    if len(digits) == 8:
        digits = digits[2:]
    if len(digits) != 6:
        return None
    try:
        return int(digits[0:2], 16), int(digits[2:4], 16), int(digits[4:6], 16)
    except ValueError:
        return None


def _relative_luminance(rgb: tuple[int, int, int]) -> float:
    """WCAG relative luminance for an sRGB triple (0-255 per channel)."""
    def channel(value: int) -> float:
        c = value / 255
        return c / 12.92 if c <= 0.03928 else ((c + 0.055) / 1.055) ** 2.4
    r, g, b = rgb
    return 0.2126 * channel(r) + 0.7152 * channel(g) + 0.0722 * channel(b)


def _wcag_contrast_ratio(hex_a: str, hex_b: str) -> float | None:
    """WCAG contrast ratio between two declared #RRGGBB/#AARRGGBB colors.

    Input: hex_a, hex_b - normalized hex color strings (see _hex_to_rgb).
    Output: contrast ratio >= 1.0, or None if either color can't be parsed.
    """
    rgb_a, rgb_b = _hex_to_rgb(hex_a), _hex_to_rgb(hex_b)
    if rgb_a is None or rgb_b is None:
        return None
    lum_a, lum_b = _relative_luminance(rgb_a), _relative_luminance(rgb_b)
    lighter, darker = max(lum_a, lum_b), min(lum_a, lum_b)
    return (lighter + 0.05) / (darker + 0.05)


def _bounds_wh(bounds: list[int]) -> tuple[int, int]:
    """Compute pixel width/height from a [left, top, right, bottom] bounds list.

    Input: bounds - four-int list [left, top, right, bottom].
    Output: (width, height) tuple; may be zero or negative for invalid rects.
    """
    left, top, right, bottom = bounds
    return right - left, bottom - top


def _area(component: dict) -> int:
    """Compute a component's bounds area, treating zero-size/inverted rects as zero.

    Input: component - a component dict with a `bounds` [left, top, right, bottom] list.
    Output: non-negative pixel area (0 for zero-size or inverted rects, instead
        of a negative number that could otherwise poison downstream comparisons).
    """
    left, top, right, bottom = component["bounds"]
    return max(0, right - left) * max(0, bottom - top)


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


def _dedupe_repeated(components: list[dict]) -> list[tuple[dict, int]]:
    """Collapse components that are repeated instances of the same
    list/grid row template into one (representative, count) pair each.

    Input: components - flagged component dicts to dedupe.
    Output: list of (representative_component, occurrence_count) pairs, in
        first-seen order. Grouped by (resource_id, width, height) — the
        signature a repeated RecyclerView/ListView row template shares
        across instances. Components with no resource_id can't be safely
        correlated this way, so each is kept as its own count-1 entry.
    """
    groups: dict[tuple[str, int, int], list[dict]] = defaultdict(list)
    order: list[tuple[str, int, int]] = []
    singles: list[dict] = []
    for component in components:
        resource_id = component.get("resource_id", "")
        if not resource_id:
            singles.append(component)
            continue
        width_px, height_px = _bounds_wh(component["bounds"])
        key = (resource_id, width_px, height_px)
        if key not in groups:
            order.append(key)
        groups[key].append(component)

    result = [(component, 1) for component in singles]
    for key in order:
        members = groups[key]
        result.append((members[0], len(members)))
    return result


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


def _combined_text(component: dict) -> str:
    """Lowercase concatenation of text-like fields for token matching."""
    parts = (
        component.get("text", ""),
        component.get("content_desc", ""),
        component.get("hint", ""),
        component.get("resource_id", ""),
    )
    return " ".join(str(part) for part in parts if part).lower()


def _contains_token(text: str, tokens: tuple[str, ...]) -> bool:
    return any(token in text for token in tokens)


def _is_input_field(component: dict) -> bool:
    class_name = component.get("class", "")
    return any(input_class in class_name for input_class in INPUT_CLASSES)


def _edge_gap(bounds_a: list[int], bounds_b: list[int]) -> int:
    """Minimum pixel gap between two non-overlapping axis-aligned rectangles."""
    left_a, top_a, right_a, bottom_a = bounds_a
    left_b, top_b, right_b, bottom_b = bounds_b
    if right_a <= left_b:
        dx = left_b - right_a
    elif right_b <= left_a:
        dx = left_a - right_b
    else:
        dx = 0
    if bottom_a <= top_b:
        dy = top_b - bottom_a
    elif bottom_b <= top_a:
        dy = top_a - bottom_b
    else:
        dy = 0
    if dx == 0 and dy == 0:
        return 0
    if dx == 0:
        return dy
    if dy == 0:
        return dx
    return min(dx, dy)


def _is_nearby(bounds_a: list[int], bounds_b: list[int], max_px: int) -> bool:
    """True when rectangle centers are within max_px (cheap proximity check)."""
    ax = (bounds_a[0] + bounds_a[2]) // 2
    ay = (bounds_a[1] + bounds_a[3]) // 2
    bx = (bounds_b[0] + bounds_b[2]) // 2
    by = (bounds_b[1] + bounds_b[3]) // 2
    return abs(ax - bx) <= max_px and abs(ay - by) <= max_px


def _has_nearby_label(input_component: dict, components: list[dict]) -> bool:
    """True when a TextView-like label sits near an input field."""
    if input_component.get("label_for"):
        return True
    if _has_parent_sibling_label(input_component, components):
        return True
    for candidate in components:
        class_name = candidate.get("class", "")
        if not any(marker in class_name for marker in LABEL_CLASS_MARKERS):
            continue
        if not candidate.get("text"):
            continue
        if _is_nearby(input_component["bounds"], candidate["bounds"], NEARBY_LABEL_PX):
            return True
    return False


def _has_parent_sibling_label(input_component: dict, components: list[dict]) -> bool:
    """True when a sibling TextView under the same parent sits above the input."""
    parent_id = input_component.get("parent_id", "")
    if not parent_id:
        return False
    input_top = input_component["bounds"][1]
    for candidate in components:
        if candidate["component_id"] == input_component["component_id"]:
            continue
        if candidate.get("parent_id") != parent_id:
            continue
        class_name = candidate.get("class", "")
        if not any(marker in class_name for marker in LABEL_CLASS_MARKERS):
            continue
        if not candidate.get("text"):
            continue
        if candidate["bounds"][3] <= input_top + 30:
            return True
    return False


def _has_sibling_token(anchor: dict, components: list[dict], tokens: tuple[str, ...]) -> bool:
    """True when a component sharing anchor's parent_id (a genuine tree
    sibling, not just a bounds-distance guess) matches one of tokens."""
    parent_id = anchor.get("parent_id", "")
    if not parent_id:
        return False
    for candidate in components:
        if candidate["component_id"] == anchor["component_id"]:
            continue
        if candidate.get("parent_id") != parent_id:
            continue
        if _contains_token(_combined_text(candidate), tokens):
            return True
    return False


def _is_audio_component(component: dict, *, has_video: bool) -> bool:
    if component.get("media_type") == "audio":
        return True
    class_name = component.get("class", "")
    resource_text = _combined_text(component)
    if any(marker in class_name for marker in AUDIO_CLASS_MARKERS):
        return True
    if "MediaPlayer" in class_name and not has_video:
        return True
    return _contains_token(resource_text, AUDIO_RESOURCE_TOKENS)


def _is_video_component(component: dict) -> bool:
    if component.get("media_type") == "video":
        return True
    class_name = component.get("class", "")
    return "VideoView" in class_name or "MediaPlayer" in class_name


def _is_decorative_focusable(component: dict) -> bool:
    important = component.get("important_for_accessibility", "").lower()
    if important in {"no", "nohideDescendants", "no_hide_descendants"}:
        return True
    if not component.get("focusable") or component.get("clickable"):
        return False
    if component.get("text") or component.get("content_desc"):
        return False
    class_name = component.get("class", "")
    return any(marker in class_name for marker in DECORATIVE_CLASS_MARKERS) and _area(component) > 0


def _screen_has_token(components: list[dict], tokens: tuple[str, ...]) -> bool:
    return any(_contains_token(_combined_text(component), tokens) for component in components)


def _has_nearby_token(
    anchor: dict,
    components: list[dict],
    tokens: tuple[str, ...],
    max_px: int,
) -> bool:
    for candidate in components:
        if candidate["component_id"] == anchor["component_id"]:
            continue
        if not _contains_token(_combined_text(candidate), tokens):
            continue
        if _is_nearby(anchor["bounds"], candidate["bounds"], max_px):
            return True
    return False


def _has_nearby_image(anchor: dict, components: list[dict], max_px: int) -> bool:
    for candidate in components:
        class_name = candidate.get("class", "")
        if "ImageView" not in class_name and "ImageButton" not in class_name:
            continue
        if _area(candidate) <= 0:
            continue
        if _is_nearby(anchor["bounds"], candidate["bounds"], max_px):
            return True
    return False

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


def check_small_touch_target(components: list[dict], dpi: int = ASSUMED_DENSITY_DPI) -> list[dict]:
    """R04: flag clickable elements whose width or height in dp is below 48dp.

    Input: components - parsed component dicts (bounds are pixels); dpi - the
        screen density to convert px to dp with, normally read from
        components.json's device_info.dpi by check() and passed in here;
        falls back to the 160dpi baseline (TBD-03) if not supplied.
    Output: list of R04 violation dicts.
    """
    violations = []
    for component in components:
        if not component.get("clickable"):
            continue
        width_px, height_px = _bounds_wh(component["bounds"])
        if width_px <= 0 or height_px <= 0:
            continue  # zero/invalid bounds are R07's concern, not R04's
        width_dp = _px_to_dp(width_px, dpi=dpi)
        height_dp = _px_to_dp(height_px, dpi=dpi)
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
    """R05: flag input-field elements with empty hint, text, and content_desc.

    Input: components - parsed component dicts. Matches any class containing
        one of INPUT_CLASSES (EditText and common cross-platform equivalents),
        not just EditText. `hint` comes from the parser's `hint`/`android:hint`
        extraction.
    Output: list of R05 violation dicts.
    """
    violations = []
    for component in components:
        class_name = component.get("class", "")
        if not any(input_class in class_name for input_class in INPUT_CLASSES):
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


def _is_a11y_relevant(component: dict) -> bool:
    """True when a component would ever be exposed to a screen reader.

    Purely structural nodes (layout containers, spacers) that are neither
    interactive nor carry any text/content_desc are never announced by
    TalkBack regardless of their bounds, so a zero-size structural node
    isn't an accessibility defect the way a zero-size button is.
    """
    if component.get("clickable") or component.get("focusable"):
        return True
    return bool(component.get("text") or component.get("content_desc"))


def check_zero_size(components: list[dict]) -> list[dict]:
    """R07: flag elements whose bounds width or height is zero (or otherwise
    invalid), restricted to elements that are actually accessibility-relevant
    (clickable/focusable, or carrying text/content_desc) via
    _is_a11y_relevant. Plain layout scaffolding (ViewGroups, Space) that
    happens to measure zero is never exposed to a screen reader, so it isn't
    flagged even when its bounds are zero/invalid.

    Input: components - parsed component dicts.
    Output: list of R07 violation dicts.
    """
    violations = []
    for component in components:
        width_px, height_px = _bounds_wh(component["bounds"])
        if (width_px <= 0 or height_px <= 0) and _is_a11y_relevant(component):
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


def _is_ancestor(ancestor_id: str, component: dict, by_id: dict[str, dict]) -> bool:
    """True when ancestor_id is a strict ancestor of component in the parent_id tree.

    Walks parent_id links (not just the immediate parent), so a clickable
    RecyclerView/ListView row nested several containers deep inside a
    clickable scrollable list is still recognized as contained by it.
    """
    seen: set[str] = set()
    parent_id = component.get("parent_id", "")
    while parent_id and parent_id not in seen:
        if parent_id == ancestor_id:
            return True
        seen.add(parent_id)
        parent = by_id.get(parent_id)
        parent_id = parent.get("parent_id", "") if parent else ""
    return False


def check_layout_overlap(components: list[dict]) -> list[dict]:
    """R08: flag pairs of clickable elements whose bounds overlap by more than
    50% of the smaller element's area.

    Input: components - parsed component dicts. Restricted to clickable
        elements with a positive bounds area (via _area()), to avoid flagging
        expected container/child nesting and to guard zero-size/inverted
        rects out before any overlap math runs on them. Pairs where one
        element is an ancestor of the other (via _is_ancestor, walking the
        full parent_id chain, not just the immediate parent) are also
        skipped — a clickable scrollable container (e.g. a clickable
        ListView) fully containing its own clickable rows is expected
        Android structure, not an overlap defect.
    Output: list of R08 violation dicts, one per overlapping pair, anchored on
        the smaller element with related_component pointing at the larger one.
    """
    by_id = {component["component_id"]: component for component in components}
    clickable = [
        component
        for component in components
        if component.get("clickable") and _area(component) > 0
    ]
    violations = []
    for i, first in enumerate(clickable):
        area1 = _area(first)
        for second in clickable[i + 1:]:
            area2 = _area(second)
            overlap_area = _overlap_area(first["bounds"], second["bounds"])
            smaller_area = min(area1, area2)
            if smaller_area == 0:
                continue  # defensive: already filtered above, guards the comparison below too
            if overlap_area <= 0.5 * smaller_area:
                continue
            smaller, larger = (first, second) if area1 <= area2 else (second, first)
            if _is_ancestor(smaller["component_id"], larger, by_id) or _is_ancestor(
                larger["component_id"], smaller, by_id
            ):
                continue
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
    """R09: flag text components whose declared text/background colors give a
    contrast ratio below 4.5:1 (optional check, see G09).

    Input: components - parsed component dicts, using the parser's
        `text_color`/`background_color` fields (see
        src.parser._get_text_color/_get_background_color — normalized
        #RRGGBB/#AARRGGBB hex, or None if the source XML has no such
        attribute).
    Output: list of R09 violation dicts. Only fires when BOTH colors are
        present on a component; this is a pure field-extraction check, not a
        heuristic — neither UIAutomator dumps nor MASC dumps carry declared
        color attributes today (confirmed by inspecting every attribute and
        wrapper block either format emits), so this will report [] on the
        current datasets. It's written to key off attribute names
        (text-color/textColor/android:textColor and their background
        counterparts) rather than one exact literal string, so a dataset
        that does expose declared colors picks this up with no code change.
    """
    # TODO: split "large text" (>=18pt / >=14pt bold, 3:1 threshold) from
    # normal text (4.5:1) once a text-size signal exists — shares the same
    # gap as R28 (no declared sp size in either supported XML format either,
    # see check_font_scale_overflow).
    violations = []
    for component in components:
        text_color = component.get("text_color")
        background_color = component.get("background_color")
        if not text_color or not background_color:
            continue
        ratio = _wcag_contrast_ratio(text_color, background_color)
        if ratio is None or ratio >= CONTRAST_RATIO_THRESHOLD:
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


# --- R11-R12: media/state rules (Ayesha) -----------------------------------------

def check_color_only_info(components: list[dict]) -> list[dict]:
    """R11: flag checkable-state controls with no text/content_desc backup for
    their on/off state.

    What it detects: a CheckBox/Switch/ToggleButton/RadioButton (or similar
    compound-button widget) with empty text AND empty content_desc. On
    Android, these widgets convey their on/off state almost entirely through
    a fill/track color change (plus, at most, a small glyph) — with no text
    or content_desc, a screen reader user gets nothing at all to indicate
    which state the control is in. Per G11 (WCAG 1.4.1), color alone must
    never be the sole carrier of meaning.

    Why it matters: colorblind users (and anyone using a grayscale/high-
    contrast display mode) cannot perceive a color-only state at all — and
    here, screen reader users can't either, since there's no text fallback.

    Scope note: this covers the "no non-visual indicator exists at all" case,
    using fields this pipeline actually has (class, checked/selected, text,
    content_desc). It does NOT cover true before/after color-diffing (e.g. a
    form field's border flipping red/green with no icon or message on an
    otherwise-labeled field) — that still needs paired snapshots or
    cross-capture screenshot diffing, neither of which exists today; see
    TODO. Overlaps with R01 (missing label) when the control is also
    clickable — same pattern as R01/R02/R30's intentional overlap elsewhere
    in this file, since G11 is a narrower, state-specific angle on the same
    underlying "no accessible name" problem.

    Input: components - parsed component dicts.
    Output: list of R11 violation dicts.
    """
    # TODO(true color-diff R11): detecting a state CHANGE shown only via a
    # color delta on an otherwise-labeled element (e.g. a red/green form
    # border with no icon/message) needs either paired before/after
    # component snapshots or cross-capture screenshot diffing — neither
    # exists in this pipeline yet (see docs/r11_r12_design.md history).
    violations = []
    for component in components:
        class_name = component.get("class", "")
        if not any(marker in class_name for marker in STATE_WIDGET_CLASS_MARKERS):
            continue
        if component.get("text") or component.get("content_desc"):
            continue
        violations.append(
            _make_violation(
                rule_id="R11",
                issue="Color-only information",
                component=component,
                guideline="G11 — Information conveyed by color alone",
                severity="High",
                recommendation=(
                    "Add a content description stating the control's current state "
                    '(e.g. "Notifications, on") so it isn\'t conveyed by color/fill alone.'
                ),
            )
        )
    return violations


def check_missing_captions(components: list[dict]) -> list[dict]:
    """R12: flag VideoView/media player components with no caption toggle found nearby.

    What it detects: any video/media-playback widget (VideoView, MediaPlayer,
    or similar) present on screen with no caption/CC/subtitle control as a
    sibling (same parent_id) or within bounds-proximity, and no such token
    found anywhere else on screen either. Per G12 (WCAG 1.2.2), video with
    spoken audio must offer captions/subtitles.

    Why it matters: Deaf and hard-of-hearing users get no equivalent to the
    audio track if there's no caption/CC control — the video is effectively
    inaccessible to them regardless of how well everything else on the screen
    is labeled.

    Detection logic: the parser preserves `parent_id` for every component, so
    a caption/CC toggle sharing the video's immediate parent (a genuine
    sibling in the tree, not just a bounds-distance guess) is checked first,
    same pattern as _has_parent_sibling_label (R20). Bounds-proximity
    (_has_nearby_token) and a screen-wide fallback catch layouts where the
    toggle isn't a direct sibling. This is a heuristic, not a certainty — a
    resource_id/content_desc/text containing "caption"/"cc"/"subtitle" is
    assumed to mean a real caption control; see TRANSCRIPT_TOKENS.

    Input: components - parsed component dicts.
    Output: list of R12 violation dicts.
    """
    violations = []
    for component in components:
        if not _is_video_component(component):
            continue
        if _has_sibling_token(component, components, TRANSCRIPT_TOKENS):
            continue
        if _has_nearby_token(component, components, TRANSCRIPT_TOKENS, NEARBY_TRANSCRIPT_PX):
            continue
        if _screen_has_token(components, TRANSCRIPT_TOKENS):
            continue
        violations.append(
            _make_violation(
                rule_id="R12",
                issue="Missing captions",
                component=component,
                guideline="G12 — Missing captions",
                severity="High",
                recommendation="Add a caption/CC toggle control near the video player.",
            )
        )
    return violations


# --- R13-R20: extended rules (Ayesha lead block, Week 4) -----------------------

def check_audio_without_transcript(components: list[dict]) -> list[dict]:
    """R13: flag audio-only media widgets with no transcript/subtitle affordance nearby.

    Input: components - parsed component dicts.
    Output: list of R13 violation dicts.
    """
    has_video = any(_is_video_component(component) for component in components)
    violations = []
    for component in components:
        if not _is_audio_component(component, has_video=has_video):
            continue
        if _screen_has_token(components, TRANSCRIPT_TOKENS):
            continue
        if _has_nearby_token(component, components, TRANSCRIPT_TOKENS, NEARBY_TRANSCRIPT_PX):
            continue
        violations.append(
            _make_violation(
                rule_id="R13",
                issue="Audio-only media without transcript",
                component=component,
                guideline="G13 — Audio-only without transcript",
                severity="High",
                recommendation=(
                    "Provide a transcript link or on-screen text alternative for audio-only content."
                ),
            )
        )
    return violations


def check_audio_only_notification(components: list[dict]) -> list[dict]:
    """R14: flag notification-style text with no nearby visible icon/banner.

    Input: components - parsed component dicts.
    Output: list of R14 violation dicts.
    """
    violations = []
    for component in components:
        text_blob = _combined_text(component)
        class_name = component.get("class", "")
        is_notification = (
            _contains_token(text_blob, NOTIFICATION_TOKENS)
            or "Notification" in class_name
        )
        if not is_notification:
            continue
        if _has_nearby_image(component, components, NEARBY_NOTIFICATION_ICON_PX):
            continue
        violations.append(
            _make_violation(
                rule_id="R14",
                issue="Audio-only notification",
                component=component,
                guideline="G14 — Audio-only notification",
                severity="Medium",
                recommendation=(
                    "Pair notification text with a visible icon or banner, not sound alone."
                ),
            )
        )
    return violations


def check_bad_focus_order(components: list[dict]) -> list[dict]:
    """R15: flag when focusable traversal order disagrees with top-to-bottom layout.

    Uses document order in components[] as a proxy for focus traversal order.
    Input: components - parsed component dicts.
    Output: list of R15 violation dicts.
    """
    focusable = [
        component
        for component in components
        if component.get("focusable") and _area(component) > 0
    ]
    if len(focusable) < 2:
        return []

    document_ids = [
        component["component_id"]
        for component in sorted(
            focusable,
            key=lambda item: (item.get("focus_order", 0), item["component_id"]),
        )
    ]
    visual_ids = [
        component["component_id"]
        for component in sorted(
            focusable,
            key=lambda item: (item["bounds"][1], item["bounds"][0], item["component_id"]),
        )
    ]
    if document_ids == visual_ids:
        return []

    out_of_order_id = next(
        doc_id for doc_id, vis_id in zip(document_ids, visual_ids) if doc_id != vis_id
    )
    offender = next(component for component in focusable if component["component_id"] == out_of_order_id)
    expected = visual_ids[document_ids.index(out_of_order_id)]
    return [
        _make_violation(
            rule_id="R15",
            issue="Bad focus order",
            component=offender,
            guideline="G15 — Logical focus order",
            severity="Medium",
            recommendation=(
                "Reorder focusable elements so traversal follows the visual top-to-bottom layout."
            ),
            related_component=expected,
        )
    ]


def check_decorative_in_focus_tree(components: list[dict]) -> list[dict]:
    """R16: flag likely decorative elements that remain in the focus tree.

    Input: components - parsed component dicts.
    Output: list of R16 violation dicts.
    """
    violations = []
    for component in components:
        if not _is_decorative_focusable(component):
            continue
        violations.append(
            _make_violation(
                rule_id="R16",
                issue="Decorative element in focus tree",
                component=component,
                guideline="G16 — Decorative element in focus tree",
                severity="Low",
                recommendation=(
                    "Remove decorative elements from the focus order (android:focusable=false "
                    "and android:importantForAccessibility=no)."
                ),
            )
        )
    return violations


def check_insufficient_spacing(components: list[dict], dpi: int = ASSUMED_DENSITY_DPI) -> list[dict]:
    """R17: flag clickable pairs whose edge gap is below 8dp.

    Input: components - parsed component dicts; dpi - screen density for dp conversion.
    Output: list of R17 violation dicts.
    """
    clickable = [
        component
        for component in components
        if component.get("clickable") and _area(component) > 0
    ]
    violations = []
    for i, first in enumerate(clickable):
        for second in clickable[i + 1:]:
            gap_px = _edge_gap(first["bounds"], second["bounds"])
            if gap_px <= 0:
                continue
            gap_dp = _px_to_dp(gap_px, dpi=dpi)
            if gap_dp >= MIN_SPACING_DP:
                continue
            smaller, larger = (first, second) if _area(first) <= _area(second) else (second, first)
            violations.append(
                _make_violation(
                    rule_id="R17",
                    issue="Insufficient spacing",
                    component=smaller,
                    guideline="G17 — Insufficient spacing",
                    severity="Medium",
                    recommendation=(
                        f"Increase spacing between adjacent controls to at least {MIN_SPACING_DP}dp."
                    ),
                    related_component=larger["component_id"],
                )
            )
    return violations


def check_multi_gesture_only(components: list[dict]) -> list[dict]:
    """R18: flag features described as multi-touch/pinch-only interactions.

    Input: components - parsed component dicts.
    Output: list of R18 violation dicts.
    """
    violations = []
    for component in components:
        text_blob = _combined_text(component)
        if not (
            _contains_token(text_blob, GESTURE_TOKENS)
            or component.get("long_clickable")
        ):
            continue
        violations.append(
            _make_violation(
                rule_id="R18",
                issue="Multi-gesture only",
                component=component,
                guideline="G18 — Multi-finger gesture",
                severity="High",
                recommendation=(
                    "Provide a single-touch alternative for users who cannot perform multi-finger gestures."
                ),
            )
        )
    return violations


def check_destructive_without_confirmation(components: list[dict]) -> list[dict]:
    """R19: flag destructive actions when no confirmation dialog/text is present.

    Input: components - parsed component dicts.
    Output: list of R19 violation dicts.
    """
    has_dialog = any(component.get("is_dialog") for component in components) or any(
        any(marker in component.get("class", "") for marker in DIALOG_CLASS_MARKERS)
        for component in components
    )
    has_confirm_text = _screen_has_token(components, CONFIRM_TOKENS)
    if has_dialog or has_confirm_text:
        return []

    violations = []
    for component in components:
        if not component.get("clickable"):
            continue
        if not _contains_token(_combined_text(component), DESTRUCTIVE_TOKENS):
            continue
        violations.append(
            _make_violation(
                rule_id="R19",
                issue="No destructive confirmation",
                component=component,
                guideline="G19 — No destructive confirmation",
                severity="Medium",
                recommendation=(
                    "Show a confirmation dialog before irreversible actions such as delete or remove."
                ),
            )
        )
    return violations


def check_hint_only_label(components: list[dict]) -> list[dict]:
    """R20: flag input fields that rely on hint text without a visible paired label.

    Input: components - parsed component dicts.
    Output: list of R20 violation dicts.
    """
    violations = []
    for component in components:
        if not _is_input_field(component):
            continue
        if not component.get("hint"):
            continue
        if component.get("text") or component.get("content_desc") or component.get("label_for"):
            continue
        if _has_nearby_label(component, components):
            continue
        violations.append(
            _make_violation(
                rule_id="R20",
                issue="Hint-only label",
                component=component,
                guideline="G20 — Label disappears on focus",
                severity="Medium",
                recommendation=(
                    "Add a persistent visible label (TextView or labelFor) instead of hint-only labeling."
                ),
            )
        )
    return violations


# --- R21-R30: extended rules (Week 4/5, G21-G30) --------------------------------

def check_vague_error_message(components: list[dict]) -> list[dict]:
    """R21: flag error-bearing labels with no text and no content_desc.

    What it detects: a TextView-like component whose resource_id or class
    names it as an error/validation message (e.g. resource_id contains
    "error"), but which carries neither visible text nor a content_desc.

    Detection logic note: the source guideline (G21) also lists "text that
    doesn't identify a specific field" as vague, but that can't be checked
    mechanically here — there's no reliable static-XML signal linking an
    error label back to the field it describes. Following this file's own
    convention for "missing label" checks (R01's text=='' AND content_desc==''
    AND R05's hint=='' AND text=='' AND content_desc==''), this only flags the
    fully-empty case. A single-condition OR (flag when *either* text or
    content_desc is empty) would misfire on every correctly-implemented error
    TextView that only sets `text` and leaves content_desc unset, which is the
    normal, correct way to label a TextView (its visible text already serves
    as the accessible name) — so OR is deliberately not used here.

    Input: components - parsed component dicts.
    Output: list of R21 violation dicts.
    """
    violations = []
    for component in components:
        class_name = component.get("class", "")
        if not any(marker in class_name for marker in LABEL_CLASS_MARKERS):
            continue
        resource_id = component.get("resource_id", "").lower()
        if not (_contains_token(resource_id, ERROR_TOKENS) or _contains_token(class_name.lower(), ERROR_TOKENS)):
            continue
        if component.get("text") or component.get("content_desc"):
            continue
        violations.append(
            _make_violation(
                rule_id="R21",
                issue="Vague error message",
                component=component,
                guideline="G21 — Vague or missing error messages",
                severity="High",
                recommendation=(
                    "Set error text that names the specific field and how to fix it "
                    "(e.g. \"Email is required\"), rather than leaving it empty."
                ),
            )
        )
    return violations


def _is_password_toggle_control(component: dict) -> bool:
    class_name = component.get("class", "")
    if "ImageButton" not in class_name and "ImageView" not in class_name:
        return False
    return _contains_token(_combined_text(component), PASSWORD_TOGGLE_TOKENS)


def check_no_password_toggle(components: list[dict]) -> list[dict]:
    """R22: flag password EditText fields with no adjacent show/hide toggle.

    Input: components - parsed component dicts. Uses the `password` field
        (already extracted by the parser via the `password` attribute or an
        inputType containing "password") to find candidates, then looks for a
        nearby ImageButton/ImageView whose resource_id/content_desc names it
        as a show/hide/reveal/visibility toggle. Proximity is measured by
        edge gap (_edge_gap), not center distance (_is_nearby): a toggle icon
        sits right at the field's trailing edge, and a wide password field's
        center can be hundreds of px from that edge, so a center-distance
        check would miss it.
    Output: list of R22 violation dicts.
    """
    violations = []
    for component in components:
        if not component.get("password"):
            continue
        has_toggle = any(
            _is_password_toggle_control(candidate)
            and _edge_gap(component["bounds"], candidate["bounds"]) <= NEARBY_PASSWORD_TOGGLE_PX
            for candidate in components
            if candidate["component_id"] != component["component_id"]
        )
        if has_toggle:
            continue
        violations.append(
            _make_violation(
                rule_id="R22",
                issue="No password toggle",
                component=component,
                guideline="G22 — Password field lacks show/hide toggle",
                severity="Medium",
                recommendation=(
                    "Add a show/hide (eye icon) toggle next to the password field so "
                    "users can verify what they typed."
                ),
            )
        )
    return violations


def check_unlabeled_nav_control(components: list[dict]) -> list[dict]:
    """R23: flag nav-style ImageButtons (back/close/home/menu) with empty content_desc.

    Input: components - parsed component dicts.
    Output: list of R23 violation dicts.
    """
    violations = []
    for component in components:
        class_name = component.get("class", "")
        if "ImageButton" not in class_name:
            continue
        if not component.get("clickable"):
            continue
        resource_id = component.get("resource_id", "").lower()
        if not _contains_token(resource_id, NAV_RESOURCE_TOKENS):
            continue
        if component.get("content_desc"):
            continue
        violations.append(
            _make_violation(
                rule_id="R23",
                issue="Unlabeled navigation control",
                component=component,
                guideline="G23 — Navigation control not labeled",
                severity="High",
                recommendation=(
                    "Add android:contentDescription naming the action, e.g. Back, Close, "
                    "Home, or Menu."
                ),
            )
        )
    return violations


def _is_toolbar_candidate(component: dict, height_px: int) -> bool:
    """True when a TextView sits in the toolbar/title region of the screen.

    Prefers an explicit naming hint (resource_id/class containing "toolbar",
    "title", etc.); falls back to a pure position heuristic (top
    TOOLBAR_REGION_FRACTION of the screen) when height_px is known. If
    height_px is unavailable (0 — no device_info, see TBD-03-style fallback
    in src/parser.py's _extract_device_info), only the naming hint applies.
    """
    class_name = component.get("class", "")
    if "TextView" not in class_name:
        return False
    resource_id = component.get("resource_id", "").lower()
    if _contains_token(resource_id, TOOLBAR_TOKENS) or _contains_token(class_name.lower(), TOOLBAR_TOKENS):
        return True
    if height_px <= 0:
        return False
    top = component["bounds"][1]
    return 0 <= top <= height_px * TOOLBAR_REGION_FRACTION


def check_missing_screen_title(components: list[dict], height_px: int = 0) -> list[dict]:
    """R24: flag an empty topmost/toolbar-region TextView (missing screen title).

    Input: components - parsed component dicts; height_px - screen height in
        pixels (from device_info, via check()), used to define the toolbar
        region when no resource_id/class naming hint is present. When
        height_px is 0 (unknown), only naming-hint candidates are considered.
    Output: list of R24 violation dicts (at most one — the single topmost
        toolbar-region candidate). Returns [] when no toolbar-region TextView
        exists at all: per G24's own detection logic ("topmost TextView ...
        has empty text AND empty content-desc"), this only fires when such a
        TextView is present and empty, not when the region has no TextView.
    """
    candidates = [component for component in components if _is_toolbar_candidate(component, height_px)]
    if not candidates:
        return []
    topmost = min(candidates, key=lambda component: component["bounds"][1])
    if topmost.get("text") or topmost.get("content_desc"):
        return []
    return [
        _make_violation(
            rule_id="R24",
            issue="Missing screen title",
            component=topmost,
            guideline="G24 — Screen has no descriptive title",
            severity="Medium",
            recommendation="Give the screen a visible, descriptive title or heading.",
        )
    ]


def check_uncontrolled_animation(components: list[dict]) -> list[dict]:
    """R25: flag auto-playing animation widgets with no pause/stop control nearby.

    Input: components - parsed component dicts. Uses the parser's
        `media_type == "animation"` classification (class contains
        AnimationView/LottieAnimationView — see _infer_media_type in
        src/parser.py; unlike its video/audio branches, there's no
        resource_id-token fallback for animation), which is treated as the
        auto-play signal per G25's own wording ("AnimationView ... present").
    Output: list of R25 violation dicts.
    """
    violations = []
    for component in components:
        if component.get("media_type") != "animation":
            continue
        if _has_nearby_token(component, components, PAUSE_STOP_TOKENS, NEARBY_ANIMATION_CONTROL_PX):
            continue
        violations.append(
            _make_violation(
                rule_id="R25",
                issue="Uncontrolled animation",
                component=component,
                guideline="G25 — Uncontrolled auto-updating content",
                severity="Medium",
                recommendation=(
                    "Add a pause/stop control near the animation so users can halt "
                    "continuous motion."
                ),
            )
        )
    return violations


def _is_session_or_countdown_text(component: dict) -> bool:
    class_name = component.get("class", "")
    is_label_or_dialog = (
        any(marker in class_name for marker in LABEL_CLASS_MARKERS)
        or component.get("is_dialog")
        or any(marker in class_name for marker in DIALOG_CLASS_MARKERS)
    )
    if not is_label_or_dialog:
        return False
    return _contains_token(_combined_text(component), SESSION_TOKENS)


def _is_extend_or_ok_control(component: dict) -> bool:
    if not component.get("clickable") or not component.get("enabled", True):
        return False
    if OK_BUTTON_RE.match(component.get("text", "").strip()):
        return True
    return _contains_token(_combined_text(component), EXTEND_SESSION_TOKENS)


def check_no_timeout_warning(components: list[dict]) -> list[dict]:
    """R26: flag countdown/session-timeout messages with no enabled Extend/OK control.

    Input: components - parsed component dicts.
    Output: list of R26 violation dicts, one per countdown/session-timeout
        indicator component found, when no enabled Extend/OK control exists
        anywhere on screen.

    Note: this gates on the countdown/session component actually carrying
    session/timeout wording (SESSION_TOKENS), rather than flagging every
    Dialog-classed element that lacks an Extend/OK button — an unrelated
    dialog (e.g. R19's delete-confirmation dialog, which has Delete/Cancel
    buttons) has no reason to offer "Extend" and must not be flagged here.
    """
    indicators = [component for component in components if _is_session_or_countdown_text(component)]
    if not indicators:
        return []
    if any(_is_extend_or_ok_control(component) for component in components):
        return []
    return [
        _make_violation(
            rule_id="R26",
            issue="No timeout warning",
            component=component,
            guideline="G26 — Session timeout without warning",
            severity="Medium",
            recommendation=(
                "Warn the user at least 20 seconds before the session expires and offer "
                "an enabled Extend/OK control."
            ),
        )
        for component in indicators
    ]


def _is_jargon_heavy(text: str) -> bool:
    words = text.split()
    if len(words) <= COMPLEX_LABEL_MIN_WORDS:
        return False
    avg_word_length = sum(len(word) for word in words) / len(words)
    return avg_word_length > COMPLEX_LABEL_AVG_WORD_CHARS


def check_complex_label_language(components: list[dict]) -> list[dict]:
    """R27: flag content_desc/hint text that is long and jargon-heavy.

    Input: components - parsed component dicts.
    Output: list of R27 violation dicts. A component is flagged at most once
        even if both content_desc and hint qualify.
    """
    violations = []
    for component in components:
        for field in ("content_desc", "hint"):
            text = component.get(field, "")
            if not text or not _is_jargon_heavy(text):
                continue
            violations.append(
                _make_violation(
                    rule_id="R27",
                    issue="Complex label language",
                    component=component,
                    guideline="G27 — Complex or jargon-heavy labels",
                    severity="Low",
                    recommendation=(
                        "Rewrite using short, plain-language wording that a low-literacy "
                        "user can understand."
                    ),
                )
            )
            break
    return violations


def check_font_scale_overflow(components: list[dict], dpi: int = ASSUMED_DENSITY_DPI) -> list[dict]:
    """R28: flag TextViews whose declared text size wouldn't fit their bounds
    height at ~200% system font scale.

    What it detects: a TextView with a declared sp text size whose bounds
    height leaves no headroom for that size doubled (~200% system font
    scale, using a standard ~1.2x line-height factor). Per G28 (WCAG 1.4.4),
    text must remain readable and unclipped up to 200% system font size.

    Why it matters: low-vision and elderly users who increase their system
    font size to read comfortably will see this text clipped or truncated —
    it works at the XML's default scale but silently breaks at the scale
    those users actually rely on.

    Detection logic: reads the parser's `text_size_sp` field (see
    src.parser._get_text_size_sp), a pure field-extraction check, not a
    heuristic. Neither UIAutomator dumps nor MASC dumps carry a declared sp
    text size anywhere (confirmed by inspecting every attribute and wrapper
    block either format emits — MASC's per-node wrapper blocks only ever
    encode class hierarchy, content-desc, and two bounds candidates), so
    this reports [] on the current datasets. It's written to key off
    attribute names (text-size/textSize/android:textSize/font-size) rather
    than assuming one exact dataset's convention, so a dataset that does
    declare text size picks this up with no code change.

    Input: components - parsed component dicts; dpi - screen density for
        sp-to-px conversion (from device_info, via check()).
    Output: list of R28 violation dicts.
    """
    violations = []
    for component in components:
        text_size_sp = component.get("text_size_sp")
        if not text_size_sp or text_size_sp <= 0:
            continue
        _, height_px = _bounds_wh(component["bounds"])
        text_size_px = text_size_sp * (dpi / 160)
        required_height_px = text_size_px * LINE_HEIGHT_FACTOR * FONT_SCALE_TARGET
        if height_px >= required_height_px:
            continue
        violations.append(
            _make_violation(
                rule_id="R28",
                issue="Font scale overflow",
                component=component,
                guideline="G28 — Text does not scale with system font size",
                severity="Medium",
                recommendation=(
                    "Use wrap_content / auto-sizing instead of a fixed height so this "
                    "text doesn't clip when the system font size is increased."
                ),
            )
        )
    return violations

def check_all_caps_body_text(components: list[dict]) -> list[dict]:
    """R29: flag textAllCaps text longer than a short label (word count > 3).

    Input: components - parsed component dicts. Relies on the parser's
        `text_all_caps` field (from textAllCaps/text-all-caps/
        android:textAllCaps — see src/parser.py's _element_to_component).
        Note: like R28's sp-size gap, neither supported XML format's sampled
        files carry this attribute in practice, so this rule mechanically
        works but will rarely fire on current real MASC/UIAutomator data
        until a capture source that preserves textAllCaps exists; it does
        fire correctly whenever the attribute is present (see
        tests/fixtures/rules/r29_all_caps_fail.xml).
    Output: list of R29 violation dicts.
    """
    violations = []
    for component in components:
        if not component.get("text_all_caps"):
            continue
        text = component.get("text", "")
        if len(text.split()) <= ALL_CAPS_MIN_WORDS:
            continue
        violations.append(
            _make_violation(
                rule_id="R29",
                issue="All-caps body text",
                component=component,
                guideline="G29 — All-caps text used for body content",
                severity="Low",
                recommendation=(
                    "Remove textAllCaps styling from paragraph/instruction text; reserve "
                    "all-caps for short labels only."
                ),
            )
        )
    return violations


def check_icon_only_no_label(components: list[dict]) -> list[dict]:
    """R30: flag clickable icon-only elements with no text and no content_desc.

    Input: components - parsed component dicts. Class match is broader than
        R02's (adds "Icon", e.g. custom IconButton widgets), and — unlike the
        source guideline table's literal condition, which omits content_desc
        — this also requires content_desc=='' so it doesn't flag icon
        controls that are already properly labeled; G30's own description
        ("no text alternative") is about the content_desc being absent, and
        R02 already establishes this AND-both-empty convention for the same
        underlying "unlabeled icon control" case.

        Repeated instances of the same list/grid row template (same
        resource_id and same bounds width/height — the signature confirmed
        against real Rico/MASC ListView rows, where every row reuses one
        resource_id) are one design decision, not N independent bugs, so
        they're collapsed into a single violation via _dedupe_repeated. A
        component with no resource_id can't be safely correlated this way
        and is always kept as its own violation.
    Output: list of R30 violation dicts.
    """
    hits = []
    for component in components:
        if not component.get("clickable"):
            continue
        if component.get("text"):
            continue
        class_name = component.get("class", "")
        if not any(marker in class_name for marker in ICON_CLASS_MARKERS):
            continue
        if component.get("content_desc"):
            continue
        hits.append(component)

    violations = []
    for representative, count in _dedupe_repeated(hits):
        issue = "Icon-only control with no label"
        if count > 1:
            issue += f" ({count} repeated instances of the same row/grid template)"
        violations.append(
            _make_violation(
                rule_id="R30",
                issue=issue,
                component=representative,
                guideline="G30 — Icon-only button with no text alternative",
                severity="High",
                recommendation="Add android:contentDescription describing the icon's action.",
            )
        )
    return violations


# --- Entry point -----------------------------------------------------------------
#
# check_small_touch_target() needs a `dpi` argument (from device_info), so it's
# called out explicitly below rather than folded into a uniform RULES tuple.

def check(components_json: dict) -> dict:
    """Run all R01-R30 rules over a components.json document and build violations.json.

    Input: components_json - dict matching the components.json schema
        (schema_version, screen_id, image_path, xml_path, device_info,
        components[]).
    Output: dict matching the violations.json schema (schema_version,
        screen_id, image_path, xml_path, total_violations, violations[],
        component_count, hidden_component_count).
    """
    all_components = components_json.get("components", [])
    # Hidden components (visibility="gone" / visible-to-user="False" in the
    # source XML — see src.parser._is_visible) are excluded ONCE here,
    # before any rule runs, rather than inside individual rules. These are
    # never rendered, never focusable, and never reachable by a screen
    # reader — Android itself already excludes them from the accessibility
    # tree — so every rule downstream would otherwise be scoring elements no
    # real user could ever encounter. On a 500-screen sample this alone
    # accounted for ~81% of all flagged violations. `visible` defaults to
    # True (see _is_visible) for formats that don't carry this signal (real
    # UIAutomator dumps), so this is a no-op filter on that data.
    components = [component for component in all_components if component.get("visible", True)]
    # TBD-03 fallback: if device_info (or its dpi) is missing, assume the
    # 160dpi baseline rather than failing.
    device_info = components_json.get("device_info") or {}
    dpi = device_info.get("dpi", ASSUMED_DENSITY_DPI)
    # R24 fallback: height_px defaults to 0 (unknown) when device_info is
    # missing/incomplete; check_missing_screen_title() only uses naming-hint
    # candidates in that case (see _is_toolbar_candidate).
    height_px = device_info.get("height_px", 0)

    violations: list[dict] = []
    violations.extend(check_missing_label(components))
    violations.extend(check_image_button_without_description(components))
    violations.extend(check_duplicate_labels(components))
    violations.extend(check_small_touch_target(components, dpi=dpi))
    violations.extend(check_unlabeled_input(components))
    violations.extend(check_disabled_control(components))
    violations.extend(check_zero_size(components))
    violations.extend(check_layout_overlap(components))
    violations.extend(check_low_contrast(components))
    violations.extend(check_text_overflow(components))
    violations.extend(check_color_only_info(components))
    violations.extend(check_missing_captions(components))
    violations.extend(check_audio_without_transcript(components))
    violations.extend(check_audio_only_notification(components))
    violations.extend(check_bad_focus_order(components))
    violations.extend(check_decorative_in_focus_tree(components))
    violations.extend(check_insufficient_spacing(components, dpi=dpi))
    violations.extend(check_multi_gesture_only(components))
    violations.extend(check_destructive_without_confirmation(components))
    violations.extend(check_hint_only_label(components))
    violations.extend(check_vague_error_message(components))
    violations.extend(check_no_password_toggle(components))
    violations.extend(check_unlabeled_nav_control(components))
    violations.extend(check_missing_screen_title(components, height_px=height_px))
    violations.extend(check_uncontrolled_animation(components))
    violations.extend(check_no_timeout_warning(components))
    violations.extend(check_complex_label_language(components))
    violations.extend(check_font_scale_overflow(components, dpi=dpi))
    violations.extend(check_all_caps_body_text(components))
    violations.extend(check_icon_only_no_label(components))

    return {
        "schema_version": components_json.get("schema_version", SCHEMA_VERSION),
        "screen_id": components_json.get("screen_id", ""),
        "image_path": components_json.get("image_path", ""),
        "xml_path": components_json.get("xml_path", ""),
        "total_violations": len(violations),
        "violations": violations,
        # Diagnostic-only counts, not consumed by any rule: how many parsed
        # components existed before the visibility filter above, and how
        # many were excluded as hidden. "component_count" == len(components)
        # + "hidden_component_count" always holds.
        "component_count": len(all_components),
        "hidden_component_count": len(all_components) - len(components),
    }