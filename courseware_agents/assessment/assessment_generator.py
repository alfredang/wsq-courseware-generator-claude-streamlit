"""
Assessment Generator Agent

Reads parsed Facilitator Guide data and generates assessment questions
(SAQ, PP, CS, PRJ, ASGN, OI, DEM, RP, OQ) using the Claude Agent SDK.
"""

import json
import os
from courseware_agents.base import run_agent_json

SYSTEM_PROMPT = """You are an expert WSQ assessment content generator.

Your task is to read course data and generate assessment questions and answers
for various assessment types. Be thorough, accurate, and create questions that properly test
the Knowledge (K) and Ability (A) statements.

CRITICAL RULES:
- You MUST respond with ONLY a valid JSON object.
- Do NOT output any preamble, commentary, or explanation before or after the JSON.
- Do NOT use tools — all data you need is provided in the prompt.
- Start your response with { and end with }.

The JSON must follow this schema:
{
    "course_title": "string",
    "assessment_types": [
        {
            "type": "string (e.g., WA (SAQ), PP, CS, PRJ, ASGN, OI, DEM, RP, OQ)",
            "code": "string (e.g., WA-SAQ)",
            "duration": "string (e.g., 1 hr)",
            "questions": [
                {
                    "scenario": "string (2-3 sentence realistic scenario)",
                    "question_statement": "string (clear, direct question)",
                    "knowledge_id": "string (e.g., K1) - for SAQ only",
                    "ability_id": ["string (e.g., A1, A2)"] - for PP/CS",
                    "learning_outcome_id": "string (e.g., LO1) - for SAQ",
                    "answer": ["string (bullet point answer 1)", "string (bullet point answer 2)"]
                }
            ]
        }
    ]
}

ASSESSMENT TYPE RULES:
1. SAQ (Short Answer Questions): One question per K statement. Questions test knowledge.
   Each question has a scenario, question, knowledge_id, learning_outcome_id, and 3-5 answer bullet points.

2. PP (Practical Performance): One question per A statement. Questions test practical skills.
   Each question has a scenario, question, ability_id list, and detailed answer steps.

3. CS (Case Study): One complex case per Learning Unit. Tests ability to apply knowledge.
   Each case has a detailed scenario, multiple questions, ability_id list, and comprehensive answers.

4. PRJ (Project): One project scenario per course. Tests comprehensive understanding.
5. ASGN (Assignment): Written tasks testing analytical abilities.
6. OI (Oral Interview): Interview questions testing verbal understanding.
7. DEM (Demonstration): Practical demonstration tasks.
8. RP (Role Play): Role-play scenarios testing interpersonal skills.
9. OQ (Oral Questioning): Direct oral questions testing knowledge.

QUESTION QUALITY:
- Scenarios should be realistic and industry-relevant
- Questions should be clear and unambiguous
- Answers should be practical and specific (not generic)
- Each question should map to specific K or A statements
"""


async def generate_assessments(
    fg_data_path: str = None,
    master_ka_path: str = None,
    output_path: str = None,
    assessment_types: list = None,
    course_context: dict = None,
    prompt_template: str = None,
) -> dict:
    """
    Generate assessment questions from course context or Facilitator Guide data.

    Args:
        fg_data_path: Path to the parsed FG data JSON file (legacy).
        master_ka_path: Path to the K/A master list JSON file (legacy).
        output_path: Path to save the assessment context JSON.
        assessment_types: List of assessment types to generate.
        course_context: Structured course data dict from Extract Course Info.
        prompt_template: Optional custom prompt template.

    Returns:
        Assessment context dict with questions for each type.
    """
    if output_path is None:
        output_path = ".output/assessment_context.json"

    # Build the source data section
    if course_context:
        source_data = json.dumps(course_context, indent=2, ensure_ascii=False)
        source_label = "COURSE CONTEXT"
    elif fg_data_path:
        with open(fg_data_path, 'r', encoding='utf-8') as f:
            source_data = f.read()
        source_label = "FACILITATOR GUIDE DATA"
    else:
        raise ValueError("Either course_context or fg_data_path must be provided.")

    # Build K/A list from course context or master file
    master_ka_text = ""
    if course_context:
        learning_units = course_context.get('Learning_Units', [])
        if learning_units:
            master_ka_text = "\n\nMASTER K/A LIST:\n"
            for lu in learning_units:
                for k in lu.get('K_numbering_description', []):
                    master_ka_text += f"  {k.get('K_number', '')}: {k.get('Description', '')}\n"
                for a in lu.get('A_numbering_description', []):
                    master_ka_text += f"  {a.get('A_number', '')}: {a.get('Description', '')}\n"
    elif master_ka_path and os.path.exists(master_ka_path):
        with open(master_ka_path, 'r', encoding='utf-8') as f:
            master_ka = json.load(f)
        master_ka_text = "\n\nMASTER K/A LIST:\n"
        for k in master_ka.get('knowledge', []):
            master_ka_text += f"  {k['id']}: {k['text']}\n"
        for a in master_ka.get('abilities', []):
            master_ka_text += f"  {a['id']}: {a['text']}\n"

    # Determine assessment types
    types_instruction = ""
    if assessment_types:
        types_instruction = f"\nGenerate assessments ONLY for these types: {', '.join(assessment_types)}"
    elif course_context:
        # Auto-detect from Assessment_Methods_Details
        methods = course_context.get('Assessment_Methods_Details', [])
        if methods:
            detected = [m.get('Method_Abbreviation', m.get('Assessment_Method', '')) for m in methods]
            types_instruction = f"\nGenerate assessments for these types found in the course: {', '.join(detected)}"
        else:
            types_instruction = "\nAuto-detect assessment types from the course data and generate questions for all applicable types."
    else:
        types_instruction = "\nAuto-detect assessment types and generate questions for all found types."

    if prompt_template:
        prompt = prompt_template
    else:
        prompt = f"""Read the following course data and generate assessment questions.
{types_instruction}

--- {source_label} ---
{source_data}
--- END ---
{master_ka_text}

Generate comprehensive assessment questions following the schema in your instructions.
Return ONLY the JSON object."""

    result = await run_agent_json(
        prompt=prompt,
        system_prompt=SYSTEM_PROMPT,
        tools=[],
        max_turns=5,
    )

    # Save to output file
    os.makedirs(os.path.dirname(output_path), exist_ok=True)
    with open(output_path, 'w', encoding='utf-8') as f:
        json.dump(result, f, indent=2, ensure_ascii=False)

    return result
