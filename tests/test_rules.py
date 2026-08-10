"""Tests for src/rules.py: run each controlled fixture through the parser and rule checker.

Fixtures live in tests/fixtures/rules/ and map to TC-02 (R01), TC-03 (R04), and
TC-04 (R05) in docs/qa_test_plan.md, plus coverage for R02, R03, R06–R10,
R11–R20, a negative/regression case, and R21–R30 (Week 4/5).
"""

from __future__ import annotations

from pathlib import Path

import pytest
from src.rules import check_audio_without_transcript
from src.rules import check_audio_only_notification
from src.rules import check_bad_focus_order
from src.rules import check_decorative_in_focus_tree
from src.rules import check_insufficient_spacing
from src.rules import check_multi_gesture_only
from src.rules import check_destructive_without_confirmation
from src.rules import check_hint_only_label

from src.parser import load_xml_root, parse_xml_tree
from src.rules import (
    check,
    check_color_only_info,
    check_font_scale_overflow,
    check_low_contrast,
    check_missing_captions,
    check_small_touch_target,
)
from src.schema_documents import build_components_document

FIXTURES_DIR = Path(__file__).resolve().parent / "fixtures" / "rules"


def _violations_for(filename: str) -> dict:
    """Parse a fixture XML and run the rule checker on it.

    Input: filename - name of an XML file under tests/fixtures/rules/.
    Output: violations.json-shaped dict returned by src.rules.check().
    """
    xml_path = FIXTURES_DIR / filename
    components = parse_xml_tree(load_xml_root(xml_path))
    components_json = build_components_document(
        screen_id=xml_path.stem,
        image_path="",
        xml_path=str(xml_path),
        components=components,
    )
    return check(components_json)


@pytest.mark.parametrize(
    "filename,expected_rule",
    [
        ("r01_missing_label_fail.xml", "R01"),
        ("r02_image_button_fail.xml", "R02"),
        ("r03_duplicate_labels_fail.xml", "R03"),
        ("r04_small_target_fail.xml", "R04"),
        ("r05_unlabeled_input_fail.xml", "R05"),
        ("r06_disabled_control_fail.xml", "R06"),
        ("r07_zero_size_fail.xml", "R07"),
        ("r08_layout_overlap_fail.xml", "R08"),
        ("r09_low_contrast_fail.xml", "R09"),
        ("r10_text_overflow_fail.xml", "R10"),
        ("r12_missing_captions_fail.xml", "R12"),
        ("r13_audio_no_transcript_fail.xml", "R13"),
        ("r14_audio_only_notification_fail.xml", "R14"),
        ("r15_bad_focus_order_fail.xml", "R15"),
        ("r16_decorative_focus_fail.xml", "R16"),
        ("r17_insufficient_spacing_fail.xml", "R17"),
        ("r18_multi_gesture_fail.xml", "R18"),
        ("r19_destructive_no_confirm_fail.xml", "R19"),
        ("r20_hint_only_label_fail.xml", "R20"),
        ("r21_vague_error_fail.xml", "R21"),
        ("r22_no_password_toggle_fail.xml", "R22"),
        ("r23_unlabeled_nav_fail.xml", "R23"),
        ("r24_missing_title_fail.xml", "R24"),
        ("r25_uncontrolled_animation_fail.xml", "R25"),
        ("r26_no_timeout_warning_fail.xml", "R26"),
        ("r27_complex_label_fail.xml", "R27"),
        ("r29_all_caps_fail.xml", "R29"),
        ("r30_icon_only_fail.xml", "R30"),
        ("r11_color_only_fail.xml", "R11"),
    ],
)
def test_rule_triggers_on_fail_fixture(filename: str, expected_rule: str) -> None:
    """Each *_fail.xml fixture must produce a violation for its target rule."""
    result = _violations_for(filename)
    rule_ids = {violation["rule_id"] for violation in result["violations"]}
    assert expected_rule in rule_ids


