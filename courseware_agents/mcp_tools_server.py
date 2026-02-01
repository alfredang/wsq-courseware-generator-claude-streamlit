"""
MCP Tools Server

This MCP server exposes all courseware tools to the Claude Agent SDK.
It wraps the 26 custom tools and makes them accessible via the
Model Context Protocol.

Author: Courseware Generator Team
Date: 26 January 2026
"""

import asyncio
import json
from typing import Any
from mcp.server import Server
from mcp.types import Tool, TextContent

# Create the MCP server
app = Server("courseware-tools")

# Import all tool implementations
from courseware_agents.tools.cp_tools import (
    parse_tsc_document,
    run_tsc_parsing_agent,
    run_extraction_pipeline,
    run_research_pipeline,
    run_justification_pipeline,
    generate_cp_document,
    save_json_output,
)

from courseware_agents.tools.courseware_tools import (
    generate_assessment_plan,
    generate_facilitator_guide,
    generate_learner_guide,
    generate_lesson_plan,
    generate_timetable,
)

from courseware_agents.tools.assessment_tools import (
    generate_saq_questions,
    generate_practical_performance,
    generate_case_study,
    parse_facilitator_guide,
    interpret_fg_content,
)

from courseware_agents.tools.brochure_tools import (
    scrape_course_info,
    generate_brochure_html,
    generate_brochure_pdf,
    create_brochure_from_cp,
    generate_marketing_content,
)

from courseware_agents.tools.document_tools import (
    extract_document_entities,
    verify_against_training_records,
    verify_company_uen,
    check_document_completeness,
)


