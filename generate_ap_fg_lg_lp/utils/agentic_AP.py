"""
File: agentic_AP.py

===============================================================================
Assessment Plan Generation Module (OpenAI SDK Version)
===============================================================================
Description:
    This module is part of the Courseware system and is responsible for generating
    assessment documents by processing structured course data and integrating assessment
    evidence extracted via an AI agent. It extracts structured justifications for various
    assessment methods (such as CS, PP, OQ, and RP), merges these justifications into the
    course data, and then populates DOCX templates to generate both an Assessment Plan (AP)
    document and an Assessment Summary Report (ASR) document.

    This version uses the OpenAI SDK directly instead of Autogen framework.

Main Functionalities:
    • extract_assessment_evidence(structured_data, model_choice):
          Uses OpenAI SDK to extract structured assessment evidence details (e.g.,
          type of evidence, submission method, marking process, retention period, and role play
          script requirements) from course learning outcomes and topics.
    • combine_assessment_methods(structured_data, evidence_data):
          Merges the extracted assessment evidence into the existing structured course data
          under "Assessment_Methods_Details" based on method abbreviations.
    • is_evidence_extracted(context):
          Checks whether all required evidence fields (evidence, submission, marking process,
          and retention period) are already present for each assessment method.
    • generate_assessment_plan(context, name_of_organisation, sfw_dataset_dir):
          Populates an Assessment Plan DOCX template with the course and assessment evidence data,
          integrates the organization's logo, and returns the path to the generated document.
    • generate_asr_document(context, name_of_organisation):
          Populates an Assessment Summary Report DOCX template with course details and returns the
          file path of the generated document.
    • generate_assessment_documents(context, name_of_organisation, sfw_dataset_dir=None):
          Coordinates the overall process by ensuring that all assessment evidence is extracted,
          merging evidence into the structured data, and generating both the AP and ASR documents.

Dependencies:
    - Standard Libraries: tempfile, json, asyncio
    - Streamlit: For configuration and accessing API keys via st.secrets.
    - Pydantic: For modeling assessment method data.
    - OpenAI SDK: For generating structured evidence using AI.
    - DocxTemplate (from docxtpl): For rendering DOCX templates.
    - Custom Helper Functions: retrieve_excel_data and process_logo_image from generate_ap_fg_lg_lp/utils/helper.

Usage:
    - Ensure that all necessary API keys and configurations are set in st.secrets.
    - Prepare a structured course context dictionary that includes assessment method details.
    - Call generate_assessment_documents(context, name_of_organisation, sfw_dataset_dir) to generate
      the Assessment Plan and Assessment Summary Report documents.
    - The function returns a tuple with file paths to the generated documents.

Author:
    Derrick Lim (Original), Migration to OpenAI SDK
Date:
    3 March 2025 (Original), Updated January 2026
===============================================================================
"""

import tempfile
import streamlit as st
import json
import asyncio
from pydantic import BaseModel
from typing import List, Union, Optional
from openai import OpenAI
from docxtpl import DocxTemplate
from generate_ap_fg_lg_lp.utils.helper import retrieve_excel_data, process_logo_image
from utils.helpers import parse_json_content

class AssessmentMethod(BaseModel):
    evidence: Union[str, List[str]]
    submission: Union[str, List[str]]
    marking_process: Union[str, List[str]]
    retention_period: str
    no_of_scripts: Union[str, None] = None  # Optional field for "RP"

class AssessmentMethods(BaseModel):
    PP: Optional[AssessmentMethod] = None
    CS: Optional[AssessmentMethod] = None
    RP: Optional[AssessmentMethod] = None
    OQ: Optional[AssessmentMethod] = None

class EvidenceGatheringPlan(BaseModel):
    assessment_methods: AssessmentMethods


def create_openai_client(model_choice: str = "GPT-4o-Mini"):
    """
    Create an OpenAI client configured with the specified model choice.

    Args:
        model_choice: Model choice string (e.g., "DeepSeek-Chat", "GPT-4o-Mini")

    Returns:
        tuple: (OpenAI client instance, model configuration dict)
    """
    from settings.model_configs import get_model_config
    from settings.api_manager import load_api_keys

    autogen_config = get_model_config(model_choice)
    config_dict = autogen_config.get("config", {})

    base_url = config_dict.get("base_url", "https://openrouter.ai/api/v1")
    api_key = config_dict.get("api_key", "")
    model = config_dict.get("model", "gpt-4o-mini")
    temperature = config_dict.get("temperature", 0.2)

    # Fallback: If no API key in config, get it dynamically based on api_provider
    if not api_key:
        api_provider = autogen_config.get("api_provider", "OPENROUTER")
        api_keys = load_api_keys()
        api_key = api_keys.get(f"{api_provider}_API_KEY", "")

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