@pytest.mark.parametrize(
    "filename,absent_rule",
    [
        ("r01_missing_label_pass.xml", "R01"),
        ("r02_image_button_pass.xml", "R02"),
        ("r07_zero_size_pass.xml", "R07"),
        ("r04_small_target_pass.xml", "R04"),
        ("r05_unlabeled_input_pass.xml", "R05"),
        ("r05_unlabeled_input_hint_pass.xml", "R05"),
        ("r09_low_contrast_pass.xml", "R09"),
        ("r10_text_overflow_pass.xml", "R10"),
        ("r12_missing_captions_pass.xml", "R12"),
        ("r13_audio_no_transcript_pass.xml", "R13"),
        ("r14_audio_only_notification_pass.xml", "R14"),
        ("r15_bad_focus_order_pass.xml", "R15"),
        ("r16_decorative_focus_pass.xml", "R16"),
        ("r17_insufficient_spacing_pass.xml", "R17"),
        ("r18_multi_gesture_pass.xml", "R18"),
        ("r19_destructive_no_confirm_pass.xml", "R19"),
        ("r20_hint_only_label_pass.xml", "R20"),
        ("r21_vague_error_pass.xml", "R21"),
        ("r22_no_password_toggle_pass.xml", "R22"),
        ("r23_unlabeled_nav_pass.xml", "R23"),
        ("r24_missing_title_pass.xml", "R24"),
        ("r25_uncontrolled_animation_pass.xml", "R25"),
        ("r26_no_timeout_warning_pass.xml", "R26"),
        ("r27_complex_label_pass.xml", "R27"),
        ("r29_all_caps_pass.xml", "R29"),
        ("r30_icon_only_pass.xml", "R30"),
        ("r11_color_only_pass.xml", "R11"),
    ],
)
def test_rule_does_not_trigger_on_pass_fixture(filename: str, absent_rule: str) -> None:
    """Each *_pass.xml fixture must NOT produce a violation for the rule it targets."""
    result = _violations_for(filename)
    rule_ids = {violation["rule_id"] for violation in result["violations"]}
    assert absent_rule not in rule_ids


def test_clean_fixture_has_zero_violations() -> None:
    """The regression fixture with no injected issues must produce zero violations."""
    result = _violations_for("clean_no_violations.xml")
    assert result["violations"] == []
    assert result["total_violations"] == 0


def test_check_output_matches_violations_json_shape() -> None:
    """check() output must carry every field required by violations.json."""
    result = _violations_for("r02_image_button_fail.xml")
    for key in ("schema_version", "screen_id", "image_path", "xml_path", "total_violations", "violations"):
        assert key in result
    assert result["total_violations"] == len(result["violations"])
    for violation in result["violations"]:
        for key in ("rule_id", "issue", "component_id", "class", "bounds", "guideline", "severity", "recommendation"):
            assert key in violation


def test_duplicate_labels_reference_related_component() -> None:
    """R03 violations must link the duplicate back to the first occurrence."""
    result = _violations_for("r03_duplicate_labels_fail.xml")
    duplicate = next(v for v in result["violations"] if v["rule_id"] == "R03")
    assert "related_component" in duplicate


def test_layout_overlap_references_related_component() -> None:
    """R08 violations must link the smaller element to the one it overlaps with."""
    result = _violations_for("r08_layout_overlap_fail.xml")
    overlap = next(v for v in result["violations"] if v["rule_id"] == "R08")
    assert "related_component" in overlap


def test_layout_overlap_ignores_zero_size_elements() -> None:
    """R08 must not crash or falsely flag a pair of zero-size (0-area) elements."""
    result = _violations_for("r08_zero_size_no_crash.xml")
    rule_ids = {violation["rule_id"] for violation in result["violations"]}
    assert "R08" not in rule_ids


def test_hint_only_label_fires_on_masc_text_hint_attribute() -> None:
    """R20 must fire end-to-end on MASC's real `text-hint` attribute, not
    just the UIAutomator-style `hint` attribute the original fixture used."""
    result = _violations_for("r20_hint_only_label_masc_fail.xml")
    rule_ids = {violation["rule_id"] for violation in result["violations"]}
    assert "R20" in rule_ids


def test_icon_only_dedupes_repeated_row_template() -> None:
    """R30 must collapse repeated instances of the same list-row icon
    template (same resource_id + same bounds size) into a single violation
    instead of one per row, while still counting the repeat in the issue text."""
    result = _violations_for("r30_icon_only_repeated_dedup.xml")
    r30 = [v for v in result["violations"] if v["rule_id"] == "R30"]
    assert len(r30) == 1
    assert "3" in r30[0]["issue"]


