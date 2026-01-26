"""
OpenAI SDK-based Practical Performance Generation Module.

This module replaces the Autogen-based agentic_PP.py with direct OpenAI SDK implementations.
Uses JSON mode for OpenRouter compatibility.

Author: Migration from Autogen to OpenAI SDK
Date: 2026-01-20
"""

import re
import asyncio
from common.common import parse_json_content
from generate_cp.utils.openai_model_client import create_openai_client


def clean_markdown(text: str) -> str:
    """Removes markdown formatting from input text."""
    if not text:
        return text
    cleaned_text = re.sub(r'\*\*(.*?)\*\*', r'\1', text)
    cleaned_text = re.sub(r'__([^_]+)__', r'\1', cleaned_text)
    cleaned_text = re.sub(r'[*_`]', '', cleaned_text)
    return cleaned_text.strip()


def extract_learning_outcome_id(lo_text: str) -> str:
    """Extracts the learning outcome ID from a string."""
    pattern = r"^(LO\d+)(?:[:\s-]+)"
    match = re.match(pattern, lo_text, re.IGNORECASE)
    return match.group(1) if match else ""


async def retrieve_content_for_learning_outcomes(extracted_data, engine):
    """Retrieves relevant course content for each learning outcome."""
    async def query_learning_unit(learning_unit):
        learning_outcome = learning_unit["learning_outcome"]
        lo_id = extract_learning_outcome_id(learning_outcome)
        ability_ids = []
        ability_texts = []
        topics_names = []

        for topic in learning_unit["topics"]:
            ability_ids.extend([ability["id"] for ability in topic["tsc_abilities"]])
            ability_texts.extend([ability["text"] for ability in topic["tsc_abilities"]])
            topics_names.append(topic["name"])

        if not topics_names:
            return learning_outcome, {
                "learning_outcome": learning_outcome,
                "learning_outcome_id": lo_id,
                "abilities": ability_ids,
                "ability_texts": ability_texts,
                "retrieved_content": "⚠️ No relevant information found."
            }

        topics_str = ", ".join(topics_names)
        query = f"""
        Show me all module content aligning with the following topics: {topics_str}
        for the Learning Outcome: {learning_outcome}.
        Retrieve ALL available content as it appears in the source without summarizing or omitting any details.
        """

        response = await engine.aquery(query)
        if not response or not getattr(response, "source_nodes", None) or not response.source_nodes:
            content = "⚠️ No relevant information found."
        else:
            content = "\n\n".join([
                f"### Page {node.metadata.get('page', 'Unknown')}\n{node.text}"
                for node in response.source_nodes
            ])

        return learning_outcome, {
            "learning_outcome": learning_outcome,
            "learning_outcome_id": lo_id,
            "abilities": ability_ids,
            "ability_texts": ability_texts,
            "retrieved_content": content
        }

    tasks = [query_learning_unit(lu) for lu in extracted_data["learning_units"]]
    results = await asyncio.gather(*tasks)
    return [result[1] for result in results]


def group_abilities(extracted_data):
    """Creates one question per unique ability (no grouping)."""
    unique_abilities = {}

    print(f"DEBUG PP: Extracting abilities from {len(extracted_data.get('learning_units', []))} learning units")

    for lu in extracted_data["learning_units"]:
        lo = lu.get("learning_outcome", "")
        if not lo:
            print(f"⚠️ WARNING: Learning unit missing learning_outcome field, skipping LU")
            continue
        lo_id = extract_learning_outcome_id(lo)
        lu_title = lu.get("learning_unit_title", "Unknown LU")
        print(f"DEBUG PP: Processing LU: {lu_title}")

        for topic in lu["topics"]:
            topic_name = topic.get("name", "Unknown Topic")
            abilities_in_topic = topic.get("tsc_abilities", [])
            print(f"  Topic: {topic_name} - {len(abilities_in_topic)} abilities")

            for ability in abilities_in_topic:
                ability_id = ability["id"]
                print(f"    Found ability: {ability_id} - {ability['text'][:50]}...")

                if ability_id in unique_abilities:
                    if topic["name"] not in unique_abilities[ability_id]["topics"]:
                        unique_abilities[ability_id]["topics"].append(topic["name"])
                        print(f"    -> Added topic to existing ability {ability_id}")
                else:
                    unique_abilities[ability_id] = {
                        "id": ability_id,
                        "text": ability["text"],
                        "learning_outcome": lo,
                        "learning_outcome_id": lo_id,
                        "topics": [topic["name"]]
                    }
                    print(f"    -> Created new ability entry: {ability_id}")

    print(f"DEBUG PP: Total unique abilities extracted: {len(unique_abilities)}")
    print(f"DEBUG PP: Ability IDs: {list(unique_abilities.keys())}")

    result = []
    for ability_id, ability_data in unique_abilities.items():
        result.append({
            "learning_outcome": ability_data["learning_outcome"],
            "learning_outcome_id": ability_data["learning_outcome_id"],
            "abilities": [ability_id],
            "ability_texts": [ability_data["text"]],
            "topics": ability_data["topics"]
        })

    print(f"DEBUG PP: Returning {len(result)} question groups")
    return result