async def extract_assessment_evidence(structured_data, model_choice: str = "GPT-4o-Mini"):
    """
    Extracts structured assessment evidence data from course details using OpenAI SDK.

    This function processes course learning outcomes, topics, and assessment methods
    to generate a structured justification for assessment evidence, submission, marking process,
    and retention periods.

    Args:
        structured_data (dict):
            The original structured data containing course details.
        model_choice (str):
            The model choice string for selecting the AI model.

    Returns:
        dict:
            A dictionary containing the structured assessment evidence details.

    Raises:
        json.JSONDecodeError:
            If the AI-generated response is not valid JSON.
        Exception:
            If the AI response is missing required fields.
    """

    client, config = create_openai_client(model_choice)

    # Build extracted content inline
    lines = []
    learning_units = structured_data.get("Learning_Units", [])

    for lu in learning_units:
        # LU Title
        lines.append(lu.get("LU_Title", ""))
        for topic in lu.get("Topics", []):
            # Topic Title
            lines.append(topic.get("Topic_Title", ""))
            # Bullet Points
            for bullet in topic.get("Bullet_Points", []):
                lines.append(bullet)
        lines.append("")  # Blank line after each LU block

    extracted_content = "\n".join(lines).strip()

    system_message = f"""
        Based on the following course details, you are to provide structured justifications for the selected Assessment Methods, aligning them with Learning Outcomes (LOs) and Topics.

        **Course Details:**
        - **Course Title:** {structured_data.get("Course_Title")}
        - **Learning Outcomes:**
        {" ".join([lu['LO'] for lu in structured_data.get('Learning_Units', [])])}
        - **Topics Covered:** {extracted_content}
        - **Assessment Methods:** {", ".join([method['Method_Abbreviation'] for method in structured_data.get('Assessment_Methods_Details', [])])}

        ---

        **Your Task:**
        - Generate structured justifications for these applicable assessment methods:
        - **CS (Case Study)**
        - **PP (Practical Performance)**
        - **OQ (Oral Questioning)**
        - **RP (Role Play)**

        - For each assessment method, extract the following:
        1. **Type of Evidence**: The specific evidence candidates will submit.
        2. **Manner of Submission**: How candidates submit their work.
        3. **Marking Process**: The evaluation criteria used by assessors.
        4. **Retention Period**: The storage duration for submitted evidence.

        ---

        **Rules:**
        - Replace "students" with "candidates."
        - Replace "instructors" with "assessors."
        - Ensure all **LOs** are addressed.
        - **Limit word length**:
        - Bullet points: Max 30 words.
        - Marking Process: Max 6 words per evaluation.
        - **Format must be consistent**:
        - **PP, CS and OQ:** Evidence must be in a list of LOs.
        - **RP:** Special handling with "No. of Role Play Scripts."

        You must return valid JSON with this structure:
        {{
            "assessment_methods": {{
                "PP": {{
                    "evidence": ["LO1: ...", "LO2: ..."],
                    "submission": ["..."],
                    "marking_process": ["..."],
                    "retention_period": "..."
                }},
                "CS": {{
                    "evidence": ["LO1: ...", "LO2: ..."],
                    "submission": ["..."],
                    "marking_process": ["..."],
                    "retention_period": "..."
                }},
                "OQ": {{
                    "evidence": ["LO1: ..."],
                    "submission": ["..."],
                    "marking_process": ["..."],
                    "retention_period": "..."
                }},
                "RP": {{
                    "evidence": "Role Play",
                    "submission": ["..."],
                    "marking_process": ["..."],
                    "retention_period": "...",
                    "no_of_scripts": "..."
                }}
            }}
        }}
    """

    evidence_task = """
    Your task is to generate the assessment evidence gathering plan.
    Return the data as a valid JSON object.
    """

    try:
        completion = client.chat.completions.create(
            model=config["model"],
            temperature=config["temperature"],
            messages=[
                {"role": "system", "content": system_message},
                {"role": "user", "content": evidence_task}
            ],
            response_format={"type": "json_object"}
        )

        response_content = completion.choices[0].message.content

        # Parse JSON content from response
        try:
            evidence_data = json.loads(response_content)
        except json.JSONDecodeError:
            evidence_data = parse_json_content(response_content)
            if evidence_data is None:
                raise ValueError(f"Could not parse JSON from response: {response_content[:500]}...")

        return evidence_data

    except Exception as e:
        print(f"Error in extract_assessment_evidence: {e}")
        raise

