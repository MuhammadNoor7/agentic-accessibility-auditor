from __future__ import annotations

from src.schema_documents import SCHEMA_VERSION

GUIDELINES = {
    "R01": "G01 — Missing accessible label",
    "R02": "G02 — Image button without description",
    "R05": "G05 — Unlabeled input field",
    "R06": "G06 — Disabled control conflict",
    "R07": "G07 — Invisible or zero-size component",
    "R08": "G08 — Layout overlap detected",
    "R10": "G10 — Potential text overflow or truncation",
}

RULE_META = {
    "R01": {
        "issue": "Missing accessible label",
        "severity": "High",
        "recommendation": "Add visible text or android:contentDescription for interactive elements.",
    },
    "R02": {
        "issue": "Image button without description",
        "severity": "High",
        "recommendation": "Add android:contentDescription with the action name, such as Back.",
    },
    "R05": {
        "issue": "Unlabeled input field",
        "severity": "High",
        "recommendation": "Add android:hint or a programmatic label linked via labelFor.",
    },
    "R06": {
        "issue": "Disabled control conflict",
        "severity": "Low",
        "recommendation": "If a component is disabled, set clickable and focusable to false to prevent screen reader confusion.",
    },
    "R07": {
        "issue": "Zero-size element",
        "severity": "Medium",
        "recommendation": "Ensure the component has non-zero width and height when visible.",
    },
    "R08": {
        "issue": "Layout overlap detected",
        "severity": "Medium",
        "recommendation": "Adjust layout constraints to prevent interactive or text components from overlapping bounds.",
    },
    "R10": {
        "issue": "Potential text overflow or truncation",
        "severity": "Medium",
        "recommendation": "Ensure bounding box width can accommodate the text length or set appropriate wrap behaviors.",
    },
}

IMAGE_CLASSES = {
    "android.widget.ImageButton",
    "android.widget.ImageView",
}
INPUT_CLASSES = {
    "android.widget.EditText",
    "android.widget.AutoCompleteTextView",
}


def _has_label(component: dict) -> bool:
    return bool(component.get("text") or component.get("content_desc"))


def _bounds_area(bounds: list[int]) -> int:
    left, top, right, bottom = bounds
    return max(0, right - left) * max(0, bottom - top)


def _check_overlap(b1: list[int], b2: list[int]) -> bool:
    # Returns True if two bounding boxes intersect
    return not (b1[2] <= b2[0] or b1[0] >= b2[2] or b1[3] <= b2[1] or b1[1] >= b2[3])


def _make_violation(rule_id: str, component: dict) -> dict:
    meta = RULE_META[rule_id]
    return {
        "rule_id": rule_id,
        "issue": meta["issue"],
        "component_id": component["component_id"],
        "class": component["class"],
        "bounds": component["bounds"],
        "guideline": GUIDELINES[rule_id],
        "severity": meta["severity"],
        "recommendation": meta["recommendation"],
    }


def check_component_rules(component: dict) -> list[dict]:
    violations: list[dict] = []
    bounds = component.get("bounds", [0, 0, 0, 0])
    class_name = component.get("class", "")
    clickable = component.get("clickable", False)
    focusable = component.get("focusable", False)
    enabled = component.get("enabled", True)
    text = component.get("text", "")

    # R07: Zero-size element
    if _bounds_area(bounds) == 0:
        violations.append(_make_violation("R07", component))

    # R01: Missing Label for active elements
    if clickable and enabled and not _has_label(component):
        violations.append(_make_violation("R01", component))

    # R02: Image button description missing
    if class_name in IMAGE_CLASSES and clickable and not _has_label(component):
        violations.append(_make_violation("R02", component))

    # R05: Unlabeled inputs
    if class_name in INPUT_CLASSES and not _has_label(component):
        violations.append(_make_violation("R05", component))

    # R06: Disabled component configuration conflict
    if not enabled and (clickable or focusable):
        violations.append(_make_violation("R06", component))

    # R10: Basic heuristic for text truncation/overflow based on size limits
    if text and _bounds_area(bounds) > 0:
        width = bounds[2] - bounds[0]
        # Common mobile baseline: if text has substantial characters but width is extremely narrow
        if len(text) > 15 and width < 120:
            violations.append(_make_violation("R10", component))

    return violations


def check_screen(screen_document: dict) -> dict:
    violations: list[dict] = []
    components = screen_document.get("components", [])
    
    # 1. Run component-level tests (R01, R02, ... , R06, R07, R10)
    for component in components:
        violations.extend(check_component_rules(component))

    # 2. Run screen-level layout tests (R08 - Layout Overlap)
    for i in range(len(components)):
        for j in range(i + 1, len(components)):
            c1, c2 = components[i], components[j]
            b1, b2 = c1.get("bounds", [0,0,0,0]), c2.get("bounds", [0,0,0,0])
            
            # Skip empty components
            if _bounds_area(b1) == 0 or _bounds_area(b2) == 0:
                continue
                
            # If both are interactive and overlap significantly, flag layout collision
            if (c1.get("clickable") or c2.get("clickable")) and _check_overlap(b1, b2):
                # Avoid duplicate flags for the same structural node pairing
                violations.append({
                    "rule_id": "R08",
                    "issue": RULE_META["R08"]["issue"],
                    "component_id": f"{c1['component_id']}<->{c2['component_id']}",
                    "class": f"{c1['class']} & {c2['class']}",
                    "bounds": b1,
                    "guideline": GUIDELINES["R08"],
                    "severity": RULE_META["R08"]["severity"],
                    "recommendation": f"Review overlap between {c1['component_id']} and {c2['component_id']}. " + RULE_META["R08"]["recommendation"],
                })

    return {
        "schema_version": SCHEMA_VERSION,
        "screen_id": screen_document["screen_id"],
        "image_path": screen_document["image_path"],
        "xml_path": screen_document["xml_path"],
        "total_violations": len(violations),
        "violations": violations,
    }