"""
Assessment Generator Module

Streamlit page for generating assessment documents (SAQ, PP, CS, etc.)
from a Facilitator Guide (FG) document.

Workflow:
1. Upload FG → Parse to text (pure Python, no AI)
2. Load pre-generated assessment context JSON (from Claude Code skill)
3. Fill assessment templates → Download

All AI reasoning (FG interpretation, assessment generation) is handled by
Claude Code skills using subscription. No API tokens needed.
"""

import streamlit as st
import os
import io
import zipfile
import json
import tempfile
import re
import hashlib

from copy import deepcopy
from docx import Document
from docx.shared import Pt, Inches, RGBColor, Cm
from docx.enum.text import WD_ALIGN_PARAGRAPH
from docx.oxml.ns import qn, nsdecls
from docx.oxml import parse_xml
from company.company_manager import get_selected_company, get_company_template

# Try to import pymupdf, fallback to pypdf2
PYMUPDF_AVAILABLE = False
try:
    import pymupdf
    PYMUPDF_AVAILABLE = True
except ImportError:
    try:
        from PyPDF2 import PdfReader
    except ImportError:
        pass

# Initialize session state keys
if 'fg_data' not in st.session_state:
    st.session_state['fg_data'] = None
if 'assessment_generated_files' not in st.session_state:
    st.session_state['assessment_generated_files'] = {}


################################################################################
# Helper function for PDF text extraction
################################################################################
def get_pdf_page_count(pdf_path):
    """Get total page count of a PDF file."""
    if PYMUPDF_AVAILABLE:
        doc = pymupdf.open(pdf_path)
        total_pages = doc.page_count
        doc.close()
        return total_pages
    else:
        from PyPDF2 import PdfReader
        reader = PdfReader(pdf_path)
        return len(reader.pages)


def extract_pdf_text(pdf_path):
    """Extract text from PDF using PyMuPDF or PyPDF2 fallback."""
    if PYMUPDF_AVAILABLE:
        doc = pymupdf.open(pdf_path)
        text_content = []
        for page_num in range(doc.page_count):
            page = doc[page_num]
            text = page.get_text()
            if text.strip():
                text_content.append({"page": page_num + 1, "text": text})
        doc.close()
        return text_content
    else:
        from PyPDF2 import PdfReader
        reader = PdfReader(pdf_path)
        text_content = []
        for page_num, page in enumerate(reader.pages):
            text = page.extract_text() or ""
            if text.strip():
                text_content.append({"page": page_num + 1, "text": text})
        return text_content


################################################################################
# Parse Facilitator Guide Document (Pure Python, no AI)
################################################################################
def parse_fg(fg_path):
    """Parse Facilitator Guide document using python-docx."""
    # Create cache directory
    cache_dir = ".output/fg_cache"
    os.makedirs(cache_dir, exist_ok=True)

    # Generate cache key from file content hash
    with open(fg_path, 'rb') as f:
        file_hash = hashlib.md5(f.read()).hexdigest()
    cache_path = os.path.join(cache_dir, f"{file_hash}.json")

    # Check cache first
    if os.path.exists(cache_path):
        print(f"Found cached FG parse result (hash: {file_hash})")
        with open(cache_path, 'r', encoding='utf-8') as f:
            return f.read()

    # Parse with python-docx
    print(f"Parsing FG document...")
    doc = Document(fg_path)

    # Extract all text from paragraphs and tables
    all_text = []
    for para in doc.paragraphs:
        if para.text.strip():
            all_text.append(para.text.strip())

    # Extract text from tables
    for table in doc.tables:
        for row in table.rows:
            row_text = []
            for cell in row.cells:
                if cell.text.strip():
                    row_text.append(cell.text.strip())
            if row_text:
                all_text.append(" | ".join(row_text))

    # Create JSON structure for parsed content
    parsed_content = [{"pages": [{"page": 1, "text": "\n".join(all_text)}]}]
    result_json = json.dumps(parsed_content)

    # Save to cache
    with open(cache_path, 'w', encoding='utf-8') as f:
        f.write(result_json)
    print(f"Cached FG parse result (hash: {file_hash})")

    return result_json


