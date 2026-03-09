"""
Courseware Audit Module

Upload a CP (source of truth) + any AP/FG/LG/LP documents.
Cross-checks each document against the CP and auto-fixes mismatches.
"""

import streamlit as st
import os
import asyncio
import tempfile
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


def _extract_cp_fields(cp_context: dict) -> dict:
    """Extract audit-comparable fields from CP interpreter output (source of truth)."""
    learning_units = cp_context.get("Learning_Units", [])

    # Learning outcomes
    los = []
    for lu in learning_units:
        lo = lu.get("LO", "")
        if lo:
            los.append(lo)

    # All topics across all LUs
    topics = []
    for lu in learning_units:
        for topic in lu.get("Topics", []):
            title = topic.get("Topic_Title", "")
            if title:
                topics.append(title)

    # LU structure: number of LUs, topics per LU
    lu_structure = []
    for i, lu in enumerate(learning_units):
        lu_topics = [t.get("Topic_Title", "") for t in lu.get("Topics", []) if t.get("Topic_Title")]
        lu_structure.append({
            "lu_number": i + 1,
            "lo": lu.get("LO", ""),
            "topic_count": len(lu_topics),
            "topic_titles": lu_topics,
        })

    # Assessment methods
    assessment_methods = cp_context.get("Assessment_Methods", [])

    # Durations
    durations = {
        "training_hours": cp_context.get("Total_Training_Hours"),
        "assessment_hours": cp_context.get("Total_Assessment_Hours"),
        "total_hours": cp_context.get("Total_Course_Duration_Hours"),
    }

    return {
        "tgs_ref_code": cp_context.get("TGS_Ref_No"),
        "course_title": cp_context.get("Course_Title"),
        "company_name": cp_context.get("Name_of_Organisation"),
        "tsc_ref_code": cp_context.get("TSC_Code"),
        "tsc_title": cp_context.get("TSC_Title"),
        "num_lus": len(learning_units),
        "learning_outcomes": los,
        "lu_structure": lu_structure,
        "durations": durations,
        "topics": topics,
        "assessment_methods": assessment_methods,
        "instructional_methods": [],  # CP may not have this
    }


def _normalize(val):
    """Normalize a string for comparison — case-insensitive, strip punctuation."""
    if val is None:
        return ""
    import re
    s = str(val).strip().lower()
    # Remove trailing dots/periods (e.g., "LTD." → "LTD")
    s = re.sub(r'\.+$', '', s)
    # Normalize internal periods in abbreviations (e.g., "PTE. LTD" → "PTE LTD")
    s = s.replace('.', '')
    # Normalize hyphens to spaces (e.g., "Role-Play" → "Role Play")
    s = s.replace('-', ' ')
    # Remove parenthetical abbreviations (e.g., "Written Exam (WE)" → "Written Exam")
    s = re.sub(r'\s*\([^)]*\)\s*', ' ', s)
    # Remove topic/LO number prefixes (e.g., "T1: Topic Name" → "Topic Name", "LO1: ..." → "...")
    s = re.sub(r'^(t\d+|lo\d+|lu\d+|topic\s*\d+)\s*[:.\-]\s*', '', s)
    # Collapse multiple spaces
    s = re.sub(r'\s+', ' ', s).strip()
    return s


def _normalize_number(val_str):
    """Extract numeric value from a duration string like '22 hrs', '22.0 hrs', '2'."""
    import re
    if not val_str:
        return None
    # Find the first number (int or float)
    match = re.search(r'(\d+\.?\d*)', str(val_str))
    if match:
        num = float(match.group(1))
        # Return as int if whole number (22.0 → 22)
        return int(num) if num == int(num) else num
    return None


