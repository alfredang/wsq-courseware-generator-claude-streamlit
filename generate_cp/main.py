"""
Main Course Proposal Generation Module - OpenAI SDK Version.

This module orchestrates the entire course proposal generation pipeline
using OpenAI SDK agents instead of the Autogen framework.

Author: Migration from Autogen to OpenAI SDK
Date: 2026-01-20
"""

from generate_cp.utils.document_parser import parse_document
from generate_cp.agents.openai_extraction_team import run_extraction_team
from generate_cp.agents.openai_research_team import run_research_team
from generate_cp.agents.openai_justification_agent import run_assessment_justification_agent, recreate_assessment_phrasing_dynamic
from generate_cp.agents.openai_tsc_agent import run_tsc_agent
from generate_cp.utils.helpers import (
    rename_keys_in_json_file,
    update_knowledge_ability_mapping,
    validate_knowledge_and_ability,
    flatten_json,
)
from generate_cp.utils.json_mapping import map_values
from generate_cp.utils.jinja_docu_replace import replace_placeholders_with_docxtpl
import json
from generate_cp.cv_main import create_course_validation
import streamlit as st
from generate_cp.excel_main import process_excel
from company.company_manager import get_selected_company, get_company_template


async def main(input_tsc) -> None:
    """
    Main entry point for course proposal generation.

    This orchestrates the full pipeline using OpenAI SDK agents:
    1. TSC Agent - Parse and correct TSC data
    2. Extraction Team - Extract course information
    3. Research Team - Generate research analysis
    4. Justification Agent (Old CP only) - Generate assessment justifications
    5. Course Validation - Generate validation surveys
    6. Excel Processing (New CP only) - Generate Excel documents

    Args:
        input_tsc: Path to the TSC input document
    """
    model_choice = st.session_state.get('selected_model')
    if not model_choice:
        st.error("❌ No model selected. Please select a model from the sidebar.")
        return
    cp_type = st.session_state.get('cp_type', "New CP")

    # Parse document
    parse_document(input_tsc, "generate_cp/json_output/output_TSC.json")

    # Load the JSON file
    with open("generate_cp/json_output/output_TSC.json", 'r', encoding='utf-8') as file:
        tsc_data = json.load(file)

    # --- TSC Agent Process (OpenAI SDK) ---
    # Replaces: create_tsc_agent() + Console(stream) + save_state() + extract_tsc_agent_json()
    tsc_parsed_data = await run_tsc_agent(
        tsc_data=tsc_data,
        model_choice=model_choice,
        stream_to_console=True
    )
    if not tsc_parsed_data:
        st.error("TSC Agent failed to return data. This may be due to an API rate limit. Please try again later or switch to a different model.")
        return
    with open("generate_cp/json_output/output_TSC.json", "w", encoding="utf-8") as out:
        json.dump(tsc_parsed_data, out, indent=2)

    # --- Extraction Team Process (OpenAI SDK) ---
    # Replaces: create_extraction_team() + Console(stream) + save_state() + extract_final_aggregator_json()
    with open("generate_cp/json_output/output_TSC.json", 'r', encoding='utf-8') as file:
        tsc_data = json.load(file)

    aggregator_data = await run_extraction_team(
        data=tsc_data,
        model_choice=model_choice,
        stream_to_console=True
    )
    if not aggregator_data:
        st.error("Extraction Team failed to return data. This may be due to an API rate limit. Please try again later or switch to a different model.")
        return
    with open("generate_cp/json_output/ensemble_output.json", "w", encoding="utf-8") as out:
        json.dump(aggregator_data, out, indent=2)

    # JSON key validation for ensemble_output to ensure key names are constant
    rename_keys_in_json_file("generate_cp/json_output/ensemble_output.json")

    update_knowledge_ability_mapping('generate_cp/json_output/output_TSC.json', 'generate_cp/json_output/ensemble_output.json')

    validate_knowledge_and_ability()

    # --- Research Team Process (OpenAI SDK) ---
    # Replaces: create_research_team() + Console(stream) + save_state() + extract_final_editor_json()
    with open("generate_cp/json_output/ensemble_output.json", 'r', encoding='utf-8') as file:
        ensemble_output = json.load(file)

    editor_data = await run_research_team(
        ensemble_output=ensemble_output,
        model_choice=model_choice,
        stream_to_console=True
    )
    if not editor_data:
        st.error("Research Team failed to return data. This may be due to an API rate limit. Please try again later or switch to a different model.")
        return
    with open("generate_cp/json_output/research_output.json", "w", encoding="utf-8") as out:
        json.dump(editor_data, out, indent=2)

    with open("generate_cp/json_output/ensemble_output.json", 'r', encoding='utf-8') as file:
        ensemble_output = json.load(file)

    if cp_type == "Old CP":
        # --- Justification Agent Process (OpenAI SDK) ---
        # Replaces: run_assessment_justification_agent() + Console(stream) + save_state() + extract_final_agent_json()
        justification_data = await run_assessment_justification_agent(
            ensemble_output=ensemble_output,
            model_choice=model_choice,
            stream_to_console=True
        )
        with open("generate_cp/json_output/justification_debug.json", "w") as f:
            json.dump(justification_data, f)

        output_phrasing = recreate_assessment_phrasing_dynamic(justification_data)

        # Load the existing research_output.json
        with open('generate_cp/json_output/research_output.json', 'r', encoding='utf-8') as f:
            research_output = json.load(f)

        # Append the new output phrasing to the research_output
        if "Assessment Phrasing" not in research_output:
            research_output["Assessment Phrasing"] = []
        # Append the new result
        research_output["Assessment Phrasing"].append(output_phrasing)

        # Save the updated research_output.json
        with open('generate_cp/json_output/research_output.json', 'w', encoding='utf-8') as f:
            json.dump(research_output, f, indent=4)

    if cp_type == "New CP":
        with open('generate_cp/json_output/research_output.json', 'r', encoding='utf-8') as f:
            research_output = json.load(f)

    # Load mapping template with key:empty list pair
    with open('generate_cp/json_output/mapping_source.json', 'r', encoding='utf-8') as file:
        mapping_source = json.load(file)

    with open('generate_cp/json_output/ensemble_output.json', encoding='utf-8') as f:
        ensemble_output = json.load(f)

    # Get research_output for mapping
    with open('generate_cp/json_output/research_output.json', 'r', encoding='utf-8') as f:
        research_output = json.load(f)

    updated_mapping_source = map_values(mapping_source, ensemble_output, research_output)
    try:
        with open('generate_cp/json_output/generated_mapping.json', 'w') as json_file:
            json.dump(updated_mapping_source, json_file, indent=4)
        print(f"Output saved to json_output/generated_mapping.json")
    except IOError as e:
        print(f"Error saving JSON to file: {e}")

    # Load the JSON file
    with open('generate_cp/json_output/generated_mapping.json', 'r') as file:
        gmap = json.load(file)

    # Flatten the JSON
    flattened_gmap = flatten_json(gmap)

    # Save the flattened JSON back to the file
    output_filename = 'generate_cp/json_output/generated_mapping.json'
    try:
        with open(output_filename, 'w') as json_file:
            json.dump(flattened_gmap, json_file, indent=4)
        print(f"Output saved to {output_filename}")
    except IOError as e:
        print(f"Error saving JSON to file: {e}")

    # Get company template or fallback to default
    selected_company = get_selected_company()
    company_template = get_company_template("course_proposal")

    json_file = "generate_cp/json_output/generated_mapping.json"
    word_file = company_template if company_template else "generate_cp/templates/CP Template_jinja.docx"
    new_word_file = "generate_cp/output_docs/CP_output.docx"

    # Apply company branding to JSON data before template generation
    with open(json_file, 'r') as f:
        json_data = json.load(f)

    # Add company information to JSON data
    json_data['company_name'] = selected_company.get('name', 'Tertiary Infotech Pte Ltd')
    json_data['company_uen'] = selected_company.get('uen', '201200696W')
    json_data['company_address'] = selected_company.get('address', '')

    # Save updated JSON with company branding
    with open(json_file, 'w') as f:
        json.dump(json_data, f, indent=2)

    replace_placeholders_with_docxtpl(json_file, word_file, new_word_file)

    # Course Validation Form Process
    await create_course_validation(model_choice=model_choice)

    if cp_type == "New CP":
        # Excel processing
        await process_excel(model_choice=model_choice)
