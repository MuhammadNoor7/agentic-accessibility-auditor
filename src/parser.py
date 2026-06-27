from __future__ import annotations

import json
from pathlib import Path
import xml.etree.ElementTree as ET

REPO_ROOT = Path(__file__).resolve().parents[1]
DEFAULT_DATASET_ROOT = REPO_ROOT.parent / "data-masc"
DEFAULT_CONTAINER_DATASET_ROOT = Path("/app/data/dataset")
DEFAULT_OUTPUT_ROOT = REPO_ROOT / "data" / "parsed"


def sanitize_text(text: str | None) -> str | None:
    if text is None:
        return None
    cleaned = " ".join(text.split())
    return cleaned or None


def build_component(node: ET.Element) -> dict:
    return {
        "tag": node.tag,
        "attributes": {key: value for key, value in node.attrib.items()},
        "text": sanitize_text(node.text),
        "children": [build_component(child) for child in node],
    }


def count_nodes(component: dict) -> int:
    return 1 + sum(count_nodes(child) for child in component.get("children", []))


def parse_xml_file(xml_path: Path, output_dir: Path) -> dict:
    tree = ET.parse(xml_path)
    root = tree.getroot()
    component_tree = build_component(root)

    output_file = output_dir / f"{xml_path.stem}_components.json"
    payload = {
        "source_file": xml_path.name,
        "component_count": count_nodes(component_tree),
        "component_tree": component_tree,
    }
    output_file.write_text(json.dumps(payload, indent=2), encoding="utf-8")
    return payload


def resolve_paths(xml_root: Path | None = None, output_root: Path | None = None) -> tuple[Path, Path]:
    if xml_root is None:
        candidates = [DEFAULT_CONTAINER_DATASET_ROOT / "xml", DEFAULT_DATASET_ROOT / "xml", REPO_ROOT / "data" / "xml"]
        for candidate in candidates:
            if candidate.exists():
                xml_root = candidate
                break
        if xml_root is None:
            xml_root = REPO_ROOT / "data" / "xml"

    if output_root is None:
        output_root = DEFAULT_OUTPUT_ROOT

    return Path(xml_root), Path(output_root)


def parse_xml_directory(xml_root: Path | None = None, output_root: Path | None = None) -> dict:
    xml_root, output_root = resolve_paths(xml_root, output_root)
    xml_root.mkdir(parents=True, exist_ok=True)
    output_root.mkdir(parents=True, exist_ok=True)

    xml_files = sorted(xml_root.rglob("*.xml"))
    for xml_path in xml_files:
        parse_xml_file(xml_path, output_root)

    return {
        "processed_files": len(xml_files),
        "source_root": xml_root.as_posix(),
        "output_root": output_root.as_posix(),
    }


def parse_dataset_folder(dataset_root: Path | None = None, output_root: Path | None = None) -> dict:
    if dataset_root is None:
        dataset_root = DEFAULT_CONTAINER_DATASET_ROOT if DEFAULT_CONTAINER_DATASET_ROOT.exists() else DEFAULT_DATASET_ROOT
    if not dataset_root.exists():
        return parse_xml_directory(output_root=output_root)
    return parse_xml_directory(dataset_root / "xml", output_root)