def _compare_to_cp(cp_val, doc_val, field_type):
    """Compare a document field value against CP (source of truth).
    Returns (status, detail)."""
    if field_type == "string":
        cp_norm = _normalize(cp_val)
        doc_norm = _normalize(doc_val)
        if not cp_norm and not doc_norm:
            return "missing", "Not in CP or document"
        if not doc_norm:
            return "missing_in_doc", "Missing in document"
        if not cp_norm:
            return "skip", "Not in CP"
        if cp_norm == doc_norm:
            return "match", "Matches CP"
        return "mismatch", "Does NOT match CP"

    elif field_type == "list":
        cp_set = set(_normalize(v) for v in (cp_val or []) if v)
        doc_set = set(_normalize(v) for v in (doc_val or []) if v)
        if not cp_set and not doc_set:
            return "missing", "Not in CP or document"
        if not doc_set:
            return "missing_in_doc", "Missing in document"
        if not cp_set:
            return "skip", "Not in CP"
        if cp_set == doc_set:
            return "match", "Matches CP"
        # Check subset relationships
        missing = cp_set - doc_set
        extra = doc_set - cp_set
        details = []
        if missing:
            details.append(f"Missing: {len(missing)} item(s)")
        if extra:
            details.append(f"Extra: {len(extra)} item(s)")
        return "mismatch", "; ".join(details) if details else "Does NOT match CP"

    elif field_type == "list_count":
        # Only compare the count of items, not the content
        cp_count = len(cp_val) if isinstance(cp_val, list) else 0
        doc_count = len(doc_val) if isinstance(doc_val, list) else 0
        if cp_count == 0 and doc_count == 0:
            return "missing", "Not in CP or document"
        if doc_count == 0:
            return "missing_in_doc", "Missing in document"
        if cp_count == 0:
            return "skip", "Not in CP"
        if cp_count == doc_count:
            return "match", f"Matches CP ({cp_count})"
        return "mismatch", f"CP={cp_count} vs Doc={doc_count}"

    elif field_type == "duration":
        # Compare each duration field individually (training, assessment, total)
        if not isinstance(cp_val, dict) and not isinstance(doc_val, dict):
            return "missing", "Not in CP or document"

        cp_dict = cp_val if isinstance(cp_val, dict) else {}
        doc_dict = doc_val if isinstance(doc_val, dict) else {}

        mismatches = []
        matches = 0
        for key in ["training_hours", "assessment_hours", "total_hours"]:
            cp_num = _normalize_number(cp_dict.get(key))
            doc_num = _normalize_number(doc_dict.get(key))
            if cp_num is None and doc_num is None:
                continue
            if cp_num is not None and doc_num is not None:
                if cp_num == doc_num:
                    matches += 1
                else:
                    label = key.replace("_", " ").title()
                    mismatches.append(f"{label}: CP={cp_num} vs Doc={doc_num}")
            elif cp_num is not None and doc_num is None:
                # Doc missing this field — not a mismatch if other fields match
                continue

        if mismatches:
            return "mismatch", "; ".join(mismatches)
        if matches > 0:
            return "match", "Matches CP"
        return "missing", "Not in CP or document"

    elif field_type == "count":
        # Compare simple counts (number of LUs, etc.)
        cp_num = int(cp_val) if cp_val is not None else None
        doc_num = int(doc_val) if doc_val is not None else None
        if cp_num is None and doc_num is None:
            return "missing", "Not in CP or document"
        if doc_num is None:
            return "missing_in_doc", "Missing in document"
        if cp_num is None:
            return "skip", "Not in CP"
        if cp_num == doc_num:
            return "match", "Matches CP"
        return "mismatch", f"CP={cp_num} vs Doc={doc_num}"

    elif field_type == "lu_structure":
        # Compare LU structure: number of LUs, topics per LU, topic titles
        cp_lus = cp_val if isinstance(cp_val, list) else []
        doc_lus = doc_val if isinstance(doc_val, list) else []
        if not cp_lus and not doc_lus:
            return "missing", "Not in CP or document"
        if not doc_lus:
            return "missing_in_doc", "Missing in document"
        if not cp_lus:
            return "skip", "Not in CP"

        issues = []

        # Check LU count
        if len(cp_lus) != len(doc_lus):
            issues.append(f"LU count: CP={len(cp_lus)} vs Doc={len(doc_lus)}")

        # Check each LU's topic count and titles
        for i in range(min(len(cp_lus), len(doc_lus))):
            cp_lu = cp_lus[i]
            doc_lu = doc_lus[i]
            cp_topics = cp_lu.get("topic_titles", [])
            doc_topics = doc_lu.get("topic_titles", [])

            if len(cp_topics) != len(doc_topics):
                issues.append(f"LU{i+1} topics: CP={len(cp_topics)} vs Doc={len(doc_topics)}")

            # Check topic title matches
            cp_topic_set = set(_normalize(t) for t in cp_topics)
            doc_topic_set = set(_normalize(t) for t in doc_topics)
            if cp_topic_set != doc_topic_set:
                missing_topics = cp_topic_set - doc_topic_set
                if missing_topics:
                    issues.append(f"LU{i+1} missing topics: {len(missing_topics)}")

        if issues:
            return "mismatch", "; ".join(issues)
        return "match", "Matches CP"

    return "unknown", ""


