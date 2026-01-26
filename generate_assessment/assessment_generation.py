"""
File: assessment_generation.py

===============================================================================
Assessment Generator Module
===============================================================================
Description:
    This module implements a Streamlit-based web application that generates
    assessment documents (e.g., Question and Answer papers) from provided input
    documents. It processes a Facilitator Guide (FG) document and a Trainer Slide
    Deck (PDF) to extract structured data, which is then used to generate assessments
    for various types of tests such as Short Answer Questions (SAQ), Practical
    Performance (PP), and Case Study (CS).

Main Functionalities:
    1. Session State Initialization:
       - Sets up key variables in Streamlit's session_state to maintain state
         across app interactions, including parsed data, extracted FG data,
         and generated assessment files.

    2. Helper Functions for Document Processing:
       - get_pdf_page_count(pdf_path): Returns the total number of pages in a PDF
       - extract_pdf_text(pdf_path): Extracts text from PDF using PyMuPDF

    3. Facilitator Guide (FG) Parsing and Interpretation:
       - parse_fg(fg_path): Parses a Facilitator Guide document using python-docx
       - interpret_fg(fg_data, model_choice): Uses AI to extract structured info

    4. Slide Deck Parsing:
       - parse_slides(slides_path): Extracts text from PDF slides using PyMuPDF

    5. Assessment Document Generation:
       - generate_documents(context, assessment_type, output_dir):
         Generates question and answer documents using docxtpl templates

    6. Streamlit Web Application (app function):
       - Provides a step-by-step user interface for uploading documents,
         parsing, generating assessments, and downloading results

Dependencies:
    - Core Libraries: os, io, zipfile, tempfile, json, asyncio, copy
    - Streamlit: streamlit (web application interface)
    - Document Parsing: pymupdf, python-docx, docxtpl
    - AI Integration: openai

Author: Derrick Lim
Date: 4 March 2025
===============================================================================
"""

import streamlit as st
import os
import io
import zipfile
import asyncio
import json
import tempfile

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
from copy import deepcopy
from docx import Document
from docxtpl import DocxTemplate
from company.company_manager import get_selected_company, get_company_template, apply_company_branding, show_company_info
import generate_assessment.utils.utils as utils
from openai import OpenAI
from generate_assessment.utils.openai_agentic_CS import generate_cs
from generate_assessment.utils.openai_agentic_PP import generate_pp
from generate_assessment.utils.openai_agentic_SAQ import generate_saq
from generate_assessment.utils.pydantic_models import FacilitatorGuideExtraction
from settings.model_configs import get_model_config
from settings.api_manager import load_api_keys
from utils.helpers import parse_json_content

################################################################################
# Initialize session_state keys at the top of the script.
################################################################################
if 'index' not in st.session_state:
    st.session_state['slides_data'] = None
if 'fg_data' not in st.session_state:
    st.session_state['fg_data'] = None
if 'saq_output' not in st.session_state:
    st.session_state['saq_output'] = None
if 'pp_output' not in st.session_state:
    st.session_state['pp_output'] = None
if 'cs_output' not in st.session_state:
    st.session_state['cs_output'] = None
if 'assessment_generated_files' not in st.session_state:
    st.session_state['assessment_generated_files'] = {}
if 'selected_model' not in st.session_state:
    st.session_state['selected_model'] = "DeepSeek-Chat"

################################################################################
# Helper function for PDF text extraction
################################################################################
def get_pdf_page_count(pdf_path):
    """Get total page count of a PDF file"""
    if PYMUPDF_AVAILABLE:
        doc = pymupdf.open(pdf_path)
        total_pages = doc.page_count
        doc.close()
        return total_pages
    else:
        # Fallback to PyPDF2
        from PyPDF2 import PdfReader
        reader = PdfReader(pdf_path)
        return len(reader.pages)

def extract_pdf_text(pdf_path):
    """Extract text from PDF using PyMuPDF or PyPDF2 fallback"""
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
        # Fallback to PyPDF2
        from PyPDF2 import PdfReader
        reader = PdfReader(pdf_path)
        text_content = []
        for page_num, page in enumerate(reader.pages):
            text = page.extract_text() or ""
            if text.strip():
                text_content.append({"page": page_num + 1, "text": text})
        return text_content

################################################################################
# Parse Facilitator Guide Document
################################################################################
def parse_fg(fg_path):
    """Parse Facilitator Guide document using python-docx"""
    import hashlib

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
    parsed_content = [{
        "pages": [{
            "page": 1,
            "text": "\n".join(all_text)
        }]
    }]

    result_json = json.dumps(parsed_content)

    # Save to cache
    with open(cache_path, 'w', encoding='utf-8') as f:
        f.write(result_json)
    print(f"Cached FG parse result for future use (hash: {file_hash})")

    return result_json

