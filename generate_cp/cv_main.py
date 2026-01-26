"""
Course Validation Main Module - OpenAI SDK Version.

This module handles the course validation process using OpenAI SDK agents
instead of the Autogen framework.

Author: Migration from Autogen to OpenAI SDK
Date: 2026-01-20
"""

from generate_cp.agents.openai_course_validation_team import run_course_validation_team
from generate_cp.utils.helpers import append_validation_output
from generate_cp.utils.json_docu_replace import replace_placeholders_in_doc
import json
import asyncio
import sys
import os


async def create_course_validation(model_choice: str) -> None:
    """
    Create course validation documents using OpenAI SDK agents.

    This replaces the Autogen-based implementation with direct OpenAI API calls.
    Generates 3 validation documents with different survey responses.

    Args:
        model_choice: The model to use (e.g., "DeepSeek-Chat", "GPT-4o-Mini")
    """
    # Load the JSON file into a Python variable
    with open('generate_cp/json_output/ensemble_output.json', 'r', encoding="utf-8") as file:
        ensemble_output = json.load(file)

    # --- Course Validation Team Process (OpenAI SDK) ---
    # Replaces: create_course_validation_team() + Console(stream) + save_state() + extract_final_editor_json()
    editor_data = await run_course_validation_team(
        ensemble_output=ensemble_output,
        model_choice=model_choice,
        stream_to_console=True
    )
    with open("generate_cp/json_output/validation_output.json", "w", encoding="utf-8") as out:
        json.dump(editor_data, out, indent=2)

    append_validation_output(
        "generate_cp/json_output/ensemble_output.json",
        "generate_cp/json_output/validation_output.json",
    )

    with open('generate_cp/json_output/validation_output.json', 'r') as file:
        validation_output = json.load(file)

    # If validation_output is a JSON string, parse it first
    if isinstance(validation_output, str):
        validation_output = json.loads(validation_output)

    # Load mapping template with key:empty list pair
    with open('generate_cp/json_output/validation_mapping_source.json', 'r') as file:
        validation_mapping_source = json.load(file)

    # Loop through the responses and create three different output documents
    responses = validation_output.get('analyst_responses', [])
    # Handle consolidated response format - duplicate single response for 3 templates
    if len(responses) == 1:
        responses = [responses[0], responses[0], responses[0]]
    elif len(responses) < 1:
        print("Error: No responses found in the JSON file.")
        sys.exit(1)

    # Load CV templates
    CV_template_1 = "generate_cp/templates/CP_validation_template_bernard.docx"
    CV_template_2 = "generate_cp/templates/CP_validation_template_dwight.docx"
    CV_template_3 = "generate_cp/templates/CP_validation_template_ferris.docx"
    CV_templates = [CV_template_1, CV_template_2, CV_template_3]

    # Iterate over responses and templates
    for i, (response, CV_template) in enumerate(zip(responses[:3], CV_templates), 1):
        # Check that 'course_info' is in 'data'
        course_info = validation_output.get("course_info")
        if not course_info:
            print(f"Error: 'course_info' is missing from the JSON data during iteration {i}.")
            sys.exit(1)

        # Create a temporary JSON file for the current response
        temp_response_json = f"generate_cp/json_output/temp_response_{i}.json"

        # Prepare the content to write to the JSON file
        json_content = {
            "course_info": course_info,
            "analyst_responses": [response]
        }

        # Write to the temporary JSON file
        with open(temp_response_json, 'w', encoding="utf-8") as temp_file:
            json.dump(json_content, temp_file, indent=4)

        # Debugging: Print the contents of temp_response_json to confirm correctness
        print(f"Debug: Contents of temp_response_json ({temp_response_json}):")
        with open(temp_response_json, 'r', encoding="utf-8") as temp_file:
            print(temp_file.read())
            analyst_response = json_content["analyst_responses"][0]

        # Extract the name of the word template without the file extension
        template_name_without_extension = os.path.splitext(os.path.basename(CV_template))[0]
        output_directory = "generate_cp/output_docs"
        os.makedirs(output_directory, exist_ok=True)

        # Define the output file name for this response in the same directory as the input file
        output_docx_version = os.path.join(output_directory, f"{template_name_without_extension}_updated.docx")

        replace_placeholders_in_doc(temp_response_json, CV_template, output_docx_version, analyst_response)


if __name__ == "__main__":
    asyncio.run(create_course_validation())
