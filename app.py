from pathlib import Path
import json
import streamlit as st

from src.parser import parse_dataset_folder
from src.rules import check_screen

st.set_page_config(page_title="Agentic Accessibility Auditor", page_icon="🧪", layout="centered")

st.title("Agentic Accessibility Auditor")
st.write("Intern 1 pipeline: parse XML UI hierarchy into schema-compliant JSON")

DATA_ROOT = Path(__file__).resolve().parent / "data"
PARSED_ROOT = DATA_ROOT / "parsed"
VIOLATIONS_ROOT = Path(__file__).resolve().parent / "outputs" / "violations"
PARSED_ROOT.mkdir(parents=True, exist_ok=True)
VIOLATIONS_ROOT.mkdir(parents=True, exist_ok=True)

st.sidebar.header("Dataset")
st.sidebar.write("Uses MASC XML from data-masc/data-masc when available.")

if st.button("Run parser + rules"):
    result = parse_dataset_folder(output_root=PARSED_ROOT)
    st.success(f"Processed {result['processed_files']} XML files")

    sample_files = sorted(PARSED_ROOT.glob("*_components.json"))
    if sample_files:
        screen_document = json.loads(sample_files[0].read_text(encoding="utf-8"))
        violations_document = check_screen(screen_document)
        violations_path = VIOLATIONS_ROOT / f"{screen_document['screen_id']}_violations.json"
        violations_path.write_text(json.dumps(violations_document, indent=2), encoding="utf-8")
        st.json({"parser": result, "sample_violations": violations_document["total_violations"]})
    else:
        st.json(result)
