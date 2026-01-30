"""
File: agentic_LG.py

===============================================================================
Learning Guide Generation Module (OpenAI SDK Version)
===============================================================================
Description:
    This module is responsible for generating a Learning Guide (LG) document for a course.
    It utilizes an AI assistant to produce structured content, including a Course Overview (90-100 words)
    and a Learning Outcome description (45-50 words), based on the provided course details.
    The generated content is then merged into a DOCX template, along with organization branding such as
    the company logo, to create a comprehensive Learning Guide tailored to potential learners.

    This version uses the OpenAI SDK directly instead of Autogen framework.

Main Functionalities:
    • generate_content(context, model_choice):
          Uses OpenAI SDK to generate a detailed Course Overview and a concise Learning Outcome
          description. The output is a JSON dictionary with keys "Course_Overview" and "LO_Description".
    • generate_learning_guide(context, name_of_organisation, model_choice):
          Retrieves the AI-generated content, integrates it into a DOCX template, inserts the organization's logo,
          renders the document, and saves it as a temporary file. Returns the file path of the generated Learning Guide.

Dependencies:
    - Standard Libraries: json, tempfile, asyncio
    - External Libraries:
         • openai (OpenAI SDK)
         • docxtpl (DocxTemplate)
    - Custom Utilities:
         • parse_json_content from utils.helpers
         • process_logo_image from generate_ap_fg_lg_lp/utils/helper

Usage:
    - Ensure the Learning Guide DOCX template and organization logo are available at the specified paths.
    - Configure the model choice and prepare a structured course context.
    - Invoke generate_learning_guide(context, name_of_organisation, model_choice) to generate the Learning Guide.
    - The function returns the file path of the generated document.

Author:
    Derrick Lim (Original), Migration to OpenAI SDK
Date:
    3 March 2025 (Original), Updated January 2026
===============================================================================
"""

import json
import tempfile
import asyncio
from openai import OpenAI
from docxtpl import DocxTemplate
from utils.helpers import parse_json_content
from generate_ap_fg_lg_lp.utils.helper import process_logo_image

LG_TEMPLATE_DIR = "generate_ap_fg_lg_lp/input/Template/LG_TGS-Ref-No_Course-Title_v1.docx"


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


async def generate_content(context, model_choice: str = "GPT-4o-Mini"):
    """
    Generates a Course Overview and Learning Outcome description for a Learning Guide.

    This function uses OpenAI SDK to generate structured content for a Learning Guide
    based on the provided course information. The generated text is strictly formatted
    according to predefined rules, ensuring precise word counts and appropriate structuring.

    Args:
        context (dict):
            A dictionary containing structured course information.
        model_choice (str):
            The model choice string for selecting the AI model.

    Returns:
        dict:
            An updated context dictionary containing:
            - `"Course_Overview"` (str): A detailed introduction to the course.
            - `"LO_Description"` (str): A concise and measurable learning outcome description.

    Raises:
        json.JSONDecodeError:
            If the AI response does not contain valid JSON content.
        Exception:
            If the response lacks the required keys `"Course_Overview"` or `"LO_Description"`.
    """
    client, config = create_openai_client(model_choice)

    system_message = """
        You are an expert in creating detailed and informative content for course descriptions. Your task is to:

        1. Generate a course overview (Learning Overview) of EXACTLY 90-100 words based on the provided Course Title. The overview MUST:
            - Start with "The `course_  title` course provides..."
            - Provide a comprehensive introduction to the course content
            - Highlight multiple key concepts or skills that will be covered in all the learning units
            - Use clear and detailed language suitable for potential learners
            - Include specific examples of topics or techniques covered

        2. Generate a learning outcome description (Learning Outcome) of EXACTLY 45-50 words based on the provided Course Title. The learning outcome MUST:
            - Start with "By the end of this course, learners will be able to..."
            - Focus on at least three key skills or knowledge areas that participants will gain
            - Use specific action verbs to describe what learners will be able to do
            - Be detailed, specific, and measurable
            - Reflect the depth and complexity of the course content

        3. Return these as a valid JSON object with keys "Course_Overview" and "LO_Description".
        Ensure that the content is tailored to the specific course title provided, reflects the depth and focus of the course, and STRICTLY adheres to the specified word counts.
        """

    agent_task = f"""
        Please:
        1. Take the complete dictionary provided:
        {context}
        2. Generate the Course Overview and Learning Outcome description.
        3. Return the JSON dictionary containing the 'Course_Overview' and 'LO_Description' key.
        """

    try:
        completion = client.chat.completions.create(
            model=config["model"],
            temperature=config["temperature"],
            messages=[
                {"role": "system", "content": system_message},
                {"role": "user", "content": agent_task}
            ],
            response_format={"type": "json_object"}
        )

        response_content = completion.choices[0].message.content

        if not response_content:
            print("No content found in the response.")
            return context

        result = parse_json_content(response_content)
        return result

    except json.JSONDecodeError as e:
        print(f"Error parsing LG content JSON: {e}")
        return context
    except Exception as e:
        print(f"Error generating LG content: {e}")
        return context


