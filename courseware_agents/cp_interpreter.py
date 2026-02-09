"""
Course Proposal (CP) Interpreter Agent

Reads parsed CP text and extracts structured course data as JSON.
Used by the courseware generation page to get context for template filling.
"""

import json
import os
from courseware_agents.base import run_agent_json

SYSTEM_PROMPT = """You are an expert WSQ (Workforce Skills Qualifications) course data extractor.

Your task is to read a parsed Course Proposal document and extract structured course information
into a specific JSON format. Be thorough and accurate.

CRITICAL: Return ONLY a valid JSON object with no additional text or explanation.

The JSON must follow this exact schema:
{
    "Course_Title": "string",
    "TSC_Title": "string (Technical Skills & Competency title)",
    "TSC_Code": "string (e.g., ICT-XXX-3.1)",
    "TSC_Category": "string",
    "TSC_Description": "string",
    "TSC_Sector": "string",
    "Proficiency_Level": "string (e.g., Level 3)",
    "Proficiency_Description": "string",
    "Skills_Framework": "string",
    "Total_Training_Hours": "string (e.g., 16 hrs)",
    "Total_Assessment_Hours": "string (e.g., 2 hrs)",
    "Total_Course_Duration_Hours": "string (e.g., 18 hrs)",
    "Course_Overview": "string (2-3 paragraph overview of the course)",
    "Learning_Units": [
        {
            "LU_Title": "string",
            "Topics": [
                {
                    "Topic_Title": "string",
                    "Bullet_Points": ["string"]
                }
            ],
            "LO": "string (Learning Outcome, e.g., LO1: ...)",
            "LO_Description": "string (detailed description of the Learning Outcome)",
            "K_numbering_description": [
                {"K_number": "K1", "Description": "string"}
            ],
            "A_numbering_description": [
                {"A_number": "A1", "Description": "string"}
            ],
            "Assessment_Methods": ["string"],
            "Instructional_Methods": ["string"]
        }
    ],
    "Assessment_Methods_Details": [
        {
            "Assessment_Method": "string (e.g., Written Assessment - Short Answer Questions)",
            "Method_Abbreviation": "string (e.g., WA-SAQ)",
            "Total_Delivery_Hours": "string",
            "Assessor_to_Candidate_Ratio": ["string"],
            "Evidence": [
                {"LO": "string", "Evidence": "string"}
            ],
            "Submission": ["string"],
            "Marking_Process": ["string"],
            "Retention_Period": "string"
        }
    ]
}

RULES:
1. Extract ALL Learning Units with their complete topics, K statements, and A statements
2. Generate a Course_Overview (2-3 paragraphs) that describes what the course covers
3. Generate LO_Description for each Learning Unit (detailed description of the outcome)
4. For Assessment_Methods_Details, include Evidence for each LO showing what evidence is required
5. If a field cannot be found in the document, use an empty string or empty list
6. Do NOT truncate or omit any data
"""


async def interpret_cp(parsed_cp_path: str, output_path: str = None,
                       course_ref_code: str = None, course_url: str = None) -> dict:
    """
    Interpret a parsed Course Proposal and extract structured course data.

    Args:
        parsed_cp_path: Path to the parsed CP text file (output/parsed_cp.md).
        output_path: Path to save the context JSON. Defaults to output/context.json.
        course_ref_code: Optional TGS reference code to supplement missing data.
        course_url: Optional course URL to fetch and supplement missing data.

    Returns:
        Structured course data as a dict.
    """
    if output_path is None:
        output_path = os.path.join(os.path.dirname(parsed_cp_path), "context.json")

    # Read the parsed CP text
    with open(parsed_cp_path, 'r', encoding='utf-8') as f:
        cp_text = f.read()

    # Build supplementary info section
    supplement = ""
    if course_ref_code:
        supplement += f"\n\nCourse Reference Code (TGS): {course_ref_code}"
        supplement += "\nUse this as the TGS_Ref_No value."
    if course_url:
        supplement += f"\n\nA course URL has been provided: {course_url}"
        supplement += "\nUse the WebFetch tool to fetch this URL and extract any missing information (e.g. Course_Fee, TGS_Ref_No, Course_Title, course description, etc.) to supplement the CP data."

    prompt = f"""Read the following parsed Course Proposal document and extract ALL structured course information into JSON format.

Follow the JSON schema exactly as specified in your instructions.

--- PARSED COURSE PROPOSAL ---
{cp_text}
--- END ---
{supplement}

Return ONLY the JSON object, no additional text."""

    tools = ["Read", "Glob", "Grep"]
    if course_url:
        tools.append("WebFetch")

    context = await run_agent_json(
        prompt=prompt,
        system_prompt=SYSTEM_PROMPT,
        tools=tools,
        max_turns=10,
    )

    # Save to output file
    os.makedirs(os.path.dirname(output_path), exist_ok=True)
    with open(output_path, 'w', encoding='utf-8') as f:
        json.dump(context, f, indent=2, ensure_ascii=False)

    return context