def extract_master_k_a_list(fg_markdown):
    """
    Extracts the master list of K and A statements from the FG markdown using regex.
    Returns a dict with 'knowledge' and 'abilities' lists.
    """
    import re
    import json

    master_k = []
    master_a = []

    # Parse JSON to extract all text content from pages
    try:
        fg_json = json.loads(fg_markdown)
        all_text = ""

        # Extract text from all pages
        if isinstance(fg_json, list):
            for doc in fg_json:
                if "pages" in doc:
                    for page in doc["pages"]:
                        if "text" in page:
                            all_text += page["text"] + "\n"

        print(f"DEBUG: Extracted {len(all_text)} chars of text from JSON")
        print(f"DEBUG: Text sample (first 2000 chars):\n{all_text[:2000]}\n")

    except json.JSONDecodeError:
        # Not JSON, treat as plain text
        all_text = fg_markdown
        print(f"DEBUG: Using plain text markdown (not JSON)")

    # Try multiple patterns to match different formats
    patterns_k = [
        r'(K\d+):\s*(.+?)(?=\n(?:K\d+:|A\d+:|TSC |##|\n\n|$))',  # Standard format
        r'\*\*?(K\d+):\*\*?\s*(.+?)(?=\n\*\*?(?:K\d+:|A\d+:)|\n\n|$)',  # Bold format
        r'(K\d+)\s*[-–]\s*(.+?)(?=\n(?:K\d+|A\d+)|\n\n|$)',  # Dash format
    ]

    patterns_a = [
        r'(A\d+):\s*(.+?)(?=\n(?:K\d+:|A\d+:|TSC |##|\n\n|$))',  # Standard format
        r'\*\*?(A\d+):\*\*?\s*(.+?)(?=\n\*\*?(?:K\d+:|A\d+:)|\n\n|$)',  # Bold format
        r'(A\d+)\s*[-–]\s*(.+?)(?=\n(?:K\d+|A\d+)|\n\n|$)',  # Dash format
    ]

    # Try all patterns for K statements
    for pattern in patterns_k:
        for match in re.finditer(pattern, all_text, re.DOTALL | re.MULTILINE):
            k_id = match.group(1)
            k_text = match.group(2).strip().replace('\n', ' ').replace('*', '')
            # Avoid duplicates
            if not any(k['id'] == k_id for k in master_k):
                master_k.append({"id": k_id, "text": k_text})

    # Try all patterns for A statements
    for pattern in patterns_a:
        for match in re.finditer(pattern, all_text, re.DOTALL | re.MULTILINE):
            a_id = match.group(1)
            a_text = match.group(2).strip().replace('\n', ' ').replace('*', '')
            # Avoid duplicates
            if not any(a['id'] == a_id for a in master_a):
                master_a.append({"id": a_id, "text": a_text})

    print(f"Master K/A List Extraction - Found {len(master_k)} K statements, {len(master_a)} A statements")
    if master_k:
        print(f"  K IDs: {[k['id'] for k in master_k]}")
    if master_a:
        print(f"  A IDs: {[a['id'] for a in master_a]}")

    return {"knowledge": master_k, "abilities": master_a}

def create_openai_client(model_choice: str = "GPT-4o-Mini"):
    """
    Create an OpenAI client configured with the specified model choice.

    Args:
        model_choice: Model choice string (e.g., "DeepSeek-Chat", "GPT-4o-Mini")

    Returns:
        tuple: (OpenAI client instance, model configuration dict)
    """
    autogen_config = get_model_config(model_choice)
    config_dict = autogen_config.get("config", {})

    base_url = config_dict.get("base_url", "https://openrouter.ai/api/v1")
    api_key = config_dict.get("api_key", "")
    model = config_dict.get("model", "gpt-4o-mini")
    temperature = config_dict.get("temperature", 0.2)

    client = OpenAI(
        base_url=base_url,
        api_key=api_key
    )

    model_config = {
        "model": model,
        "temperature": temperature,
        "base_url": base_url
    }

    return client, model_config