def generate_learning_guide(context: dict, name_of_organisation: str, model_choice: str = "GPT-4o-Mini") -> str:
    """
    Generates a Learning Guide document by populating a DOCX template with course content.

    This function retrieves AI-generated course descriptions, inserts them into a Learning Guide template,
    and adds the organization's logo before saving the document.

    Args:
        context (dict):
            A dictionary containing course details to be included in the Learning Guide.
        name_of_organisation (str):
            The name of the organization, used to retrieve and insert the corresponding logo.
        model_choice (str):
            The model choice string for selecting the AI model. Defaults to "GPT-4o-Mini".

    Returns:
        str:
            The file path of the generated Learning Guide document.

    Raises:
        FileNotFoundError:
            If the template file or the organization's logo file is missing.
        KeyError:
            If required keys such as `"Course_Overview"` or `"LO_Description"` are missing.
        IOError:
            If there are issues with reading/writing the document.
    """
    # Debug: Log incoming context for LG generation
    print("=" * 60)
    print("LG GENERATION - CONTEXT DEBUG")
    print("=" * 60)
    print(f"LG DEBUG: Course_Title = {context.get('Course_Title')}")
    print(f"LG DEBUG: Learning_Units count = {len(context.get('Learning_Units', []))}")
    print("=" * 60)

    # ================================================================
    # Validate and normalize Learning_Units structure for template
    # ================================================================
    learning_units = context.get("Learning_Units", [])

    if not isinstance(learning_units, list):
        print(f"LG DEBUG: WARNING - Learning_Units is not a list")
        learning_units = []

    validated_learning_units = []
    for i, lu in enumerate(learning_units):
        if not isinstance(lu, dict):
            continue

        validated_lu = {
            "LU_Title": lu.get("LU_Title", f"Learning Unit {i+1}"),
            "LO": lu.get("LO", ""),
            "Topics": lu.get("Topics", []),
            "K_numbering_description": lu.get("K_numbering_description", []),
            "A_numbering_description": lu.get("A_numbering_description", []),
            "Assessment_Methods": lu.get("Assessment_Methods", []),
            "Instructional_Methods": lu.get("Instructional_Methods", []),
        }

        # Validate nested structures
        validated_topics = []
        for topic in validated_lu["Topics"]:
            if isinstance(topic, dict):
                validated_topics.append({
                    "Topic_Title": topic.get("Topic_Title", ""),
                    "Bullet_Points": topic.get("Bullet_Points", [])
                })
        validated_lu["Topics"] = validated_topics

        validated_k = []
        for k in validated_lu["K_numbering_description"]:
            if isinstance(k, dict):
                validated_k.append({"K_number": k.get("K_number", ""), "Description": k.get("Description", "")})
        validated_lu["K_numbering_description"] = validated_k

        validated_a = []
        for a in validated_lu["A_numbering_description"]:
            if isinstance(a, dict):
                validated_a.append({"A_number": a.get("A_number", ""), "Description": a.get("Description", "")})
        validated_lu["A_numbering_description"] = validated_a

        validated_learning_units.append(validated_lu)

    context["Learning_Units"] = validated_learning_units
    print(f"LG DEBUG: Total validated Learning_Units = {len(validated_learning_units)}")

    content_response = asyncio.run(generate_content(context, model_choice))
    context["Course_Overview"] = content_response.get("Course_Overview")
    context["LO_Description"] = content_response.get("LO_Description")

    doc = DocxTemplate(LG_TEMPLATE_DIR)

    # Add the logo and organization details to the context
    context['company_logo'] = process_logo_image(doc, name_of_organisation)
    context['Name_of_Organisation'] = name_of_organisation

    # Ensure UEN is set from organization data
    from generate_ap_fg_lg_lp.utils.organizations import get_organizations, get_default_organization
    organizations = get_organizations()
    org = next((o for o in organizations if o["name"] == name_of_organisation), None)
    if org and org.get("uen"):
        context['UEN'] = org["uen"]
    else:
        # Fall back to default organization UEN
        default_org = get_default_organization()
        if default_org.get("uen"):
            context['UEN'] = default_org["uen"]

    # Add Document Version Control Record data
    from datetime import datetime
    current_date = datetime.now().strftime("%d %b %Y")
    context['Rev_No'] = "1.0"
    context['Effective_Date'] = current_date
    context['Author'] = ""
    context['Reviewed_By'] = ""
    context['Approved_By'] = ""

    # Prepare Assessment Summary with full LO descriptions and abbreviated assessment methods
    assessment_summary = []
    learning_units = context.get("Learning_Units", [])

    # Map full assessment method names to abbreviations
    method_abbreviations = {
        "Written Assessment - Short Answer Questions": "WA-SAQ",
        "Written Assessment": "WA",
        "Written Exam": "WA-SAQ",
        "Practical Performance": "PP",
        "Practical Exam": "PP",
        "Case Study": "CS",
        "Oral Questioning": "OQ",
        "Role Play": "RP",
        "Project": "PJ",
        "Portfolio": "PF",
        "Observation": "OB",
    }

    for lu in learning_units:
        # Get full LO description
        lo_full = lu.get("LO", "")

        # Get assessment methods and convert to abbreviations
        assessment_methods = lu.get("Assessment_Methods", [])
        abbreviated_methods = []
        for method in assessment_methods:
            # Check if it's already an abbreviation
            if method in ["WA-SAQ", "WA", "PP", "CS", "OQ", "RP", "PJ", "PF", "OB"]:
                abbreviated_methods.append(method)
            else:
                # Look up abbreviation
                abbr = method_abbreviations.get(method, method)
                # If not found, try to create abbreviation from first letters
                if abbr == method and len(method) > 5:
                    words = method.split()
                    abbr = "-".join([w[0].upper() for w in words if w[0].isupper() or w == words[0]])
                abbreviated_methods.append(abbr)

        assessment_summary.append({
            "LO": lo_full,
            "Assessment_Methods": ", ".join(abbreviated_methods)
        })

    context['Assessment_Summary'] = assessment_summary

    # Also update Learning_Units to have abbreviated assessment methods
    for i, lu in enumerate(learning_units):
        assessment_methods = lu.get("Assessment_Methods", [])
        abbreviated_methods = []
        for method in assessment_methods:
            if method in ["WA-SAQ", "WA", "PP", "CS", "OQ", "RP", "PJ", "PF", "OB"]:
                abbreviated_methods.append(method)
            else:
                abbr = method_abbreviations.get(method, method)
                if abbr == method and len(method) > 5:
                    words = method.split()
                    abbr = "-".join([w[0].upper() for w in words if w[0].isupper() or w == words[0]])
                abbreviated_methods.append(abbr)
        context['Learning_Units'][i]['Assessment_Methods_Abbr'] = ", ".join(abbreviated_methods)

    doc.render(context, autoescape=True)
    # Use a temporary file to save the document
    with tempfile.NamedTemporaryFile(delete=False, suffix=".docx") as tmp_file:
        doc.save(tmp_file.name)
        output_path = tmp_file.name  # Get the path to the temporary file

    return output_path  # Return the path to the temporary file