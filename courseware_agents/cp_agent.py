"""
Course Proposal (CP) Agent

This agent handles Course Proposal generation from TSC documents.
It coordinates the extraction and research pipelines.

Author: Courseware Generator Team
Date: 26 January 2026
"""

from agents import function_tool
from courseware_agents.base import create_agent
import json
import os


@function_tool
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


@function_tool
async def run_tsc_parsing_agent(tsc_data_json: str, model_choice: str = "DeepSeek-Chat") -> str:
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


@function_tool
async def run_extraction_pipeline(tsc_data_json: str, model_choice: str = "DeepSeek-Chat") -> str:
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


@function_tool
async def run_research_pipeline(ensemble_output_json: str, model_choice: str = "DeepSeek-Chat") -> str:
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


@function_tool
async def run_justification_pipeline(ensemble_output_json: str, model_choice: str = "DeepSeek-Chat") -> str:
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


@function_tool
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


@function_tool
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


# System instructions for the CP Agent
CP_AGENT_INSTRUCTIONS = """You are the Course Proposal (CP) Agent, specialized in generating Course Proposal documents from TSC (Training Standards and Competencies) files.

## Your Capabilities

1. **Document Parsing**: Parse TSC documents (DOCX format) to extract raw data
2. **TSC Processing**: Clean and structure TSC data using the TSC parsing agent
3. **Data Extraction**: Extract course information, learning outcomes, and assessment methods
4. **Research Analysis**: Generate job role analysis and industry relevance
5. **Document Generation**: Create formatted CP Word documents

## Workflow

When a user wants to generate a Course Proposal:

1. **Receive TSC Document**
   - Get the file path to the TSC document
   - Use `parse_tsc_document` to parse it

2. **Process TSC Data**
   - Use `run_tsc_parsing_agent` to clean the raw data

3. **Extract Course Information**
   - Use `run_extraction_pipeline` to extract:
     - Course Information (title, hours, industry)
     - Learning Outcomes (LOs, K and A statements)
     - TSC and Topics
     - Assessment Methods

4. **Research Analysis**
   - Use `run_research_pipeline` to generate:
     - Relevant job roles
     - Industry analysis
     - Course recommendations

5. **Generate Document** (if requested)
   - Use `generate_cp_document` to create the final Word document

## Important Notes

- All data is passed as JSON strings between tools
- Always explain what you're doing at each step
- Report any errors or issues clearly
- Save intermediate outputs for debugging
- Default model is DeepSeek-Chat but can be changed

## Example Interaction

User: "Generate a Course Proposal from the TSC file at uploads/tsc_ai.docx"

Response: "I'll generate the Course Proposal. Let me:
1. Parse the TSC document
2. Process and extract the data
3. Run research analysis
4. Generate the CP document

Starting with document parsing..."
"""

# Create the CP Agent instance
cp_agent = create_agent(
    name="CP Agent",
    instructions=CP_AGENT_INSTRUCTIONS,
    tools=[
        parse_tsc_document,
        run_tsc_parsing_agent,
        run_extraction_pipeline,
        run_research_pipeline,
        run_justification_pipeline,
        generate_cp_document,
        save_json_output,
    ],
    model_name="DeepSeek-Chat",
    handoff_description="Specialized agent for Course Proposal (CP) generation from TSC documents"
)
