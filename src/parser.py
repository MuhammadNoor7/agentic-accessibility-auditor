from __future__ import annotations

import json
import re
from pathlib import Path

from lxml import etree

from src.schema_documents import SCHEMA_VERSION

REPO_ROOT = Path(__file__).resolve().parents[1]
DEFAULT_OUTPUT_ROOT = REPO_ROOT / "data" / "parsed"
DEFAULT_CONTAINER_DATASET_ROOT = Path("/app/data/dataset")

DATASET_CANDIDATES = [
    REPO_ROOT / "data" / "data-masc",
    REPO_ROOT / "data-masc" / "data-masc",
    REPO_ROOT.parent / "data-masc",
    DEFAULT_CONTAINER_DATASET_ROOT,
]

UIAUTOMATOR_BOUNDS_RE = re.compile(r"\[(\d+),(\d+)\]\[(\d+),(\d+)\]")


def resolve_dataset_root(dataset_root: Path | None = None) -> Path | None:
    if dataset_root is not None:
        return dataset_root if dataset_root.exists() else None
    for candidate in DATASET_CANDIDATES:
        xml_dir = candidate / "xml"
        if xml_dir.exists():
            return candidate
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
        output_root = DEFAULT_OUTPUT_ROOT

    return Path(xml_root), Path(output_root), resolved_dataset


def _read_xml_root(xml_path: Path) -> etree._Element:
    raw = xml_path.read_bytes().replace(b"\x00", b"")
    return etree.fromstring(raw)


def _parse_bool(value: str | None, default: bool = False) -> bool:
    if value is None:
        return default
    return value.strip().lower() in {"true", "1", "yes"}


def _parse_uiautomator_bounds(bounds: str | None) -> list[int] | None:
    if not bounds:
        return None
    match = UIAUTOMATOR_BOUNDS_RE.search(bounds)
    if not match:
        return None
    return [int(match.group(1)), int(match.group(2)), int(match.group(3)), int(match.group(4))]


def _parse_masc_bounds(node: etree._Element) -> list[int] | None:
    wrappers = [child for child in node if child.tag == "wrapper"]
    for wrapper in reversed(wrappers):
        values: list[int] = []
        for value_node in wrapper:
            if value_node.tag != "node":
                continue
            raw = value_node.get("value")
            if raw is None:
                continue
            try:
                values.append(int(raw))
            except ValueError:
                continue
        if len(values) == 4:
            return values
    return None


def _normalize_string(value: str | None) -> str:
    if value is None:
        return ""
    cleaned = " ".join(value.split())
    return cleaned


def _build_screen_id(xml_path: Path, xml_root: Path) -> str:
    relative_parent = xml_path.parent.name
    stem = xml_path.stem
    if relative_parent and relative_parent != xml_root.name:
        return f"{relative_parent}_{stem}"
    return stem


def _relative_dataset_path(dataset_root: Path | None, path: Path) -> str:
    if dataset_root is not None:
        try:
            return path.relative_to(REPO_ROOT).as_posix()
        except ValueError:
            return path.relative_to(dataset_root.parent).as_posix()
    return path.as_posix()


def _screenshot_path(xml_path: Path, dataset_root: Path | None) -> str:
    if dataset_root is None:
        return f"data/xml/{xml_path.name.replace('.xml', '.png')}"

    screenshots_root = dataset_root / "screenshots"
    relative_xml = xml_path.relative_to(dataset_root / "xml")
    screenshot = screenshots_root / relative_xml.with_suffix(".png")
    return _relative_dataset_path(dataset_root, screenshot)


def _xml_relative_path(xml_path: Path, dataset_root: Path | None) -> str:
    if dataset_root is None:
        return f"data/xml/{xml_path.name}"
    return _relative_dataset_path(dataset_root, xml_path)


def _parse_node(node: etree._Element, component_index: int) -> dict | None:
    class_name = node.get("class")
    if not class_name:
        return None

    bounds = _parse_uiautomator_bounds(node.get("bounds")) or _parse_masc_bounds(node)
    if bounds is None:
        bounds = [0, 0, 0, 0]

    content_desc = _normalize_string(node.get("content-desc") or node.get("content_desc"))

    return {
        "component_id": f"c_{component_index:03d}",
        "class": class_name,
        "text": _normalize_string(node.get("text")),
        "content_desc": content_desc,
        "resource_id": _normalize_string(node.get("resource-id")),
        "clickable": _parse_bool(node.get("clickable")),
        "enabled": _parse_bool(node.get("enabled"), default=True),
        "focusable": _parse_bool(node.get("focusable")),
        "bounds": bounds,
    }


def parse_xml_tree(root: etree._Element) -> list[dict]:
    components: list[dict] = []
    component_index = 1
    for node in root.iter("node"):
        component = _parse_node(node, component_index)
        if component is None:
            continue
        components.append(component)
        component_index += 1
    return components


def build_screen_document(
    xml_path: Path,
    xml_root_dir: Path,
    dataset_root: Path | None,
) -> dict:
    screen_id = _build_screen_id(xml_path, xml_root_dir)
    tree_root = _read_xml_root(xml_path)
    return {
        "schema_version": SCHEMA_VERSION,
        "screen_id": screen_id,
        "image_path": _screenshot_path(xml_path, dataset_root),
        "xml_path": _xml_relative_path(xml_path, dataset_root),
        "components": parse_xml_tree(tree_root),
    }

def parse_xml_file(
    xml_path: Path,
    output_dir: Path,
    xml_root_dir: Path,
    dataset_root: Path | None,
) -> dict:
    payload = build_screen_document(xml_path, xml_root_dir, dataset_root)
    output_file = output_dir / f"{xml_path.stem}_components.json"
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
