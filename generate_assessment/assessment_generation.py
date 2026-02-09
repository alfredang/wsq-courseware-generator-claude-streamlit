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
import asyncio

from copy import deepcopy
from docx import Document
from docxtpl import DocxTemplate
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
    cache_dir = "data/fg_cache"
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
# Generate documents (Question and Answer papers) - Template filling only
################################################################################
def generate_documents(context: dict, assessment_type: str, output_dir: str) -> dict:
    """Fill assessment document templates with pre-generated content."""
    os.makedirs(output_dir, exist_ok=True)

    # Get company template or fallback to default
    selected_company = get_selected_company()
    company_assessment_template = get_company_template("assessment")

    if company_assessment_template:
        qn_template = company_assessment_template
        ans_template = company_assessment_template
    else:
        TEMPLATES = {
            "QUESTION": f"generate_assessment/utils/Templates/(Template) {assessment_type} - Course Title - v1.docx",
            "ANSWER": f"generate_assessment/utils/Templates/(Template) Answer to {assessment_type} - Course Title - v1.docx"
        }
        qn_template = TEMPLATES["QUESTION"]
        ans_template = TEMPLATES["ANSWER"]

    # Add company branding to context
    context['company_name'] = selected_company.get('name', 'Tertiary Infotech Academy Pte Ltd')
    context['company_uen'] = selected_company.get('uen', '201200696W')
    context['company_address'] = selected_company.get('address', '')

    question_doc = DocxTemplate(qn_template)
    answer_doc = DocxTemplate(ans_template)

    def format_questions(questions):
        formatted = []
        for q in questions:
            formatted_q = {**q}
            if "ability_id" in formatted_q:
                ability_ids = formatted_q["ability_id"]
                if not isinstance(ability_ids, list):
                    formatted_q["ability_id"] = [ability_ids] if ability_ids else []
                elif not ability_ids:
                    formatted_q["ability_id"] = []

            if assessment_type in ["PP", "CS"]:
                formatted_q.pop("learning_outcome_id", None)
            else:
                if "learning_outcome_id" not in formatted_q or not formatted_q["learning_outcome_id"]:
                    formatted_q["learning_outcome_id"] = ""
                elif isinstance(formatted_q["learning_outcome_id"], list):
                    formatted_q["learning_outcome_id"] = ", ".join(formatted_q["learning_outcome_id"])

            formatted.append(formatted_q)
        return formatted

    def deduplicate_questions(questions):
        if assessment_type not in ["PP", "CS"]:
            return questions
        seen_abilities = set()
        unique_questions = []
        for q in questions:
            ability_ids = q.get("ability_id", [])
            if isinstance(ability_ids, list):
                ability_key = tuple(sorted(ability_ids))
            else:
                ability_key = (ability_ids,)
            if ability_key not in seen_abilities:
                seen_abilities.add(ability_key)
                unique_questions.append(q)
        return unique_questions

    deduped_questions = deduplicate_questions(context.get("questions", []))
    formatted_questions = format_questions(deduped_questions)

    answer_context = {
        **context,
        "questions": [
            {**question, "answer": _ensure_list(question.get("answer"))}
            for question in formatted_questions
        ]
    }
    question_context = {
        **context,
        "questions": [
            {**question, "answer": None}
            for question in formatted_questions
        ]
    }

    answer_doc.render(answer_context)
    question_doc.render(question_context)

    question_tempfile = tempfile.NamedTemporaryFile(
        delete=False, suffix=f"_{assessment_type}_Questions.docx"
    )
    question_tempfile.close()

    answer_tempfile = tempfile.NamedTemporaryFile(
        delete=False, suffix=f"_{assessment_type}_Answers.docx"
    )
    answer_tempfile.close()

    question_doc.save(question_tempfile.name)
    answer_doc.save(answer_tempfile.name)

    return {
        "ASSESSMENT_TYPE": assessment_type,
        "QUESTION": question_tempfile.name,
        "ANSWER": answer_tempfile.name
    }


