# --------------------------------------------------------------
# convert_json_to_xml.py
# --------------------------------------------------------------
# Purpose: Convert the 2 299 JSON view‑hierarchy files that were
# copied to `data/json/` into UIAutomator‑style XML files and store
# them under `data/xml/<category>/`.
# --------------------------------------------------------------

import os
import json
import xml.etree.ElementTree as ET
from pathlib import Path
import shutil

# ----------------------------------------------------------------------
# Configuration – adjust only if your folder layout changes
# ----------------------------------------------------------------------
PROJECT_ROOT = r"d:/internship/agentic-accessibility-auditor"

# Source JSON root (populated by `copy_matched_jsons.py`)
JSON_ROOT = os.path.join(PROJECT_ROOT, "data", "json")

# Destination XML root (must already exist – we’ll create sub‑folders)
XML_ROOT = os.path.join(PROJECT_ROOT, "data", "xml")

# Mapping from category name (lower‑case) to the exact sub‑folder name in the
# JSON archive – this matches the mapping you already use elsewhere.
CATEGORY_MAP = {
    "chat": "Chat",
    "home": "Home",
    "list": "List",
    "login": "Login",
    "maps": "Map",
    "menu": "Menu",
    "profile": "Profile",
    "settings": "Setting",
    "welcome": "Welcome",
    "search": "Search",
}

# ----------------------------------------------------------------------
# Helper: recursively turn a dict / list into XML Elements
# ----------------------------------------------------------------------
def dict_to_elem(name: str, data) -> ET.Element:
    """
    Convert a Python dict (or list) into an ElementTree node.
    - dict → <name key1="value1" key2="value2">…children…</name>
    - list → series of child nodes with the same name
    The UIAutomator XML format mainly uses a `<node …/>` tag, so we
    translate everything into `<node>` elements.
    """
    if isinstance(data, dict):
        elem = ET.Element("node")
        for k, v in data.items():
            # Primitive values become attributes
            if isinstance(v, (str, int, float, bool)):
                elem.set(k, str(v))
            else:
                # Complex values become child elements (recursive)
                child = dict_to_elem(k, v)
                elem.append(child)
        return elem
    elif isinstance(data, list):
        # For a list we create a dummy wrapper and attach each item as a child
        wrapper = ET.Element("wrapper")
        for item in data:
            wrapper.append(dict_to_elem(name, item))
        return wrapper
    else:
        # Primitive – represent as a simple <node value="…"/>
        leaf = ET.Element("node")
        leaf.set("value", str(data))
        return leaf


def convert_one_json(json_path: Path, xml_path: Path):
    """
    Load a JSON file, convert it to XML, and write the XML file.
    """
    try:
        with json_path.open("r", encoding="utf-8") as jf:
            data = json.load(jf)

        # The root element for UIAutomator xml is <hierarchy>
        root = ET.Element("hierarchy")

        # The MASC JSON files store the hierarchy under a top‑level key
        # (often “root” or “viewHierarchy”).  We just feed the whole dict.
        root.append(dict_to_elem("root", data))

        tree = ET.ElementTree(root)

        # Make sure the destination folder exists
        xml_path.parent.mkdir(parents=True, exist_ok=True)

        # Write a pretty‑printed XML file (UTF‑8, with XML declaration)
        tree.write(str(xml_path), encoding="utf-8", xml_declaration=True)
        print(f"[OK] {json_path.name} → {xml_path.relative_to(PROJECT_ROOT)}")
    except Exception as e:
        print(f"[ERROR] Failed to convert {json_path}: {e}")


# ----------------------------------------------------------------------
# Main conversion loop
# ----------------------------------------------------------------------
def main():
    total_copied = 0
    total_converted = 0

    # Ensure the top‑level XML folder exists
    os.makedirs(XML_ROOT, exist_ok=True)

    for cat, archive_name in CATEGORY_MAP.items():
        json_cat_dir = Path(JSON_ROOT) / cat
        xml_cat_dir = Path(XML_ROOT) / cat

        if not json_cat_dir.is_dir():
            print(f"[WARN] No JSON source folder for category: {cat}")
            continue

        # Create the per‑category XML sub‑folder
        xml_cat_dir.mkdir(parents=True, exist_ok=True)

        # Process every *.json file in this category
        for json_file in json_cat_dir.glob("*.json"):
            total_copied += 1
            xml_file = xml_cat_dir / f"{json_file.stem}.xml"
            convert_one_json(json_file, xml_file)
            total_converted += 1

    print("\n=== Summary ===")
    print(f"JSON files found:      {total_copied}")
    print(f"XML files generated:   {total_converted}")
    print(f"Output root:           {XML_ROOT}")


if __name__ == "__main__":
    main()
