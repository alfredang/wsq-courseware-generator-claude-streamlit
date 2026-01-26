"""
Brochure Agent

This agent handles generation of course marketing brochures.
It can scrape course information from URLs and generate
professional brochure documents.

Author: Courseware Generator Team
Date: 26 January 2026
"""

from agents import function_tool
from courseware_agents.base import create_agent
from courseware_agents.schemas import BrochureAgentResponse, BrochureContent
import json


@function_tool
def scrape_course_info(url: str) -> str:
    """
    Scrape course information from a MySkillsFuture or training provider URL.

    Args:
        url: URL of the course page to scrape

    Returns:
        Extracted course information as JSON string
    """
    from generate_brochure.brochure_generation import web_scrape_course_info

    course_data = web_scrape_course_info(url)
    return json.dumps(course_data.to_dict())


@function_tool
def generate_brochure_html(course_data_json: str) -> str:
    """
    Generate brochure HTML from course data.

    Args:
        course_data_json: Course information as JSON string

    Returns:
        Generated HTML content
    """
    from pathlib import Path
    from jinja2 import Template

    course_data = json.loads(course_data_json)

    # Load brochure template
    template_dir = Path(__file__).resolve().parent.parent / "generate_brochure" / "brochure_template"
    template_path = template_dir / "brochure_template.html"

    if template_path.exists():
        with open(template_path, 'r', encoding='utf-8') as f:
            template_content = f.read()
        template = Template(template_content)
        return template.render(**course_data)
    else:
        # Generate basic HTML if template not found
        return f"""
        <html>
        <head><title>{course_data.get('course_title', 'Course Brochure')}</title></head>
        <body>
            <h1>{course_data.get('course_title', 'Course')}</h1>
            <p>{' '.join(course_data.get('course_description', []))}</p>
        </body>
        </html>
        """


@function_tool
def generate_brochure_pdf(html_content: str, output_path: str) -> str:
    """
    Generate PDF brochure from HTML content.

    Args:
        html_content: HTML content to convert
        output_path: Path to save the PDF

    Returns:
        Path to generated PDF file or error message
    """
    import os

    os.makedirs(os.path.dirname(output_path) if os.path.dirname(output_path) else '.', exist_ok=True)

    try:
        from xhtml2pdf import pisa
        with open(output_path, 'wb') as pdf_file:
            pisa_status = pisa.CreatePDF(html_content, dest=pdf_file)
        if pisa_status.err:
            return f"Error generating PDF: {pisa_status.err}"
        return output_path
    except ImportError:
        return "PDF generation library not available"


@function_tool
def create_brochure_from_cp(cp_data_json: str) -> str:
    """
    Create brochure data from Course Proposal data.

    Args:
        cp_data_json: Course Proposal JSON data as string

    Returns:
        Brochure data as JSON string
    """
    cp_data = json.loads(cp_data_json)

    course_info = cp_data.get("Course Information", {})
    learning_outcomes = cp_data.get("Learning Outcomes", {})
    tsc_topics = cp_data.get("TSC and Topics", {})

    tsc_title = tsc_topics.get("TSC Title", [""])
    if isinstance(tsc_title, list):
        tsc_title = tsc_title[0] if tsc_title else ""

    tsc_code = tsc_topics.get("TSC Code", [""])
    if isinstance(tsc_code, list):
        tsc_code = tsc_code[0] if tsc_code else ""

    brochure_data = {
        "course_title": course_info.get("Course Title", ""),
        "course_description": [
            f"This {course_info.get('Industry', '')} course provides comprehensive training "
            f"over {course_info.get('Course Duration (Number of Hours)', '')} hours."
        ],
        "learning_outcomes": learning_outcomes.get("Learning Outcomes", []),
        "tsc_title": tsc_title,
        "tsc_code": tsc_code,
        "tsc_framework": course_info.get("Industry", ""),
        "duration_hrs": str(course_info.get("Course Duration (Number of Hours)", "")),
        "session_days": "",
        "wsq_funding": {},
        "tgs_reference_no": "",
        "gst_exclusive_price": "",
        "gst_inclusive_price": "",
        "course_details_topics": [],
        "course_url": ""
    }

    topics = tsc_topics.get("Topics", [])
    for topic in topics:
        brochure_data["course_details_topics"].append({
            "title": topic,
            "subtopics": []
        })

    return json.dumps(brochure_data)


@function_tool
async def generate_marketing_content(
    course_data_json: str,
    model_choice: str = "GPT-4o-Mini"
) -> str:
    """
    Use AI to generate compelling marketing content for the brochure.

    Args:
        course_data_json: Basic course information as JSON string
        model_choice: Model to use for content generation

    Returns:
        Enhanced course data with marketing content as JSON string
    """
    from settings.model_configs import get_model_config
    from openai import OpenAI

    course_data = json.loads(course_data_json)
    config = get_model_config(model_choice)

    client = OpenAI(
        api_key=config["config"]["api_key"],
        base_url=config["config"]["base_url"]
    )

    prompt = f"""Create compelling marketing content for this course brochure:

Course Title: {course_data.get('course_title', '')}
Current Description: {' '.join(course_data.get('course_description', []))}
Learning Outcomes: {course_data.get('learning_outcomes', [])}
Industry: {course_data.get('tsc_framework', '')}

Generate:
1. An engaging tagline (one sentence)
2. An enhanced course description (2-3 sentences)
3. 3-5 key benefits for learners
4. A call-to-action statement

Return as JSON with keys: tagline, enhanced_description, benefits, cta"""

    response = client.chat.completions.create(
        model=config["config"]["model"],
        temperature=0.7,
        messages=[
            {"role": "system", "content": "You are a marketing copywriter for educational courses."},
            {"role": "user", "content": prompt}
        ],
        response_format={"type": "json_object"}
    )

    marketing = json.loads(response.choices[0].message.content)

    enhanced_data = course_data.copy()
    enhanced_data["tagline"] = marketing.get("tagline", "")
    enhanced_data["course_description"] = [marketing.get("enhanced_description", "")] + enhanced_data.get("course_description", [])
    enhanced_data["benefits"] = marketing.get("benefits", [])
    enhanced_data["cta"] = marketing.get("cta", "")

    return json.dumps(enhanced_data)


# System instructions for the Brochure Agent
BROCHURE_AGENT_INSTRUCTIONS = """You are the Brochure Agent, specialized in creating professional marketing brochures for courses.

## Capabilities

1. **Web Scraping**: `scrape_course_info(url)` - Extract course info from URLs
2. **Data Transform**: `create_brochure_from_cp(cp_json)` - Convert CP to brochure format
3. **Marketing Copy**: `generate_marketing_content(course_json)` - Generate engaging content
4. **HTML Generation**: `generate_brochure_html(course_json)` - Create HTML brochure
5. **PDF Generation**: `generate_brochure_pdf(html, path)` - Create PDF brochure

## Workflow

1. Get course data (from URL or CP)
2. Optionally enhance with marketing content
3. Generate HTML and/or PDF

All data is passed as JSON strings.
"""

# Create the Brochure Agent instance
brochure_agent = create_agent(
    name="Brochure Agent",
    instructions=BROCHURE_AGENT_INSTRUCTIONS,
    tools=[
        scrape_course_info,
        generate_brochure_html,
        generate_brochure_pdf,
        create_brochure_from_cp,
        generate_marketing_content,
    ],
    model_name="GPT-4o-Mini",
    handoff_description="Specialized agent for creating course marketing brochures"
)