def test_layout_overlap_ignores_ancestor_descendant_pairs() -> None:
    """R08 must not flag a clickable scrollable container (e.g. ListView) against
    its own clickable row nested several levels below it — expected Android
    list/RecyclerView structure, not an overlap defect."""
    result = _violations_for("r08_ancestor_nesting_pass.xml")
    rule_ids = {violation["rule_id"] for violation in result["violations"]}
    assert "R08" not in rule_ids


def test_color_only_info_ignores_non_checkable_widgets() -> None:
    """R11 only targets checkable-state widgets (CheckBox/Switch/ToggleButton/
    RadioButton); an unlabeled EditText is R05's/R20's concern, not R11's."""
    components = [
        {
            "component_id": "c_001",
            "class": "android.widget.EditText",
            "text": "",
            "content_desc": "",
            "hint": "",
            "resource_id": "com.example.app:id/email",
            "clickable": True,
            "enabled": True,
            "focusable": True,
            "bounds": [0, 0, 400, 100],
        }
    ]
    assert check_color_only_info(components) == []


def test_low_contrast_returns_empty_without_declared_colors() -> None:
    """R09 only fires when the parser extracted BOTH text_color and
    background_color from the source XML; neither UIAutomator nor MASC
    dumps declare colors, so this must return [] with those fields absent."""
    components = [
        {
            "component_id": "c_001",
            "class": "android.widget.TextView",
            "text": "Hello",
            "content_desc": "",
            "hint": "",
            "resource_id": "com.example.app:id/label",
            "clickable": False,
            "enabled": True,
            "focusable": False,
            "bounds": [0, 0, 100, 30],
            "text_color": None,
            "background_color": None,
        }
    ]
    assert check_low_contrast(components) == []


def test_low_contrast_flags_low_contrast_declared_colors() -> None:
    """R09 must fire when declared text_color/background_color give a
    contrast ratio below 4.5:1 (two close shades of gray)."""
    component = {
        "component_id": "c_001",
        "class": "android.widget.TextView",
        "text": "Hello",
        "content_desc": "",
        "hint": "",
        "resource_id": "com.example.app:id/label",
        "clickable": False,
        "enabled": True,
        "focusable": False,
        "bounds": [0, 0, 100, 30],
        "text_color": "#AAAAAA",
        "background_color": "#B4B4B4",
    }
    violations = check_low_contrast([component])
    assert len(violations) == 1
    assert violations[0]["rule_id"] == "R09"


def test_low_contrast_ignores_high_contrast_declared_colors() -> None:
    """R09 must not fire for clearly high-contrast declared colors (black
    text on a white background, ratio far above 4.5:1)."""
    component = {
        "component_id": "c_001",
        "class": "android.widget.TextView",
        "text": "Hello",
        "content_desc": "",
        "hint": "",
        "resource_id": "com.example.app:id/label",
        "clickable": False,
        "enabled": True,
        "focusable": False,
        "bounds": [0, 0, 100, 30],
        "text_color": "#000000",
        "background_color": "#FFFFFF",
    }
    assert check_low_contrast([component]) == []


def test_font_scale_overflow_returns_empty_without_declared_text_size() -> None:
    """R28 only fires when the parser extracted a text_size_sp value from the
    source XML; neither UIAutomator nor MASC dumps declare one, so this must
    return [] with that field absent, even for cramped-looking bounds."""
    components = [
        {
            "component_id": "c_001",
            "class": "android.widget.TextView",
            "text": "Some fairly long paragraph of body text",
            "content_desc": "",
            "hint": "",
            "resource_id": "com.example.app:id/body_text",
            "clickable": False,
            "enabled": True,
            "focusable": False,
            "bounds": [0, 0, 400, 20],
            "text_size_sp": None,
        }
    ]
    assert check_font_scale_overflow(components) == []


def test_font_scale_overflow_flags_cramped_declared_text_size() -> None:
    """R28 must fire when the declared text_size_sp, doubled (~200% scale)
    with a standard line-height factor, wouldn't fit the bounds height.

    At the 160dpi baseline, 16sp needs ~16 * 1.2 * 2.0 = 38.4px; a 20px
    bounds height can't fit that.
    """
    component = {
        "component_id": "c_001",
        "class": "android.widget.TextView",
        "text": "Cramped text",
        "content_desc": "",
        "hint": "",
        "resource_id": "com.example.app:id/label",
        "clickable": False,
        "enabled": True,
        "focusable": False,
        "bounds": [0, 0, 200, 20],
        "text_size_sp": 16,
    }
    violations = check_font_scale_overflow([component], dpi=160)
    assert len(violations) == 1
    assert violations[0]["rule_id"] == "R28"


