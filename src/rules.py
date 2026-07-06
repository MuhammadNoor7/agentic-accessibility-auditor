"""Stage 2 rule checker: evaluates parsed UI components against accessibility rules R01-R20.

Consumes a components.json-shaped dict (see docs/json_schemas.md) and produces a
violations.json-shaped dict validated by docs/schemas/auditor_schema.json.
"""

from __future__ import annotations

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
        elements with a positive bounds area (via _area()), to avoid flagging
        expected container/child nesting and to guard zero-size/inverted
        rects out before any overlap math runs on them.
    Output: list of R08 violation dicts, one per overlapping pair, anchored on
        the smaller element with related_component pointing at the larger one.
    """
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


# --- R11-R12: media/state rules (Ayesha) -----------------------------------------

def check_color_only_info(components: list[dict]) -> list[dict]:
    """R11: flag state changes/meaning conveyed by color alone, with no icon or text.

    What it detects: interactive or status-bearing elements (e.g. a toggle,
    checkbox, form field, or status chip) whose only indicator of state
    (on/off, valid/invalid, selected/unselected) is a change in color, with no
    accompanying icon, text label, or shape change. Per G11 (WCAG 1.4.1),
    color alone must never be the sole carrier of meaning.

    Why it matters: colorblind users (and anyone using a grayscale/high-
    contrast display mode) cannot perceive a color-only state change at all —
    a red/green "invalid/valid" field with no icon or message is invisible to
    them, so they can't tell the form failed validation.

    Detection logic when implemented: a single static UIAutomator XML snapshot
    has no notion of "before/after a state change" — this needs either (a) two
    component snapshots of the same screen (before/after a state-changing
    interaction) diffed against each other by resource_id, so only the color-
    coded delta is inspected for an accompanying text/content_desc/icon-class
    change, or (b) screenshot pixel analysis (similar in spirit to R09) to spot
    same-shape/same-position elements that differ only in color across two
    captures. Neither input is available to this rule checker today.

    Input: components - parsed component dicts.
    Output: list of R11 violation dicts. Currently always [] — see TODO.
    """
    # TODO(R11 implementation plan):
    #   1. Extend components.json to optionally carry paired before/after
    #      component snapshots (or a `state` field) keyed by resource_id.
    #   2. For each pair where bounds/class/resource_id match but a color-
    #      coded style differs, check whether text/content_desc/class also
    #      changed; if not, flag R11.
    #   3. Until that data exists, this stays a documented no-op stub.
    violations: list[dict] = []
    return violations


def check_missing_captions(components: list[dict]) -> list[dict]:
    """R12: flag VideoView/media player components with no caption toggle found nearby.

    What it detects: any video/media-playback widget (VideoView, MediaPlayer,
    or similar) present on screen. Per G12 (WCAG 1.2.2), video with spoken
    audio must offer captions/subtitles.

    Why it matters: Deaf and hard-of-hearing users get no equivalent to the
    audio track if there's no caption/CC control — the video is effectively
    inaccessible to them regardless of how well everything else on the screen
    is labeled.

    Detection logic when implemented: components.json is currently a flat
    list with no parent/sibling/adjacency information, so "is there a caption
    toggle near this video" can't be answered precisely yet. Today this stub
    conservatively flags every VideoView/MediaPlayer component it finds
    (a coarse approximation that will over-flag videos that do have a caption
    toggle elsewhere on screen). Once the parser preserves tree adjacency (or
    at minimum simple bounds-proximity), this should instead only flag a video
    when no sibling component within a reasonable distance has a resource_id/
    content_desc suggesting "caption"/"cc"/"subtitle".

    Input: components - parsed component dicts.
    Output: list of R12 violation dicts.
    """
    # TODO(R12 implementation plan):
    #   1. Preserve XML tree adjacency (parent/sibling relationships, or at
    #      least bounds-proximity) in components.json so nearby elements can
    #      be inspected instead of guessed at.
    #   2. Before flagging, search siblings/nearby components for a
    #      resource_id/content_desc/text containing "caption"/"cc"/"subtitle".
    #   3. Only flag if no such control is found — replacing today's
    #      unconditional flag-every-media-player behavior below.
    violations = []
    for component in components:
        if not _is_video_component(component):
            continue
        if _screen_has_token(components, TRANSCRIPT_TOKENS):
            continue
        if _has_nearby_token(component, components, TRANSCRIPT_TOKENS, NEARBY_TRANSCRIPT_PX):
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


# --- Entry point -----------------------------------------------------------------
#
# check_small_touch_target() needs a `dpi` argument (from device_info), so it's
# called out explicitly below rather than folded into a uniform RULES tuple.

def check(components_json: dict) -> dict:
    """Run all R01-R20 rules over a components.json document and build violations.json.

    Input: components_json - dict matching the components.json schema
        (schema_version, screen_id, image_path, xml_path, device_info,
        components[]).
    Output: dict matching the violations.json schema (schema_version,
        screen_id, image_path, xml_path, total_violations, violations[]).
    """
    components = components_json.get("components", [])
    # TBD-03 fallback: if device_info (or its dpi) is missing, assume the
    # 160dpi baseline rather than failing.
    device_info = components_json.get("device_info") or {}
    dpi = device_info.get("dpi", ASSUMED_DENSITY_DPI)

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

    return {
        "schema_version": components_json.get("schema_version", SCHEMA_VERSION),
        "screen_id": components_json.get("screen_id", ""),
        "image_path": components_json.get("image_path", ""),
        "xml_path": components_json.get("xml_path", ""),
        "total_violations": len(violations),
        "violations": violations,
    }