def extract_master_k_a_list(fg_markdown):
    """
    Extracts the master list of K and A statements from the FG markdown using regex.
    Returns a dict with 'knowledge' and 'abilities' lists.
    """
    master_k = []
    master_a = []

    # Parse JSON to extract all text content from pages
    try:
        fg_json = json.loads(fg_markdown)
        all_text = ""
        if isinstance(fg_json, list):
            for doc in fg_json:
                if "pages" in doc:
                    for page in doc["pages"]:
                        if "text" in page:
                            all_text += page["text"] + "\n"
    except json.JSONDecodeError:
        all_text = fg_markdown

    # Try multiple patterns to match different formats
    patterns_k = [
        r'(K\d+):\s*(.+?)(?=\n(?:K\d+:|A\d+:|TSC |##|\n\n|$))',
        r'\*\*?(K\d+):\*\*?\s*(.+?)(?=\n\*\*?(?:K\d+:|A\d+:)|\n\n|$)',
        r'(K\d+)\s*[-–]\s*(.+?)(?=\n(?:K\d+|A\d+)|\n\n|$)',
    ]

    patterns_a = [
        r'(A\d+):\s*(.+?)(?=\n(?:K\d+:|A\d+:|TSC |##|\n\n|$))',
        r'\*\*?(A\d+):\*\*?\s*(.+?)(?=\n\*\*?(?:K\d+:|A\d+:)|\n\n|$)',
        r'(A\d+)\s*[-–]\s*(.+?)(?=\n(?:K\d+|A\d+)|\n\n|$)',
    ]

    for pattern in patterns_k:
        for match in re.finditer(pattern, all_text, re.DOTALL | re.MULTILINE):
            k_id = match.group(1)
            k_text = match.group(2).strip().replace('\n', ' ').replace('*', '')
            if not any(k['id'] == k_id for k in master_k):
                master_k.append({"id": k_id, "text": k_text})

    for pattern in patterns_a:
        for match in re.finditer(pattern, all_text, re.DOTALL | re.MULTILINE):
            a_id = match.group(1)
            a_text = match.group(2).strip().replace('\n', ' ').replace('*', '')
            if not any(a['id'] == a_id for a in master_a):
                master_a.append({"id": a_id, "text": a_text})

    print(f"Master K/A List - Found {len(master_k)} K statements, {len(master_a)} A statements")
    return {"knowledge": master_k, "abilities": master_a}


################################################################################
# Parse Slide Deck Document (Pure Python, no AI)
################################################################################
def parse_slides(slides_path):
    """Parse PDF slides and extract text content."""
    print(f"Parsing slides from: {slides_path}")

    total_pages = get_pdf_page_count(slides_path)
    start_page = min(17, total_pages)
    end_page = max(start_page, total_pages - 6)

    slides_content = []

    if PYMUPDF_AVAILABLE:
        doc = pymupdf.open(slides_path)
        for page_num in range(start_page - 1, end_page):
            if page_num < doc.page_count:
                page = doc[page_num]
                text = page.get_text()
                if text.strip():
                    slides_content.append({"page": page_num + 1, "text": text.strip()})
        doc.close()
    else:
        from PyPDF2 import PdfReader
        reader = PdfReader(slides_path)
        for page_num in range(start_page - 1, end_page):
            if page_num < len(reader.pages):
                text = reader.pages[page_num].extract_text() or ""
                if text.strip():
                    slides_content.append({"page": page_num + 1, "text": text.strip()})

    print(f"Extracted text from {len(slides_content)} pages")
    return {"slides": slides_content, "total_pages": total_pages}


################################################################################
# Utility function to ensure answers are always a list
################################################################################
def _ensure_list(answer):
    if isinstance(answer, list):
        return answer
    elif isinstance(answer, str):
        return [answer]
    return []


################################################################################
# Assessment document formatting helpers (Standard WSQ Format)
################################################################################

# Assessment type code → full display name mapping
_TYPE_DISPLAY_MAP = {
    "WA (SAQ)": "Written Assessment (SAQ)",
    "WA-SAQ": "Written Assessment (SAQ)",
    "PP": "Practical Performance Assessment",
    "CS": "Case Study Assessment",
    "PRJ": "Project Assessment",
    "ASGN": "Assignment Assessment",
    "OI": "Oral Interview Assessment",
    "DEM": "Demonstration Assessment",
    "RP": "Role Play Assessment",
    "OQ": "Oral Questioning Assessment",
}


def _get_assessment_type_display(assessment_type: str) -> str:
    """Map assessment type codes to full display names for document titles."""
    return _TYPE_DISPLAY_MAP.get(assessment_type, f"{assessment_type} Assessment")


def _is_saq_type(assessment_type: str) -> bool:
    """Check if assessment type is SAQ (written short-answer questions)."""
    return assessment_type in ("WA (SAQ)", "WA-SAQ")