def test_font_scale_overflow_ignores_roomy_declared_text_size() -> None:
    """R28 must not fire when the bounds height comfortably fits the
    declared text size doubled."""
    component = {
        "component_id": "c_001",
        "class": "android.widget.TextView",
        "text": "Roomy text",
        "content_desc": "",
        "hint": "",
        "resource_id": "com.example.app:id/label",
        "clickable": False,
        "enabled": True,
        "focusable": False,
        "bounds": [0, 0, 200, 80],
        "text_size_sp": 16,
    }
    assert check_font_scale_overflow([component], dpi=160) == []


def test_font_scale_overflow_respects_dpi_parameter() -> None:
    """R28 must scale its sp-to-px conversion by whatever dpi is passed in,
    same convention as R04/check_small_touch_target."""
    component = {
        "component_id": "c_001",
        "class": "android.widget.TextView",
        "text": "Dpi-sensitive text",
        "content_desc": "",
        "hint": "",
        "resource_id": "com.example.app:id/label",
        "clickable": False,
        "enabled": True,
        "focusable": False,
        "bounds": [0, 0, 200, 40],
        "text_size_sp": 16,
    }
    # At 160dpi, 16sp needs ~38.4px — comfortably fits a 40px bounds height.
    assert check_font_scale_overflow([component], dpi=160) == []
    # At 320dpi (2x), the same 16sp needs ~76.8px — no longer fits.
    violations = check_font_scale_overflow([component], dpi=320)
    assert len(violations) == 1
    assert violations[0]["rule_id"] == "R28"


def test_missing_captions_uses_sibling_over_bounds_distance() -> None:
    """R12 must recognize a caption toggle sharing the video's parent_id (a
    genuine tree sibling) even when it's far outside NEARBY_TRANSCRIPT_PX in
    bounds-distance — proving the new sibling check adds real coverage
    bounds-proximity alone would miss."""
    components = [
        {
            "component_id": "c_001",
            "class": "android.widget.VideoView",
            "text": "",
            "content_desc": "",
            "hint": "",
            "resource_id": "com.example.app:id/video_player",
            "clickable": False,
            "enabled": True,
            "focusable": False,
            "bounds": [0, 0, 200, 200],
            "parent_id": "c_parent",
        },
        {
            "component_id": "c_002",
            "class": "android.widget.ImageButton",
            "text": "",
            "content_desc": "Toggle captions",
            "hint": "",
            "resource_id": "com.example.app:id/cc_toggle",
            "clickable": True,
            "enabled": True,
            "focusable": True,
            # Far away in bounds-distance (> NEARBY_TRANSCRIPT_PX=400 on both axes).
            "bounds": [900, 900, 950, 950],
            "parent_id": "c_parent",
        },
    ]
    assert check_missing_captions(components) == []


def test_r12_stub_returns_empty_list_for_non_media_components() -> None:
    """R12 (check_missing_captions) only matches VideoView/MediaPlayer classes;
    it must return [] when no such component is present."""
    components = [
        {
            "component_id": "c_001",
            "class": "android.widget.Button",
            "text": "Play",
            "content_desc": "",
            "hint": "",
            "resource_id": "com.example.app:id/play_button",
            "clickable": True,
            "enabled": True,
            "focusable": True,
            "bounds": [0, 0, 200, 100],
        }
    ]
    assert check_missing_captions(components) == []

def test_audio_without_transcript_ignores_video_components() -> None:
    """R13 must not flag a VideoView as 'audio-only' — a component with a
    picture track has a visual channel, so it isn't the audio-only case
    R13 is meant to catch. Without this guard, any video player without a
    transcript link would be wrongly flagged."""
    components = [
        {
            "component_id": "c_001",
            "class": "android.widget.VideoView",
            "text": "",
            "content_desc": "",
            "hint": "",
            "resource_id": "com.example.app:id/video_player",
            "clickable": False,
            "enabled": True,
            "focusable": False,
            "bounds": [0, 0, 200, 200],
        }
    ]
    assert check_audio_without_transcript(components) == []


