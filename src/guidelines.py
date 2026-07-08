"""G01-G30 accessibility guidelines and the canonical R01-R30 -> guideline_ids mapping.

Transcribed from docs/accessibility_guidelines_report.md (sections 2-4), which is
the canonical source also referenced by docs/json_schemas.md. Kept as a plain
Python module (not re-parsed from the markdown) so the explainer layer has a
stable, importable mapping that doesn't depend on doc formatting.
"""

from __future__ import annotations

# --- G01-G30: guideline_id -> {description, user_group, wcag} -----------------

GUIDELINES: dict[str, dict[str, str]] = {
    "G01": {"description": "Every interactive element must have a visible or programmatic label for screen readers.", "user_group": "Blind / Low Vision", "wcag": "4.1.2"},
    "G02": {"description": "ImageButton and clickable ImageView must have a content description.", "user_group": "Blind", "wcag": "1.1.1"},
    "G03": {"description": "No two interactive elements should share identical text/content-desc unless same action.", "user_group": "Blind / Cognitive", "wcag": "4.1.2"},
    "G04": {"description": "Tappable elements must meet minimum size (48x48 dp).", "user_group": "Motor / Elderly", "wcag": "2.5.5"},
    "G05": {"description": "Every EditText must have a programmatic label (hint, labelFor, or content-desc).", "user_group": "Blind / Cognitive", "wcag": "1.3.1"},
    "G06": {"description": "Critical controls must not be disabled without explanation or alternative.", "user_group": "All Users", "wcag": "2.1.1"},
    "G07": {"description": "Zero-area or invalid bounds must be removed from focus tree.", "user_group": "All / Blind", "wcag": "1.3.1"},
    "G08": {"description": "Elements must not overlap in ways that hide content or break focus order.", "user_group": "All / Blind", "wcag": "1.3.2"},
    "G09": {"description": "Text and UI components must meet minimum contrast ratios.", "user_group": "Low Vision / Color Blind", "wcag": "1.4.3"},
    "G10": {"description": "Text bounds must fit full content without clipping.", "user_group": "Low Vision / Cognitive", "wcag": "1.4.4"},
    "G11": {"description": "Color must not be the only indicator of state or meaning.", "user_group": "Color Blind", "wcag": "1.4.1"},
    "G12": {"description": "Video with spoken audio must provide captions/subtitles.", "user_group": "Deaf / Hard of Hearing", "wcag": "1.2.2"},
    "G13": {"description": "Audio-only content must have a text transcript in the UI.", "user_group": "Deaf / Hard of Hearing", "wcag": "1.2.1"},
    "G14": {"description": "Alerts must include visual indicators, not sound alone.", "user_group": "Deaf / Hard of Hearing", "wcag": "1.3.3"},
    "G15": {"description": "Focus order must follow natural top-to-bottom reading sequence.", "user_group": "Blind / Motor", "wcag": "1.3.2 / 2.4.3"},
    "G16": {"description": "Decorative elements must be excluded from accessibility focus.", "user_group": "Blind", "wcag": "1.3.1"},
    "G17": {"description": "Adjacent targets need >=8 dp spacing to prevent mis-taps.", "user_group": "Motor Impaired", "wcag": "2.5.5"},
    "G18": {"description": "All functionality must work with a single pointer.", "user_group": "Motor / Single Hand", "wcag": "2.1.1"},
    "G19": {"description": "Irreversible actions must require confirmation.", "user_group": "Motor / Cognitive", "wcag": "3.3.4"},
    "G20": {"description": "Labels must remain visible while typing.", "user_group": "Cognitive / Memory", "wcag": "3.3.2"},
    "G21": {"description": "Errors must identify the field and how to fix it.", "user_group": "Cognitive / Blind", "wcag": "3.3.1 / 3.3.3"},
    "G22": {"description": "Password fields should offer reveal/hide control.", "user_group": "Cognitive / Motor", "wcag": "3.3.1"},
    "G23": {"description": "Back, home, close, menu buttons must have descriptive labels.", "user_group": "Blind", "wcag": "2.4.6"},
    "G24": {"description": "Every screen needs a visible title or heading.", "user_group": "Blind / Cognitive", "wcag": "2.4.2"},
    "G25": {"description": "Animation/auto-update must be pausable/stoppable.", "user_group": "Cognitive / Epilepsy / ADHD", "wcag": "2.2.2"},
    "G26": {"description": "Timed sessions must warn >=20s before expiry with extend option.", "user_group": "Cognitive / Slow Readers", "wcag": "2.2.1"},
    "G27": {"description": "Use plain, simple language in labels and hints.", "user_group": "Cognitive / Low Literacy", "wcag": "3.1.5"},
    "G28": {"description": "Text must remain readable at 200% system font size.", "user_group": "Low Vision / Elderly", "wcag": "1.4.4"},
    "G29": {"description": "All-caps must not be used for paragraph or instruction text.", "user_group": "Cognitive / Dyslexia", "wcag": "3.1.5"},
    "G30": {"description": "Icon-only buttons must have content-desc describing the action.", "user_group": "Blind / Low Literacy", "wcag": "1.1.1"},
}

