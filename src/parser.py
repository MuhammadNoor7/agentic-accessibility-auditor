from __future__ import annotations

import json
import re
from pathlib import Path

from lxml import etree

from src.schema_documents import SCHEMA_VERSION, build_components_document

REPO_ROOT = Path(__file__).resolve().parents[1]
DEFAULT_OUTPUT_ROOT = REPO_ROOT / "data" / "parsed"
DEFAULT_CONTAINER_DATASET_ROOT = Path("/app/data/data-masc")
GENERIC_DATASET_ROOT = REPO_ROOT / "data"

DATASET_CANDIDATES = [
    REPO_ROOT / "data" / "data-masc",
    REPO_ROOT / "data" / "data-rico-holdout",
    GENERIC_DATASET_ROOT,
    DEFAULT_CONTAINER_DATASET_ROOT,
]

UIAUTOMATOR_BOUNDS_RE = re.compile(r"\[(\d+),(\d+)\]\[(\d+),(\d+)\]")
SPACE_BOUNDS_RE = re.compile(r"^(\d+)\s+(\d+)\s+(\d+)\s+(\d+)$")

SKIP_TAGS = {"hierarchy", "wrapper"}

# TBD-03 baseline density, used when the XML root carries no density metadata.
DEFAULT_DENSITY_DPI = 160


def resolve_dataset_root(dataset_root: Path | None = None) -> Path | None:
    """Resolve an explicit dataset_root, or auto-detect MASC/Rico/generic/container
    layout by probing for an xml/ subfolder. None if nothing matches."""
    if dataset_root is not None:
        path = Path(dataset_root)
        if not path.is_absolute():
            path = (REPO_ROOT / path).resolve()
        return path if path.exists() else None
    for candidate in (
        REPO_ROOT / "data" / "data-masc",
        REPO_ROOT / "data" / "data-rico-holdout",
        DEFAULT_CONTAINER_DATASET_ROOT,
    ):
        if (candidate / "xml").exists():
            return candidate
    if (GENERIC_DATASET_ROOT / "xml").is_dir():
        return GENERIC_DATASET_ROOT
    return None


def resolve_parsed_root(dataset_root: Path | None = None) -> Path:
    """Return the parsed/ output folder for a dataset root, or the default output root if none resolves."""
    resolved = resolve_dataset_root(dataset_root)
    if resolved is not None:
        if resolved == GENERIC_DATASET_ROOT:
            return resolved / "parsed"
        return resolved / "parsed"
    return DEFAULT_OUTPUT_ROOT


def infer_dataset_root_for_xml(xml_path: Path) -> Path | None:
    """Infer which known dataset (MASC/Rico) an XML file belongs to, from its path."""
    resolved_xml = xml_path.resolve()
    for candidate in DATASET_CANDIDATES:
        if candidate == DEFAULT_CONTAINER_DATASET_ROOT:
            continue
        xml_root = (candidate / "xml").resolve()
        if not xml_root.is_dir():
            continue
        try:
            resolved_xml.relative_to(xml_root)
            return candidate
        except ValueError:
            continue
    return None


def resolve_paths(
    xml_root: Path | None = None,
    output_root: Path | None = None,
    dataset_root: Path | None = None,
) -> tuple[Path, Path, Path | None]:
    """Fill in any unset xml_root/output_root from dataset_root auto-detection.
    Returns (xml_root, output_root, resolved_dataset_root)."""
    resolved_dataset = resolve_dataset_root(dataset_root)
    if xml_root is None:
        if resolved_dataset is not None:
            xml_root = resolved_dataset / "xml"
        else:
            xml_root = REPO_ROOT / "data" / "xml"

    if output_root is None:
        output_root = resolve_parsed_root(resolved_dataset)

    return Path(xml_root), Path(output_root), resolved_dataset


def load_xml_root(xml_path: Path) -> etree._Element:
    """Load XML, stripping null bytes that break parsers (e.g. chat/49879.xml)."""
    raw = xml_path.read_bytes().replace(b"\x00", b"")
    return etree.fromstring(raw)