# Tool definitions with JSON schemas
TOOL_DEFINITIONS = [
    # CP Agent Tools
    Tool(
        name="parse_tsc_document",
        description="Parse a TSC document (DOCX) and extract structured data",
        inputSchema={
            "type": "object",
            "properties": {
                "file_path": {"type": "string", "description": "Path to the TSC document file"},
                "output_path": {"type": "string", "description": "Path to save the parsed JSON output", "default": "generate_cp/json_output/output_TSC.json"}
            },
            "required": ["file_path"]
        }
    ),
    Tool(
        name="run_tsc_parsing_agent",
        description="Run the TSC parsing agent to clean and structure TSC data",
        inputSchema={
            "type": "object",
            "properties": {
                "tsc_data_json": {"type": "string", "description": "Raw parsed TSC data as JSON string"},
                "model_choice": {"type": "string", "description": "Model to use for parsing", "default": "claude-sonnet-4"}
            },
            "required": ["tsc_data_json"]
        }
    ),
    Tool(
        name="run_extraction_pipeline",
        description="Extract course information, learning outcomes, topics, and assessment methods from TSC data",
        inputSchema={
            "type": "object",
            "properties": {
                "tsc_data_json": {"type": "string", "description": "Structured TSC data as JSON string"},
                "model_choice": {"type": "string", "description": "Model to use for extraction", "default": "claude-sonnet-4"}
            },
            "required": ["tsc_data_json"]
        }
    ),
    Tool(
        name="run_research_pipeline",
        description="Run job role analysis and course enhancement research",
        inputSchema={
            "type": "object",
            "properties": {
                "ensemble_output_json": {"type": "string", "description": "Extracted course data as JSON string"},
                "model_choice": {"type": "string", "description": "Model to use for research", "default": "claude-sonnet-4"}
            },
            "required": ["ensemble_output_json"]
        }
    ),
    Tool(
        name="run_justification_pipeline",
        description="Generate assessment justifications for Old CP format",
        inputSchema={
            "type": "object",
            "properties": {
                "ensemble_output_json": {"type": "string", "description": "Extracted course data as JSON string"},
                "model_choice": {"type": "string", "description": "Model to use", "default": "claude-sonnet-4"}
            },
            "required": ["ensemble_output_json"]
        }
    ),
    Tool(
        name="generate_cp_document",
        description="Generate the final CP Word document from mapped data",
        inputSchema={
            "type": "object",
            "properties": {
                "mapping_data_json": {"type": "string", "description": "Mapped data for document placeholders as JSON string"},
                "template_path": {"type": "string", "description": "Path to the CP template document"},
                "output_path": {"type": "string", "description": "Path to save the generated document"}
            },
            "required": ["mapping_data_json", "template_path", "output_path"]
        }
    ),
    Tool(
        name="save_json_output",
        description="Save data to a JSON file",
        inputSchema={
            "type": "object",
            "properties": {
                "data_json": {"type": "string", "description": "Data to save as JSON string"},
                "output_path": {"type": "string", "description": "Path to save the JSON file"}
            },
            "required": ["data_json", "output_path"]
        }
    ),
    
    # Courseware Agent Tools
    Tool(
        name="generate_assessment_plan",
        description="Generate Assessment Plan (AP) document from course data",
        inputSchema={
            "type": "object",
            "properties": {
                "course_data_json": {"type": "string", "description": "Course proposal data as JSON string"},
                "organization_json": {"type": "string", "description": "Organization details as JSON string"},
                "model_choice": {"type": "string", "description": "Model to use for generation", "default": "claude-sonnet-4"}
            },
            "required": ["course_data_json", "organization_json"]
        }
    ),
    Tool(
        name="generate_facilitator_guide",
        description="Generate Facilitator Guide (FG) document",
        inputSchema={
            "type": "object",
            "properties": {
                "course_data_json": {"type": "string", "description": "Course proposal data as JSON string"},
                "organization_json": {"type": "string", "description": "Organization details as JSON string"},
                "model_choice": {"type": "string", "description": "Model to use for generation", "default": "claude-sonnet-4"}
            },
            "required": ["course_data_json", "organization_json"]
        }
    ),
    Tool(
        name="generate_learner_guide",
        description="Generate Learner Guide (LG) document",
        inputSchema={
            "type": "object",
            "properties": {
                "course_data_json": {"type": "string", "description": "Course proposal data as JSON string"},
                "organization_json": {"type": "string", "description": "Organization details as JSON string"},
                "model_choice": {"type": "string", "description": "Model to use for generation", "default": "claude-sonnet-4"}
            },
            "required": ["course_data_json", "organization_json"]
        }
    ),
    Tool(
        name="generate_lesson_plan",
        description="Generate Lesson Plan (LP) document",
        inputSchema={
            "type": "object",
            "properties": {
                "course_data_json": {"type": "string", "description": "Course proposal data as JSON string"},
                "organization_json": {"type": "string", "description": "Organization details as JSON string"},
                "model_choice": {"type": "string", "description": "Model to use for generation", "default": "claude-sonnet-4"}
            },
            "required": ["course_data_json", "organization_json"]
        }
    ),
    Tool(
        name="generate_timetable",
        description="Generate course timetable",
        inputSchema={
            "type": "object",
            "properties": {
                "course_data_json": {"type": "string", "description": "Course proposal data as JSON string"},
                "start_date": {"type": "string", "description": "Course start date (YYYY-MM-DD)"},
                "organization_json": {"type": "string", "description": "Organization details as JSON string"}
            },
            "required": ["course_data_json", "start_date", "organization_json"]
        }
    ),
    
    # Assessment Agent Tools
    Tool(
        name="generate_saq_questions",
        description="Generate Short Answer Questions (SAQ) assessment",
        inputSchema={
            "type": "object",
            "properties": {
                "fg_data_json": {"type": "string", "description": "Facilitator Guide data as JSON string"},
                "slides_data": {"type": "string", "description": "Optional slide deck content as text", "default": ""},
                "model_choice": {"type": "string", "description": "Model to use for generation", "default": "claude-sonnet-4"}
            },
            "required": ["fg_data_json"]
        }
    ),
    Tool(
        name="generate_practical_performance",
        description="Generate Practical Performance (PP) assessment",
        inputSchema={
            "type": "object",
            "properties": {
                "fg_data_json": {"type": "string", "description": "Facilitator Guide data as JSON string"},
                "slides_data": {"type": "string", "description": "Optional slide deck content as text", "default": ""},
                "model_choice": {"type": "string", "description": "Model to use for generation", "default": "claude-sonnet-4"}
            },
            "required": ["fg_data_json"]
        }
    ),
    Tool(
        name="generate_case_study",
        description="Generate Case Study (CS) assessment",
        inputSchema={
            "type": "object",
            "properties": {
                "fg_data_json": {"type": "string", "description": "Facilitator Guide data as JSON string"},
                "slides_data": {"type": "string", "description": "Optional slide deck content as text", "default": ""},
                "model_choice": {"type": "string", "description": "Model to use for generation", "default": "claude-sonnet-4"}
            },
            "required": ["fg_data_json"]
        }
    ),
    Tool(
        name="parse_facilitator_guide",
        description="Parse a Facilitator Guide document to extract structure",
        inputSchema={
            "type": "object",
            "properties": {
                "file_path": {"type": "string", "description": "Path to the FG document (DOCX)"}
            },
            "required": ["file_path"]
        }
    ),
    Tool(
        name="interpret_fg_content",
        description="Use AI to interpret and structure FG content",
        inputSchema={
            "type": "object",
            "properties": {
                "raw_data_json": {"type": "string", "description": "Raw parsed FG data as JSON string"},
                "model_choice": {"type": "string", "description": "Model to use for interpretation", "default": "claude-sonnet-4"}
            },
            "required": ["raw_data_json"]
        }
    ),
    
    # Brochure Agent Tools
    Tool(
        name="scrape_course_info",
        description="Scrape course information from a MySkillsFuture or training provider URL",
        inputSchema={
            "type": "object",
            "properties": {
                "url": {"type": "string", "description": "URL of the course page to scrape"}
            },
            "required": ["url"]
        }
    ),
    Tool(
        name="generate_brochure_html",
        description="Generate brochure HTML from course data",
        inputSchema={
            "type": "object",
            "properties": {
                "course_data_json": {"type": "string", "description": "Course information as JSON string"}
            },
            "required": ["course_data_json"]
        }
    ),
    Tool(
        name="generate_brochure_pdf",
        description="Generate PDF brochure from HTML content",
        inputSchema={
            "type": "object",
            "properties": {
                "html_content": {"type": "string", "description": "HTML content to convert"},
                "output_path": {"type": "string", "description": "Path to save the PDF"}
            },
            "required": ["html_content", "output_path"]
        }
    ),
    Tool(
        name="create_brochure_from_cp",
        description="Create brochure data from Course Proposal data",
        inputSchema={
            "type": "object",
            "properties": {
                "cp_data_json": {"type": "string", "description": "Course Proposal JSON data as string"}
            },
            "required": ["cp_data_json"]
        }
    ),
    Tool(
        name="generate_marketing_content",
        description="Use AI to generate compelling marketing content for the brochure",
        inputSchema={
            "type": "object",
            "properties": {
                "course_data_json": {"type": "string", "description": "Basic course information as JSON string"},
                "model_choice": {"type": "string", "description": "Model to use for content generation", "default": "claude-sonnet-4"}
            },
            "required": ["course_data_json"]
        }
    ),
    
    # Document Agent Tools
    Tool(
        name="extract_document_entities",
        description="Extract named entities from a document using AI",
        inputSchema={
            "type": "object",
            "properties": {
                "file_path": {"type": "string", "description": "Path to the document (PDF or image)"},
                "custom_instructions": {"type": "string", "description": "Custom extraction instructions", "default": "Extract the name of the person, company, UEN, masked NRIC, and document date."}
            },
            "required": ["file_path"]
        }
    ),
    Tool(
        name="verify_against_training_records",
        description="Verify extracted entities against training records",
        inputSchema={
            "type": "object",
            "properties": {
                "extracted_entities_json": {"type": "string", "description": "Entities as JSON string"},
                "threshold": {"type": "number", "description": "Minimum similarity score for match (0-100)", "default": 80.0}
            },
            "required": ["extracted_entities_json"]
        }
    ),
    Tool(
        name="verify_company_uen",
        description="Verify a company UEN against ACRA database",
        inputSchema={
            "type": "object",
            "properties": {
                "uen": {"type": "string", "description": "The UEN to verify"}
            },
            "required": ["uen"]
        }
    ),
    Tool(
        name="check_document_completeness",
        description="Check if a document has all required sections/fields",
        inputSchema={
            "type": "object",
            "properties": {
                "file_path": {"type": "string", "description": "Path to the document"}
            },
            "required": ["file_path"]
        }
    ),
]

