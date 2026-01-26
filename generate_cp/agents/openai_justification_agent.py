"""
OpenAI SDK-based Justification Agent.

This module replaces the Autogen-based justification_agent.py with direct OpenAI SDK implementations.
Uses JSON mode for OpenRouter compatibility.

The justification agent provides assessment method justifications.

Author: Migration from Autogen to OpenAI SDK
Date: 2026-01-20
"""

import json
import sys
from typing import Dict, Any
from generate_cp.utils.openai_model_client import create_openai_client


def extract_json_from_response(content: str) -> dict:
    """
    Extract JSON from a response string, handling markdown code blocks.

    Args:
        content: The response content that may contain JSON

    Returns:
        Parsed JSON dictionary
    """
    if content is None:
        return {}

    # Try to find JSON in markdown code block
    if "```json" in content:
        start = content.find("```json") + 7
        end = content.find("```", start)
        if end != -1:
            content = content[start:end].strip()
    elif "```" in content:
        start = content.find("```") + 3
        end = content.find("```", start)
        if end != -1:
            content = content[start:end].strip()

    # Try to find JSON object boundaries
    if "{" in content:
        start = content.find("{")
        # Find matching closing brace
        depth = 0
        end = start
        for i, char in enumerate(content[start:], start):
            if char == "{":
                depth += 1
            elif char == "}":
                depth -= 1
                if depth == 0:
                    end = i + 1
                    break
        content = content[start:end]

    try:
        return json.loads(content)
    except json.JSONDecodeError as e:
        print(f"Warning: Failed to parse JSON: {e}")
        return {}


def justification_task(ensemble_output):
    """Generate the justification task prompt."""
    return f"""
    1. Based on the extracted data from {ensemble_output}, generate your justifications.
    2. Ensure your responses are structured in JSON format.
    3. Return a full JSON object with all your answers according to the schema.
    4. You MUST ensure that your response is a valid JSON object, do not make any mistakes that might cause JSON parsing errors.
    """


def recreate_assessment_phrasing_dynamic(json_data):
    """
    Recreate assessment phrasing dynamically from JSON data.

    Args:
        json_data: Assessment method JSON data

    Returns:
        Formatted phrasing string
    """
    phrasing_list = []

    # Check for which assessment method is present in the JSON data
    for method_key, method_data in json_data['assessment_methods'].items():
        if method_data:
            # Header with method name and description
            phrasing = f"{method_data['name']}:\n{method_data['description']}\n\n"
            phrasing += f"{method_data['focus']}\n{method_data['tasks'][0]}\n\n" if 'tasks' in method_data else ""

            # Type of Evidence
            phrasing += "Type of Evidence:\n"
            if isinstance(method_data['evidence'], dict):
                for lo, evidence in method_data['evidence'].items():
                    phrasing += f"•\tFor {lo}: {evidence}\n"
            else:
                phrasing += f"•\t{method_data['evidence']}\n"

            # Manner of Submission
            phrasing += "Manner of Submission:\n"
            if isinstance(method_data['submission'], list):
                for submission in method_data['submission']:
                    phrasing += f"•\t{submission}\n"
            else:
                phrasing += f"{method_data['submission']}\n\n"

            # Marking Process
            phrasing += "Marking Process: \n"
            for criteria in method_data['marking_process']:
                phrasing += f"•\t{criteria}\n"

            # Retention Period
            phrasing += f"Retention Period:\n•\t{method_data['retention_period']}\n"

            # No. of Role Play Scripts (specific to Role Play)
            if method_key == "role_play" and "no_of_scripts" in method_data:
                phrasing += f"No. of Role Play Scripts:\n•\t{method_data['no_of_scripts']}\n"

            phrasing_list.append(phrasing)
            break  # Exit after finding the first present method since only one will be there

    return "\n".join(phrasing_list)


