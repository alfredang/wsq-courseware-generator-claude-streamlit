"""
Course Proposal (CP) Tools

Tool implementations for CP Agent - Course Proposal generation from TSC documents.

Author: Courseware Generator Team
Date: 26 January 2026
"""

import json
import os


def parse_tsc_document(file_path: str, output_path: str = "generate_cp/json_output/output_TSC.json") -> str:
    """
    Parse a TSC document (DOCX) and extract structured data.

    Args:
        file_path: Path to the TSC document file
        output_path: Path to save the parsed JSON output

    Returns:
        JSON string containing the parsed TSC data
    """
    from generate_cp.utils.document_parser import parse_document

    # Ensure output directory exists
    os.makedirs(os.path.dirname(output_path), exist_ok=True)

    # Parse the document
    parse_document(file_path, output_path)

    # Load and return the parsed data as JSON string
    with open(output_path, 'r', encoding='utf-8') as f:
        data = json.load(f)
    return json.dumps(data)


async def run_tsc_parsing_agent(tsc_data_json: str, model_choice: str = "claude-sonnet-4") -> str:
    """
    Run the TSC parsing agent to clean and structure TSC data.

    Args:
        tsc_data_json: Raw parsed TSC data as JSON string
        model_choice: Model to use for parsing

    Returns:
        Cleaned and structured TSC data as JSON string
    """
    from generate_cp.agents.openai_tsc_agent import run_tsc_agent

    tsc_data = json.loads(tsc_data_json)
    result = await run_tsc_agent(
        tsc_data=tsc_data,
        model_choice=model_choice,
        stream_to_console=False
    )
    return json.dumps(result)


async def run_extraction_pipeline(tsc_data_json: str, model_choice: str = "claude-sonnet-4") -> str:
    """
    Run the extraction team to extract course information from TSC data.

    This extracts:
    - Course Information (title, hours, industry)
    - Learning Outcomes (LOs, K statements, A statements)
    - TSC and Topics
    - Assessment Methods

    Args:
        tsc_data_json: Structured TSC data as JSON string
        model_choice: Model to use for extraction

    Returns:
        Extracted course information as JSON string
    """
    from generate_cp.agents.openai_extraction_team import run_extraction_team

    tsc_data = json.loads(tsc_data_json)
    result = await run_extraction_team(
        data=tsc_data,
        model_choice=model_choice,
        stream_to_console=False
    )
    return json.dumps(result)


async def run_research_pipeline(ensemble_output_json: str, model_choice: str = "claude-sonnet-4") -> str:
    """
    Run the research team for job role analysis and course enhancement.

    This generates:
    - Job roles related to the course
    - Industry relevance analysis
    - Course recommendations

    Args:
        ensemble_output_json: Extracted course data as JSON string
        model_choice: Model to use for research

    Returns:
        Research output as JSON string
    """
    from generate_cp.agents.openai_research_team import run_research_team

    ensemble_output = json.loads(ensemble_output_json)
    result = await run_research_team(
        ensemble_output=ensemble_output,
        model_choice=model_choice,
        stream_to_console=False
    )
    return json.dumps(result)


async def run_justification_pipeline(ensemble_output_json: str, model_choice: str = "claude-sonnet-4") -> str:
    """
    Run the assessment justification agent for Old CP format.

    Args:
        ensemble_output_json: Extracted course data as JSON string
        model_choice: Model to use

    Returns:
        Assessment justifications as JSON string
    """
    from generate_cp.agents.openai_justification_agent import run_assessment_justification_agent

    ensemble_output = json.loads(ensemble_output_json)
    result = await run_assessment_justification_agent(
        ensemble_output=ensemble_output,
        model_choice=model_choice,
        stream_to_console=False
    )
    return json.dumps(result)


def generate_cp_document(mapping_data_json: str, template_path: str, output_path: str) -> str:
    """
    Generate the final CP Word document from mapped data.

    Args:
        mapping_data_json: Mapped data for document placeholders as JSON string
        template_path: Path to the CP template document
        output_path: Path to save the generated document

    Returns:
        Path to the generated document
    """
    from generate_cp.utils.jinja_docu_replace import replace_placeholders_with_docxtpl

    mapping_data = json.loads(mapping_data_json)
    replace_placeholders_with_docxtpl(template_path, output_path, mapping_data)
    return output_path


def save_json_output(data_json: str, output_path: str) -> str:
    """
    Save data to a JSON file.

    Args:
        data_json: Data to save as JSON string
        output_path: Path to save the JSON file

    Returns:
        Path to the saved file
    """
    data = json.loads(data_json)
    os.makedirs(os.path.dirname(output_path), exist_ok=True)
    with open(output_path, 'w', encoding='utf-8') as f:
        json.dump(data, f, indent=2, ensure_ascii=False)
    return output_path