def _read_xml_root(xml_path: Path) -> etree._Element:
    """Alias for load_xml_root (internal call sites)."""
    return load_xml_root(xml_path)


def _parse_bool(value: str | None, default: bool = False) -> bool:
    """Parse an XML attribute string ("true"/"1"/"yes") into a bool."""
    if value is None:
        return default
    return value.strip().lower() in {"true", "1", "yes"}


def _normalize_string(value: str | None) -> str:
    """Strip null bytes and collapse whitespace in an XML attribute value."""
    if value is None:
        return ""
    return " ".join(str(value).replace("\x00", "").split())


def _parse_uiautomator_bounds(bounds: str | None) -> list[int] | None:
    """Parse UIAutomator's "[l,t][r,b]" bounds format into [l, t, r, b]."""
    if not bounds:
        return None
    match = UIAUTOMATOR_BOUNDS_RE.search(bounds)
    if not match:
        return None
    return [int(match.group(1)), int(match.group(2)), int(match.group(3)), int(match.group(4))]


def _parse_space_bounds(bounds: str | None) -> list[int] | None:
    """Parse Rico's space-separated "l t r b" bounds format into [l, t, r, b]."""
    if not bounds:
        return None
    match = SPACE_BOUNDS_RE.match(bounds.strip())
    if not match:
        return None
    return [int(match.group(1)), int(match.group(2)), int(match.group(3)), int(match.group(4))]


def _parse_bounds_attr(raw: str | None) -> list[int] | None:
    """Parse bounds in either UIAutomator or Rico format, whichever matches."""
    return _parse_uiautomator_bounds(raw) or _parse_space_bounds(raw)


def _parse_masc_bounds(node: etree._Element) -> list[int] | None:
    """Pick a node's bounds from its candidate `<wrapper>` blocks.

    A MASC widget node typically carries exactly two 4-number wrapper
    candidates: an earlier one in container-relative ("local") coordinates,
    and a later one in absolute screen coordinates. The later one is what
    every position-dependent rule needs (R04 touch target, R08 overlap, R17
    spacing, R24 title region, ...), and it is valid 100% of the time for
    visible elements (verified against an 80-file MASC sample). It is only
    unreliable for `visibility="gone"` elements (~30% invalid there,
    typically a negative-width rect) — almost certainly because whatever
    walks the parent chain to compute "absolute" position breaks down
    through a collapsed/never-actually-measured ancestor. Blindly preferring
    the earlier ("local") candidate instead would fix gone elements only
    partially (still ~10% invalid there) while breaking visible elements'
    real screen position — so this prefers the last candidate and only
    falls back to an earlier one when the last is an inverted rect
    (right < left or bottom < top).
    """
    candidates: list[list[int]] = []
    for wrapper in node.findall("wrapper"):
        values: list[int] = []
        for value_node in wrapper:
            if value_node.tag != "node":
                continue
            raw = value_node.get("value")
            if raw is None or raw in ("None", ""):
                values = []
                break
            try:
                values.append(int(float(raw)))
            except ValueError:
                values = []
                break
        if len(values) == 4:
            candidates.append(values)

    if not candidates:
        return None
    for bounds in reversed(candidates):
        left, top, right, bottom = bounds
        if right >= left and bottom >= top:
            return bounds
    # Every candidate was an inverted rect — return the last one anyway so
    # callers still get a value; R07 (zero/invalid-size) already exists
    # downstream to flag it, and (once visibility filtering is applied in
    # check()) a gone element reaching this fallback won't reach the rules
    # at all.
    return candidates[-1]


def _get_text(elem: etree._Element) -> str:
    """Extract an element's visible text from the direct attribute or a MASC wrapper block."""
    direct = _normalize_string(elem.get("text"))
    if direct:
        return direct
    for wrapper in elem.findall("wrapper"):
        values = [_normalize_string(child.get("value")) for child in wrapper.findall("node")]
        if len(values) == 1 and values[0] and values[0] not in ("None",):
            return values[0]
    return ""


