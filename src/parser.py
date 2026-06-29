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


def resolve_dataset_root(dataset_root: Path | None = None) -> Path | None:
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
    resolved = resolve_dataset_root(dataset_root)
    if resolved is not None:
        if resolved == GENERIC_DATASET_ROOT:
            return resolved / "parsed"
        return resolved / "parsed"
    return DEFAULT_OUTPUT_ROOT


def infer_dataset_root_for_xml(xml_path: Path) -> Path | None:
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
    return load_xml_root(xml_path)


def _parse_bool(value: str | None, default: bool = False) -> bool:
    if value is None:
        return default
    return value.strip().lower() in {"true", "1", "yes"}


def _normalize_string(value: str | None) -> str:
    if value is None:
        return ""
    return " ".join(str(value).replace("\x00", "").split())


def _parse_uiautomator_bounds(bounds: str | None) -> list[int] | None:
    if not bounds:
        return None
    match = UIAUTOMATOR_BOUNDS_RE.search(bounds)
    if not match:
        return None
    return [int(match.group(1)), int(match.group(2)), int(match.group(3)), int(match.group(4))]


def _parse_space_bounds(bounds: str | None) -> list[int] | None:
    if not bounds:
        return None
    match = SPACE_BOUNDS_RE.match(bounds.strip())
    if not match:
        return None
    return [int(match.group(1)), int(match.group(2)), int(match.group(3)), int(match.group(4))]


def _parse_bounds_attr(raw: str | None) -> list[int] | None:
    return _parse_uiautomator_bounds(raw) or _parse_space_bounds(raw)


def _parse_masc_bounds(node: etree._Element) -> list[int] | None:
    wrappers = [child for child in node if child.tag == "wrapper"]
    for wrapper in reversed(wrappers):
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
            return values
    return None


def _get_text(elem: etree._Element) -> str:
    direct = _normalize_string(elem.get("text"))
    if direct:
        return direct
    for wrapper in elem.findall("wrapper"):
        values = [_normalize_string(child.get("value")) for child in wrapper.findall("node")]
        if len(values) == 1 and values[0] and values[0] not in ("None",):
            return values[0]
    return ""


def _get_content_desc(elem: etree._Element) -> str:
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


def _tag_to_class(tag: str) -> str:
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
    for attr in ("class", "className", "class-name"):
        value = _normalize_string(elem.get(attr))
        if value:
            return value
    if elem.tag == "node":
        return ""
    return _tag_to_class(elem.tag)


def _extract_bounds(elem: etree._Element) -> list[int] | None:
    bounds = _parse_bounds_attr(elem.get("bounds"))
    if bounds is not None:
        return bounds
    return _parse_masc_bounds(elem)


def _element_to_component(elem: etree._Element, component_index: int) -> dict | None:
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

    return {
        "component_id": f"c_{component_index:03d}",
        "class": class_name,
        "text": _get_text(elem),
        "content_desc": _get_content_desc(elem),
        "resource_id": _normalize_string(elem.get("resource-id") or elem.get("resource_id")),
        "clickable": _parse_bool(elem.get("clickable")),
        "enabled": _parse_bool(elem.get("enabled"), default=True),
        "focusable": _parse_bool(elem.get("focusable")),
        "bounds": bounds,
    }


def parse_xml_tree(root: etree._Element) -> list[dict]:
    """Hybrid parser: UIAutomator, MASC, Rico, and generic layout XML in one pass."""
    components: list[dict] = []
    component_index = 1
    for elem in root.iter():
        component = _element_to_component(elem, component_index)
        if component is None:
            continue
        components.append(component)
        component_index += 1
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
    relative_parent = xml_path.parent.name
    stem = xml_path.stem
    if relative_parent and relative_parent != xml_root.name:
        return f"{relative_parent}_{stem}"
    return stem


def _relative_dataset_path(path: Path) -> str:
    try:
        return path.resolve().relative_to(REPO_ROOT).as_posix()
    except ValueError:
        return path.resolve().as_posix()


def _find_screenshot_file(xml_path: Path, dataset_root: Path) -> Path | None:
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
    xml_path = xml_path.resolve()
    if dataset_root is None:
        try:
            return xml_path.relative_to(REPO_ROOT).as_posix()
        except ValueError:
            return xml_path.as_posix()
    return _relative_dataset_path(xml_path)


def _parsed_output_path(xml_path: Path, output_dir: Path, dataset_root: Path | None) -> Path:
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


def build_screen_document(
    xml_path: Path,
    xml_root_dir: Path,
    dataset_root: Path | None,
) -> dict:
    xml_path = xml_path.resolve()
    xml_root_dir = xml_root_dir.resolve()
    screen_id = _build_screen_id(xml_path, xml_root_dir)
    tree_root = _read_xml_root(xml_path)
    return build_components_document(
        screen_id=screen_id,
        image_path=infer_image_path(xml_path) if dataset_root is None else _screenshot_path(xml_path, dataset_root),
        xml_path=_xml_relative_path(xml_path, dataset_root),
        components=parse_xml_tree(tree_root),
    )


def parse_xml_file(
    xml_path: Path,
    output_dir: Path,
    xml_root_dir: Path,
    dataset_root: Path | None,
) -> dict:
    payload = build_screen_document(xml_path, xml_root_dir, dataset_root)
    output_file = _parsed_output_path(xml_path, output_dir, dataset_root)
    output_file.write_text(json.dumps(payload, indent=2), encoding="utf-8")
    return payload


def parse_xml_directory(
    xml_root: Path | None = None,
    output_root: Path | None = None,
    dataset_root: Path | None = None,
) -> dict:
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
    resolved_dataset = resolve_dataset_root(dataset_root)
    if resolved_dataset is None:
        return parse_xml_directory(output_root=output_root)
    return parse_xml_directory(resolved_dataset / "xml", output_root, resolved_dataset)