def _format_val(val):
    """Format a value for display in the comparison table."""
    if isinstance(val, list):
        # Check if it's lu_structure (list of dicts with lu_number)
        if val and isinstance(val[0], dict) and "lu_number" in val[0]:
            parts = []
            for lu in val:
                n = lu.get("topic_count", 0)
                parts.append(f"LU{lu['lu_number']}: {n} topics")
            return ", ".join(parts)
        return ", ".join(str(v) for v in val) if val else "-"
    elif isinstance(val, dict):
        parts = [f"{k}: {v}" for k, v in val.items() if v]
        return "; ".join(parts) if parts else "-"
    return str(val) if val else "-"


# Which doc types are expected to contain each field
# None = all doc types should have it
AUDIT_FIELDS = [
    ("TGS Ref Code", "tgs_ref_code", "string", None),
    ("Course Title", "course_title", "string", None),
    ("Company Name", "company_name", "string", None),
    ("TSC Ref Code", "tsc_ref_code", "string", ["AP", "FG", "LG"]),
    ("TSC Title", "tsc_title", "string", ["AP", "FG", "LG"]),
    ("No. of Learning Units", "num_lus", "count", ["AP", "FG", "LG", "LP"]),
    ("Learning Outcomes (Count)", "learning_outcomes", "list_count", ["AP", "FG", "LG"]),
    ("LU Structure (Topics per LU)", "lu_structure", "lu_structure", ["FG", "LG"]),
    ("Durations", "durations", "duration", None),
    ("Topics (All)", "topics", "list", None),
    ("Assessment Methods", "assessment_methods", "list", ["AP"]),
    ("Instructional Methods", "instructional_methods", "list", ["FG", "LG", "LP"]),
]


def _extract_doc_type(label: str) -> str:
    """Extract doc type (AP/FG/LG/LP) from audit label like 'LP: filename.docx'."""
    for dt in DOC_TYPES:
        if label.upper().startswith(dt):
            return dt
    return ""


def run_cp_cross_check(cp_fields: dict, doc_results: dict):
    """Compare each document's extracted fields against CP source of truth.

    Returns list of rows: [{Field, Status, CP (Source of Truth), doc1_label, doc2_label, ...}]
    """
    results = []
    for display_name, field_key, field_type, applicable_types in AUDIT_FIELDS:
        cp_val = cp_fields.get(field_key)

        row = {"Field": display_name, "CP (Source of Truth)": _format_val(cp_val)}

        worst_status = "match"
        has_applicable_doc = False

        for doc_label, doc_data in doc_results.items():
            doc_type = _extract_doc_type(doc_label)

            # Skip this field if not applicable to this doc type
            if applicable_types and doc_type and doc_type not in applicable_types:
                row[doc_label] = "N/A"
                continue

            has_applicable_doc = True
            doc_val = doc_data.get(field_key)
            status, detail = _compare_to_cp(cp_val, doc_val, field_type)
            row[doc_label] = _format_val(doc_val)

            if status == "mismatch":
                worst_status = "mismatch"
            elif status == "missing_in_doc" and worst_status != "mismatch":
                worst_status = "missing_in_doc"

        # If no documents were applicable for this field, mark as skip
        if not has_applicable_doc:
            worst_status = "skip"

        row["Status"] = "MISMATCH" if worst_status == "mismatch" else (
            "Missing in doc" if worst_status == "missing_in_doc" else (
                "N/A" if worst_status == "skip" else "Matches CP"
            )
        )
        row["_status"] = worst_status
        results.append(row)

    return results