def _get_content_desc(elem: etree._Element) -> str:
    """Extract an element's accessibility content description, from the direct attribute or a MASC wrapper block."""
    direct = _normalize_string(elem.get("content-desc") or elem.get("content_desc"))
    if direct:
        return direct
    for wrapper in elem.findall("wrapper"):
        for child in wrapper.findall("node"):
            raw = child.get("value")
            if raw and raw not in ("None", "") and not raw.replace(".", "", 1).isdigit():
                if "android." not in raw and "java." not in raw:
                    return _normalize_string(raw)
    return ""


def _is_visible(elem: etree._Element) -> bool:
    """Whether Android itself would ever actually render this element.

    Input: elem - the source XML element.
    Output: False when `visibility="gone"` or `visible-to-user="False"` (both
        MASC attributes — confirmed present on every MASC widget node in a
        20-file sample, 1,539 occurrences of each, always paired). Neither
        attribute exists in real UIAutomator dumps (they don't capture a
        "gone" concept the same way), so this defaults to True when both are
        absent — an element the parser has no reason to believe is hidden.
    """
    if elem.get("visibility") == "gone":
        return False
    if elem.get("visible-to-user") == "False":
        return False
    return True


def _get_hint(elem: etree._Element) -> str:
    """Extract an input field's hint text, if present.

    Input: elem - the source XML element.
    Output: normalized hint string from the `hint`/`android:hint`/`text-hint`
        attribute, or "" if none is present. `text-hint` is MASC's actual
        attribute name (confirmed against real data-masc XML — `hint` and
        `android:hint` never appear there at all), so without it every MASC
        EditText's hint was silently dropped and R20 (hint-only label) could
        never fire on real MASC screens.
    """
    return _normalize_string(elem.get("hint") or elem.get("android:hint") or elem.get("text-hint"))


def _get_first_attr(elem: etree._Element, *names: str) -> str:
    """Return the first present XML attribute value from a list of aliases."""
    for name in names:
        value = elem.get(name)
        if value is not None and str(value).strip():
            return _normalize_string(value)
    return ""


def _get_input_type(elem: etree._Element) -> str:
    """Extract an EditText's declared input-type attribute, if present."""
    return _get_first_attr(elem, "input-type", "inputType", "android:inputType")


def _is_password_input(elem: etree._Element, input_type: str) -> bool:
    """True when the password attribute is set or input_type names a password variant."""
    if _parse_bool(elem.get("password")):
        return True
    lowered = input_type.lower()
    return "password" in lowered or "textpassword" in lowered.replace(" ", "")


def _get_important_for_accessibility(elem: etree._Element) -> str:
    """Extract the element's importantForAccessibility attribute, lowercased."""
    return _get_first_attr(
        elem,
        "important-for-accessibility",
        "importantForAccessibility",
        "android:importantForAccessibility",
    ).lower()


def _get_label_for(elem: etree._Element) -> str:
    """Extract the resource-id an element's labelFor attribute points at, if present."""
    return _get_first_attr(elem, "label-for", "labelFor", "android:labelFor")


def _get_text_size_sp(elem: etree._Element) -> float | None:
    """Extract a declared text size in sp, if the source XML carries one.

    Input: elem - the source XML element.
    Output: the numeric sp value (unit suffix like "sp"/"px"/"dp" stripped),
        or None if no such attribute is present. Neither UIAutomator dumps
        nor MASC dumps carry this today (confirmed by inspecting every
        wrapper block MASC emits) — this exists so a dataset that *does*
        expose it (e.g. a custom instrumentation dump) is picked up
        automatically, used by R09/R28.
    """
    raw = _get_first_attr(elem, "text-size", "textSize", "android:textSize", "font-size", "fontSize")
    if not raw:
        return None
    match = re.match(r"^(-?\d+(?:\.\d+)?)", raw.strip())
    if not match:
        return None
    try:
        return float(match.group(1))
    except ValueError:
        return None


