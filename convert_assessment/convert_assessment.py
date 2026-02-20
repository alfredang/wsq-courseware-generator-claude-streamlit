"""
Assessment Conversion Module

Streamlit page for batch converting existing assessment documents to the
standardised WSQ client-ready format.

Workflow:
1. Upload multiple assessment DOCX files at once
2. Set preferences (duration override, etc.)
3. AI extracts structured data from each file
4. Rebuild all documents in WSQ format
5. Download all as ZIP
"""

import streamlit as st
import os
import io
import json
import tempfile
import zipfile

from docx import Document
from courseware_agents.base import run_agent_json
from generate_assessment.assessment_generation import (
    _build_assessment_doc,
    _get_assessment_full_name,
)


EXTRACTION_SYSTEM_PROMPT = """You are an expert at reading assessment documents and extracting structured data.

You will receive the full text content of an assessment document (question paper or answer key).
Extract ALL information into the JSON schema below.

CRITICAL RULES:
- Respond with ONLY a valid JSON object. No preamble or commentary.
- Start your response with { and end with }.
- Do NOT use tools — all data is provided in the prompt.
- Extract EVERY question found in the document. Do not skip any.
- For knowledge_id, look for patterns like (K1), (K2), K1, K2 near the question.
- For ability_id, look for patterns like (A1), (A2), A1, A2 near the question.
- For learning_outcome_id, look for patterns like LO1, LO2 near the question.
- If the document contains answers, extract them. If not, leave answer as empty list.
- Detect the assessment type from the document title or content (e.g., SAQ, PP, CS, OQ).
- Detect whether this is a question paper (no answers) or answer key (has answers).

JSON Schema:
{
    "course_title": "string (the course name from the document title)",
    "assessment_type": "string (e.g., WA (SAQ), PP, CS, OQ)",
    "assessment_code": "string (e.g., WA-SAQ, PP, CS, OQ)",
    "duration": "string (e.g., 60 mins, 1 hr) - extract from document or use empty string",
    "has_answers": true/false,
    "questions": [
        {
            "scenario": "string (the scenario text, or empty string if none)",
            "question_statement": "string (the question text)",
            "knowledge_id": "string (e.g., K1) or null",
            "ability_id": ["string (e.g., A1)"] or null,
            "learning_outcome_id": "string (e.g., LO1) or null",
            "answer": ["string (answer bullet point 1)", "string (answer bullet point 2)"]
        }
    ]
}
"""


def _extract_docx_text(docx_file) -> str:
    """Extract all text from a DOCX file (uploaded file or path)."""
    doc = Document(docx_file)
    all_text = []

    for para in doc.paragraphs:
        if para.text.strip():
            all_text.append(para.text.strip())

    for table in doc.tables:
        for row in table.rows:
            row_text = []
            for cell in row.cells:
                if cell.text.strip():
                    row_text.append(cell.text.strip())
            if row_text:
                all_text.append(" | ".join(row_text))

    return "\n".join(all_text)


async def _extract_assessment_data(doc_text: str) -> dict:
    """Use Claude Agent SDK to extract structured assessment data from document text."""
    prompt = f"""Extract the structured assessment data from this document text.

--- DOCUMENT TEXT ---
{doc_text}
--- END ---

Return ONLY the JSON object following the schema in your instructions."""

    result = await run_agent_json(
        prompt=prompt,
        system_prompt=EXTRACTION_SYSTEM_PROMPT,
        tools=[],
        max_turns=3,
    )
    return result


def app():
    st.title("Convert Assessment")
    st.markdown("Upload existing assessment documents to batch convert them to the standardised WSQ client-ready format.")

    # File uploader - multiple DOCX files
    uploaded_files = st.file_uploader(
        "Upload Assessment Documents (.docx)",
        type=["docx"],
        accept_multiple_files=True,
        key="convert_assessment_upload",
        help="Upload all your assessment DOCX files at once (question papers and answer keys)"
    )

    if not uploaded_files:
        st.info("Upload your assessment DOCX files — you can select multiple files at once. They will all be converted and downloaded as a ZIP.")
        return

    # Show uploaded files
    st.markdown(f"**{len(uploaded_files)} file(s) uploaded:**")
    for f in uploaded_files:
        st.markdown(f"- {f.name}")

    # Convert button
    if st.button("Convert All to WSQ Format", type="primary"):
        converted_files = {}
        progress_bar = st.progress(0)
        status_text = st.empty()
        total = len(uploaded_files)

        for i, uploaded_file in enumerate(uploaded_files):
            status_text.text(f"Converting {i+1}/{total}: {uploaded_file.name}...")
            progress_bar.progress((i) / total)

            try:
                # Step 1: Extract text from DOCX
                uploaded_file.seek(0)
                doc_text = _extract_docx_text(uploaded_file)

                if not doc_text.strip():
                    st.error(f"Could not extract text from {uploaded_file.name}")
                    continue

                # Step 2: AI extracts structured data
                import asyncio
                extracted = asyncio.run(_extract_assessment_data(doc_text))

                if not extracted or not isinstance(extracted, dict):
                    st.error(f"AI could not parse {uploaded_file.name}")
                    continue

                # Step 3: Build context from extracted data
                course_title = extracted.get('course_title', '')
                assessment_code = extracted.get('assessment_code', extracted.get('assessment_type', 'SAQ'))
                duration = extracted.get('duration', '60 mins')
                questions = extracted.get('questions', [])
                has_answers = extracted.get('has_answers', False)

                if not questions:
                    st.warning(f"No questions found in {uploaded_file.name}")
                    continue

                context = {
                    'course_title': course_title,
                    'duration': duration,
                    'assessment_code': assessment_code,
                }

                # Step 4: Rebuild document in WSQ format
                assessment_type = extracted.get('assessment_type', assessment_code)
                new_doc = _build_assessment_doc(context, assessment_type, questions, include_answers=has_answers)

                # Save to bytes
                tmp = tempfile.NamedTemporaryFile(delete=False, suffix=".docx")
                tmp.close()
                new_doc.save(tmp.name)
                with open(tmp.name, 'rb') as f:
                    doc_bytes = f.read()
                os.unlink(tmp.name)

                # Build output filename
                base_name = os.path.splitext(uploaded_file.name)[0]
                out_name = f"{base_name} (WSQ Format).docx"
                converted_files[out_name] = doc_bytes

                doc_type = "Answer Key" if has_answers else "Question Paper"
                st.success(f"{uploaded_file.name} — {len(questions)} questions ({doc_type})")

            except Exception as e:
                st.error(f"Error converting {uploaded_file.name}: {e}")

        progress_bar.progress(1.0)
        status_text.text(f"Done! {len(converted_files)}/{total} files converted.")

        # Store converted files in session state
        if converted_files:
            st.session_state['converted_assessment_files'] = converted_files
            st.rerun()

    # Download section
    converted = st.session_state.get('converted_assessment_files', {})
    if converted:
        st.markdown("---")
        st.subheader(f"Download Converted Files ({len(converted)} files)")

        # Always show ZIP download
        zip_buffer = io.BytesIO()
        with zipfile.ZipFile(zip_buffer, "w", zipfile.ZIP_DEFLATED) as zipf:
            for name, data in converted.items():
                zipf.writestr(name, data)
        zip_buffer.seek(0)

        st.download_button(
            label=f"Download All ({len(converted)} files) as ZIP",
            data=zip_buffer.getvalue(),
            file_name="converted_assessments.zip",
            mime="application/zip",
        )