async def interpret_fg(fg_data, model_choice: str = "GPT-4o-Mini"):
    """
    Interprets and extracts structured data from a Facilitator Guide document using OpenAI SDK.

    Args:
        fg_data: The FG document data
        model_choice: The model choice string for selecting the AI model

    Returns:
        dict: Extracted structured data from the FG document
    """
    # First, extract the master K/A list using regex
    print("🔧 USING NEW CODE WITH AUTO-INJECTION v2.0 (OpenAI SDK)")
    master_list = extract_master_k_a_list(fg_data)

    client, config = create_openai_client(model_choice)

    system_message = f"""
        You are an expert at structured data extraction. Extract the following details from the FG Document:
        - Course Title
        - TSC Proficiency Level
        - Learning Units (LUs):
            * Name of the Learning Unit (learning_unit_title field)
            * Topics in the Learning Unit:
                - Name of the Topic
                - Description of the Topic (bullet points or sub-topics)
                - Full Knowledge Statements (tsc_knowledges) associated with the topic, including their identifiers and text (e.g., K1: Range of AI applications)
                - Full Ability Statements (tsc_abilities) associated with the topic, including their identifiers and text (e.g., A1: Analyze algorithms in the AI applications)
            * Learning Outcome (LO) for each Learning Unit
        - Assessment Types and Durations:
            * Extract assessment types and their durations in the format:
                {{"code": "WA-SAQ", "duration": "1 hr"}}
                {{"code": "PP", "duration": "0.5 hr"}}
                {{"code": "CS", "duration": "30 mins"}}
            * Interpret abbreviations of assessment methods to their correct types (e.g., "WA-SAQ," "PP," "CS").

        CRITICAL INSTRUCTIONS FOR K AND A STATEMENTS:
        1. The document will contain a complete list of TSC Knowledge statements (K1, K2, K3... Kn) and TSC Abilities (A1, A2, A3... An)
        2. You MUST extract EVERY SINGLE K and A statement - do not skip any
        3. Each K/A statement should appear in the relevant topics where it's used
        4. If a K/A statement appears in multiple topics, include it in all relevant topics
        5. Double-check that you've included ALL K statements from K1 to the highest K number
        6. Double-check that you've included ALL A statements from A1 to the highest A number
        7. Do NOT skip K4, K5, A2, A3, etc. - extract them ALL

        Use this JSON schema:
        {json.dumps(FacilitatorGuideExtraction.model_json_schema(), indent=2)}
        """

    # Build the master list string for the prompt
    master_k_str = "\n".join([f"  {k['id']}: {k['text']}" for k in master_list['knowledge']])
    master_a_str = "\n".join([f"  {a['id']}: {a['text']}" for a in master_list['abilities']])

    agent_task = f"""
    Please extract and structure the following data: {fg_data}.

    MASTER LIST OF ALL K AND A STATEMENTS (YOU MUST INCLUDE ALL OF THESE):

    TSC Knowledge Statements:
    {master_k_str if master_k_str else "  (None found - extract from document)"}

    TSC Ability Statements:
    {master_a_str if master_a_str else "  (None found - extract from document)"}

    INSTRUCTIONS:
    1. Extract course title, TSC proficiency level, and learning units from the document
    2. For each topic in each learning unit, map the relevant K and A statements from the master list above
    3. EVERY K and A statement from the master list MUST appear in at least one topic
    4. If a K/A statement isn't clearly associated with a specific topic, add it to the most relevant topic
    5. Include the full learning_unit_title for each learning unit
    6. Extract assessment types and durations

    VALIDATION - Before returning, verify:
    - ALL K statements from the master list are included in topics
    - ALL A statements from the master list are included in topics
    - No K or A statements are skipped

    Return the extracted information as a complete JSON dictionary containing the specified fields.
    Do not truncate or omit any data. Include all fields and their full content.
    Do not use '...' or any placeholders to replace data.

    Simply return the JSON dictionary object directly.
    """

    try:
        completion = client.chat.completions.create(
            model=config["model"],
            temperature=config["temperature"],
            messages=[
                {"role": "system", "content": system_message},
                {"role": "user", "content": agent_task}
            ],
            response_format={"type": "json_object"},
            max_tokens=16384
        )

        raw_content = completion.choices[0].message.content

        if not raw_content:
            print("ERROR: No response from LLM during FG interpretation")
            return None

        # Debug: Log raw response
        print(f"FG Interpretation - Response length: {len(raw_content)} chars")
        print(f"FG Interpretation - First 500 chars: {raw_content[:500]}")
        print(f"FG Interpretation - Last 500 chars: {raw_content[-500:]}")

    except Exception as e:
        print(f"ERROR: Exception during FG interpretation: {e}")
        return None

    context = parse_json_content(raw_content)

    if context is None:
        print("ERROR: parse_json_content returned None - invalid JSON")
        print(f"Raw response: {raw_content}")
    else:
        # Validate K/A extraction
        all_k_ids = set()
        all_a_ids = set()

        if "learning_units" in context:
            for lu in context["learning_units"]:
                for topic in lu.get("topics", []):
                    for k in topic.get("tsc_knowledges", []):
                        all_k_ids.add(k.get("id", ""))
                    for a in topic.get("tsc_abilities", []):
                        all_a_ids.add(a.get("id", ""))

        print(f"FG Interpretation - Extracted K statements: {sorted(all_k_ids)}")
        print(f"FG Interpretation - Extracted A statements: {sorted(all_a_ids)}")
        print(f"FG Interpretation - Total: {len(all_k_ids)} K, {len(all_a_ids)} A")

        # Check for missing K/A statements and inject them from master list
        missing_k = [k for k in master_list['knowledge'] if k['id'] not in all_k_ids]
        missing_a = [a for a in master_list['abilities'] if a['id'] not in all_a_ids]

        if missing_k or missing_a:
            print(f"⚠️ LLM missed some K/A statements. Injecting them from master list...")
            print(f"  Missing K: {[k['id'] for k in missing_k]}")
            print(f"  Missing A: {[a['id'] for a in missing_a]}")

            # Find the first topic in the first learning unit to inject missing K/A
            if "learning_units" in context and context["learning_units"]:
                first_lu = context["learning_units"][0]
                if "topics" in first_lu and first_lu["topics"]:
                    first_topic = first_lu["topics"][0]

                    # Inject missing K statements
                    if "tsc_knowledges" not in first_topic:
                        first_topic["tsc_knowledges"] = []
                    for k in missing_k:
                        first_topic["tsc_knowledges"].append(k)

                    # Inject missing A statements
                    if "tsc_abilities" not in first_topic:
                        first_topic["tsc_abilities"] = []
                    for a in missing_a:
                        first_topic["tsc_abilities"].append(a)

                    print(f"✅ Injected {len(missing_k)} K and {len(missing_a)} A statements into first topic")

                    # Verify after injection
                    all_k_ids_after = set()
                    all_a_ids_after = set()
                    for lu in context["learning_units"]:
                        for topic in lu.get("topics", []):
                            for k in topic.get("tsc_knowledges", []):
                                all_k_ids_after.add(k.get("id", ""))
                            for a in topic.get("tsc_abilities", []):
                                all_a_ids_after.add(a.get("id", ""))

                    print(f"After injection - Total: {len(all_k_ids_after)} K, {len(all_a_ids_after)} A")
                    print(f"  K IDs: {sorted(all_k_ids_after)}")
                    print(f"  A IDs: {sorted(all_a_ids_after)}")

    return context

