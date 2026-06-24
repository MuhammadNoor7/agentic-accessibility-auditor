import xml.etree.ElementTree as ET
import json
import os
import glob

def parse_xml_to_json(xml_file_path, output_json_path):
    try:
        # Parse the XML file
        tree = ET.parse(xml_file_path)
        root = tree.getroot()
        
        components = []
        
        # Iterate through all nodes in the XML
        for node in root.iter('node'):
            component = {
                "class": node.attrib.get("class"),
                "text": node.attrib.get("text"),
                "content-desc": node.attrib.get("content-desc"),
                "bounds": node.attrib.get("bounds"),
                "checkable": node.attrib.get("checkable"),
                "clickable": node.attrib.get("clickable")
            }
            components.append(component)
        
        # Save the extracted data
        with open(output_json_path, 'w', encoding='utf-8') as f:
            json.dump(components, f, indent=4)
        
        print(f"Successfully converted: {xml_file_path} -> {output_json_path}")
        
    except Exception as e:
        print(f"Failed to process {xml_file_path}: {e}")

def run_batch_process():
    # Inside the container, our mounted data is at /app/data-masc
    # We check both the root /app/data-masc and a potential nested folder
    search_path = '/app/data-masc/*.xml'
    
    # Debugging: Print current working directory and search path
    print(f"Searching for XML files in: {search_path}")
    
    os.makedirs('outputs', exist_ok=True)
    
    xml_files = glob.glob(search_path)
    
    # If nothing found, try looking for nested folders (common with unzipped datasets)
    if not xml_files:
        print("No files in root. Checking for nested 'data-masc' directory...")
        xml_files = glob.glob('/app/data-masc/**/*.xml', recursive=True)
    
    if not xml_files:
        print("Still no XML files found. Please verify the folder structure inside the container.")
        return

    # Process up to 3 files
    for xml_file in xml_files[:3]:
        file_name = os.path.basename(xml_file).replace('.xml', '.json')
        output_path = os.path.join('outputs', file_name)
        parse_xml_to_json(xml_file, output_path)

if __name__ == "__main__":
    run_batch_process()