def _setup_page(doc):
    """Configure A4 page with standard assessment margins."""
    section = doc.sections[0]
    section.top_margin = Inches(0.30)
    section.bottom_margin = Inches(0.30)
    section.left_margin = Inches(0.50)
    section.right_margin = Inches(0.50)


def _add_para(doc, text, size=11, bold=False, alignment=None):
    """Add a paragraph with Arial font styling."""
    p = doc.add_paragraph()
    if alignment is not None:
        p.alignment = alignment
    run = p.add_run(text)
    run.font.name = 'Arial'
    run.font.size = Pt(size)
    run.bold = bold
    return p


def _add_bordered_table(doc, cell_paragraphs=None):
    """Add a 1x1 table with black borders matching the standard format.

    Args:
        doc: Document instance.
        cell_paragraphs: List of strings for cell content.
            If None, adds empty lines for a write-in answer box.
    """
    table = doc.add_table(rows=1, cols=1)

    # Set explicit black borders via XML (matching reference docs)
    tbl = table._tbl
    tblPr = tbl.tblPr
    if tblPr is None:
        tblPr = parse_xml(f'<w:tblPr {nsdecls("w")}/>')
        tbl.insert(0, tblPr)
    borders = parse_xml(
        f'<w:tblBorders {nsdecls("w")}>'
        '  <w:top w:val="single" w:sz="8" w:space="0" w:color="000000"/>'
        '  <w:left w:val="single" w:sz="8" w:space="0" w:color="000000"/>'
        '  <w:bottom w:val="single" w:sz="8" w:space="0" w:color="000000"/>'
        '  <w:right w:val="single" w:sz="8" w:space="0" w:color="000000"/>'
        '  <w:insideH w:val="single" w:sz="8" w:space="0" w:color="000000"/>'
        '  <w:insideV w:val="single" w:sz="8" w:space="0" w:color="000000"/>'
        '</w:tblBorders>'
    )
    tblPr.append(borders)

    cell = table.cell(0, 0)

    if cell_paragraphs is None:
        # Empty answer box for question papers
        cell.text = ""
        for _ in range(6):
            cell.add_paragraph("")
    else:
        # Filled answer box for answer keys
        cell.text = ""
        for i, text in enumerate(cell_paragraphs):
            if i == 0:
                p = cell.paragraphs[0]
                run = p.add_run(text)
            else:
                p = cell.add_paragraph()
                run = p.add_run(text)
            run.font.name = 'Arial'
            run.font.size = Pt(11)

    return table


def _get_competency_tag(question: dict, assessment_type: str) -> str:
    """Build competency tag like (K1) or (A1) for the question text."""
    if _is_saq_type(assessment_type):
        kid = question.get('knowledge_id', '')
        if kid:
            return f" ({kid})"
    else:
        aids = question.get('ability_id', [])
        if isinstance(aids, str):
            aids = [aids]
        if aids:
            return f" ({', '.join(aids)})"
    return ""