def combine_assessment_methods(structured_data, evidence_data):
    """
    Merges assessment evidence details into the structured data under 'Assessment_Methods_Details'.

    This function updates the existing assessment method details in the structured data 
    with extracted evidence-related information, including evidence type, submission method, 
    marking process, and retention period.

    Args:
        structured_data (dict): 
            The original structured course data.
        evidence_data (dict): 
            The extracted assessment evidence details.

    Returns:
        dict: 
            Updated structured data with merged assessment evidence details.
    """

    # Extract evidence data for assessment methods
    evidence_methods = evidence_data.get("assessment_methods", {})

    # Iterate over Assessment_Methods_Details to integrate evidence data
    for method in structured_data.get("Assessment_Methods_Details", []):
        method_abbr = method.get("Method_Abbreviation")

        # Match the evidence data based on the abbreviation
        if method_abbr in evidence_methods:
            evidence_details = evidence_methods[method_abbr]
            
            
            if "WA-SAQ" in method_abbr:
            # Update the method with detailed evidence data
                method.update({
                    "Evidence": evidence_details.get("evidence", ""),
                    "Submission": evidence_details.get("submission", ""),
                    "Marking_Process": evidence_details.get("marking_process", ""),
                    "Retention_Period": evidence_details.get("retention_period", "")
                })

            if "PP" in method_abbr or "CS" in method_abbr or "OQ" in method_abbr:
            # Update the method with detailed evidence data
                method.update({
                    "Evidence": evidence_details.get("evidence", []),
                    "Submission": evidence_details.get("submission", []),
                    "Marking_Process": evidence_details.get("marking_process", []),
                    "Retention_Period": evidence_details.get("retention_period", "")
                })

            # Include no_of_scripts for Role Play (RP) assessment
            if method_abbr == "RP":
                method.update({
                    "Evidence": evidence_details.get("evidence", ""),
                    "Submission": evidence_details.get("submission", ""),
                    "Marking_Process": evidence_details.get("marking_process", []),
                    "Retention_Period": evidence_details.get("retention_period", "")
                })
                method["No_of_Scripts"] = evidence_details.get("no_of_scripts", "Not specified")

    return structured_data

AP_TEMPLATE_DIR = "generate_ap_fg_lg_lp/input/Template/AP_TGS-Ref-No_Course-Title_v1.docx"  
ASR_TEMPLATE_DIR = "generate_ap_fg_lg_lp/input/Template/ASR_TGS-Ref-No_Course-Title_v1.docx"  

# Check if assessment methods already contain necessary details
def is_evidence_extracted(context):
    """
    Checks whether all necessary assessment evidence fields are already present in the context.

    This function verifies if evidence-related fields such as "Evidence", "Submission", 
    "Marking_Process", and "Retention_Period" are available for each assessment method.

    Args:
        context (dict): 
            The course context dictionary containing assessment method details.

    Returns:
        bool: 
            True if all required fields are present, False otherwise.
    """

    for method in context.get("Assessment_Methods_Details", []):
        method_abbr = method.get("Method_Abbreviation")
        # Skip checking for WA-SAQ entirely, as it is hardcoded in the template.
        if method_abbr == "WA-SAQ":
            continue
        # For other methods, check the required keys.
        for key in ["Evidence", "Submission", "Marking_Process", "Retention_Period"]:
            # For RP, skip checking "Evidence" and "Submission"
            if method_abbr == "RP" and key in ["Evidence", "Submission"]:
                continue
            if method.get(key) is None:
                return False
    return True