def _fix_text_in_docx(file_bytes: bytes, replacements: list[tuple[str, str]]) -> bytes:
    """Apply text replacements to a DOCX file. Returns fixed file bytes.

    Args:
        file_bytes: Original DOCX content
        replacements: List of (old_text, new_text) pairs to replace
    """
    with tempfile.NamedTemporaryFile(delete=False, suffix=".docx") as tmp:
        tmp.write(file_bytes)
        tmp_path = tmp.name

    try:
        doc = Document(tmp_path)
        fix_count = 0

        for old_text, new_text in replacements:
            if not old_text or not new_text or old_text == new_text:
                continue

            # Replace in paragraphs
            for para in doc.paragraphs:
                if old_text in para.text:
                    for run in para.runs:
                        if old_text in run.text:
                            run.text = run.text.replace(old_text, new_text)
                            fix_count += 1

            # Replace in tables
            for table in doc.tables:
                for row in table.rows:
                    for cell in row.cells:
                        if old_text in cell.text:
                            for para in cell.paragraphs:
                                for run in para.runs:
                                    if old_text in run.text:
                                        run.text = run.text.replace(old_text, new_text)
                                        fix_count += 1

            # Replace in headers/footers
            for section in doc.sections:
                for header_footer in [section.header, section.footer]:
                    if header_footer:
                        for para in header_footer.paragraphs:
                            if old_text in para.text:
                                for run in para.runs:
                                    if old_text in run.text:
                                        run.text = run.text.replace(old_text, new_text)
                                        fix_count += 1

        # Save to bytes
        out_path = tmp_path + "_fixed.docx"
        doc.save(out_path)
        with open(out_path, "rb") as f:
            result = f.read()
        os.remove(out_path)
        return result, fix_count
    finally:
        os.remove(tmp_path)


def _build_replacements(cp_fields: dict, doc_fields: dict) -> list[tuple[str, str]]:
    """Build a list of (old_text, new_text) replacements from mismatches."""
    replacements = []

    for _, field_key, field_type, _applicable in AUDIT_FIELDS:
        cp_val = cp_fields.get(field_key)
        doc_val = doc_fields.get(field_key)
        if not cp_val or not doc_val:
            continue

        if field_type == "string":
            cp_str = str(cp_val).strip()
            doc_str = str(doc_val).strip()
            if cp_str and doc_str and _normalize(cp_str) != _normalize(doc_str):
                replacements.append((doc_str, cp_str))

        elif field_type == "duration":
            if isinstance(cp_val, dict) and isinstance(doc_val, dict):
                for dur_key in ["training_hours", "assessment_hours", "total_hours"]:
                    cv = str(cp_val.get(dur_key, "")).strip()
                    dv = str(doc_val.get(dur_key, "")).strip()
                    if cv and dv and _normalize(cv) != _normalize(dv):
                        replacements.append((dv, cv))

        # For lists (topics, LOs, assessment methods) — match by position
        elif field_type == "list":
            cp_list = cp_val if isinstance(cp_val, list) else []
            doc_list = doc_val if isinstance(doc_val, list) else []
            for i, doc_item in enumerate(doc_list):
                doc_str = str(doc_item).strip()
                if not doc_str:
                    continue
                # Try to find best match from CP
                matched = False
                for cp_item in cp_list:
                    cp_str = str(cp_item).strip()
                    if _normalize(cp_str) == _normalize(doc_str):
                        matched = True
                        break
                if not matched and i < len(cp_list):
                    # Position-based replacement
                    cp_str = str(cp_list[i]).strip()
                    if cp_str and doc_str:
                        replacements.append((doc_str, cp_str))

    return replacements


