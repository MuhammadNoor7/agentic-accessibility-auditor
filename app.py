import json
from pathlib import Path

import streamlit as st

from src.parser import (
    parse_dataset_folder,
    parse_xml_file,
    resolve_dataset_root,
    resolve_parsed_root,
)
from test_run import write_violations

ROOT = Path(__file__).resolve().parent
UPLOAD_XML = ROOT / "data" / "xml"
UPLOAD_SCREENSHOTS = ROOT / "data" / "screenshots"
UPLOAD_PARSED = ROOT / "data" / "parsed"

st.set_page_config(page_title="Agentic Accessibility Auditor", layout="wide")

st.title("Agentic Accessibility Auditor")
st.markdown(
    "Upload a UIAutomator XML dump to produce `components.json` (pipeline stage 1). "
    "Screenshot is optional."
)

dataset_root = resolve_dataset_root()
parsed_root = resolve_parsed_root(dataset_root)

st.sidebar.header("Batch parser")
st.sidebar.write(f"Active dataset: `{dataset_root}`" if dataset_root else "No dataset under `data/`.")
st.sidebar.write(f"Parsed output: `{parsed_root}`")
if st.sidebar.button("Run batch parser"):
    result = parse_dataset_folder(dataset_root=dataset_root)
    st.sidebar.success(f"Processed {result['processed_files']} file(s)")
    st.sidebar.json(result)

col1, col2 = st.columns(2)

with col1:
    st.subheader("1. Upload Screenshot (.png/.jpg)")
    image_file = st.file_uploader("Choose a screenshot", type=["png", "jpg", "jpeg"])

with col2:
    st.subheader("2. Upload UIAutomator Dump (.xml)")
    xml_file = st.file_uploader("Choose an XML dump", type=["xml"])

if st.button("Parse XML to Components", type="primary"):
    if not xml_file:
        st.error("Please upload an XML file.")
    else:
        with st.spinner("Parsing..."):
            UPLOAD_XML.mkdir(parents=True, exist_ok=True)
            UPLOAD_SCREENSHOTS.mkdir(parents=True, exist_ok=True)
            UPLOAD_PARSED.mkdir(parents=True, exist_ok=True)

            xml_path = UPLOAD_XML / xml_file.name
            xml_path.write_bytes(xml_file.getbuffer())

            if image_file:
                img_path = UPLOAD_SCREENSHOTS / image_file.name
                img_path.write_bytes(image_file.getbuffer())

            try:
                components_doc = parse_xml_file(
                    xml_path,
                    UPLOAD_PARSED,
                    UPLOAD_XML,
                    dataset_root=None,
                )
            except Exception as exc:
                st.error(f"Parse failed: {type(exc).__name__}: {exc}")
                st.stop()

            st.session_state["components_doc"] = components_doc
            st.session_state["output_path"] = str(UPLOAD_PARSED / f"{xml_path.stem}_components.json")
            st.session_state["base_name"] = xml_path.stem

            # Stage 2: run the rule checker immediately after parsing. Failures
            # here must not crash the app — components.json already parsed fine
            # and should still be shown even if the rule checker has a problem.
            try:
                violations_doc = write_violations(components_doc)
                st.session_state["violations_doc"] = violations_doc
                st.session_state["violations_path"] = str(
                    Path("outputs") / "violations" / f"{components_doc['screen_id']}_violations.json"
                )
                st.session_state["violations_error"] = None
            except Exception as exc:
                st.session_state["violations_doc"] = None
                st.session_state["violations_path"] = None
                st.session_state["violations_error"] = f"{type(exc).__name__}: {exc}"

if "components_doc" in st.session_state:
    components_doc = st.session_state["components_doc"]
    output_path = st.session_state["output_path"]
    base_name = st.session_state["base_name"]
    components_list = components_doc["components"]

    st.success("Parsing complete!")
    st.subheader("Summary")
    st.metric("Total Components Parsed", len(components_list))
    st.caption(f"Saved to `{output_path}`")

    if components_list:
        st.subheader("UI fields (table)")
        st.dataframe(components_list, use_container_width=True)
    else:
        st.warning("No components extracted — check XML format and bounds.")

    st.subheader("components.json preview")
    st.json(components_doc)

    st.download_button(
        label="Download components.json",
        data=json.dumps(components_doc, indent=2),
        file_name=f"{base_name}_components.json",
        mime="application/json",
    )

    st.subheader("Accessibility violations (Stage 2)")
    violations_error = st.session_state.get("violations_error")
    violations_doc = st.session_state.get("violations_doc")

    if violations_error:
        st.error(f"Rule checker failed: {violations_error}")
    elif violations_doc is not None:
        total_violations = violations_doc["total_violations"]
        st.metric("Total Violations", total_violations)
        st.caption(f"Saved to `{st.session_state.get('violations_path')}`")

        if total_violations == 0:
            st.success("No violations found")
        else:
            violations_table = [
                {
                    "rule_id": violation["rule_id"],
                    "issue": violation["issue"],
                    "severity": violation["severity"],
                    "component_id": violation["component_id"],
                    "recommendation": violation["recommendation"],
                }
                for violation in violations_doc["violations"]
            ]
            st.dataframe(violations_table, use_container_width=True)

        st.subheader("violations.json preview")
        st.json(violations_doc)

        st.download_button(
            label="Download violations.json",
            data=json.dumps(violations_doc, indent=2),
            file_name=f"{base_name}_violations.json",
            mime="application/json",
        )