# Tool function mapping
TOOL_FUNCTIONS = {
    # CP Tools
    "parse_tsc_document": parse_tsc_document,
    "run_tsc_parsing_agent": run_tsc_parsing_agent,
    "run_extraction_pipeline": run_extraction_pipeline,
    "run_research_pipeline": run_research_pipeline,
    "run_justification_pipeline": run_justification_pipeline,
    "generate_cp_document": generate_cp_document,
    "save_json_output": save_json_output,
    # Courseware Tools
    "generate_assessment_plan": generate_assessment_plan,
    "generate_facilitator_guide": generate_facilitator_guide,
    "generate_learner_guide": generate_learner_guide,
    "generate_lesson_plan": generate_lesson_plan,
    "generate_timetable": generate_timetable,
    # Assessment Tools
    "generate_saq_questions": generate_saq_questions,
    "generate_practical_performance": generate_practical_performance,
    "generate_case_study": generate_case_study,
    "parse_facilitator_guide": parse_facilitator_guide,
    "interpret_fg_content": interpret_fg_content,
    # Brochure Tools
    "scrape_course_info": scrape_course_info,
    "generate_brochure_html": generate_brochure_html,
    "generate_brochure_pdf": generate_brochure_pdf,
    "create_brochure_from_cp": create_brochure_from_cp,
    "generate_marketing_content": generate_marketing_content,
    # Document Tools
    "extract_document_entities": extract_document_entities,
    "verify_against_training_records": verify_against_training_records,
    "verify_company_uen": verify_company_uen,
    "check_document_completeness": check_document_completeness,
}