################################################################################
# Generate documents (Question and Answer papers) - Standard WSQ Format
################################################################################
def _build_assessment_doc(context: dict, assessment_type: str, questions: list, include_answers: bool) -> Document:
    """Build an assessment Word document following the WSQ standard format.

    Question papers include: Title, Section A (Trainee Info), Section B
    (Instructions), Section C (Questions with empty answer boxes), and
    Assessor Sign-off.

    Answer keys include: Title and Questions with filled answer tables.
    """
    doc = Document()

    # Set default font to Arial 11pt
    style = doc.styles['Normal']
    style.font.name = 'Arial'
    style.font.size = Pt(11)

    _setup_page(doc)

    course_title = context.get('course_title', '')
    duration = context.get('duration', '')
    display_type = _get_assessment_type_display(assessment_type)
    is_saq = _is_saq_type(assessment_type)

    # ── Title ──
    if include_answers:
        _add_para(doc, f"Answers to {course_title}", size=18, bold=True,
                  alignment=WD_ALIGN_PARAGRAPH.CENTER)
    else:
        _add_para(doc, course_title, size=18, bold=True,
                  alignment=WD_ALIGN_PARAGRAPH.CENTER)

    _add_para(doc, display_type, size=18, bold=True,
              alignment=WD_ALIGN_PARAGRAPH.CENTER)

    if not include_answers:
        # ── Section A: Trainee Information ──
        doc.add_paragraph()
        _add_para(doc, "A: Trainee Information:", bold=True)
        doc.add_paragraph()
        _add_para(doc, "Trainee Name (as Per NRIC): _______________________________")
        doc.add_paragraph()
        _add_para(doc, "Last three digits and alphabet of NRIC/FIN: _________________")
        doc.add_paragraph()
        _add_para(doc, "Date: __________________")
        doc.add_paragraph()

        # ── Section B: Assessment Instruction ──
        _add_para(doc, "B: Assessment Instruction", bold=True)
        doc.add_paragraph()

        if is_saq:
            _add_para(doc, "This is the Written Assessment (Q&A)")
        else:
            _add_para(doc, f"This is a {display_type}")

        _add_para(doc, f"Duration: {duration}")
        doc.add_paragraph()

        num_questions = len(questions)
        if is_saq:
            _add_para(doc, f"1. The assessor will pass the questions in hard copy to you. "
                      f"There are {num_questions} questions. You need to answer all the questions.")
            _add_para(doc, "2. This is an open-book exam that must be completed individually.")
            _add_para(doc, "3. You need to get all answers correct to be competent.")
        else:
            _add_para(doc, "1. The assessor will pass the case study in hard copy to you.")
            _add_para(doc, "2. This is an open-book exam that must be completed individually.")

        doc.add_paragraph()
        _add_para(doc, "Submission Procedure:")
        _add_para(doc, "1. Please pass the hard copy to the assessor after completion.")
        doc.add_paragraph()

        # ── Section C: Questions ──
        if is_saq:
            _add_para(doc, "C: Questions and Answers", bold=True)
        else:
            _add_para(doc, "C. Practical Performance", bold=True)
        doc.add_paragraph()

        # PP/CS: case study scenario before questions
        if not is_saq and questions:
            scenario = questions[0].get('scenario', '')
            if scenario:
                _add_para(doc, "Case Study 1:", bold=True)
                _add_para(doc, scenario)
                doc.add_paragraph()

        # Questions with empty answer boxes
        for idx, q in enumerate(questions, 1):
            question_text = q.get('question_statement', q.get('question', ''))
            tag = _get_competency_tag(q, assessment_type)
            _add_para(doc, f"Q{idx}. {question_text}{tag}")
            _add_bordered_table(doc)
            doc.add_paragraph()

        # ── Assessor Sign-off ──
        doc.add_paragraph()
        _add_para(doc, "_" * 74, bold=True)
        _add_para(doc, "For Official Use Only", bold=True)
        doc.add_paragraph()
        _add_para(doc, "Grade: __________ (C / NYC)")
        doc.add_paragraph()
        doc.add_paragraph()
        _add_para(doc, "Assessor Name: _______________\t\tAssessor NRIC: _____________")
        doc.add_paragraph()
        doc.add_paragraph()
        _add_para(doc, "Date: ________________________\t\tSignature:  _________________")

    else:
        # ── Answer Key: questions with filled answer tables ──
        doc.add_paragraph()
        for idx, q in enumerate(questions, 1):
            question_text = q.get('question_statement', q.get('question', ''))
            tag = _get_competency_tag(q, assessment_type)
            _add_para(doc, f"Q{idx}. {question_text}{tag}")

            answers = _ensure_list(q.get('answer', []))
            cell_lines = ["Suggestive answers (not exhaustive):", ""]
            for ans in answers:
                cell_lines.append(str(ans))

            _add_bordered_table(doc, cell_paragraphs=cell_lines)
            doc.add_paragraph()

    return doc


def generate_documents(context: dict, assessment_type: str, output_dir: str, company: dict = None) -> dict:
    """Generate assessment question paper and answer key as Word documents."""
    os.makedirs(output_dir, exist_ok=True)

    selected_company = company if company is not None else get_selected_company()
    context['company_name'] = selected_company.get('name', 'Tertiary Infotech Academy Pte Ltd')
    context['company_uen'] = selected_company.get('uen', '201200696W')
    context['company_address'] = selected_company.get('address', '')

    questions = context.get("questions", [])

    # Build question paper (no answers)
    q_doc = _build_assessment_doc(context, assessment_type, questions, include_answers=False)
    q_file = tempfile.NamedTemporaryFile(delete=False, suffix=f"_{assessment_type}_Questions.docx")
    q_file.close()
    q_doc.save(q_file.name)

    # Build answer key (with answers)
    a_doc = _build_assessment_doc(context, assessment_type, questions, include_answers=True)
    a_file = tempfile.NamedTemporaryFile(delete=False, suffix=f"_{assessment_type}_Answers.docx")
    a_file.close()
    a_doc.save(a_file.name)

    return {
        "ASSESSMENT_TYPE": assessment_type,
        "QUESTION": q_file.name,
        "ANSWER": a_file.name,
    }