def test_audio_only_notification_ignores_nearby_icon() -> None:
    """R14 must not flag notification-style text when a visible icon/banner
    sits nearby — the rule exists to catch sound-only alerts, not ones that
    are already paired with a visual cue."""
    components = [
        {
            "component_id": "c_001",
            "class": "android.widget.TextView",
            "text": "New message notification",
            "content_desc": "",
            "hint": "",
            "resource_id": "com.example.app:id/notif_text",
            "clickable": False,
            "enabled": True,
            "focusable": False,
            "bounds": [0, 0, 200, 40],
        },
        {
            "component_id": "c_002",
            "class": "android.widget.ImageView",
            "text": "",
            "content_desc": "notification icon",
            "hint": "",
            "resource_id": "com.example.app:id/notif_icon",
            "clickable": False,
            "enabled": True,
            "focusable": False,
            "bounds": [0, 40, 40, 80],
        },
    ]
    assert check_audio_only_notification(components) == []

def test_bad_focus_order_ignores_single_focusable() -> None:
    """R15 needs at least 2 focusable elements to compare order; with only
    one, there's nothing to be 'out of order' relative to."""
    components = [
        {
            "component_id": "c_001", "class": "android.widget.Button",
            "text": "OK", "content_desc": "", "hint": "",
            "resource_id": "com.example.app:id/ok", "clickable": True,
            "enabled": True, "focusable": True, "bounds": [0, 0, 100, 50],
        }
    ]
    assert check_bad_focus_order(components) == []


def test_decorative_in_focus_tree_ignores_non_focusable() -> None:
    """R16 only concerns elements actually in the focus tree; a non-focusable
    decorative image can't cause a focus-tree accessibility problem."""
    components = [
        {
            "component_id": "c_001", "class": "android.widget.ImageView",
            "text": "", "content_desc": "", "hint": "",
            "resource_id": "com.example.app:id/deco", "clickable": False,
            "enabled": True, "focusable": False, "bounds": [0, 0, 50, 50],
        }
    ]
    assert check_decorative_in_focus_tree(components) == []


def test_insufficient_spacing_ignores_well_spaced_targets() -> None:
    """R17 should not flag two clickable elements with generous spacing
    between them (well above the 8dp minimum)."""
    components = [
        {
            "component_id": "c_001", "class": "android.widget.Button",
            "text": "A", "content_desc": "", "hint": "",
            "resource_id": "com.example.app:id/a", "clickable": True,
            "enabled": True, "focusable": True, "bounds": [0, 0, 100, 100],
        },
        {
            "component_id": "c_002", "class": "android.widget.Button",
            "text": "B", "content_desc": "", "hint": "",
            "resource_id": "com.example.app:id/b", "clickable": True,
            "enabled": True, "focusable": True, "bounds": [500, 0, 600, 100],
        },
    ]
    assert check_insufficient_spacing(components) == []


def test_multi_gesture_only_ignores_normal_text() -> None:
    """R18 should not flag ordinary controls with no gesture-related
    language and no long-click behavior."""
    components = [
        {
            "component_id": "c_001", "class": "android.widget.Button",
            "text": "Submit", "content_desc": "", "hint": "",
            "resource_id": "com.example.app:id/submit", "clickable": True,
            "enabled": True, "focusable": True, "bounds": [0, 0, 100, 50],
            "long_clickable": False,
        }
    ]
    assert check_multi_gesture_only(components) == []


def test_destructive_without_confirmation_ignores_when_confirm_text_present() -> None:
    """R19 should not flag a destructive action if confirmation language is
    already present somewhere on screen."""
    components = [
        {
            "component_id": "c_001", "class": "android.widget.Button",
            "text": "Delete account", "content_desc": "", "hint": "",
            "resource_id": "com.example.app:id/delete", "clickable": True,
            "enabled": True, "focusable": True, "bounds": [0, 0, 100, 50],
        },
        {
            "component_id": "c_002", "class": "android.widget.TextView",
            "text": "Are you sure you want to continue?", "content_desc": "",
            "hint": "", "resource_id": "com.example.app:id/confirm_text",
            "clickable": False, "enabled": True, "focusable": False,
            "bounds": [0, 60, 200, 90],
        },
    ]
    assert check_destructive_without_confirmation(components) == []


