"""
Assessment Tools

Tool implementations for Assessment Agent - SAQ/PP/CS assessment generation.

Author: Courseware Generator Team
Date: 26 January 2026
"""

import json


async def generate_saq_questions(
    fg_data_json: str,
    slides_data: str = "",
    model_choice: str = "claude-sonnet-4"
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
    from generate_assessment.utils.claude_agentic_SAQ import generate_saq

    fg_data = json.loads(fg_data_json)
    slides = slides_data if slides_data else None

    result = await generate_saq(
        fg_data=fg_data,
        slides_data=slides,
        model_choice=model_choice
    )
    return json.dumps({"status": "success", "type": "SAQ", "data": result})


async def generate_practical_performance(
    fg_data_json: str,
    slides_data: str = "",
    model_choice: str = "claude-sonnet-4"
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
    from generate_assessment.utils.claude_agentic_PP import generate_pp

    fg_data = json.loads(fg_data_json)
    slides = slides_data if slides_data else None

    result = await generate_pp(
        fg_data=fg_data,
        slides_data=slides,
        model_choice=model_choice
    )
    return json.dumps({"status": "success", "type": "PP", "data": result})


async def generate_case_study(
    fg_data_json: str,
    slides_data: str = "",
    model_choice: str = "claude-sonnet-4"
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
    from generate_assessment.utils.claude_agentic_CS import generate_cs

    fg_data = json.loads(fg_data_json)
    slides = slides_data if slides_data else None

    result = await generate_cs(
        fg_data=fg_data,
        slides_data=slides,
        model_choice=model_choice
    )
    return json.dumps({"status": "success", "type": "CS", "data": result})


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


async def interpret_fg_content(
    raw_data_json: str,
    model_choice: str = "claude-sonnet-4"
) -> str:
    """
    Use AI to interpret and structure FG content.

    Args:
        raw_data_json: Raw parsed FG data as JSON string
        model_choice: Model to use for interpretation

    Returns:
        Structured FG data as JSON string
    """
    import anthropic

    raw_data = json.loads(raw_data_json)

    client = anthropic.Anthropic()

    prompt = f"""Analyze this Facilitator Guide content and extract:
1. Learning Outcomes (LOs)
2. Topics covered
3. Key activities
4. Assessment criteria

Content:
{json.dumps(raw_data, indent=2)}

Return a structured JSON with these sections."""

    response = client.messages.create(
        model="claude-sonnet-4-20250514",
        max_tokens=4096,
        messages=[
            {"role": "user", "content": prompt}
        ]
    )

    return response.content[0].text