def app():
    st.title("Courseware Audit")
    st.caption("Cross-check your AP, FG, LG, LP against the CP (source of truth) and auto-fix mismatches.")

    # Initialize session state
    if "audit_cp_context" not in st.session_state:
        st.session_state.audit_cp_context = None
    if "audit_docs" not in st.session_state:
        st.session_state.audit_docs = {}
    if "audit_results" not in st.session_state:
        st.session_state.audit_results = {}
    if "audit_cp_fields" not in st.session_state:
        st.session_state.audit_cp_fields = {}
    if "audit_comparison" not in st.session_state:
        st.session_state.audit_comparison = []

    # Prompt templates (editable, collapsed)
    from utils.prompt_template_editor import render_prompt_templates
    render_prompt_templates("courseware_audit", "Prompt Templates (Courseware Audit)")

    # ── CP Source of Truth (from Extract Course Info page) ──
    _existing_cp = st.session_state.get("extracted_course_info")
    if not _existing_cp:
        st.warning(
            "No CP data found. Please go to **Extract Course Info** first, "
            "upload your CP, and extract the course information. "
            "Then come back here to audit your documents."
        )
        return

    # Only initialize from CP data on first load — don't overwrite edits
    if st.session_state.audit_cp_context is None:
        st.session_state.audit_cp_context = _existing_cp

    if st.session_state.audit_cp_context:
        cp_ctx = st.session_state.audit_cp_context

        # Editable company name override
        current_company = cp_ctx.get("Name_of_Organisation", "")
        if "audit_company_override" not in st.session_state:
            st.session_state.audit_company_override = current_company

        new_company = st.text_input(
            "Company Name (editable — overrides CP value for audit)",
            value=st.session_state.audit_company_override,
            key="audit_company_input",
        )
        if new_company != st.session_state.audit_company_override:
            st.session_state.audit_company_override = new_company

        # Apply company override to CP context for audit
        cp_ctx_for_audit = dict(cp_ctx)
        cp_ctx_for_audit["Name_of_Organisation"] = st.session_state.audit_company_override

        cp_fields = _extract_cp_fields(cp_ctx_for_audit)
        st.session_state.audit_cp_fields = cp_fields

        with st.expander("CP Source of Truth (extracted fields)", expanded=False):
            st.json(cp_fields)

        # ── Upload documents to audit ──
        st.subheader("Upload Documents to Audit")
        st.write("Upload your AP, FG, LG, and/or LP documents to check against the CP.")

        uploaded_files = st.file_uploader(
            "Upload courseware documents",
            type=["docx", "pdf"],
            accept_multiple_files=True,
            key="audit_doc_uploader",
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
                        key=f"audit_type_{fname}",
                        label_visibility="collapsed",
                    )

                st.session_state.audit_docs[f"{doc_type}: {fname}"] = {
                    "file": uploaded_file,
                    "type": doc_type,
                    "name": fname,
                }

        # ── Run Audit ──
        if st.button("Run Audit Against CP", type="primary"):
            docs = st.session_state.audit_docs
            if not docs:
                st.error("Please upload at least 1 document to audit.")
            else:
                from courseware_agents.audit.audit_agent import extract_audit_fields

                # Extract text + run audit agent on each document
                audit_results = {}
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

                    if not text.strip():
                        st.warning(f"No text extracted from {fname}")
                        continue

                    with st.spinner(f"Auditing {label} against CP..."):
                        try:
                            result = asyncio.run(extract_audit_fields(text, doc_info["type"]))
                            audit_results[label] = result
                        except Exception as e:
                            st.error(f"Error auditing {label}: {e}")
                            audit_results[label] = {}

                st.session_state.audit_results = audit_results

                # Run comparison against CP
                comparison = run_cp_cross_check(cp_fields, audit_results)
                st.session_state.audit_comparison = comparison

                st.success(f"Audit complete. Checked {len(audit_results)} document(s) against CP.")
                st.rerun()

    # ── Display Results ──
    if st.session_state.audit_comparison:
        comparison = st.session_state.audit_comparison
        audit_results = st.session_state.audit_results
        cp_fields = st.session_state.audit_cp_fields

        st.subheader("Audit Results — CP vs Documents")

        # Build DataFrame
        df = pd.DataFrame(comparison)
        status_col = df.pop("_status")

        def highlight_row(row):
            idx = row.name
            status = status_col.iloc[idx]
            if status == "mismatch":
                return ["background-color: #fca5a5; color: #000000"] * len(row)
            elif status == "match":
                return ["background-color: #86efac; color: #000000"] * len(row)
            elif status in ("missing_in_doc", "skip"):
                return ["background-color: #fde68a; color: #000000"] * len(row)
            return [""] * len(row)

        styled = df.style.apply(highlight_row, axis=1)
        st.dataframe(styled, use_container_width=True, hide_index=True)

        # Summary metrics
        statuses = status_col.tolist()
        mismatches = statuses.count("mismatch")
        matches = statuses.count("match")
        missing = statuses.count("missing_in_doc") + statuses.count("missing") + statuses.count("skip")

        col1, col2, col3 = st.columns(3)
        col1.metric("Matches CP", matches)
        col2.metric("Mismatches", mismatches)
        col3.metric("Missing/Skipped", missing)

        # ── Auto-Fix ──
        if mismatches > 0:
            st.warning(f"Found {mismatches} field(s) that don't match the CP.")

            st.subheader("Auto-Fix Mismatches")
            st.write("Replace mismatched values in your documents with the correct CP values.")

            if st.button("Auto-Fix All Documents", type="primary"):
                fixed_files = {}
                docs = st.session_state.audit_docs

                for label, doc_info in docs.items():
                    fname = doc_info["name"]
                    ext = fname.rsplit(".", 1)[-1].lower()

                    if ext != "docx":
                        st.warning(f"Cannot auto-fix {fname} — only DOCX files are supported for auto-fix.")
                        continue

                    doc_fields = audit_results.get(label, {})
                    replacements = _build_replacements(cp_fields, doc_fields)

                    if not replacements:
                        st.info(f"{label}: No fixable mismatches found.")
                        continue

                    with st.spinner(f"Fixing {fname}... ({len(replacements)} replacement(s))"):
                        file_bytes = doc_info["file"].getvalue()
                        try:
                            fixed_bytes, fix_count = _fix_text_in_docx(file_bytes, replacements)
                            fixed_files[label] = {
                                "bytes": fixed_bytes,
                                "name": fname.replace(".docx", "_FIXED.docx"),
                                "replacements": replacements,
                                "fix_count": fix_count,
                            }
                        except Exception as e:
                            st.error(f"Error fixing {fname}: {e}")

                if fixed_files:
                    st.success(f"Fixed {len(fixed_files)} document(s)!")

                    for label, fix_info in fixed_files.items():
                        with st.expander(f"{label} — {fix_info['fix_count']} fix(es) applied"):
                            for old_text, new_text in fix_info["replacements"]:
                                st.markdown(f"- ~~{old_text}~~ → **{new_text}**")

                            st.download_button(
                                f"Download {fix_info['name']}",
                                data=fix_info["bytes"],
                                file_name=fix_info["name"],
                                mime="application/vnd.openxmlformats-officedocument.wordprocessingml.document",
                                key=f"download_{label}",
                            )
                else:
                    st.info("No documents needed fixing or only non-DOCX files were uploaded.")
        else:
            st.success("All documents match the CP perfectly!")

        # Raw extraction details
        with st.expander("Raw Extracted Fields (per document)", expanded=False):
            for label, data in audit_results.items():
                st.markdown(f"**{label}**")
                st.json(data)