def test_hint_only_label_ignores_field_with_content_desc() -> None:
    """R20 should not flag an input field that relies on hint text if it
    also has a real content_desc as a durable label."""
    components = [
        {
            "component_id": "c_001", "class": "android.widget.EditText",
            "text": "", "content_desc": "Email address", "hint": "Email",
            "resource_id": "com.example.app:id/email", "clickable": True,
            "enabled": True, "focusable": True, "bounds": [0, 0, 200, 50],
        }
    ]
    assert check_hint_only_label(components) == []
    
def test_check_handles_missing_image_path_gracefully() -> None:
    """check() must not crash when image_path points to a nonexistent file;
    R09 (check_low_contrast) in particular must gracefully return [] rather
    than trying to open a screenshot that isn't there."""
    components_json = build_components_document(
        screen_id="missing_image_test",
        image_path="data/screenshots/does_not_exist.jpg",
        xml_path="tests/fixtures/rules/does_not_matter.xml",
        components=[
            {
                "component_id": "c_001",
                "class": "android.widget.Button",
                "text": "Continue",
                "content_desc": "",
                "hint": "",
                "resource_id": "com.example.app:id/continue_button",
                "clickable": True,
                "enabled": True,
                "focusable": True,
                "bounds": [0, 0, 300, 120],
            }
        ],
    )
    result = check(components_json)
    rule_ids = {violation["rule_id"] for violation in result["violations"]}
    assert "R09" not in rule_ids
    assert result["total_violations"] == 0


def test_small_touch_target_respects_dpi_parameter() -> None:
    """R04 must scale its 48dp threshold by whatever dpi is passed in, not a fixed 160."""
    component = {
        "component_id": "c_001",
        "class": "android.widget.Button",
        "text": "OK",
        "content_desc": "",
        "hint": "",
        "resource_id": "com.example.app:id/btn_ok",
        "clickable": True,
        "enabled": True,
        "focusable": True,
        "bounds": [0, 0, 100, 100],
    }
    # At the 160dpi baseline, 100px == 100dp — comfortably above the 48dp minimum.
    assert check_small_touch_target([component], dpi=160) == []
    # At 420dpi, 100px == 100 * 160/420 =~ 38dp — below the 48dp minimum.
    violations = check_small_touch_target([component], dpi=420)
    assert len(violations) == 1
    assert violations[0]["rule_id"] == "R04"


def test_parser_device_info_falls_back_to_component_bounds() -> None:
    """Neither UIAutomator's nor MASC's <hierarchy> root ever carries a `bounds`
    attribute, so device_info.width_px/height_px used to stay 0 even though real
    screen content exists. build_screen_document() must fall back to the union
    of parsed components' bounds so R24 has a real screen height to work with."""
    from src.parser import build_screen_document

    xml_path = FIXTURES_DIR / "r24_missing_title_fail.xml"
    doc = build_screen_document(xml_path, FIXTURES_DIR, dataset_root=None)
    assert doc["device_info"]["width_px"] == 1080
    assert doc["device_info"]["height_px"] == 1920


def test_missing_screen_title_fires_through_check_with_position_heuristic() -> None:
    """R24 must also fire via check() using the position heuristic alone (no
    toolbar/title naming hint), once device_info.height_px is populated."""
    components = [
        {
            "component_id": "c_001",
            "class": "android.widget.FrameLayout",
            "text": "",
            "content_desc": "",
            "hint": "",
            "resource_id": "",
            "clickable": False,
            "enabled": True,
            "focusable": False,
            "bounds": [0, 0, 1080, 1920],
        },
        {
            "component_id": "c_002",
            "class": "android.widget.TextView",
            "text": "",
            "content_desc": "",
            "hint": "",
            "resource_id": "com.example.app:id/header_label",
            "clickable": False,
            "enabled": True,
            "focusable": False,
            "bounds": [40, 20, 600, 90],
        },
    ]
    components_json = build_components_document(
        screen_id="position_heuristic_test",
        image_path="",
        xml_path="",
        components=components,
        device_info={"dpi": 160, "width_px": 1080, "height_px": 1920},
    )
    result = check(components_json)
    rule_ids = {violation["rule_id"] for violation in result["violations"]}
    assert "R24" in rule_ids


