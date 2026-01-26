"""
Assessment Agent

This agent handles generation of assessment materials:
- Short Answer Questions (SAQ)
- Practical Performance (PP)
- Case Studies (CS)

Author: Courseware Generator Team
Date: 26 January 2026
"""

from agents import function_tool
from courseware_agents.base import create_agent
import json


@function_tool
async def generate_saq_questions(
    fg_data_json: str,
    slides_data: str = "",
    model_choice: str = "DeepSeek-Chat"
) -> str:
    """
    Generate Short Answer Questions (SAQ) assessment.

    Args:
        fg_data_json: Facilitator Guide data as JSON string
        slides_data: Optional slide deck content as text
        model_choice: Model to use for generation

    Returns:
        Generated SAQ questions and answers as JSON string
    """
    from generate_assessment.utils.openai_agentic_SAQ import generate_saq

    fg_data = json.loads(fg_data_json)
    slides = slides_data if slides_data else None

    result = await generate_saq(
        fg_data=fg_data,
        slides_data=slides,
        model_choice=model_choice
    )
    return json.dumps({"status": "success", "type": "SAQ", "data": result})


@function_tool
async def generate_practical_performance(
    fg_data_json: str,
    slides_data: str = "",
    model_choice: str = "DeepSeek-Chat"
) -> str:
    """
    Generate Practical Performance (PP) assessment.

    Args:
        fg_data_json: Facilitator Guide data as JSON string
        slides_data: Optional slide deck content as text
        model_choice: Model to use for generation

    Returns:
        Generated PP assessment as JSON string
    """
    from generate_assessment.utils.openai_agentic_PP import generate_pp

    fg_data = json.loads(fg_data_json)
    slides = slides_data if slides_data else None

    result = await generate_pp(
        fg_data=fg_data,
        slides_data=slides,
        model_choice=model_choice
    )
    return json.dumps({"status": "success", "type": "PP", "data": result})


@function_tool
async def generate_case_study(
    fg_data_json: str,
    slides_data: str = "",
    model_choice: str = "DeepSeek-Chat"
) -> str:
    """
    Generate Case Study (CS) assessment.

    Args:
        fg_data_json: Facilitator Guide data as JSON string
        slides_data: Optional slide deck content as text
        model_choice: Model to use for generation

    Returns:
        Generated case study as JSON string
    """
    from generate_assessment.utils.openai_agentic_CS import generate_cs

    fg_data = json.loads(fg_data_json)
    slides = slides_data if slides_data else None

    result = await generate_cs(
        fg_data=fg_data,
        slides_data=slides,
        model_choice=model_choice
    )
    return json.dumps({"status": "success", "type": "CS", "data": result})


@function_tool
def parse_facilitator_guide(file_path: str) -> str:
    """
    Parse a Facilitator Guide document to extract structure.

    Args:
        file_path: Path to the FG document (DOCX)

    Returns:
        Parsed FG data as JSON string
    """
    from docx import Document
    from docx.text.paragraph import Paragraph
    from docx.oxml.text.paragraph import CT_P
    from docx.oxml.table import CT_Tbl
    from docx.table import Table

    doc = Document(file_path)
    data = {"content": [], "tables": []}

    for element in doc.element.body:
        if isinstance(element, CT_P):
            para = Paragraph(element, doc)
            text = para.text.strip()
            if text:
                data["content"].append(text)
        elif isinstance(element, CT_Tbl):
            table = Table(element, doc)
            table_data = []
            for row in table.rows:
                row_data = [cell.text.strip() for cell in row.cells]
                table_data.append(row_data)
            data["tables"].append(table_data)

    return json.dumps(data)


@function_tool
async def interpret_fg_content(
    raw_data_json: str,
    model_choice: str = "DeepSeek-Chat"
) -> str:
    """
    Use AI to interpret and structure FG content.

    Args:
        raw_data_json: Raw parsed FG data as JSON string
        model_choice: Model to use for interpretation

    Returns:
        Structured FG data as JSON string
    """
    from settings.model_configs import get_model_config
    from openai import OpenAI

    raw_data = json.loads(raw_data_json)
    config = get_model_config(model_choice)

    client = OpenAI(
        api_key=config["config"]["api_key"],
        base_url=config["config"]["base_url"]
    )

    prompt = f"""Analyze this Facilitator Guide content and extract:
1. Learning Outcomes (LOs)
2. Topics covered
3. Key activities
4. Assessment criteria

Content:
{json.dumps(raw_data, indent=2)}

Return a structured JSON with these sections."""

    response = client.chat.completions.create(
        model=config["config"]["model"],
        temperature=config["config"]["temperature"],
        messages=[
            {"role": "system", "content": "You are an expert at analyzing educational documents."},
            {"role": "user", "content": prompt}
        ],
        response_format={"type": "json_object"}
    )

    return response.choices[0].message.content


# System instructions for the Assessment Agent
ASSESSMENT_AGENT_INSTRUCTIONS = """You are the Assessment Agent, specialized in generating assessment materials for courseware.

## Assessment Types

1. **SAQ** - Short Answer Questions for knowledge verification
2. **PP** - Practical Performance for hands-on skill assessment
3. **CS** - Case Studies for scenario-based assessment

## Workflow

1. Parse FG document: `parse_facilitator_guide(file_path)`
2. Interpret content: `interpret_fg_content(raw_data_json)`
3. Generate assessments using the specific tool

## Important Notes

- All data is passed as JSON strings
- Assessments align with learning outcomes
- Include clear marking criteria
"""

# Create the Assessment Agent instance
assessment_agent = create_agent(
    name="Assessment Agent",
    instructions=ASSESSMENT_AGENT_INSTRUCTIONS,
    tools=[
        generate_saq_questions,
        generate_practical_performance,
        generate_case_study,
        parse_facilitator_guide,
        interpret_fg_content,
    ],
    model_name="DeepSeek-Chat",
    handoff_description="Specialized agent for generating SAQ, PP, and Case Study assessments"
)