async def generate_pp_scenario_openai(client, config, data) -> str:
    """Generates a practical performance scenario using OpenAI SDK."""
    course_title = data["course_title"]

    learning_outcomes = [lu["learning_outcome"] for lu in data["learning_units"]]
    abilities = [ability["text"] for lu in data["learning_units"] for topic in lu["topics"] for ability in topic["tsc_abilities"]]

    outcomes_text = "\n".join([f"- {lo}" for lo in learning_outcomes])
    abilities_text = "\n".join([f"- {ability}" for ability in abilities])

    system_message = "You are an expert in instructional design. Create a concise, realistic scenario based on the provided course details."

    user_task = f"""
    You are tasked with designing a realistic practical performance assessment scenario for the course '{course_title}'.

    The scenario should align with the following:

    Learning Outcomes:
    {outcomes_text}

    Abilities:
    {abilities_text}

    The scenario should describe a company or organization facing practical challenges and provide background context aligning to the Learning Outcomes and abilities.
    End the scenario by stating the learner's role in the company.
    Ensure the scenario is concise (1 paragraph), realistic, and action-oriented.
    """

    try:
        completion = client.chat.completions.create(
            model=config["model"],
            temperature=config["temperature"],
            messages=[
                {"role": "system", "content": system_message},
                {"role": "user", "content": user_task}
            ]
        )

        return completion.choices[0].message.content.strip()

    except Exception as e:
        print(f"Error generating PP scenario: {e}")
        return "A company is facing challenges in implementing new technologies. You are a consultant hired to help."


async def generate_pp_for_lo_openai(client, config, course_title, assessment_duration, scenario, learning_outcome, learning_outcome_id, retrieved_content, ability_ids, ability_texts):
    """Generates a question-answer pair for a specific Learning Outcome using OpenAI SDK."""
    system_message = """
    You are an expert at creating simple, practical performance tasks.

    Guidelines:
    1. Keep tasks SIMPLE and PRACTICAL - focus on one clear action
    2. Write the task in 1-2 simple sentences
    3. MUST end with: "Take snapshots of your commands at each step and paste them below."
    4. Answer MUST start with: "The snapshot should include: " followed by the expected output
    5. Keep the expected output short and clear

    You must return valid JSON with this structure:
    {
        "learning_outcome_id": "<learning_outcome_id>",
        "question_statement": "<simple task>. Take snapshots of your commands at each step and paste them below.",
        "answer": ["The snapshot should include: <expected output>"],
        "ability_id": ["<list_of_ability_ids>"]
    }
    """

    user_task = f"""
    Generate one practical performance assessment question-answer pair using the following details:
    - Course Title: '{course_title}'
    - Assessment Duration: '{assessment_duration}'
    - Scenario: '{scenario}'
    - Learning Outcome: '{learning_outcome}'
    - Learning Outcome ID: '{learning_outcome_id}'
    - REQUIRED Ability IDs: {ability_ids}
    - Ability Statements: {', '.join(ability_texts)}
    - Retrieved Content: {retrieved_content}

    Instructions:
    1. Formulate a direct, hands-on task question in 2 sentences maximum without any prefatory phrases.
    2. The question must end with "Take snapshots of your commands at each step and paste them below."
    4. The answer must start with "The snapshot should include: " followed solely by the final output or solution.
    5. Include the learning outcome id in your response as "learning_outcome_id".
    6. CRITICAL: You MUST use EXACTLY these ability IDs in your response: {ability_ids}
    7. Return your output in valid JSON.
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
            raise ValueError(f"Failed to parse PP response for {learning_outcome_id}")

        llm_returned_abilities = qa_result.get("ability_id", [])
        if llm_returned_abilities != ability_ids:
            print(f"⚠️ LLM returned wrong abilities! Expected {ability_ids}, got {llm_returned_abilities}. Using expected.")

        return {
            "learning_outcome_id": qa_result.get("learning_outcome_id", learning_outcome_id),
            "question_statement": qa_result.get("question_statement", "Question not provided."),
            "answer": qa_result.get("answer", ["Answer not available."]),
            "ability_id": ability_ids
        }

    except Exception as e:
        print(f"Error generating PP question for {learning_outcome_id}: {e}")
        return None


async def generate_pp(extracted_data, index, model_client, model_choice: str = "DeepSeek-Chat"):
    """
    Generates a full practical performance assessment using OpenAI SDK.

    Args:
        extracted_data: Extracted facilitator guide data
        index: Knowledge retrieval index
        model_client: Legacy parameter (not used)
        model_choice: Model selection string

    Returns:
        dict: Structured dictionary with course_title, duration, scenario, and questions
    """
    from settings.api_manager import load_api_keys
    client, config = create_openai_client(model_choice)
    extracted_data = dict(extracted_data)

    scenario = await generate_pp_scenario_openai(client, config, extracted_data)

    # Content retrieval simplified - no longer using vector index
    lo_content_dict = {lo["Learning_Outcome"]: "" for lo in extracted_data.get("Learning_Outcomes", [])}

    assessment_duration = ""
    for assessment in extracted_data["assessments"]:
        if "PP" in assessment["code"]:
            assessment_duration = assessment["duration"]
            break

    grouped_abilities = group_abilities(extracted_data)

    questions = []
    for group in grouped_abilities:
        combined_content = []
        for item in lo_content_dict:
            if any(topic in item.get("retrieved_content", "") for topic in group["topics"]):
                combined_content.append(item["retrieved_content"])

        if not combined_content:
            combined_content = [item["retrieved_content"] for item in lo_content_dict]

        retrieved_content = "\n\n".join(combined_content)

        print(f"DEBUG PP: Generating question for {group['abilities']}...")
        result = await generate_pp_for_lo_openai(
            client, config,
            extracted_data["course_title"],
            assessment_duration,
            scenario,
            group["learning_outcome"],
            group["learning_outcome_id"],
            retrieved_content,
            group["abilities"],
            group["ability_texts"]
        )
        if result:
            questions.append(result)

    print(f"DEBUG PP: Successfully generated {len(questions)} questions")
    print(f"DEBUG PP: Total ability groups: {len(grouped_abilities)}")

    return {
        "course_title": extracted_data["course_title"],
        "duration": assessment_duration,
        "scenario": scenario,
        "questions": questions
    }