def _get_color_attr(elem: etree._Element, *names: str) -> str | None:
    """Extract a declared color attribute as a normalized #RRGGBB/#AARRGGBB hex string.

    Input: elem - the source XML element; names - attribute name aliases to
        try, in order.
    Output: the hex string as-is (uppercased, with leading '#'), or None if
        no such attribute is present or it isn't recognizably hex. Used by
        R09 to compute a real WCAG contrast ratio when a dataset provides
        declared colors (neither UIAutomator nor MASC dumps do today).
    """
    raw = _get_first_attr(elem, *names)
    if not raw:
        return None
    candidate = raw.strip().upper()
    if re.fullmatch(r"#[0-9A-F]{6}", candidate) or re.fullmatch(r"#[0-9A-F]{8}", candidate):
        return candidate
    return None


def _get_text_color(elem: etree._Element) -> str | None:
    """Extract a declared text color, if the source XML carries one (used by R09)."""
    return _get_color_attr(elem, "text-color", "textColor", "android:textColor")


def _get_background_color(elem: etree._Element) -> str | None:
    """Extract a declared background color, if the source XML carries one (used by R09)."""
    return _get_color_attr(
        elem, "background-color", "backgroundColor", "android:background", "background"
    )


def _infer_media_type(class_name: str, resource_id: str) -> str:
    """Classify media-bearing widgets for R12/R13/R25 rule mapping."""
    if any(marker in class_name for marker in ("VideoView", "ExoPlayer", "StyledPlayerView")):
        return "video"
    if any(
        marker in class_name
        for marker in ("AudioView", "SoundRecorder", "VoiceRecorder", "MediaRecorder", "MediaPlayer")
    ):
        return "audio"
    if any(marker in class_name for marker in ("AnimationView", "LottieAnimationView")):
        return "animation"
    resource_lower = resource_id.lower()
    if any(token in resource_lower for token in ("videoview", "video_player", "player_view")):
        return "video"
    if any(token in resource_lower for token in ("audio", "podcast", "voice_memo", "sound_recorder")):
        return "audio"
    return ""


def _is_dialog_class(class_name: str) -> bool:
    """True when class_name matches one of the known dialog widget classes."""
    return any(
        marker in class_name
        for marker in ("Dialog", "AlertDialog", "BottomSheetDialog", "DialogTitle")
    )


def _tag_to_class(tag: str) -> str:
    """Map a Rico-style XML tag name (e.g. "TextView") to its fully-qualified
    Android class name (e.g. "android.widget.TextView")."""
    if tag in SKIP_TAGS or tag == "node":
        return ""
    if tag == "PhoneWindow_DecorView":
        return "com.android.internal.policy.PhoneWindow$DecorView"
    if tag.startswith(("android.", "com.", "java.")):
        return tag
    if "EditText" in tag:
        return "android.widget.EditText"
    if "TextView" in tag or tag in {"DialogTitle"}:
        return "android.widget.TextView"
    if tag in {"ImageButton", "ActionMenuItemView"} or "ImageButton" in tag:
        return "android.widget.ImageButton"
    if "ImageView" in tag:
        return "android.widget.ImageView"
    if tag.startswith("View"):
        return f"android.view.{tag.replace('Compat', '')}"
    if tag[0].isupper():
        return f"android.widget.{tag}"
    return ""


def _infer_class(elem: etree._Element) -> str:
    """Determine an element's Android class name from its class attribute, or
    fall back to mapping its raw XML tag via _tag_to_class."""
    for attr in ("class", "className", "class-name"):
        value = _normalize_string(elem.get(attr))
        if value:
            return value
    if elem.tag == "node":
        return ""
    return _tag_to_class(elem.tag)


def _extract_bounds(elem: etree._Element) -> list[int] | None:
    """Extract an element's bounds from its bounds attribute, or fall back to MASC wrapper blocks."""
    bounds = _parse_bounds_attr(elem.get("bounds"))
    if bounds is not None:
        return bounds
    return _parse_masc_bounds(elem)


