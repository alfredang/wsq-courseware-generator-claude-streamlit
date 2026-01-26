"""
Excel Main Processing Module - OpenAI SDK Version.

This module handles the Excel generation pipeline using OpenAI SDK agents
instead of the Autogen framework.

Author: Migration from Autogen to OpenAI SDK
Date: 2026-01-20
"""

from generate_cp.utils.excel_replace_xml import process_excel_update, preserve_excel_metadata, cleanup_old_files
from generate_cp.utils.excel_conversion_pipeline import map_new_key_names_excel, create_instructional_dataframe
from generate_cp.agents.openai_excel_agents import (
    run_course_agent,
    run_ka_analysis_agent,
    run_im_agent
)
import json
import asyncio
import os
from generate_cp.utils.helpers import load_json_file

def combine_json_files(file1_path, file2_path):
    """
    Combines the data from two JSON files into a list of dictionaries.

    Args:
        file1_path (str): The path to the first JSON file (course_agent_data.json).
        file2_path (str): The path to the second JSON file (ka_agent_data.json).

    Returns:
        list: A list containing two dictionaries, one for course_overview and one for KA_Analysis.
    """
    with open(file1_path, 'r', encoding='utf-8') as f1:
        data1 = json.load(f1)
    with open(file2_path, 'r', encoding='utf-8') as f2:
        data2 = json.load(f2)

    # Handle null data
    if data1 is None:
        print(f"Warning: {file1_path} contains null data. Using empty dict.")
        data1 = {}
    if data2 is None:
        print(f"Warning: {file2_path} contains null data. Using empty dict.")
        data2 = {}

    combined_data = [
        data1,
        data2
    ]
    return combined_data

async def process_excel(model_choice: str) -> None:
    """
    Process Excel generation using OpenAI SDK agents.

    This replaces the Autogen-based implementation with direct OpenAI API calls.
    The output format and file paths remain identical for backward compatibility.

    Args:
        model_choice: The model to use (e.g., "DeepSeek-Chat", "GPT-4o-Mini")
    """
    json_data_path = "generate_cp/json_output/generated_mapping.json"
    excel_template_path = "generate_cp/templates/CP_excel_template.xlsx"
    output_excel_path_modified = "generate_cp/output_docs/CP_template_updated_cells_output.xlsx"
    output_excel_path_preserved = "generate_cp/output_docs/CP_template_metadata_preserved.xlsx"
    ensemble_output_path = "generate_cp/json_output/ensemble_output.json"

    # Load the existing JSON data
    with open('generate_cp/json_output/research_output.json', 'r', encoding='utf-8') as f:
        research_output = json.load(f)
    with open('generate_cp/json_output/ensemble_output.json', 'r', encoding='utf-8') as f:
        ensemble_output = json.load(f)

    # Validate loaded data
    if ensemble_output is None or not isinstance(ensemble_output, dict):
        print("Error: ensemble_output.json contains null or invalid data.")
        return
    if research_output is None:
        print("Warning: research_output.json contains null data. Using empty dict.")
        research_output = {}

    # --- Course Agent (OpenAI SDK) ---
    # Replaces: create_course_agent() + Console(stream) + save_state() + extract_agent_json()
    course_agent_data = await run_course_agent(
        ensemble_output=ensemble_output,
        model_choice=model_choice,
        stream_to_console=True
    )
    with open("generate_cp/json_output/course_agent_data.json", "w", encoding="utf-8") as f:
        json.dump(course_agent_data, f)

    # Reload ensemble_output for subsequent agents
    with open('generate_cp/json_output/ensemble_output.json', 'r', encoding='utf-8') as f:
        ensemble_output = json.load(f)

    # --- KA Analysis Agent (OpenAI SDK) ---
    # Replaces: create_ka_analysis_agent() + Console(stream) + save_state() + extract_agent_json()
    instructional_methods_data = create_instructional_dataframe(ensemble_output)
    print(instructional_methods_data)

    ka_agent_data = await run_ka_analysis_agent(
        ensemble_output=ensemble_output,
        instructional_methods_data=instructional_methods_data,
        model_choice=model_choice,
        stream_to_console=True
    )
    with open("generate_cp/json_output/ka_agent_data.json", "w", encoding="utf-8") as out:
        json.dump(ka_agent_data, out, indent=2)

    # Combine the JSON files
    excel_data = combine_json_files(
        "generate_cp/json_output/course_agent_data.json",
        "generate_cp/json_output/ka_agent_data.json"
    )

    # --- Instructional Methods Agent (OpenAI SDK) ---
    # Replaces: create_instructional_methods_agent() + Console(stream) + save_state() + extract_agent_json()
    with open('generate_cp/json_output/instructional_methods.json', 'r', encoding='utf-8') as f:
        instructional_methods_descriptions = json.load(f)
    if instructional_methods_descriptions is None:
        print("Warning: instructional_methods.json contains null data. Using empty dict.")
        instructional_methods_descriptions = {}

    im_agent_data = await run_im_agent(
        ensemble_output=ensemble_output,
        instructional_methods_json=instructional_methods_descriptions,
        model_choice=model_choice,
        stream_to_console=True
    )
    with open("generate_cp/json_output/im_agent_data.json", "w", encoding="utf-8") as out:
        json.dump(im_agent_data, out, indent=2)

    # Write the combined data to excel_data.json
    with open("generate_cp/json_output/excel_data.json", "w", encoding="utf-8") as out:
        json.dump(excel_data, out, indent=2)

    generated_mapping_path = "generate_cp/json_output/generated_mapping.json"
    generated_mapping = load_json_file(generated_mapping_path)
    if generated_mapping is None:
        print("Warning: generated_mapping.json contains null data. Using empty dict.")
        generated_mapping = {}

    output_json_file = "generate_cp/json_output/generated_mapping.json"
    excel_data_path = "generate_cp/json_output/excel_data.json"

    map_new_key_names_excel(generated_mapping_path, generated_mapping, output_json_file, excel_data_path, ensemble_output)

    # Cleanup old files before generating new ones
    cleanup_old_files(output_excel_path_modified, output_excel_path_preserved)

    # Process Excel update using XML-based code
    process_excel_update(json_data_path, excel_template_path, output_excel_path_modified, ensemble_output_path)

    # Preserve metadata from template
    preserve_excel_metadata(excel_template_path, output_excel_path_modified, output_excel_path_preserved)
