import json
import os
from pathlib import Path

from src.parser import parse_xml_file, resolve_paths
from src.rules import check_screen

root = Path(__file__).resolve().parent
parsed_root = root / "data" / "parsed"
violations_root = root / "outputs" / "violations"
parsed_root.mkdir(parents=True, exist_ok=True)
violations_root.mkdir(parents=True, exist_ok=True)

xml_root, _, dataset_root = resolve_paths()

# Process configuration limits (0 means process all files)
max_files_raw = os.environ.get("PARSER_MAX_FILES", "0") 
max_files = int(max_files_raw)
xml_files = sorted(xml_root.rglob("*.xml"))
if max_files > 0:
    xml_files = xml_files[:max_files]

print(f"Starting batch process pipeline for {len(xml_files)} XML files...")

errors: list[str] = []
processed_count = 0

for xml_path in xml_files:
    try:
        # Step 1: Run XML parser to generate components schema
        screen_doc = parse_xml_file(xml_path, parsed_root, xml_root, dataset_root)
        
        # Step 2: Directly feed parsed schema into the completed Rule Checker engine
        violations_doc = check_screen(screen_doc)
        
        # Step 3: Write out compliant violations log
        violations_path = violations_root / f"{screen_doc['screen_id']}_violations.json"
        violations_path.write_text(json.dumps(violations_doc, indent=2), encoding="utf-8")
        processed_count += 1
    except Exception as exc:
        errors.append(f"{xml_path.name}: {exc}")

result = {
    "processed_files": processed_count,
    "failed_files": len(errors),
    "source_root": xml_root.as_posix(),
    "output_root": parsed_root.as_posix(),
    "errors": errors[:20],
}
print("\n=== Pipeline Execution Results ===")
print(json.dumps(result, indent=2))