# Async tools that need special handling
ASYNC_TOOLS = {
    "run_tsc_parsing_agent",
    "run_extraction_pipeline",
    "run_research_pipeline",
    "run_justification_pipeline",
    "generate_assessment_plan",
    "generate_facilitator_guide",
    "generate_learner_guide",
    "generate_lesson_plan",
    "generate_saq_questions",
    "generate_practical_performance",
    "generate_case_study",
    "interpret_fg_content",
    "generate_marketing_content",
}


@app.list_tools()
async def list_tools() -> list[Tool]:
    """Return list of available tools."""
    return TOOL_DEFINITIONS


@app.call_tool()
async def call_tool(name: str, arguments: dict) -> list[TextContent]:
    """Execute a tool and return the result."""
    if name not in TOOL_FUNCTIONS:
        return [TextContent(type="text", text=json.dumps({"error": f"Unknown tool: {name}"}))]
    
    try:
        func = TOOL_FUNCTIONS[name]
        
        # Handle async vs sync functions
        if name in ASYNC_TOOLS:
            result = await func(**arguments)
        else:
            result = func(**arguments)
        
        return [TextContent(type="text", text=result if isinstance(result, str) else json.dumps(result))]
    except Exception as e:
        return [TextContent(type="text", text=json.dumps({"error": str(e)}))]


async def main():
    """Run the MCP server."""
    from mcp.server.stdio import stdio_server
    
    async with stdio_server() as (read_stream, write_stream):
        await app.run(
            read_stream,
            write_stream,
            app.create_initialization_options()
        )


if __name__ == "__main__":
    asyncio.run(main())
