import xml.etree.ElementTree as ET
import json
import os
import glob

def parse_xml_to_json(xml_file_path):
    try:
        tree = ET.parse(xml_file_path)
        root = tree.getroot()
        components = []
        for elem in root.iter('node'):
            components.append({
                "class": elem.attrib.get("class"),
                "text": elem.attrib.get("text"),
                "content-desc": elem.attrib.get("content-desc"),
                "bounds": elem.attrib.get("bounds")
            })
        return components
    except Exception as e:
        print(f"Error parsing {xml_file_path}: {e}")
        return []

def run_batch_process():
    # Recursively find EVERY .xml file inside the mapped directory
    all_files = glob.glob('/app/**/*.xml', recursive=True)
    
    if not all_files:
        print("CRITICAL: Still no XML files found inside /app. Check volume bindings.")
        return

    print(f"Found {len(all_files)} XML files total. Commencing full batch parsing...")
    os.makedirs('/app/outputs', exist_ok=True)
    
    for xml_file in all_files:
        data = parse_xml_to_json(xml_file)
        
        # Get parent folder layout to avoid namespace collisions
        # e.g., /app/.../xml/welcome/ui.xml -> welcome_ui.json
        path_parts = xml_file.split(os.sep)
        if len(path_parts) >= 2:
            parent_folder = path_parts[-2]
            base_file = path_parts[-1].replace('.xml', '.json')
            file_name = f"{parent_folder}_{base_file}"
        else:
            file_name = os.path.basename(xml_file).replace('.xml', '.json')
            
        output_path = f'/app/outputs/{file_name}'
        with open(output_path, 'w', encoding='utf-8') as f:
            json.dump(data, f, indent=4)
            
    print(f"SUCCESS: Batch processing complete. Generated {len(all_files)} JSON files.")

if __name__ == "__main__":
    run_batch_process()