################################################################################
# Streamlit app
################################################################################
DEFAULT_ASSESSMENT_PROMPT = """Generate assessment questions for the course: {course_title}

Assessment types to generate: {assessment_types}

Use the following course data including Learning Units, K/A statements,
topics, and assessment method details to create comprehensive questions.

--- COURSE CONTEXT ---
{course_context}
--- END ---

{master_ka_list}

Generate comprehensive assessment questions following the schema in your instructions.
Return ONLY the JSON object."""


def app():
    st.title("Generate Assessment")

    selected_company = get_selected_company()
    extracted_info = st.session_state.get('extracted_course_info')

    # Prompt Templates (editable, collapsed)
    from utils.prompt_template_editor import render_prompt_templates
    render_prompt_templates("assessment", "Prompt Templates (Assessment)")

    # ----- Dependency check -----
    from utils.agent_runner import submit_agent_job, get_job
    from utils.agent_status import render_page_job_status

    extract_job = get_job("extract_course_info")
    if extract_job and extract_job.get("status") == "running":
        st.info("Course info extraction is still running. Please wait for it to complete.")

    # Generate Assessment
    if st.button("Generate Assessment", type="primary"):
        if not extracted_info:
            st.error("Please extract course info first.")
        elif extract_job and extract_job.get("status") == "running":
            st.warning("Please wait for course info extraction to complete.")
        else:
            # Pre-capture data for background thread (can't access session_state from thread)
            _company = dict(selected_company)
            _extracted_info = dict(extracted_info)

            def _fill_assessment_templates(result):
                """Post-process: fill assessment templates in background thread."""
                if not result or not isinstance(result, dict):
                    return {"fg_data": result, "generated_files": {}}

                assessment_types = result.get('assessment_types', [])
                generated_files = {}
                for assessment in assessment_types:
                    a_type = assessment.get('type', assessment.get('code', 'Unknown'))
                    questions = assessment.get('questions', [])
                    if not questions:
                        continue
                    try:
                        doc_context = {
                            "course_title": result.get('course_title', ''),
                            "duration": assessment.get('duration', ''),
                            "questions": questions,
                        }
                        files = generate_documents(doc_context, a_type, ".output", company=_company)
                        generated_files[a_type] = files
                    except Exception as e:
                        print(f"Error generating {a_type}: {e}")

                return {"fg_data": result, "generated_files": generated_files}

            from courseware_agents.assessment_generator import generate_assessments
            job = submit_agent_job(
                key="generate_assessment",
                label="Generate Assessment",
                async_fn=generate_assessments,
                kwargs={"course_context": _extracted_info},
                post_process=_fill_assessment_templates,
            )

            if job is None:
                st.warning("Assessment generation is already running.")
            else:
                st.rerun()

    # ----- Agent Status -----
    def _on_assessment_complete(job):
        post = job.get("post_results") or {}
        if post:
            st.session_state['fg_data'] = post.get("fg_data")
            st.session_state['assessment_generated_files'] = post.get("generated_files", {})

    job_status = render_page_job_status(
        "generate_assessment",
        on_complete=_on_assessment_complete,
        running_message="AI Agent generating assessments...",
    )

    # Download
    generated_files = st.session_state.get('assessment_generated_files', {})
    if generated_files and any(
        ((file_paths.get('QUESTION') and os.path.exists(file_paths.get('QUESTION'))) or
        (file_paths.get('ANSWER') and os.path.exists(file_paths.get('ANSWER'))))
        for file_paths in generated_files.values()
    ):
        course_title = "Course Title"
        if st.session_state.get('fg_data'):
            course_title = st.session_state['fg_data'].get("course_title", "Course Title")

        zip_buffer = io.BytesIO()
        with zipfile.ZipFile(zip_buffer, "w", zipfile.ZIP_DEFLATED) as zipf:
            for assessment_type, file_paths in generated_files.items():
                q_path = file_paths.get('QUESTION')
                a_path = file_paths.get('ANSWER')

                if q_path and os.path.exists(q_path):
                    display_type = _get_assessment_type_display(assessment_type)
                    q_file_name = f"{display_type} - {course_title}.docx"
                    zipf.write(q_path, arcname=q_file_name)

                if a_path and os.path.exists(a_path):
                    display_type = _get_assessment_type_display(assessment_type)
                    a_file_name = f"Answers to {display_type} - {course_title}.docx"
                    zipf.write(a_path, arcname=a_file_name)

        zip_buffer.seek(0)

        st.download_button(
            label="Download All Assessments (ZIP)",
            data=zip_buffer.getvalue(),
            file_name="assessments.zip",
            mime="application/zip"
        )

    # =========================================================================
    # Add Assessment to AP (Annex)
    # =========================================================================
    st.markdown("---")
    st.subheader("Add Assessment to AP")

    from add_assessment_to_ap.annex_assessment_v2 import merge_documents

    plan_file = st.file_uploader(
        "Upload Assessment Plan (.docx)",
        type=["docx"],
        key="plan_upload",
        help="Upload the main Assessment Plan document"
    )

    # Build assessment types dynamically from extracted course info
    assessment_types = []
    if extracted_info:
        methods = extracted_info.get('Assessment_Methods_Details', [])
        for m in methods:
            abbr = m.get('Method_Abbreviation', '')
            name = m.get('Assessment_Method', '')
            if abbr == 'WA-SAQ':
                assessment_types.append("WA (SAQ)")
            elif abbr:
                assessment_types.append(abbr)
            elif name:
                assessment_types.append(name)
    # Fallback if no course info
    if not assessment_types:
        assessment_types = ["WA (SAQ)", "PP", "CS", "Oral Questioning"]
    assessment_files = {}

    for a_type in assessment_types:
        with st.expander(f"{a_type}", expanded=False):
            col1, col2 = st.columns(2)
            with col1:
                q_file = st.file_uploader(
                    "Question Paper", type=["docx"], key=f"q_{a_type}",
                    help=f"Upload the question paper for {a_type}"
                )
            with col2:
                a_file = st.file_uploader(
                    "Answer Paper", type=["docx"], key=f"a_{a_type}",
                    help=f"Upload the answer paper for {a_type}"
                )
            if q_file or a_file:
                assessment_files[a_type] = {"question": q_file, "answer": a_file}

    if st.button("Generate Merged Document", type="primary", key="merge_btn"):
        if not plan_file:
            st.error("Please upload an Assessment Plan document first.")
        elif not assessment_files:
            st.error("Please upload at least one Question or Answer paper.")
        else:
            try:
                with st.spinner("Merging documents..."):
                    merged_doc_bytes = merge_documents(plan_file, assessment_files)
                st.success("Document merged successfully!")
                base_name = os.path.splitext(plan_file.name)[0]
                st.download_button(
                    label="Download Merged Document",
                    data=merged_doc_bytes,
                    file_name=f"{base_name}_with_annex.docx",
                    mime="application/vnd.openxmlformats-officedocument.wordprocessingml.document",
                    key="download_merged"
                )
            except Exception as e:
                st.error(f"Error merging documents: {e}")