def test_icon_only_no_label_does_not_flag_properly_labeled_icon() -> None:
    """R30 must not fire on a clickable icon-class element that already has a
    content_desc — only the fully-unlabeled case should be flagged."""
    from src.rules import check_icon_only_no_label

    component = {
        "component_id": "c_001",
        "class": "android.widget.ImageButton",
        "text": "",
        "content_desc": "Add to favorites",
        "hint": "",
        "resource_id": "com.example.app:id/btn_favorite",
        "clickable": True,
        "enabled": True,
        "focusable": True,
        "bounds": [0, 0, 100, 100],
    }
    assert check_icon_only_no_label([component]) == []


def test_check_filters_hidden_components_before_running_rules() -> None:
    """check() must exclude visible=False components before any rule runs —
    a clickable, unlabeled button that's hidden must not produce an R01
    violation, even though the identical visible button does."""
    hidden_button = {
        "component_id": "c_001",
        "class": "android.widget.Button",
        "text": "",
        "content_desc": "",
        "hint": "",
        "resource_id": "com.example.app:id/hidden_btn",
        "clickable": True,
        "enabled": True,
        "focusable": True,
        "bounds": [0, 0, 200, 100],
        "visible": False,
    }
    visible_button = {
        "component_id": "c_002",
        "class": "android.widget.Button",
        "text": "",
        "content_desc": "",
        "hint": "",
        "resource_id": "com.example.app:id/visible_btn",
        "clickable": True,
        "enabled": True,
        "focusable": True,
        "bounds": [300, 0, 500, 100],
        "visible": True,
    }
    components_json = build_components_document(
        screen_id="visibility_filter_test",
        image_path="",
        xml_path="",
        components=[hidden_button, visible_button],
    )
    result = check(components_json)
    r01_component_ids = {v["component_id"] for v in result["violations"] if v["rule_id"] == "R01"}
    assert r01_component_ids == {"c_002"}


def test_check_reports_component_and_hidden_counts() -> None:
    """check() must report component_count (total before filtering) and
    hidden_component_count (how many were excluded) as diagnostics."""
    components = [
        {
            "component_id": "c_001",
            "class": "android.widget.Button",
            "text": "Visible",
            "content_desc": "",
            "hint": "",
            "resource_id": "",
            "clickable": True,
            "enabled": True,
            "focusable": True,
            "bounds": [0, 0, 200, 100],
            "visible": True,
        },
        {
            "component_id": "c_002",
            "class": "android.widget.TextView",
            "text": "Hidden one",
            "content_desc": "",
            "hint": "",
            "resource_id": "",
            "clickable": False,
            "enabled": True,
            "focusable": False,
            "bounds": [0, 0, 0, 0],
            "visible": False,
        },
        {
            "component_id": "c_003",
            "class": "android.widget.TextView",
            "text": "Hidden two",
            "content_desc": "",
            "hint": "",
            "resource_id": "",
            "clickable": False,
            "enabled": True,
            "focusable": False,
            "bounds": [0, 0, 0, 0],
            "visible": False,
        },
    ]
    components_json = build_components_document(
        screen_id="diagnostic_count_test", image_path="", xml_path="", components=components
    )
    result = check(components_json)
    assert result["component_count"] == 3
    assert result["hidden_component_count"] == 2


def test_check_defaults_to_visible_when_field_absent() -> None:
    """Components without a `visible` key at all (e.g. real UIAutomator data,
    which never sets it) must be treated as visible, not filtered out."""
    component = {
        "component_id": "c_001",
        "class": "android.widget.Button",
        "text": "",
        "content_desc": "",
        "hint": "",
        "resource_id": "com.example.app:id/btn",
        "clickable": True,
        "enabled": True,
        "focusable": True,
        "bounds": [0, 0, 200, 100],
        # no "visible" key at all
    }
    components_json = build_components_document(
        screen_id="no_visible_field_test", image_path="", xml_path="", components=[component]
    )
    result = check(components_json)
    assert result["component_count"] == 1
    assert result["hidden_component_count"] == 0
    assert any(v["rule_id"] == "R01" for v in result["violations"])
