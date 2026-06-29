from pathlib import Path

import streamlit as st

from src.parser import parse_dataset_folder, resolve_dataset_root, resolve_parsed_root

st.set_page_config(page_title="Agentic Accessibility Auditor", page_icon="🧪", layout="centered")

st.title("Agentic Accessibility Auditor")
st.write("Intern 1 pipeline: parse XML UI hierarchy into schema-compliant JSON")

DATA_ROOT = Path(__file__).resolve().parent / "data"
dataset_root = resolve_dataset_root()
parsed_root = resolve_parsed_root(dataset_root)
parsed_root.mkdir(parents=True, exist_ok=True)

st.sidebar.header("Dataset")
st.sidebar.write(f"Active dataset: `{dataset_root}`" if dataset_root else "No dataset found under `data/`.")
st.sidebar.write(f"Parsed output: `{parsed_root}`")

if st.button("Run parser"):
    result = parse_dataset_folder(dataset_root=dataset_root)
    st.success(f"Processed {result['processed_files']} XML files")
    st.json(result)