################################################################################
# Streamlit app
################################################################################
def app():
    st.title("Generate Assessment")

    selected_company = get_selected_company()

    # Step 1: Upload and Parse FG
    st.subheader("Step 1: Upload and Parse Facilitator Guide")
    st.write("Upload your Facilitator Guide (.docx) to parse it. The parsed text will be saved for the Claude Code skill.")

    fg_doc_file = st.file_uploader("Upload Facilitator Guide (.docx)", type=["docx"])

    if fg_doc_file is not None and 'fg_parsed' not in st.session_state:
        fg_filepath = None
        try:
            with st.spinner("Parsing Facilitator Guide..."):
                import generate_assessment.utils.utils as utils
                fg_filepath = utils.save_uploaded_file(fg_doc_file, "data")
                fg_text = parse_fg(fg_filepath)

                # Save parsed FG
                os.makedirs("output", exist_ok=True)
                with open("output/parsed_fg.json", "w", encoding="utf-8") as f:
                    f.write(fg_text)

                # Extract K/A list for reference
                master_list = extract_master_k_a_list(fg_text)
                with open("output/fg_master_ka.json", "w", encoding="utf-8") as f:
                    json.dump(master_list, f, indent=2)

                st.session_state['fg_parsed'] = True
                st.success("FG parsed successfully.")

                if master_list['knowledge'] or master_list['abilities']:
                    with st.expander("K/A Statements Found", expanded=False):
                        st.write(f"**Knowledge:** {len(master_list['knowledge'])} | **Abilities:** {len(master_list['abilities'])}")

        except Exception as e:
            st.error(f"Error parsing Facilitator Guide: {e}")
        finally:
            if fg_filepath and os.path.exists(fg_filepath):
                os.remove(fg_filepath)

    # Clear parsing flags if file is removed
    if fg_doc_file is None and 'fg_parsed' in st.session_state:
        del st.session_state['fg_parsed']
        if 'fg_data' in st.session_state:
            del st.session_state['fg_data']
        if 'assessment_generated_files' in st.session_state:
            st.session_state['assessment_generated_files'] = {}

    # Step 2: Generate or Load Assessment Context
    st.subheader("Step 2: Generate Assessment Content")

    col1, col2 = st.columns(2)

    with col1:
        if st.session_state.get('fg_parsed'):
            if st.button("Generate with AI Agent", type="primary"):
                try:
                    with st.spinner("AI Agent generating assessments... This may take 1-2 minutes."):
                        from courseware_agents.assessment_generator import generate_assessments
                        result = asyncio.run(generate_assessments(
                            fg_data_path="output/parsed_fg.json",
                            master_ka_path="output/fg_master_ka.json",
                        ))
                        st.session_state['fg_data'] = result
                        st.success(f"Assessment content generated: {result.get('course_title', 'Unknown')}")
                        types = result.get('assessment_types', [])
                        if types:
                            st.info(f"Generated {len(types)} assessment type(s): {', '.join(t.get('type', t.get('code', '')) for t in types)}")
                except Exception as e:
                    st.error(f"Error generating assessments: {e}")
        else:
            st.info("Upload and parse a Facilitator Guide first.")

    with col2:
        st.write("Or load pre-generated context:")

    context_json_file = st.file_uploader("Upload assessment context JSON", type=["json"], key="assessment_context_upload")

    # Check for output/assessment_context.json
    if os.path.exists("output/assessment_context.json") and not context_json_file:
        st.info("Found `output/assessment_context.json` from Claude Code skill.")
        if st.button("Load from output/assessment_context.json"):
            try:
                with open("output/assessment_context.json", "r", encoding="utf-8") as f:
                    assessment_data = json.load(f)
                st.session_state['fg_data'] = assessment_data
                st.success(f"Assessment context loaded: {assessment_data.get('course_title', 'Unknown Course')}")

                # Show what assessment types are available
                if 'assessment_types' in assessment_data:
                    types = assessment_data['assessment_types']
                    st.info(f"Available assessment types: {', '.join(t.get('type', t.get('code', '')) for t in types)}")

            except Exception as e:
                st.error(f"Error loading assessment context: {e}")

    if context_json_file:
        try:
            assessment_data = json.load(context_json_file)
            st.session_state['fg_data'] = assessment_data
            st.success(f"Assessment context loaded: {assessment_data.get('course_title', 'Unknown Course')}")
        except Exception as e:
            st.error(f"Error loading context JSON: {e}")

    # Step 3: Generate Assessment Documents
    st.subheader("Step 3: Generate Assessment Documents")

    fg_data = st.session_state.get('fg_data')
    if fg_data and isinstance(fg_data, dict):
        # Check for pre-generated assessment types with questions
        assessment_types = fg_data.get('assessment_types', [])

        if assessment_types:
            st.info(f"Found {len(assessment_types)} assessment type(s) ready for template filling.")

            if st.button("Generate Assessment Documents", type="primary"):
                st.session_state['assessment_generated_files'] = {}

                for assessment in assessment_types:
                    a_type = assessment.get('type', assessment.get('code', 'Unknown'))
                    questions = assessment.get('questions', [])

                    if not questions:
                        st.warning(f"No questions found for {a_type}. Skipping.")
                        continue

                    try:
                        with st.spinner(f"Generating {a_type} documents..."):
                            context = {
                                "course_title": fg_data.get('course_title', ''),
                                "duration": assessment.get('duration', ''),
                                "questions": questions,
                            }
                            files = generate_documents(context, a_type, "output")
                            st.session_state['assessment_generated_files'][a_type] = files
                    except Exception as e:
                        st.error(f"Error generating {a_type}: {e}")

                if st.session_state['assessment_generated_files']:
                    st.success("Assessment documents generated successfully!")
        else:
            st.info("No assessment types found in context. Make sure the Claude Code skill generated assessment content with questions.")

    # Step 4: Download
    generated_files = st.session_state.get('assessment_generated_files', {})
    if generated_files and any(
        ((file_paths.get('QUESTION') and os.path.exists(file_paths.get('QUESTION'))) or
        (file_paths.get('ANSWER') and os.path.exists(file_paths.get('ANSWER'))))
        for file_paths in generated_files.values()
    ):
        st.subheader("Step 4: Download Assessments")

        course_title = "Course Title"
        if st.session_state.get('fg_data'):
            course_title = st.session_state['fg_data'].get("course_title", "Course Title")

        zip_buffer = io.BytesIO()
        with zipfile.ZipFile(zip_buffer, "w", zipfile.ZIP_DEFLATED) as zipf:
            for assessment_type, file_paths in generated_files.items():
                q_path = file_paths.get('QUESTION')
                a_path = file_paths.get('ANSWER')

                if q_path and os.path.exists(q_path):
                    q_file_name = f"{assessment_type} - {course_title}.docx"
                    zipf.write(q_path, arcname=q_file_name)

                if a_path and os.path.exists(a_path):
                    a_file_name = f"Answer to {assessment_type} - {course_title}.docx"
                    zipf.write(a_path, arcname=a_file_name)

        zip_buffer.seek(0)

        st.download_button(
            label="Download All Assessments (ZIP)",
            data=zip_buffer.getvalue(),
            file_name="assessments.zip",
            mime="application/zip"
        )

    # Reset Button
    if st.button("Reset Course Data", type="primary"):
        st.session_state['fg_data'] = None
        st.session_state['assessment_generated_files'] = {}
        if 'fg_parsed' in st.session_state:
            del st.session_state['fg_parsed']
        st.success("Course data has been reset.")