################################################################################
# Convert Existing Assessments to Standard Format
################################################################################

_Q_PATTERN = re.compile(
    r'^(?:'
    r'Q\s*(\d+)\s*[\.:\)]\s*'   # Q1. / Q1: / Q1)
    r'|Question\s+(\d+)\s*[\.:\)]?\s*'  # Question 1 / Question 1.
    r')',
    re.IGNORECASE,
)

_COMPETENCY_TAG_PATTERN = re.compile(
    r'\(\s*([KA]\d+(?:\s*,\s*[KA]\d+)*)\s*\)\s*$'
)

# Reverse mapping: display name → short code
_DISPLAY_TO_CODE = {v: k for k, v in _TYPE_DISPLAY_MAP.items()}
_DISPLAY_TO_CODE["Written Assessment (SAQ)"] = "WA (SAQ)"


def parse_uploaded_assessment(file_bytes) -> dict:
    """Parse an uploaded assessment DOCX and extract questions + answers.

    Walks the document body elements in order (paragraphs interleaved with
    tables). Questions are identified by Q-number patterns; the table
    immediately following a question is its answer box.

    Returns dict with keys: title, questions, has_answers, detected_type,
    detected_duration, scenario.
    """
    doc = Document(io.BytesIO(file_bytes))

    body_elements = []
    for elem in doc.element.body:
        tag = elem.tag.split('}')[-1]
        if tag == 'p':
            # Collect all run text for the paragraph
            text_parts = []
            for r in elem.findall('{http://schemas.openxmlformats.org/wordprocessingml/2006/main}r'):
                for t in r.findall('{http://schemas.openxmlformats.org/wordprocessingml/2006/main}t'):
                    text_parts.append(t.text or '')
            text = ''.join(text_parts).strip()
            body_elements.append(('para', text))
        elif tag == 'tbl':
            # Extract all cell text from a 1x1 table
            ns = '{http://schemas.openxmlformats.org/wordprocessingml/2006/main}'
            cells = elem.findall(f'.//{ns}tc')
            lines = []
            if cells:
                for p in cells[0].findall(f'{ns}p'):
                    ptext = []
                    for r in p.findall(f'{ns}r'):
                        for t in r.findall(f'{ns}t'):
                            ptext.append(t.text or '')
                    line = ''.join(ptext).strip()
                    lines.append(line)
            body_elements.append(('table', lines))

    # --- Extract metadata from title paragraphs ---
    title_lines = []
    detected_type = ""
    detected_duration = ""
    is_answer_doc = False
    scenario = ""

    for tag, content in body_elements[:25]:
        if tag != 'para' or not content:
            continue
        low = content.lower()
        if low.startswith("answer"):
            is_answer_doc = True
        if "duration:" in low:
            detected_duration = content.split(":", 1)[1].strip()
        # Check for assessment type keywords in title
        if not detected_type:
            for display_name in _TYPE_DISPLAY_MAP.values():
                if display_name.lower() in low:
                    detected_type = _DISPLAY_TO_CODE.get(display_name, "")
                    break
        # Collect title lines (non-section-header, non-empty, before questions)
        if not content.startswith(("A:", "B:", "C:", "C.", "Q", "1.", "2.", "3.", "Duration", "This is")):
            if not _Q_PATTERN.match(content):
                title_lines.append(content)

    # Build course title from first title line (strip "Answers to" prefix)
    course_title = ""
    for line in title_lines:
        cleaned = re.sub(r'^Answers?\s+to\s+', '', line, flags=re.IGNORECASE).strip()
        # Skip lines that are just the assessment type name
        if cleaned.lower() not in [v.lower() for v in _TYPE_DISPLAY_MAP.values()]:
            course_title = cleaned
            break

    # --- Walk elements to extract questions and answers ---
    questions = []
    has_answers = is_answer_doc
    current_q_text = ""
    pending_scenario = ""

    i = 0
    while i < len(body_elements):
        tag, content = body_elements[i]

        if tag == 'para':
            # Check for case study
            if content.lower().startswith("case study"):
                # Next non-empty paragraph is the scenario text
                for j in range(i + 1, min(i + 5, len(body_elements))):
                    if body_elements[j][0] == 'para' and body_elements[j][1]:
                        if not _Q_PATTERN.match(body_elements[j][1]):
                            pending_scenario = body_elements[j][1]
                            break
                i += 1
                continue

            # Check for question pattern
            m = _Q_PATTERN.match(content)
            if m:
                current_q_text = _Q_PATTERN.sub('', content).strip()
                # Look ahead for table (answer box)
                answer_lines = []
                for j in range(i + 1, min(i + 4, len(body_elements))):
                    if body_elements[j][0] == 'table':
                        cell_lines = body_elements[j][1]
                        # Filter out empty lines and "Suggestive answers" prefix
                        for line in cell_lines:
                            stripped = line.strip()
                            if stripped and not stripped.lower().startswith("suggestive answer"):
                                answer_lines.append(stripped)
                        if answer_lines:
                            has_answers = True
                        break

                # Extract competency tag from question text
                knowledge_id = ""
                ability_ids = []
                tag_match = _COMPETENCY_TAG_PATTERN.search(current_q_text)
                if tag_match:
                    tags_str = tag_match.group(1)
                    current_q_text = current_q_text[:tag_match.start()].strip()
                    for t in re.split(r'\s*,\s*', tags_str):
                        t = t.strip()
                        if t.startswith('K'):
                            knowledge_id = t
                        elif t.startswith('A'):
                            ability_ids.append(t)

                q_dict = {
                    "question_statement": current_q_text,
                    "answer": answer_lines,
                }
                if knowledge_id:
                    q_dict["knowledge_id"] = knowledge_id
                if ability_ids:
                    q_dict["ability_id"] = ability_ids
                if pending_scenario:
                    q_dict["scenario"] = pending_scenario

                questions.append(q_dict)

        i += 1

    # Auto-detect type from competency tags if not found in title
    if not detected_type and questions:
        has_k = any(q.get('knowledge_id') for q in questions)
        has_a = any(q.get('ability_id') for q in questions)
        if has_k and not has_a:
            detected_type = "WA (SAQ)"
        elif has_a and not has_k:
            detected_type = "PP"

    return {
        "course_title": course_title,
        "questions": questions,
        "has_answers": has_answers,
        "detected_type": detected_type,
        "detected_duration": detected_duration,
        "scenario": pending_scenario,
    }


