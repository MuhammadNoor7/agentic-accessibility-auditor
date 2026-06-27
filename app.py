from pathlib import Path
import streamlit as st

from src.parser import parse_dataset_folder

st.set_page_config(page_title="Agentic Accessibility Auditor", page_icon="🧪", layout="centered")

st.title("Agentic Accessibility Auditor")
st.write("Intern 1 pipeline: parse XML UI hierarchy into component JSON")

DATA_ROOT = Path(__file__).resolve().parent / "data"
PARSED_ROOT = DATA_ROOT / "parsed"
PARSED_ROOT.mkdir(parents=True, exist_ok=True)

st.sidebar.header("Dataset")
st.sidebar.write("The app will use the MASC XML dataset automatically when it is available.")

if st.button("Run parser"):
    result = parse_dataset_folder(output_root=PARSED_ROOT)
    st.success(f"Processed {result['processed_files']} XML files")
    st.json(result)