################################################################################
# Parse Slide Deck Document
################################################################################
def parse_slides(slides_path):
    """Parse PDF slides and extract text content using PyMuPDF or PyPDF2 fallback"""
    print(f"Parsing slides from: {slides_path}")

    total_pages = get_pdf_page_count(slides_path)
    # Skip first 16 and last 6 pages (typically cover/intro and end pages)
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
                    slides_content.append({
                        "page": page_num + 1,
                        "text": text.strip()
                    })
        doc.close()
    else:
        # Fallback to PyPDF2
        from PyPDF2 import PdfReader
        reader = PdfReader(slides_path)
        for page_num in range(start_page - 1, end_page):
            if page_num < len(reader.pages):
                text = reader.pages[page_num].extract_text() or ""
                if text.strip():
                    slides_content.append({
                        "page": page_num + 1,
                        "text": text.strip()
                    })

    print(f"Extracted text from {len(slides_content)} pages")

    # Return as a simple dict with the extracted content
    return {"slides": slides_content, "total_pages": total_pages}

################################################################################
# Utility function to ensure answers are always a list.
################################################################################
def _ensure_list(answer):
    if isinstance(answer, list):
        return answer
    elif isinstance(answer, str):
        return [answer]
    return []

################################################################################
# Generate documents (Question and Answer papers)
################################################################################
def generate_documents(context: dict, assessment_type: str, output_dir: str) -> dict:
    os.makedirs(output_dir, exist_ok=True)
    
    # Get company template or fallback to default
    selected_company = get_selected_company()
    company_assessment_template = get_company_template("assessment")
    
    if company_assessment_template:
        # Use company-specific template
        qn_template = company_assessment_template
        ans_template = company_assessment_template  # Use same template, different context
    else:
        # Use default templates
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
    # Format questions for template rendering
    def format_questions(questions):
        formatted = []
        for q in questions:
            formatted_q = {**q}

            # Keep ability_id as list - template iterates it correctly
            # Just ensure it's always a list
            if "ability_id" in formatted_q:
                ability_ids = formatted_q["ability_id"]
                if not isinstance(ability_ids, list):
                    formatted_q["ability_id"] = [ability_ids] if ability_ids else []
                elif not ability_ids:
                    formatted_q["ability_id"] = []

            # Remove learning_outcome_id for PP and CS - only need ability
            # Use None instead of "" to remove it from template context
            if assessment_type in ["PP", "CS"]:
                formatted_q.pop("learning_outcome_id", None)  # Remove the key entirely
            else:
                # For other types (SAQ), ensure learning_outcome_id is present
                if "learning_outcome_id" not in formatted_q or not formatted_q["learning_outcome_id"]:
                    formatted_q["learning_outcome_id"] = ""
                elif isinstance(formatted_q["learning_outcome_id"], list):
                    formatted_q["learning_outcome_id"] = ", ".join(formatted_q["learning_outcome_id"])

            formatted.append(formatted_q)
        return formatted

    # Deduplicate questions by ability_id for PP/CS
    def deduplicate_questions(questions):
        if assessment_type not in ["PP", "CS"]:
            return questions

        seen_abilities = set()
        unique_questions = []

        print(f"DEBUG: Before deduplication - {len(questions)} questions:")
        for i, q in enumerate(questions):
            ability_ids = q.get("ability_id", [])
            print(f"  Q{i+1}: Ability={ability_ids}")

        for q in questions:
            ability_ids = q.get("ability_id", [])
            if isinstance(ability_ids, list):
                ability_key = tuple(sorted(ability_ids))
            else:
                ability_key = (ability_ids,)

            if ability_key not in seen_abilities:
                seen_abilities.add(ability_key)
                unique_questions.append(q)
                print(f"✅ Kept question with abilities: {ability_ids}")
            else:
                print(f"⚠️ Skipped duplicate question for abilities: {ability_ids}")

        print(f"Deduplication: {len(questions)} → {len(unique_questions)} questions")
        print(f"Final unique abilities: {sorted([tuple(q.get('ability_id', [])) for q in unique_questions])}")
        return unique_questions

    deduped_questions = deduplicate_questions(context.get("questions", []))
    formatted_questions = format_questions(deduped_questions)

    # Debug: Show what's in each question
    print(f"DEBUG: Rendering {len(formatted_questions)} questions for {assessment_type}")
    for i, q in enumerate(formatted_questions[:3]):  # Show first 3
        lo_id = q.get("learning_outcome_id", "N/A")
        a_ids = q.get("ability_id", "N/A")
        print(f"  Q{i+1}: LO={lo_id}, Ability={a_ids}")

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
    answer_doc.render(answer_context, autoescape=True)
    question_doc.render(question_context, autoescape=True)
    question_tempfile = tempfile.NamedTemporaryFile(
        delete=False, suffix=f"_{assessment_type}_Questions.docx"
    )
    answer_tempfile = tempfile.NamedTemporaryFile(
        delete=False, suffix=f"_{assessment_type}_Answers.docx"
    )
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

    # Get selected company and templates
    selected_company = get_selected_company()
    assessment_template_path = get_company_template("assessment")

    st.subheader("Step 1: Upload Relevant Documents")
    st.write("Upload your Facilitator Guide (.docx) to generate assessments. Trainer Slide Deck (.pdf) is optional for enhanced content.")

    # Load API keys from Settings UI with fallback to secrets
    api_keys = load_api_keys()

    selected_config = get_model_config(st.session_state['selected_model'])
    
    # Check if model configuration exists
    if not selected_config:
        st.error(f"❌ Model configuration not found for: {st.session_state['selected_model']}")
        st.info("💡 **Solution**: Go to Model Selection and choose a different model (e.g., GPT-4o-Mini)")
        return
    
    # Check if config section exists
    if not selected_config.get("config"):
        st.error(f"❌ Invalid model configuration for: {st.session_state['selected_model']}")
        return
        
    # Get API key from config or load from Settings UI
    api_key = selected_config["config"].get("api_key")
    
    # If no API key in config, use OpenRouter (recommended) or OpenAI key
    if not api_key:
        # All models are accessed via OpenRouter - use OpenRouter API key
        api_key = api_keys.get("OPENROUTER_API_KEY", "")
        # Fallback to OpenAI API key for native OpenAI models
        if not api_key:
            api_key = api_keys.get("OPENAI_API_KEY", "")
    
    if not api_key:
        st.error(f"❌ API key for {st.session_state['selected_model']} is not provided.")
        st.info("💡 **Solution**: Go to Settings → LLM Models & API Keys to add the required API key")
        return
    model_name = selected_config["config"]["model"]
    temperature = selected_config["config"].get("temperature", 0)
    base_url = selected_config["config"].get("base_url", None)

    # Extract model_info from the selected configuration (if provided)
    model_info = selected_config["config"].get("model_info", None)

    # Test API connection before proceeding using OpenAI SDK
    try:
        test_client = OpenAI(
            api_key=api_key,
            base_url=base_url if base_url else "https://api.openai.com/v1"
        )
        # Simple test to verify connection
        test_client.models.list()
    except Exception as e:
        st.error(f"❌ Failed to create API client: {e}")
        if "401" in str(e) or "unauthorized" in str(e).lower():
            st.error("🔑 **API Key Issue**: Invalid or expired API key")
        elif "quota" in str(e).lower() or "rate" in str(e).lower():
            st.error("📊 **Quota Issue**: API quota exceeded or rate limit hit")
        elif "connection" in str(e).lower():
            st.error("🌐 **Network Issue**: Cannot connect to API service")
        # Don't return - continue anyway as some APIs don't support models.list()

    # Store the model choice for use in the generation functions
    model_choice = st.session_state['selected_model']

    fg_doc_file = st.file_uploader("Upload Facilitator Guide (.docx)", type=["docx"])

    # Auto-parse Facilitator Guide when uploaded
    if fg_doc_file is not None and 'fg_parsed' not in st.session_state:
        fg_filepath = None
        try:
            with st.spinner("Auto-parsing Facilitator Guide..."):
                fg_filepath = utils.save_uploaded_file(fg_doc_file, "data")
                fg_data = parse_fg(fg_filepath)  # Now cached!

                # Cache LLM interpretation too
                import hashlib
                fg_hash = hashlib.md5(fg_data.encode()).hexdigest()
                interp_cache_path = f"data/fg_cache/{fg_hash}_interpreted.json"

                if os.path.exists(interp_cache_path):
                    print(f"✅ Found cached FG interpretation")
                    with open(interp_cache_path, 'r', encoding='utf-8') as f:
                        interpreted_data = json.load(f)

                    # Apply filter to cached data too (in case cache was created before filter was added)
                    if "assessments" in interpreted_data and isinstance(interpreted_data["assessments"], list):
                        original_count = len(interpreted_data["assessments"])
                        filtered_assessments = []
                        seen_durations = {}

                        for assessment in interpreted_data["assessments"]:
                            code = assessment.get("code", "")
                            duration = assessment.get("duration", "")
                            is_suspicious = False

                            # Filter CS with duplicate duration
                            if duration in seen_durations and code in ["CS", "CASE STUDY"]:
                                print(f"⚠️ Filtering suspicious {code} from cache (duplicate duration: {duration})")
                                is_suspicious = True

                            if code == "CS" and duration in [a.get("duration") for a in filtered_assessments]:
                                print(f"⚠️ Filtering suspicious CS from cache (matches existing duration: {duration})")
                                is_suspicious = True

                            if not is_suspicious:
                                filtered_assessments.append(assessment)
                                seen_durations[duration] = code

                        if original_count != len(filtered_assessments):
                            interpreted_data["assessments"] = filtered_assessments
                            print(f"✅ Filtered {original_count - len(filtered_assessments)} suspicious assessment(s) from cache")
                else:
                    print(f"⏳ Interpreting FG with LLM (this may take 10-30 seconds)...")
                    interpreted_data = asyncio.run(interpret_fg(fg_data, model_choice))

                    # Validate and filter hallucinated assessments
                    if "assessments" in interpreted_data and isinstance(interpreted_data["assessments"], list):
                        original_count = len(interpreted_data["assessments"])
                        filtered_assessments = []
                        seen_durations = {}

                        for assessment in interpreted_data["assessments"]:
                            code = assessment.get("code", "")
                            duration = assessment.get("duration", "")

                            # Check for suspicious patterns
                            is_suspicious = False

                            # Pattern 1: Same duration as another assessment (sign of hallucination)
                            if duration in seen_durations and code in ["CS", "CASE STUDY"]:
                                print(f"⚠️ Filtering suspicious {code} assessment (duplicate duration: {duration})")
                                is_suspicious = True

                            # Pattern 2: CS with same duration as PP or SAQ
                            if code == "CS" and duration in [a.get("duration") for a in filtered_assessments]:
                                print(f"⚠️ Filtering suspicious CS assessment (matches existing duration: {duration})")
                                is_suspicious = True

                            if not is_suspicious:
                                filtered_assessments.append(assessment)
                                seen_durations[duration] = code

                        interpreted_data["assessments"] = filtered_assessments
                        if original_count != len(filtered_assessments):
                            print(f"✅ Filtered {original_count - len(filtered_assessments)} suspicious assessment(s)")

                    # Save interpretation to cache
                    with open(interp_cache_path, 'w', encoding='utf-8') as f:
                        json.dump(interpreted_data, f, indent=2)
                    print(f"✅ Cached FG interpretation")

                # Validate the interpreted data is a dictionary
                if interpreted_data is None or not isinstance(interpreted_data, dict):
                    error_msg = "Failed to parse Facilitator Guide. "
                    if interpreted_data is None:
                        error_msg += "The LLM returned None (check console logs for details). "
                    else:
                        error_msg += f"The LLM returned {type(interpreted_data)} instead of dict. "
                    error_msg += "This usually means: (1) JSON was truncated due to max_tokens limit, (2) Invalid JSON format, or (3) LLM timeout. Check terminal/console for debug logs."
                    raise ValueError(error_msg)

                st.session_state['fg_data'] = interpreted_data
                st.session_state['fg_parsed'] = True
                st.success("✅ Facilitator Guide automatically parsed and ready for assessment generation!")
        except Exception as e:
            st.error(f"❌ Error auto-parsing Facilitator Guide: {e}")
            if 'fg_data' in st.session_state:
                del st.session_state['fg_data']
        finally:
            if fg_filepath and os.path.exists(fg_filepath):
                os.remove(fg_filepath)

    slide_deck_file = st.file_uploader("Upload Trainer Slide Deck (.pdf) - Optional", type=["pdf"])

    # Auto-parse Slide Deck when uploaded
    if slide_deck_file is not None and 'slides_parsed' not in st.session_state:
        slides_filepath = None
        try:
            with st.spinner("Auto-parsing Trainer Slide Deck..."):
                slides_filepath = utils.save_uploaded_file(slide_deck_file, "data")
                st.session_state['slides_data'] = parse_slides(slides_filepath)
                st.session_state['slides_parsed'] = True
            # Success message outside spinner context to ensure spinner clears first
            st.success("✅ Trainer Slide Deck automatically parsed for enhanced content!")
        except Exception as e:
            st.error(f"❌ Error auto-parsing Slide Deck: {e}")
            if 'index' in st.session_state:
                del st.session_state['slides_data']
        finally:
            if slides_filepath and os.path.exists(slides_filepath):
                os.remove(slides_filepath)

    # Clear parsing flags if files are removed
    if fg_doc_file is None and 'fg_parsed' in st.session_state:
        del st.session_state['fg_parsed']
        if 'fg_data' in st.session_state:
            del st.session_state['fg_data']
        if 'assessment_generated_files' in st.session_state:
            del st.session_state['assessment_generated_files']

    if slide_deck_file is None and 'slides_parsed' in st.session_state:
        del st.session_state['slides_parsed']
        if 'index' in st.session_state:
            del st.session_state['slides_data']

    st.subheader("Step 2: Generate Assessments")

    # Show Generate Assessments button if FG is parsed
    if st.session_state.get('fg_data') and isinstance(st.session_state.get('fg_data'), dict) and not st.session_state.get('assessment_generated_files'):
        if st.button("🚀 Generate Assessments", type="primary"):
            assessments = st.session_state['fg_data'].get('assessments', [])

            # Auto-detect which assessment types are available
            available_types = []

            # Debug: Show all assessment codes found
            print(f"DEBUG: Found {len(assessments)} assessments in FG:")
            for i, assessment in enumerate(assessments):
                code = assessment.get('code', '')
                duration = assessment.get('duration', '')
                print(f"  Assessment {i+1}: code='{code}', duration='{duration}'")

            for assessment in assessments:
                code = assessment.get('code', '').upper().strip()

                # Use word boundary matching to avoid false positives (e.g., "PROCESS" shouldn't match "CS")
                detected = False

                # Check for WA (SAQ)
                if 'WA-SAQ' in code or 'WA (SAQ)' in code or 'SAQ' in code or (code.startswith('WA') and 'SAQ' in code):
                    if 'WA (SAQ)' not in available_types:
                        available_types.append('WA (SAQ)')
                        print(f"DEBUG: Detected WA (SAQ) from code: '{code}'")
                    detected = True

                # Check for PP - be more strict
                if code == 'PP' or 'PP' == code or '-PP' in code or 'PP-' in code or '(PP)' in code:
                    if 'PP' not in available_types:
                        available_types.append('PP')
                        print(f"DEBUG: Detected PP from code: '{code}'")
                    detected = True

                # Check for CS - be VERY strict to avoid false positives
                # Only match exact CS or CS with delimiters, not substrings
                if code == 'CS' or code == 'CASE STUDY' or code == 'WA-CS' or code == 'CS-' in code or code.startswith('CS-') or code.endswith('-CS') or '(CS)' in code:
                    if 'CS' not in available_types:
                        available_types.append('CS')
                        print(f"DEBUG: Detected CS from code: '{code}'")
                    detected = True

                if not detected:
                    print(f"DEBUG: Skipped unrecognized code: '{code}'")

            if available_types:
                st.info(f"📋 Auto-detected assessment types: {', '.join(available_types)}")
                st.info("🚀 Starting automatic assessment generation...")

                # Auto-generate assessments
                st.session_state['assessment_generated_files'] = {}

                try:
                    # Use slide deck index if available, otherwise None
                    index = st.session_state.get('index', None)

                    for assessment_type in available_types:
                        max_retries = 3
                        base_delay = 30

                        for attempt in range(max_retries):
                            try:
                                if assessment_type == "WA (SAQ)":
                                    with st.spinner(f"Auto-generating Written Assessment (SAQ)... (attempt {attempt + 1}/{max_retries})"):
                                        saq_context = asyncio.run(generate_saq(st.session_state['fg_data'], index, model_choice))
                                        files = generate_documents(saq_context, assessment_type, "output")
                                        st.session_state['assessment_generated_files'][assessment_type] = files
                                elif assessment_type == "PP":
                                    with st.spinner(f"Auto-generating Practical Performance... (attempt {attempt + 1}/{max_retries})"):
                                        pp_context = asyncio.run(generate_pp(st.session_state['fg_data'], index, model_choice))
                                        files = generate_documents(pp_context, assessment_type, "output")
                                        st.session_state['assessment_generated_files'][assessment_type] = files
                                elif assessment_type == "CS":
                                    with st.spinner(f"Auto-generating Case Study... (attempt {attempt + 1}/{max_retries})"):
                                        cs_context = asyncio.run(generate_cs(st.session_state['fg_data'], index, model_choice))
                                        files = generate_documents(cs_context, assessment_type, "output")
                                        st.session_state['assessment_generated_files'][assessment_type] = files
                                break  # Success, exit retry loop
                            except Exception as e:
                                error_str = str(e)
                                if ("connection" in error_str.lower() or "503" in error_str or
                                    "overloaded" in error_str.lower() or "unavailable" in error_str.lower() or
                                    "timeout" in error_str.lower()):
                                    if attempt < max_retries - 1:  # Not the last attempt
                                        delay = base_delay * (2 ** attempt)
                                        st.warning(f"Connection issue for {assessment_type}, retrying in {delay} seconds...")
                                        import time
                                        time.sleep(delay)
                                        continue
                                    else:
                                        raise Exception(f"Failed to generate {assessment_type} after {max_retries} attempts. Last error: {error_str}")
                                else:
                                    # Re-raise non-connection errors immediately
                                    raise e

                    if st.session_state['assessment_generated_files']:
                        st.success("✅ All assessments automatically generated!")

                except Exception as e:
                    st.error(f"Error auto-generating assessments: {e}")
            else:
                st.warning("⚠️ No assessment types detected in the document. Please ensure your Facilitator Guide contains assessment duration and ratio information.")

    # Manual override section (for cases where auto-detection fails or user wants to override)
    with st.expander("🔧 Manual Assessment Selection (Optional Override)"):
        st.write("Use this section only if auto-detection failed or you want to generate specific assessments manually:")
        saq = st.checkbox("Short Answer Questions (SAQ)")
        pp = st.checkbox("Practical Performance (PP)")
        cs = st.checkbox("Case Study (CS)")

        if st.button("Generate Selected Assessments"):
            st.session_state['assessment_generated_files'] = {}

            if not st.session_state.get('fg_data'):
                st.error("❌ Please upload the Facilitator Guide first.")
                return
            else:
                selected_types = []
                if saq:
                    selected_types.append("WA (SAQ)")
                if pp:
                    selected_types.append("PP")
                if cs:
                    selected_types.append("CS")
                if not selected_types:
                    st.error("❌ Please select at least one assessment type to generate.")
                    return

                st.success("✅ Proceeding with manual assessment generation...")
                try:
                    # Use slide deck index if available, otherwise None
                    index = st.session_state.get('index', None)

                    for assessment_type in selected_types:
                        max_retries = 3
                        base_delay = 30

                        for attempt in range(max_retries):
                            try:
                                if assessment_type == "WA (SAQ)":
                                    with st.spinner(f"Generating Written Assessment (SAQ)... (attempt {attempt + 1}/{max_retries})"):
                                        saq_context = asyncio.run(generate_saq(st.session_state['fg_data'], index, model_choice))
                                        files = generate_documents(saq_context, assessment_type, "output")
                                        st.session_state['assessment_generated_files'][assessment_type] = files
                                elif assessment_type == "PP":
                                    with st.spinner(f"Generating Practical Performance... (attempt {attempt + 1}/{max_retries})"):
                                        pp_context = asyncio.run(generate_pp(st.session_state['fg_data'], index, model_choice))
                                        files = generate_documents(pp_context, assessment_type, "output")
                                        st.session_state['assessment_generated_files'][assessment_type] = files
                                elif assessment_type == "CS":
                                    with st.spinner(f"Generating Case Study... (attempt {attempt + 1}/{max_retries})"):
                                        cs_context = asyncio.run(generate_cs(st.session_state['fg_data'], index, model_choice))
                                        files = generate_documents(cs_context, assessment_type, "output")
                                        st.session_state['assessment_generated_files'][assessment_type] = files
                                break  # Success, exit retry loop
                            except Exception as e:
                                error_str = str(e)
                                if ("connection" in error_str.lower() or "503" in error_str or
                                    "overloaded" in error_str.lower() or "unavailable" in error_str.lower() or
                                    "timeout" in error_str.lower()):
                                    if attempt < max_retries - 1:  # Not the last attempt
                                        delay = base_delay * (2 ** attempt)
                                        st.warning(f"Connection issue for {assessment_type}, retrying in {delay} seconds...")
                                        import time
                                        time.sleep(delay)
                                        continue
                                    else:
                                        raise Exception(f"Failed to generate {assessment_type} after {max_retries} attempts. Last error: {error_str}")
                                else:
                                    # Re-raise non-connection errors immediately
                                    raise e

                    if st.session_state['assessment_generated_files']:
                        st.success("✅ Manual assessments successfully generated!")

                except Exception as e:
                    st.error(f"Error generating assessments: {e}")

    generated_files = st.session_state.get('assessment_generated_files', {})
    # Check if any assessment type has a valid QUESTION or ANSWER file
    if generated_files and any(
        ((file_paths.get('QUESTION') and os.path.exists(file_paths.get('QUESTION'))) or 
        (file_paths.get('ANSWER') and os.path.exists(file_paths.get('ANSWER'))))
        for file_paths in generated_files.values()
    ):
        course_title = "Course Title"
        # If fg_data is available, update course_title accordingly.
        if st.session_state.get('fg_data'):
            course_title = st.session_state['fg_data'].get("course_title", "Course Title")
        
        # Create an in-memory ZIP file containing all available assessment documents.
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
        
        # Reset the buffer's position to the beginning
        zip_buffer.seek(0)
        
        st.download_button(
            label="Download All Assessments (ZIP)",
            data=zip_buffer.getvalue(),
            file_name="assessments.zip",
            mime="application/zip"
        )
    else:
        st.info("No files have been generated yet. Please generate assessments first.")

    ############################################################################
    # Reset Button at the Bottom
    ############################################################################
    if st.button("Reset Course Data", type="primary"):
        st.session_state['slides_data'] = None
        st.session_state['fg_data'] = None
        st.session_state['assessment_generated_files'] = {}
        st.session_state['saq_output'] = None
        st.session_state['pp_output'] = None
        st.session_state['cs_output'] = None
        st.success("Course data has been reset.")