def convert_assessment_app():
    """Streamlit page for converting existing assessments to standard format."""
    st.title("Convert Assessment")
    st.markdown("Upload existing assessment documents to convert them to the WSQ standard format.")

    uploaded_files = st.file_uploader(
        "Upload Assessment Documents",
        type=["docx"],
        accept_multiple_files=True,
        key="convert_assessment_upload",
        help="Upload question papers and/or answer keys (.docx)"
    )

    if not uploaded_files:
        st.info("Upload one or more assessment DOCX files to get started.")
        return

    # Parse each uploaded file
    parsed_docs = []
    for f in uploaded_files:
        try:
            result = parse_uploaded_assessment(f.read())
            result["filename"] = f.name
            parsed_docs.append(result)
            f.seek(0)
        except Exception as e:
            st.error(f"Error parsing {f.name}: {e}")

    if not parsed_docs:
        return

    # Auto-detect values from first document
    first = parsed_docs[0]
    default_title = first.get("course_title", "")
    default_type = first.get("detected_type", "WA (SAQ)")
    default_duration = first.get("detected_duration", "60 mins")

    # Config section
    st.subheader("Settings")
    col1, col2, col3 = st.columns(3)

    type_options = list(_TYPE_DISPLAY_MAP.keys())
    default_type_idx = type_options.index(default_type) if default_type in type_options else 0

    with col1:
        course_title = st.text_input("Course Title", value=default_title, key="convert_course_title")
    with col2:
        assessment_type = st.selectbox(
            "Assessment Type",
            type_options,
            index=default_type_idx,
            format_func=_get_assessment_type_display,
            key="convert_assessment_type",
        )
    with col3:
        duration = st.text_input("Duration", value=default_duration, key="convert_duration")

    # Preview extracted questions
    st.subheader("Extracted Questions")
    for doc_info in parsed_docs:
        doc_label = doc_info["filename"]
        doc_type = "Answer Key" if doc_info["has_answers"] else "Question Paper"
        questions = doc_info.get("questions", [])

        with st.expander(f"{doc_label} ({doc_type} — {len(questions)} questions)", expanded=True):
            if not questions:
                st.warning("No questions detected in this document.")
                continue
            for idx, q in enumerate(questions, 1):
                q_text = q.get("question_statement", "")
                tag = ""
                if q.get("knowledge_id"):
                    tag = f" ({q['knowledge_id']})"
                elif q.get("ability_id"):
                    tag = f" ({', '.join(q['ability_id'])})"
                st.markdown(f"**Q{idx}.** {q_text}{tag}")
                if q.get("answer"):
                    with st.container():
                        for ans in q["answer"]:
                            st.markdown(f"- {ans}")

    # Convert button
    if st.button("Convert to Standard Format", type="primary", key="convert_btn"):
        if not course_title:
            st.error("Please enter a course title.")
            return

        converted_files = []
        for doc_info in parsed_docs:
            questions = doc_info.get("questions", [])
            if not questions:
                continue

            doc_context = {
                "course_title": course_title,
                "duration": duration,
                "questions": questions,
            }

            display_type = _get_assessment_type_display(assessment_type)

            if doc_info["has_answers"]:
                # Generate answer key
                out_doc = _build_assessment_doc(doc_context, assessment_type, questions, include_answers=True)
                out_name = f"Answers to {display_type} - {course_title}.docx"
            else:
                # Generate question paper
                out_doc = _build_assessment_doc(doc_context, assessment_type, questions, include_answers=False)
                out_name = f"{display_type} - {course_title}.docx"

            tmp = tempfile.NamedTemporaryFile(delete=False, suffix=".docx")
            tmp.close()
            out_doc.save(tmp.name)
            converted_files.append({"path": tmp.name, "name": out_name})

        if not converted_files:
            st.error("No questions found to convert.")
            return

        st.success(f"Converted {len(converted_files)} document(s) to standard format.")

        if len(converted_files) == 1:
            with open(converted_files[0]["path"], "rb") as f:
                st.download_button(
                    label=f"Download {converted_files[0]['name']}",
                    data=f.read(),
                    file_name=converted_files[0]["name"],
                    mime="application/vnd.openxmlformats-officedocument.wordprocessingml.document",
                    key="download_converted_single",
                )
        else:
            zip_buffer = io.BytesIO()
            with zipfile.ZipFile(zip_buffer, "w", zipfile.ZIP_DEFLATED) as zipf:
                for cf in converted_files:
                    zipf.write(cf["path"], arcname=cf["name"])
            zip_buffer.seek(0)
            st.download_button(
                label="Download All Converted (ZIP)",
                data=zip_buffer.getvalue(),
                file_name=f"Converted Assessments - {course_title}.zip",
                mime="application/zip",
                key="download_converted_zip",
            )
