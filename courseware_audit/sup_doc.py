"""
Courseware Audit Module

Upload AP, FG, LG, LP documents and cross-check consistency of key fields:
TGS Ref Code, Course Title, Company Name, TSC Ref Code/Title,
Learning Outcomes, Durations, Topics, Assessment Methods, Instructional Methods.
"""

import streamlit as st
import os
import asyncio
import tempfile
import json
import pandas as pd
from docx import Document

# Optional PDF support
PYMUPDF_AVAILABLE = False
try:
    import pymupdf
    PYMUPDF_AVAILABLE = True
except ImportError:
    try:
        from PyPDF2 import PdfReader
    except ImportError:
        pass


DOC_TYPES = ["AP", "FG", "LG", "LP"]


def extract_text_from_docx(file_bytes):
    """Extract all text from a DOCX file."""
    with tempfile.NamedTemporaryFile(delete=False, suffix=".docx") as tmp:
        tmp.write(file_bytes)
        tmp_path = tmp.name

    try:
        doc = Document(tmp_path)
        parts = []
        for para in doc.paragraphs:
            if para.text.strip():
                parts.append(para.text.strip())
        for table in doc.tables:
            for row in table.rows:
                cells = [cell.text.strip() for cell in row.cells if cell.text.strip()]
                if cells:
                    parts.append(" | ".join(cells))
        return "\n".join(parts)
    finally:
        os.remove(tmp_path)


def extract_text_from_pdf(file_bytes):
    """Extract text from a PDF file."""
    with tempfile.NamedTemporaryFile(delete=False, suffix=".pdf") as tmp:
        tmp.write(file_bytes)
        tmp_path = tmp.name

    try:
        if PYMUPDF_AVAILABLE:
            doc = pymupdf.open(tmp_path)
            parts = []
            for page in doc:
                text = page.get_text()
                if text.strip():
                    parts.append(text.strip())
            doc.close()
            return "\n".join(parts)
        else:
            reader = PdfReader(tmp_path)
            parts = []
            for page in reader.pages:
                text = page.extract_text() or ""
                if text.strip():
                    parts.append(text.strip())
            return "\n".join(parts)
    finally:
        os.remove(tmp_path)


def _normalize(val):
    """Normalize a string for comparison."""
    if val is None:
        return ""
    return str(val).strip().lower()


def _compare_strings(values):
    """Compare string values across documents. Returns (status, detail)."""
    non_null = {k: v for k, v in values.items() if v and str(v).strip()}
    if len(non_null) == 0:
        return "missing", "Not found in any document"
    if len(non_null) == 1:
        return "single", f"Only in {list(non_null.keys())[0]}"
    normalized = {k: _normalize(v) for k, v in non_null.items()}
    unique_vals = set(normalized.values())
    if len(unique_vals) == 1:
        return "match", "Consistent"
    return "mismatch", "MISMATCH"


def _compare_lists(values):
    """Compare list values across documents. Returns (status, detail)."""
    non_null = {}
    for k, v in values.items():
        if v and isinstance(v, list) and len(v) > 0:
            non_null[k] = set(_normalize(item) for item in v)
    if len(non_null) == 0:
        return "missing", "Not found in any document"
    if len(non_null) == 1:
        return "single", f"Only in {list(non_null.keys())[0]}"
    all_sets = list(non_null.values())
    if all(s == all_sets[0] for s in all_sets):
        return "match", "Consistent"
    return "mismatch", "MISMATCH"


def _compare_durations(values):
    """Compare duration dicts across documents. Returns (status, detail)."""
    non_null = {}
    for k, v in values.items():
        if v and isinstance(v, dict):
            total = v.get("total_hours") or v.get("training_hours")
            if total:
                non_null[k] = _normalize(total)
    if len(non_null) == 0:
        return "missing", "Not found in any document"
    if len(non_null) == 1:
        return "single", f"Only in {list(non_null.keys())[0]}"
    unique_vals = set(non_null.values())
    if len(unique_vals) == 1:
        return "match", "Consistent"
    return "mismatch", "MISMATCH"


def run_cross_check(audit_results):
    """Run cross-check comparison across all audit results."""
    fields = [
        ("TGS Ref Code", "tgs_ref_code", "string"),
        ("Course Title", "course_title", "string"),
        ("Company Name", "company_name", "string"),
        ("TSC Ref Code", "tsc_ref_code", "string"),
        ("TSC Title", "tsc_title", "string"),
        ("Learning Outcomes", "learning_outcomes", "list"),
        ("Durations", "durations", "duration"),
        ("Topics", "topics", "list"),
        ("Assessment Methods", "assessment_methods", "list"),
        ("Instructional Methods", "instructional_methods", "list"),
    ]

    results = []
    for display_name, field_key, field_type in fields:
        values = {}
        for doc_label, data in audit_results.items():
            values[doc_label] = data.get(field_key)

        if field_type == "string":
            status, detail = _compare_strings(values)
        elif field_type == "list":
            status, detail = _compare_lists(values)
        elif field_type == "duration":
            status, detail = _compare_durations(values)
        else:
            status, detail = "unknown", ""

        # Build row with values from each document
        row = {"Field": display_name, "Status": detail}
        for doc_label in audit_results:
            val = values.get(doc_label)
            if isinstance(val, list):
                row[doc_label] = ", ".join(str(v) for v in val) if val else "-"
            elif isinstance(val, dict):
                parts = [f"{k}: {v}" for k, v in val.items() if v]
                row[doc_label] = "; ".join(parts) if parts else "-"
            else:
                row[doc_label] = str(val) if val else "-"
        row["_status"] = status
        results.append(row)

    return results