async def run_assessment_justification_agent(
    ensemble_output: Dict[str, Any],
    model_choice: str,
    stream_to_console: bool = True
) -> Dict[str, Any]:
    """
    Run the assessment justification agent.

    Provides justification for assessment methods based on course details.

    Args:
        ensemble_output: Dictionary containing course data
        model_choice: Model selection string
        stream_to_console: Whether to stream output to console

    Returns:
        Dict containing assessment method justifications
    """
    client, config = create_openai_client(model_choice)

    system_message = f"""
    Based on the following course details, you are to provide justification for the appropriate Assessment Method followng a defined structure.
    The course details are as follows:
    Course Title: {ensemble_output.get('Course Information', {}).get('Course Title', [])}
    Learning Outcomes: {ensemble_output.get('Learning Outcomes', {}).get('Learning Outcomes', [])}
    Topics Covered: {ensemble_output.get('Assessment Methods', {}).get('Course Outline', [])}
    Assessment Methods: {ensemble_output.get('Assessment Methods', {}).get('Assessment Methods', [])}

    The Written Assessment or WA-SAQ will always be present in Assessment Methods, you may ignore that. Your focus is on justifying either the Case Study, Practical Performance, Oral Questioning, or Role Play, whichever is applicable.
    Your justification must only be for one method at a time, do not mix up both.

    Provide justifications for why the assessment method aligns with the course learning outcomes and topics.
    For each assessment method, you will provide a breakdown that includes:

    1) Type of Evidence: What candidates will submit to demonstrate their understanding or skills.
    2) Manner of Submission: How the candidates will submit their work to assessors.
    3) Marking Process: How assessors will evaluate the work, including rubrics or specific evaluation criteria.
    4) Retention Period: How long the submitted work will be stored for auditing or compliance purposes.

    Rules:
    Replace "students" with "candidates."
    Replace "instructors" with "assessors."
    You are to return your output in a JSON structure as seen in the examples below.
    Ensure that all LOs are addressed.
    Limit word length for all bulleted points to one sentence, not more than 30 words.
    The Marking Process should consist of 3 different evaluations, keep it concise with not more than 6 words.

    Practical Performance (PP) Example:
    A practical Performance (PP) assessment will provide direct evidence of whether candidates have acquired the competency for the ability statements by solving a scenario-based problem.

    The Practical Performance (PP) assessment focuses on providing authentic "Show Me Application" evidence of candidates' ability to apply Microsoft 365 Office tools and Copilot features to enhance productivity in realistic workplace tasks. Candidates will complete a series of practical tasks that demonstrate their ability to use the advanced functionalities of Microsoft Excel, Word, and PowerPoint, integrating Copilot to optimize performance.
    Type of Evidence:
    •	For LO1: Candidates will create an Excel workbook using formulas, functions, and Copilot's automation to demonstrate how Microsoft 365 tools can enhance workplace efficiency.
    •	For LO2: Candidates will use Microsoft Word to create and modify tables, automate formatting and review processes with Copilot, and submit the final document.
    •	For LO3: Candidates will develop a multimedia PowerPoint presentation with design and content enhancements assisted by Copilot.
    Manner of Submission:
    •	Candidates will submit their Excel workbooks, Word documents, and PowerPoint presentations, as well as any additional supporting documentation that details how they utilized Microsoft 365 tools and Copilot features to enhance productivity. This includes annotated screenshots or documentation showing Copilot's contributions to task completion.
    Marking Process:
    •	Effectiveness in Using Copilot.
    •	Quality of Outputs.
    •	Efficiency and Customization.
    Retention Period:
    •	All submitted evidence, including Excel workbooks, Word documents, PowerPoint presentations, and assessment records, will be retained for 3 years to ensure compliance with institutional policies and for auditing purposes.

    Case Study (CS) example:
    A case study (Written Assessment) consists of scenarios that allow an assessment of the candidate's mastery of abilities. The assessor can collect process evidence to assess the candidate's competencies against the learning outcomes. It allows consistent interpretation of evidence and reliable assessment outcomes.

    This case study assessment focuses on providing authentic "Show Me Application" evidence of candidates' ability to apply Agile design thinking and Generative AI to foster innovation in an organizational context.
    Type of Evidence:
    •	For LO1: Candidates will submit a report demonstrating how they integrated design thinking methodologies and agile principles.
    •	For LO2: Candidates will conduct a problem-framing exercise using stakeholder inputs, create a persona mapping based on user insights, and submit a report.
    •	For LO3: Candidates will lead an innovation project using Agile and design thinking approaches.
    •	For LO4: Candidates will submit a strategic plan detailing how they developed and scaled design thinking methodologies across the organization.
    Manner of Submission:
    •	Candidates will submit their case study reports and any additional supporting documents to the assessors electronically via the designated learning management system.
    Marking Process:
    •	Integration of Methodologies.
    •	Stakeholder Analysis.
    •	Project Leadership and Tools.
    Retention Period: All submitted case study reports and accompanying documentation will be retained for 3 years to ensure compliance with institutional policies and for auditing purposes.

    Role Play (RP) example:
    Role Play assessments allow learners to demonstrate their ability to apply learned concepts in simulated real-world interactions, focusing on the practical application of sales closure skills.

    Type of Evidence: Role Play
    Manner of Submission:
    •	Assessor will evaluate the candidate using an observation checklist for the role play.
    Marking Process:
    •	Effectiveness of sales recommendations.
    •	Application of sales techniques.
    •	Presentation of follow-up steps and metrics.
    Retention Period: 3 years.
    No. of Role Play Scripts: To ensure fairness among learners, a minimum of two distinct role-play scripts or scenarios will be prepared for this assessment


    **Your response must be ONLY the JSON structure, formatted exactly as per the example below, enclosed in a code block (i.e., triple backticks ```). Do not include any additional text or explanations outside the JSON code block. Do not include any headings or introductions. Just output the JSON code block.**
    "assessment_methods": {{
        "practical_performance": {{
        "name": "Practical Performance (PP)",
        "description": "A practical Performance (PP) assessment will provide direct evidence of whether candidates have acquired the competency for the ability statements by solving a scenario-based problem.",
        "focus": "The Practical Performance (PP) assessment focuses on providing authentic \"Show Me Application\" evidence of candidates' ability to apply Microsoft 365 Office tools and Copilot features to enhance productivity in realistic workplace tasks.",
        "tasks": [
            "Candidates will complete a series of practical tasks that demonstrate their ability to use the advanced functionalities of Microsoft Excel, Word, and PowerPoint, integrating Copilot to optimize performance."
        ],
        "evidence": {{
            "LO1": "Candidates will create an Excel workbook using formulas, functions, and Copilot's automation to demonstrate how Microsoft 365 tools can enhance workplace efficiency.",
            "LO2": "Candidates will use Microsoft Word to create and modify tables, automate formatting and review processes with Copilot, and submit the final document.",
            "LO3": "Candidates will develop a multimedia PowerPoint presentation with design and content enhancements assisted by Copilot."
        }},
        "submission": [
            "Candidates will submit their Excel workbooks, Word documents, and PowerPoint presentations, as well as any additional supporting documentation that details how they utilized Microsoft 365 tools and Copilot features to enhance productivity.",
            "This includes annotated screenshots or documentation showing Copilot's contributions to task completion."
        ],
        "marking_process": [
            "Effectiveness in Using Copilot.",
            "Quality of Outputs.",
            "Efficiency and Customization."
        ],
        "retention_period": "All submitted evidence, including Excel workbooks, Word documents, PowerPoint presentations, and assessment records, will be retained for 3 years to ensure compliance with institutional policies and for auditing purposes."
        }}
    }}

    However, in the case of Role Play assessment, you are to format it as follows:
    "assessment_methods": {{
        "role_play": {{
        "name": "Role Play (RP)",
        "description": "Role Play assessments allow learners to demonstrate their ability to apply learned concepts in simulated real-world interactions, focusing on the practical application of sales closure skills.",
        "focus": "Role Play assessments allow learners to demonstrate their ability to apply learned concepts in simulated real-world interactions, focusing on the practical application of sales closure skills.",
        "evidence": "Role play",
        "submission": ["Assessor will evaluate the candidate using an observation checklist for the role play."],
        "marking_process": [
            "Effectiveness of sales recommendations.",
            "Application of sales techniques.",
            "Presentation of follow-up steps and metrics."
        ],
        "retention_period": "3 years",
        "no_of_scripts": "To ensure fairness among learners, a minimum of two distinct role-play scripts or scenarios will be pre-pared for this assessment"
        }}
    }}

    However, in the case of Oral Questioning assessment, you are to format it as follows:
    "assessment_methods": {{
        "oral_questioning": {{
        "name": "Oral Questioning (OQ)",
        "description": "Oral Questioning assessments allow candidates to demonstrate their understanding of concepts through verbal responses, focusing on the practical application of [skills].",
        "evidence": {{
            "LO1": "",
            "LO2": "",
        }},
        "submission": ["Candidates will verbally respond to assessors during a structured questioning session."],
        "marking_process": [
        ],
        "retention_period": "All oral questioning recordings and assessment notes will be retained for 2 years for compliance and auditing.",
        }}
    }}

    """

    user_task = justification_task(ensemble_output)

    if stream_to_console:
        print("\n" + "=" * 80)
        print("ASSESSMENT JUSTIFICATION AGENT - Generating Assessment Justifications")
        print("=" * 80)

    try:
        completion = client.chat.completions.create(
            model=config["model"],
            temperature=config["temperature"],
            messages=[
                {"role": "system", "content": system_message},
                {"role": "user", "content": user_task}
            ],
            response_format={"type": "json_object"}
        )

        content = completion.choices[0].message.content
        parsed_json = extract_json_from_response(content)

        if stream_to_console:
            print("\n[Assessment Justification Agent Response]")
            print(json.dumps(parsed_json, indent=2))
            print("=" * 80 + "\n")

        return parsed_json

    except Exception as e:
        print(f"Error in assessment justification agent: {e}", file=sys.stderr)
        raise
