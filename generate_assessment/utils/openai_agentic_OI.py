"""
OpenAI SDK-based Oral Interview Assessment Generation Module.

Uses JSON mode for OpenRouter compatibility.
"""

import re
import asyncio
from generate_assessment.utils.pydantic_models import FacilitatorGuideExtraction
from utils.helpers import parse_json_content
from generate_cp.utils.openai_model_client import create_openai_client
from utils.prompt_loader import load_prompt


def extract_learning_outcome_id(lo_text: str) -> str:
    pattern = r"^(LO\d+)(?:[:\s-]+)"
    match = re.match(pattern, lo_text, re.IGNORECASE)
    return match.group(1) if match else ""


def group_abilities(extracted_data):
    unique_abilities = {}
    for lu in extracted_data["learning_units"]:
        lo = lu.get("learning_outcome", "")
        if not lo:
            continue
        lo_id = extract_learning_outcome_id(lo)
        for topic in lu["topics"]:
            for ability in topic.get("tsc_abilities", []):
                ability_id = ability["id"]
                if ability_id not in unique_abilities:
                    unique_abilities[ability_id] = {
                        "id": ability_id,
                        "text": ability["text"],
                        "learning_outcome": lo,
                        "learning_outcome_id": lo_id,
                        "topics": [topic["name"]]
                    }
                elif topic["name"] not in unique_abilities[ability_id]["topics"]:
                    unique_abilities[ability_id]["topics"].append(topic["name"])

    result = []
    for ability_id, ability_data in unique_abilities.items():
        result.append({
            "learning_outcome": ability_data["learning_outcome"],
            "learning_outcome_id": ability_data["learning_outcome_id"],
            "abilities": [ability_id],
            "ability_texts": [ability_data["text"]],
            "topics": ability_data["topics"]
        })
    return result


async def generate_oi_for_lo(client, config, course_title, assessment_duration, learning_outcome, learning_outcome_id, retrieved_content, ability_ids, ability_texts):
    system_message = load_prompt("assessment/oral_interview")

    user_task = f"""
    Generate a Oral Interview assessment question-answer pair using the following details:
    - Course Title: '{course_title}'
    - Assessment Duration: '{assessment_duration}'
    - Learning Outcome: '{learning_outcome}'
    - Learning Outcome ID: '{learning_outcome_id}'
    - REQUIRED Ability IDs: {ability_ids}
    - Ability Statements: {', '.join(ability_texts)}
    - Retrieved Content: {retrieved_content}

    Instructions:
    1. Use the retrieved content to generate one question-answer pair aligned with the Learning Outcome.
    2. The question should directly assess the associated abilities.
    3. CRITICAL: You MUST use EXACTLY these ability IDs in your response: {ability_ids}
    4. Return your output in valid JSON.
    """

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
        content_response = completion.choices[0].message.content
        qa_result = parse_json_content(content_response)
        if qa_result is None or not isinstance(qa_result, dict):
            raise ValueError(f"Failed to parse OI response for {learning_outcome_id}")
        return {
            "learning_outcome_id": qa_result.get("learning_outcome_id", learning_outcome_id),
            "question_statement": qa_result.get("question_statement", "Question not provided."),
            "answer": qa_result.get("answer", ["Answer not available."]),
            "ability_id": ability_ids
        }
    except Exception as e:
        print(f"Error generating OI question for {learning_outcome_id}: {e}")
        return None


async def generate_oi(extracted_data: FacilitatorGuideExtraction, index, model_client, model_choice: str = "DeepSeek-Chat"):
    client, config = create_openai_client(model_choice)
    extracted_data = dict(extracted_data)

    assessment_duration = ""
    for assessment in extracted_data["assessments"]:
        code = assessment["code"].upper()
        if "OI" in code or "ORAL INTERVIEW" in code:
            assessment_duration = assessment["duration"]
            break

    grouped_abilities = group_abilities(extracted_data)

    questions = []
    for group in grouped_abilities:
        result = await generate_oi_for_lo(
            client, config,
            extracted_data["course_title"],
            assessment_duration,
            group["learning_outcome"],
            group["learning_outcome_id"],
            "",  # Retrieved content placeholder
            group["abilities"],
            group["ability_texts"]
        )
        if result:
            questions.append(result)

    return {
        "course_title": extracted_data["course_title"],
        "duration": assessment_duration,
        "scenario": "",
        "questions": questions
    }