def app():
    st.title("Courseware Audit")

    # Initialize session state
    if "audit_docs" not in st.session_state:
        st.session_state.audit_docs = {}
    if "audit_results" not in st.session_state:
        st.session_state.audit_results = {}

    # Upload section
    st.subheader("Upload Documents")
    st.write("Upload your courseware documents and assign each a document type for cross-checking.")

    uploaded_files = st.file_uploader(
        "Upload courseware documents",
        type=["docx", "pdf"],
        accept_multiple_files=True,
        key="audit_uploader",
    )

    if uploaded_files:
        for uploaded_file in uploaded_files:
            fname = uploaded_file.name
            # Auto-detect doc type from filename
            default_type = 0
            fname_upper = fname.upper()
            for i, dt in enumerate(DOC_TYPES):
                if fname_upper.startswith(dt) or f"_{dt}_" in fname_upper or f"_{dt}." in fname_upper:
                    default_type = i
                    break

            col1, col2 = st.columns([3, 1])
            with col1:
                st.text(fname)
            with col2:
                doc_type = st.selectbox(
                    "Type",
                    DOC_TYPES,
                    index=default_type,
                    key=f"type_{fname}",
                    label_visibility="collapsed",
                )

            # Store the file data with its assigned type
            st.session_state.audit_docs[f"{doc_type}: {fname}"] = {
                "file": uploaded_file,
                "type": doc_type,
                "name": fname,
            }

    # Run Audit button
    if st.button("Run Audit", type="primary"):
        docs = st.session_state.audit_docs
        if not docs or len(docs) < 2:
            st.error("Please upload at least 2 documents to cross-check.")
        else:
            from courseware_audit.audit_agent import extract_audit_fields
            from utils.agent_runner import submit_agent_job

            # Pre-extract text from all documents
            doc_texts = {}
            for label, doc_info in docs.items():
                file_obj = doc_info["file"]
                fname = doc_info["name"]
                file_bytes = file_obj.getvalue()

                with st.spinner(f"Parsing {fname}..."):
                    ext = fname.rsplit(".", 1)[-1].lower()
                    if ext == "docx":
                        text = extract_text_from_docx(file_bytes)
                    elif ext == "pdf":
                        text = extract_text_from_pdf(file_bytes)
                    else:
                        text = ""
                    doc_texts[label] = (text, doc_info["type"])

            # Run audit agent on each document
            audit_results = {}
            for label, (text, doc_type) in doc_texts.items():
                if not text.strip():
                    st.warning(f"No text extracted from {label}")
                    continue
                with st.spinner(f"AI Agent auditing {label}..."):
                    try:
                        result = asyncio.run(extract_audit_fields(text, doc_type))
                        audit_results[label] = result
                    except Exception as e:
                        st.error(f"Error auditing {label}: {e}")
                        audit_results[label] = {}

            st.session_state.audit_results = audit_results
            st.success(f"Audit complete. Analyzed {len(audit_results)} documents.")
            st.rerun()

    # Display results
    if st.session_state.audit_results:
        audit_results = st.session_state.audit_results

        # Raw extraction results per document
        with st.expander("Extracted Fields (per document)", expanded=False):
            for label, data in audit_results.items():
                st.markdown(f"**{label}**")
                st.json(data)

        # Cross-check comparison table
        st.subheader("Cross-Check Results")
        comparison = run_cross_check(audit_results)

        if comparison:
            df = pd.DataFrame(comparison)
            # Remove internal status column for display
            status_col = df.pop("_status")

            def highlight_row(row):
                idx = row.name
                status = status_col.iloc[idx]
                if status == "mismatch":
                    return ["background-color: #ffcccc"] * len(row)
                elif status == "match":
                    return ["background-color: #ccffcc"] * len(row)
                elif status == "single":
                    return ["background-color: #fff3cc"] * len(row)
                return [""] * len(row)

            styled = df.style.apply(highlight_row, axis=1)
            st.dataframe(styled, use_container_width=True, hide_index=True)

            # Summary
            statuses = status_col.tolist()
            mismatches = statuses.count("mismatch")
            matches = statuses.count("match")
            missing = statuses.count("missing") + statuses.count("single")

            col1, col2, col3 = st.columns(3)
            col1.metric("Consistent", matches)
            col2.metric("Mismatches", mismatches)
            col3.metric("Missing/Partial", missing)

            if mismatches > 0:
                st.warning(f"Found {mismatches} field(s) with inconsistencies across documents.")
            else:
                st.success("All common fields are consistent across documents.")
