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
         • parse_json_content from common.common
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
from common.common import parse_json_content
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

    content_response = asyncio.run(generate_content(context, model_choice))
    context["Course_Overview"] = content_response.get("Course_Overview")
    context["LO_Description"] = content_response.get("LO_Description") 

    doc = DocxTemplate(LG_TEMPLATE_DIR)

    # Add the logo to the context
    context['company_logo'] = process_logo_image(doc, name_of_organisation)
    context['Name_of_Organisation'] = name_of_organisation

    doc.render(context, autoescape=True)
    # Use a temporary file to save the document
    with tempfile.NamedTemporaryFile(delete=False, suffix=".docx") as tmp_file:
        doc.save(tmp_file.name)
        output_path = tmp_file.name  # Get the path to the temporary file

    return output_path  # Return the path to the temporary file