def generate_assessment_plan(context: dict, name_of_organisation, sfw_dataset_dir, model_name=None, api_key=None, base_url=None) -> str:
    """
    Generates an Assessment Plan (AP) document by populating a DOCX template with course assessment details.

    This function retrieves assessment-related data, including structured assessment evidence,
    inserts an organization's logo, and saves the populated Assessment Plan document.

    Args:
        context (dict):
            The structured course data including assessment methods.
        name_of_organisation (str):
            The name of the organization, used to retrieve and insert the corresponding logo.
        sfw_dataset_dir (str):
            The file path to the Excel dataset containing additional course-related data.
        model_name (str, optional):
            The AI model name to use. Defaults to value from st.secrets if not provided.
        api_key (str, optional):
            The API key for the AI model. Defaults to value from st.secrets if not provided.
        base_url (str, optional):
            The base URL for the API. Defaults to None.

    Returns:
        str:
            The file path of the generated Assessment Plan document.

    Raises:
        FileNotFoundError:
            If the template file or organization's logo file is missing.
        KeyError:
            If required assessment details are missing.
        IOError:
            If there are issues with reading/writing the document.
    """

    if not is_evidence_extracted(context):
        print("Extracting missing assessment evidence...")

        # Get model choice from session state (set by user in sidebar)
        import streamlit as st
        model_choice = st.session_state.get('selected_model')
        if not model_choice:
            raise ValueError("No model selected. Please select a model from the sidebar.")

        evidence = asyncio.run(extract_assessment_evidence(structured_data=context, model_choice=model_choice))
        context = combine_assessment_methods(context, evidence)
    else:
        print("Skipping assessment evidence extraction as all required fields are already present.")

    doc = DocxTemplate(AP_TEMPLATE_DIR)

    context = retrieve_excel_data(context, sfw_dataset_dir)

    # Add the logo to the context
    context['company_logo'] = process_logo_image(doc, name_of_organisation)
    context['Name_of_Organisation'] = name_of_organisation
    doc.render(context, autoescape=True)

    # Use a temporary file to save the document
    with tempfile.NamedTemporaryFile(delete=False, suffix=".docx") as tmp_file:
        doc.save(tmp_file.name)
        output_path = tmp_file.name  # Get the path to the temporary file

    return output_path  # Return the path to the temporary file

def generate_asr_document(context: dict, name_of_organisation) -> str:
    """
    Generates an Assessment Summary Report (ASR) document.

    This function populates an ASR DOCX template with the given course context 
    and organization's details before saving the document.

    Args:
        context (dict): 
            The structured course data used for the summary report.
        name_of_organisation (str): 
            The name of the organization, used to include the correct details in the document.

    Returns:
        str: 
            The file path of the generated Assessment Summary Report document.

    Raises:
        FileNotFoundError: 
            If the template file is missing.
        IOError: 
            If there are issues with reading/writing the document.
    """

    doc = DocxTemplate(ASR_TEMPLATE_DIR)
    context['Name_of_Organisation'] = name_of_organisation

    doc.render(context)

    # Use a temporary file to save the document
    with tempfile.NamedTemporaryFile(delete=False, suffix=".docx") as tmp_file:
        doc.save(tmp_file.name)
        output_path = tmp_file.name  # Get the path to the temporary file

    return output_path  # Return the path to the temporary file

def generate_assessment_documents(context: dict, name_of_organisation, sfw_dataset_dir=None, model_name=None, api_key=None, base_url=None):
    """
    Generates both the Assessment Plan (AP) and Assessment Summary Report (ASR) documents.

    This function first ensures that assessment evidence is extracted and merged into 
    the structured course data. It then generates the corresponding DOCX files.

    Args:
        context (dict): 
            The structured course data including assessment methods.
        name_of_organisation (str): 
            The name of the organization, used for document customization.
        sfw_dataset_dir (str, optional): 
            The file path to the Excel dataset containing course-related data. 
            Defaults to a predefined dataset file.

    Returns:
        tuple:
            - `str`: File path of the generated Assessment Plan document.
            - `str`: File path of the generated Assessment Summary Report document.

    Raises:
        Exception: 
            If any issue occurs during the document generation process.
    """
    
    try:
        # Use the provided template directory or default
        if sfw_dataset_dir is None:
            sfw_dataset_dir = "generate_ap_fg_lg_lp/input/dataset/Sfw_dataset-2022-03-30 copy.xlsx"

        # Generate the Assessment Plan document
        ap_output_path = generate_assessment_plan(context, name_of_organisation, sfw_dataset_dir, model_name, api_key, base_url)
        # Generate the Assessment Summary Report document
        asr_output_path = generate_asr_document(context, name_of_organisation)

        return ap_output_path, asr_output_path
    except Exception as e:
        print(f"An error occurred during document generation: {e}")
        import traceback
        print(f"Full traceback: {traceback.format_exc()}")
        # Also raise the exception so it shows in Streamlit
        raise Exception(f"Assessment document generation failed: {str(e)}")