def _element_to_component(
    elem: etree._Element,
    component_index: int,
    *,
    parent_component_id: str | None = None,
) -> dict | None:
    """Build one components.json entry (R13-R20 extended fields included) from
    an XML element, or None if it's a non-widget/skip-tag node."""
    if elem.tag in SKIP_TAGS:
        return None

    class_name = _infer_class(elem)
    if not class_name:
        return None

    bounds = _extract_bounds(elem)
    is_uiautomator_node = elem.tag == "node" or bool(
        elem.get("class") or elem.get("className") or elem.get("class-name")
    )

    if bounds is None:
        if is_uiautomator_node:
            bounds = [0, 0, 0, 0]
        else:
            return None

    resource_id = _normalize_string(elem.get("resource-id") or elem.get("resource_id"))
    input_type = _get_input_type(elem)

    return {
        "component_id": f"c_{component_index:03d}",
        "class": class_name,
        "text": _get_text(elem),
        "content_desc": _get_content_desc(elem),
        "hint": _get_hint(elem),
        "resource_id": resource_id,
        "clickable": _parse_bool(elem.get("clickable")),
        "enabled": _parse_bool(elem.get("enabled"), default=True),
        "focusable": _parse_bool(elem.get("focusable")),
        "bounds": bounds,
        "focus_order": component_index,
        "parent_id": parent_component_id or "",
        "long_clickable": _parse_bool(elem.get("long-clickable") or elem.get("longClickable")),
        "scrollable": _parse_bool(elem.get("scrollable")),
        "selected": _parse_bool(elem.get("selected")),
        "checked": _parse_bool(elem.get("checked")),
        "password": _is_password_input(elem, input_type),
        "text_all_caps": _parse_bool(
            elem.get("textAllCaps") or elem.get("text-all-caps") or elem.get("android:textAllCaps")
        ),
        "input_type": input_type,
        "important_for_accessibility": _get_important_for_accessibility(elem),
        "media_type": _infer_media_type(class_name, resource_id),
        "is_dialog": _is_dialog_class(class_name),
        "label_for": _get_label_for(elem),
        "text_size_sp": _get_text_size_sp(elem),
        "text_color": _get_text_color(elem),
        "background_color": _get_background_color(elem),
        "visible": _is_visible(elem),
    }


def _walk_xml_tree(
    elem: etree._Element,
    components: list[dict],
    component_index: int,
    parent_component_id: str | None,
) -> int:
    """Depth-first walk that preserves parent links and document order."""
    component = _element_to_component(
        elem,
        component_index,
        parent_component_id=parent_component_id,
    )
    current_parent_id = parent_component_id
    if component is not None:
        components.append(component)
        current_parent_id = component["component_id"]
        component_index += 1

    for child in elem:
        if child.tag == "wrapper":
            # MASC nests real widgets inside <wrapper> blocks; descend without
            # emitting a component for the wrapper itself.
            component_index = _walk_xml_tree(
                child,
                components,
                component_index,
                current_parent_id,
            )
            continue
        if child.tag in SKIP_TAGS:
            continue
        component_index = _walk_xml_tree(
            child,
            components,
            component_index,
            current_parent_id,
        )
    return component_index


def parse_xml_tree(root: etree._Element) -> list[dict]:
    """Hybrid parser: UIAutomator, MASC, Rico, and generic layout XML in one pass."""
    components: list[dict] = []
    _walk_xml_tree(root, components, 1, None)
    for index, component in enumerate(components, start=1):
        component["focus_order"] = index
    return components


def parse_ui_xml(xml_path: str | Path) -> list[dict]:
    """Parse any supported Android UI XML file into component dicts."""
    return parse_xml_tree(load_xml_root(Path(xml_path)))


def infer_image_path(xml_path: str | Path) -> str:
    """Guess screenshot path for MASC, Rico, or generic upload layouts."""
    path = Path(xml_path).resolve()
    dataset_root = infer_dataset_root_for_xml(path)
    if dataset_root is not None:
        return _screenshot_path(path, dataset_root)

    stem = path.stem
    category = path.parent.name if path.parent.name != "xml" else ""
    for ext in (".jpg", ".jpeg", ".png"):
        candidates = [
            path.parent / f"{stem}{ext}",
            path.parent.parent / "screenshots" / category / f"{stem}{ext}" if category else None,
            path.parent.parent / "screenshots" / f"{stem}{ext}",
            REPO_ROOT / "data" / "screenshots" / category / f"{stem}{ext}" if category else None,
            REPO_ROOT / "data" / "screenshots" / f"{stem}{ext}",
        ]
        for candidate in candidates:
            if candidate is not None and candidate.is_file():
                return _relative_dataset_path(candidate)
    fallback = path.parent.parent / "screenshots" / f"{stem}.jpg"
    if category:
        fallback = path.parent.parent / "screenshots" / category / f"{stem}.jpg"
    return _relative_dataset_path(fallback)