# --- R01-R30: rule_id -> [guideline_id, ...] -----------------------------------
# Canonical mapping, aligned with docs/accessibility_guidelines_report.md
# section 3/4 and docs/json_schemas.md's "Guidelines (G01-G30) -> rules mapping".

RULE_GUIDELINES: dict[str, list[str]] = {
    "R01": ["G01", "G02", "G30"],
    "R02": ["G02", "G30"],
    "R03": ["G03"],
    "R04": ["G04", "G17"],
    "R05": ["G05", "G20"],
    "R06": ["G06", "G26"],
    "R07": ["G07", "G25"],
    "R08": ["G08", "G15"],
    "R09": ["G09", "G11"],
    "R10": ["G10", "G28", "G29"],
    "R11": ["G11"],
    "R12": ["G12"],
    "R13": ["G13"],
    "R14": ["G14"],
    "R15": ["G15", "G16"],
    "R16": ["G16"],
    "R17": ["G17"],
    "R18": ["G18"],
    "R19": ["G19"],
    "R20": ["G05", "G20"],
    "R21": ["G21"],
    "R22": ["G22"],
    "R23": ["G01", "G23"],
    "R24": ["G24"],
    "R25": ["G25"],
    "R26": ["G26"],
    "R27": ["G27"],
    "R28": ["G10", "G28"],
    "R29": ["G29"],
    "R30": ["G01", "G30"],
}

# --- R01-R30: rule_id -> short plain-language detection logic ------------------
# Condensed from docs/accessibility_guidelines_report.md section 3, "Detection
# logic" column. Given to the LLM as context, not shown verbatim to end users.

RULE_DETECTION_LOGIC: dict[str, str] = {
    "R01": "Clickable element has empty text AND empty content-desc.",
    "R02": "ImageButton or clickable ImageView has empty content-desc.",
    "R03": "Two or more clickable elements share identical text or content-desc.",
    "R04": "Clickable element's width or height is below 48dp.",
    "R05": "EditText (or input-like widget) has empty hint AND empty text AND empty content-desc.",
    "R06": "Clickable element is disabled with no explanation text nearby.",
    "R07": "Element's bounds have zero or invalid width/height.",
    "R08": "Two clickable elements overlap by more than 50% of the smaller element's area.",
    "R09": "Declared text/background color contrast ratio is below 4.5:1.",
    "R10": "TextView's text length is disproportionate to its bounds area (likely to clip/overflow).",
    "R11": "A checkable-state widget (CheckBox/Switch/etc.) has no text or content-desc backing its on/off state.",
    "R12": "A video component has no caption/CC toggle nearby or elsewhere on screen.",
    "R13": "An audio-only component has no transcript/subtitle affordance nearby.",
    "R14": "Notification-style text/element has no nearby visible icon or banner.",
    "R15": "Focusable element traversal order disagrees with top-to-bottom visual layout.",
    "R16": "A likely-decorative element remains focusable/in the accessibility focus tree.",
    "R17": "Gap between two clickable elements is below 8dp.",
    "R18": "A feature is described as requiring a multi-touch/pinch gesture with no single-touch alternative.",
    "R19": "A destructive-action control (delete/remove/etc.) has no confirmation dialog or text nearby.",
    "R20": "An input field relies on hint text only, with no persistent visible paired label.",
    "R21": "An error-labeled TextView has empty text AND empty content-desc.",
    "R22": "A password EditText has no adjacent show/hide toggle control.",
    "R23": "A nav-style ImageButton (back/close/home/menu) has empty content-desc.",
    "R24": "The topmost toolbar/title-region TextView has empty text AND empty content-desc.",
    "R25": "An auto-playing animation widget has no pause/stop control nearby.",
    "R26": "A countdown/session-timeout message has no enabled Extend/OK control anywhere on screen.",
    "R27": "content-desc or hint text is long and jargon-heavy (many words, long average word length).",
    "R28": "A TextView's declared text size would not fit its bounds height at ~200% system font scale.",
    "R29": "textAllCaps text is longer than a short label (more than 3 words).",
    "R30": "A clickable icon-only element has empty text AND empty content-desc.",
}


def guideline_ids_for_rule(rule_id: str) -> list[str]:
    """Look up the guideline_ids a rule implements.

    Input: rule_id - e.g. "R01".
    Output: list of guideline_id strings (e.g. ["G01", "G02", "G30"]), or [] if
        rule_id is not in the canonical mapping.
    """
    return RULE_GUIDELINES.get(rule_id, [])


def guideline_text(guideline_id: str) -> dict[str, str] | None:
    """Look up a guideline's description/user_group/wcag.

    Input: guideline_id - e.g. "G01".
    Output: dict with description/user_group/wcag, or None if unknown.
    """
    return GUIDELINES.get(guideline_id)