def _build_screen_id(xml_path: Path, xml_root: Path) -> str:
    """Derive a screen_id from an XML file's category subfolder + filename stem."""
    relative_parent = xml_path.parent.name
    stem = xml_path.stem
    if relative_parent and relative_parent != xml_root.name:
        return f"{relative_parent}_{stem}"
    return stem


def _relative_dataset_path(path: Path) -> str:
    """Return path as a POSIX-style string relative to the repo root, or absolute if outside it."""
    try:
        return path.resolve().relative_to(REPO_ROOT).as_posix()
    except ValueError:
        return path.resolve().as_posix()


def _find_screenshot_file(xml_path: Path, dataset_root: Path) -> Path | None:
    """Locate the screenshot matching an XML file under dataset_root/screenshots/, by mirrored path or flat filename."""
    screenshots_root = dataset_root / "screenshots"
    relative_xml = xml_path.resolve().relative_to((dataset_root / "xml").resolve())
    for ext in (".jpg", ".jpeg", ".png"):
        candidate = screenshots_root / relative_xml.with_suffix(ext)
        if candidate.is_file():
            return candidate
    flat = screenshots_root / f"{xml_path.stem}.jpg"
    if flat.is_file():
        return flat
    return None


def _screenshot_path(xml_path: Path, dataset_root: Path | None) -> str:
    """Resolve the repo-relative screenshot path for an XML file within a dataset."""
    xml_path = xml_path.resolve()
    if dataset_root is None:
        return infer_image_path(xml_path)

    screenshot = _find_screenshot_file(xml_path, dataset_root)
    if screenshot is not None:
        return _relative_dataset_path(screenshot)

    relative_xml = xml_path.relative_to((dataset_root / "xml").resolve())
    fallback = dataset_root / "screenshots" / relative_xml.with_suffix(".jpg")
    return _relative_dataset_path(fallback)


def _xml_relative_path(xml_path: Path, dataset_root: Path | None) -> str:
    """Return the XML file's path relative to the repo root (or dataset_root's convention)."""
    xml_path = xml_path.resolve()
    if dataset_root is None:
        try:
            return xml_path.relative_to(REPO_ROOT).as_posix()
        except ValueError:
            return xml_path.as_posix()
    return _relative_dataset_path(xml_path)


def _parsed_output_path(xml_path: Path, output_dir: Path, dataset_root: Path | None) -> Path:
    """Compute (and create) the output components.json path for an XML file, mirroring its category subfolder."""
    xml_path = xml_path.resolve()
    if dataset_root is not None and (dataset_root / "xml").is_dir():
        try:
            category_dir = output_dir / xml_path.relative_to((dataset_root / "xml").resolve()).parent
        except ValueError:
            category_dir = output_dir
    else:
        category_dir = output_dir / xml_path.parent.name if xml_path.parent.name != "xml" else output_dir
    category_dir.mkdir(parents=True, exist_ok=True)
    return category_dir / f"{xml_path.stem}_components.json"


def _extract_device_info(root: etree._Element, components: list[dict] | None = None) -> dict:
    """Extract screen density and dimensions from the XML root element's attributes.

    Input: root - the top-level parsed XML element (e.g. <hierarchy>); components -
        already-parsed component dicts for this screen, used as a fallback for
        width/height when the root element itself carries no bounds (see below).
    Output: {"dpi": int, "width_px": int, "height_px": int}. Falls back to
        DEFAULT_DENSITY_DPI when the XML carries no density metadata, which is
        true for standard UIAutomator dumps (TBD-03).

    Width/height fallback: neither UIAutomator's <hierarchy> root nor MASC's
    <hierarchy> root ever carries a `bounds` attribute directly (MASC puts the
    real screen extent on a descendant DecorView's `wrapper` block instead), so
    root.get("bounds") is always None in practice and width_px/height_px used
    to silently stay 0. Since R24 (missing screen title) needs a real screen
    height to define a "toolbar/title region", this falls back to the union of
    all parsed components' bounds (the furthest right/bottom edge seen), which
    in practice equals the root container's full-screen bounds.
    """
    dpi_raw = root.get("density") or root.get("android:density")
    try:
        dpi = int(float(dpi_raw)) if dpi_raw else DEFAULT_DENSITY_DPI
    except ValueError:
        dpi = DEFAULT_DENSITY_DPI

    width_px = height_px = 0
    root_bounds = _parse_bounds_attr(root.get("bounds"))
    if root_bounds is not None:
        left, top, right, bottom = root_bounds
        width_px = max(0, right - left)
        height_px = max(0, bottom - top)
    elif components:
        width_px = max((component["bounds"][2] for component in components), default=0)
        height_px = max((component["bounds"][3] for component in components), default=0)

    return {"dpi": dpi, "width_px": width_px, "height_px": height_px}


def build_screen_document(
    xml_path: Path,
    xml_root_dir: Path,
    dataset_root: Path | None,
) -> dict:
    """Parse one XML file into a full components.json document (screen_id, image_path, components, device_info)."""
    xml_path = xml_path.resolve()
    xml_root_dir = xml_root_dir.resolve()
    screen_id = _build_screen_id(xml_path, xml_root_dir)
    tree_root = _read_xml_root(xml_path)
    components = parse_xml_tree(tree_root)
    return build_components_document(
        screen_id=screen_id,
        image_path=infer_image_path(xml_path) if dataset_root is None else _screenshot_path(xml_path, dataset_root),
        xml_path=_xml_relative_path(xml_path, dataset_root),
        components=components,
        device_info=_extract_device_info(tree_root, components),
    )


def parse_xml_file(
    xml_path: Path,
    output_dir: Path,
    xml_root_dir: Path,
    dataset_root: Path | None,
) -> dict:
    """Parse one XML file and write its components.json to output_dir; returns the parsed payload."""
    payload = build_screen_document(xml_path, xml_root_dir, dataset_root)
    output_file = _parsed_output_path(xml_path, output_dir, dataset_root)
    output_file.write_text(json.dumps(payload, indent=2), encoding="utf-8")
    return payload


def parse_xml_directory(
    xml_root: Path | None = None,
    output_root: Path | None = None,
    dataset_root: Path | None = None,
) -> dict:
    """Batch-parse every XML file under xml_root, writing each components.json and
    collecting per-file errors. Returns a summary dict (processed/failed counts, errors)."""
    xml_root, output_root, dataset_root = resolve_paths(xml_root, output_root, dataset_root)
    xml_root.mkdir(parents=True, exist_ok=True)
    output_root.mkdir(parents=True, exist_ok=True)

    xml_files = sorted(xml_root.rglob("*.xml"))
    errors: list[str] = []
    for xml_path in xml_files:
        try:
            parse_xml_file(xml_path, output_root, xml_root, dataset_root)
        except Exception as exc:
            errors.append(f"{xml_path.name}: {exc}")

    return {
        "processed_files": len(xml_files) - len(errors),
        "failed_files": len(errors),
        "source_root": xml_root.as_posix(),
        "output_root": output_root.as_posix(),
        "dataset_root": dataset_root.as_posix() if dataset_root else None,
        "errors": errors[:20],
    }


def parse_dataset_folder(
    dataset_root: Path | None = None,
    output_root: Path | None = None,
) -> dict:
    """Batch-parse an entire auto-detected (or explicit) dataset's xml/ folder."""
    resolved_dataset = resolve_dataset_root(dataset_root)
    if resolved_dataset is None:
        return parse_xml_directory(output_root=output_root)
    return parse_xml_directory(resolved_dataset / "xml", output_root, resolved_dataset)