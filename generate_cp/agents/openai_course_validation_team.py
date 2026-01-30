"""
OpenAI SDK-based Course Validation Team.

This module replaces the Autogen-based course_validation_team.py with direct OpenAI SDK implementations.
Uses JSON mode for OpenRouter compatibility.

The course validation team consists of 2 sequential agents:
1. Analyst - Generates 3 distinct sets of survey answers
2. Editor - Consolidates outputs into structured JSON

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


def validation_task(ensemble_output):
    """Generate the validation task prompt."""
    return f"""
    1. Extract data from the following JSON file: {ensemble_output}
    2. Generate 3 distinct sets of answers to two specific survey questions.
    3. Map the extracted data according to the schemas.
    4. Return a full JSON object with all the extracted data according to the schema.
    """


async def run_analyst_agent(
    ensemble_output: Dict[str, Any],
    model_choice: str,
    stream_to_console: bool = True
) -> Dict[str, Any]:
    """
    Run the analyst agent.

    Generates 3 distinct sets of survey answers about performance gaps and training needs.

    Args:
        ensemble_output: Dictionary containing course data
        model_choice: Model selection string
        stream_to_console: Whether to stream output to console

    Returns:
        Dict containing analyst responses
    """
    client, config = create_openai_client(model_choice)

    system_message = f"""
    Using the following information from {ensemble_output}:
    1. Course title (e.g., "Data Analytics for Business")
    2. Industry (e.g., "Retail")
    3. Learning outcomes expected from the course (e.g., "Better decision-making using data, automation of business reports")

    Generate 3 distinct sets of answers to two specific survey questions.
    Survey Questions and Structure:

    {{
    Question 1: What are the performance gaps in the industry?
    Question 1 Guidelines: You are to provide a short description (1-2 paragraphs) of what the key performance issues are within the specified industry. This will be based on general industry knowledge, considering the context of the course.

    Question 2: Why you think this WSQ course will address the training needs for the industry?
    Question 2 Guidelines: You are to explain in a short paragraph (1-2 paragraphs) how the course you mentioned can help address those performance gaps in the industry. Each response will be tied to one or two of the learning outcomes you provided, without directly mentioning them.

    }}

    Rules for Each Response:
    Distinct Answers: You will provide three different answers by focusing on different learning outcomes in each response.
    Concise Structure: Each response will have no more than two paragraphs, with each paragraph containing fewer than 120 words.

    No Mention of Certain Elements:
    You won't mention the specific industry in the response.
    You won't mention or restate the learning outcomes explicitly.
    You won't indicate that I am acting in a director role.

    You are to output your response in this JSON format, do not change the keys:
    Output Format (for each of the 3 sets):
    What are the performance gaps in the industry?
    [Answer here based on the industry and course details you provide]

    Why do you think this WSQ course will address the training needs for the industry?
    [Answer here showing how the course helps address the gaps based on relevant learning outcomes]

    By following these steps, you aim to provide actionable insights that match the course content to the training needs within the specified industry.
    """

    user_task = validation_task(ensemble_output)

    if stream_to_console:
        print("\n" + "=" * 80)
        print("ANALYST AGENT - Generating Survey Responses")
        print("=" * 80)

    try:
        completion = client.chat.completions.create(
            model=config["model"],
            temperature=config["temperature"],
            max_tokens=8000,  # Limit for OpenRouter free tier
            messages=[
                {"role": "system", "content": system_message},
                {"role": "user", "content": user_task}
            ],
            response_format={"type": "json_object"}
        )

        content = completion.choices[0].message.content
        parsed_json = extract_json_from_response(content)

        if stream_to_console:
            print("\n[Analyst Agent Response]")
            print(json.dumps(parsed_json, indent=2))
            print("=" * 80 + "\n")

        return parsed_json

    except Exception as e:
        print(f"Error in analyst agent: {e}", file=sys.stderr)
        raise


async def run_validation_editor_agent(
    analyst_data: Dict[str, Any],
    model_choice: str,
    stream_to_console: bool = True
) -> Dict[str, Any]:
    """
    Run the editor agent to consolidate analyst outputs.

    Args:
        analyst_data: Output from analyst agent
        model_choice: Model selection string
        stream_to_console: Whether to stream output to console

    Returns:
        Dict containing consolidated validation output
    """
    client, config = create_openai_client(model_choice)

    system_message = """
    You are to combine the outputs from the following agents into a single JSON object, do NOT aggregate output from the validator agent:
        1) analyst
    Return the combined output into a single JSON file.

    Follow this structure and naming convention below:
    {
        "analyst_responses": [
            {
                "What are the performance gaps in the industry?": "",
                "Why do you think this WSQ course will address the training needs for the industry?": ""
            }
        ]
    }
    """

    user_task = f"""
    Combine the following analyst data into the required JSON format:

    Analyst Data:
    {json.dumps(analyst_data, indent=2)}

    Return only the combined JSON object with the analyst_responses array.
    """

    if stream_to_console:
        print("\n" + "=" * 80)
        print("EDITOR AGENT - Consolidating Analyst Responses")
        print("=" * 80)

    try:
        completion = client.chat.completions.create(
            model=config["model"],
            temperature=config["temperature"],
            max_tokens=8000,  # Limit for OpenRouter free tier
            messages=[
                {"role": "system", "content": system_message},
                {"role": "user", "content": user_task}
            ],
            response_format={"type": "json_object"}
        )

        content = completion.choices[0].message.content
        parsed_json = extract_json_from_response(content)

        if stream_to_console:
            print("\n[Editor Agent Response]")
            print(json.dumps(parsed_json, indent=2))
            print("=" * 80 + "\n")

        return parsed_json

    except Exception as e:
        print(f"Error in validation editor agent: {e}", file=sys.stderr)
        raise


async def run_course_validation_team(
    ensemble_output: Dict[str, Any],
    model_choice: str,
    stream_to_console: bool = True
) -> Dict[str, Any]:
    """
    Run the full course validation team pipeline.

    This replaces the Autogen RoundRobinGroupChat with sequential OpenAI API calls.
    Executes: Analyst -> Editor

    Args:
        ensemble_output: Dictionary containing course data
        model_choice: Model selection string
        stream_to_console: Whether to stream output to console

    Returns:
        Dict containing consolidated validation output
    """
    if stream_to_console:
        print("\n" + "=" * 80)
        print("COURSE VALIDATION TEAM - Starting Validation Pipeline")
        print("=" * 80)

    # Run agents sequentially (mimics RoundRobinGroupChat with max_turns=2)
    analyst_data = await run_analyst_agent(
        ensemble_output=ensemble_output,
        model_choice=model_choice,
        stream_to_console=stream_to_console
    )

    # Editor consolidates findings
    consolidated_output = await run_validation_editor_agent(
        analyst_data=analyst_data,
        model_choice=model_choice,
        stream_to_console=stream_to_console
    )

    if stream_to_console:
        print("\n" + "=" * 80)
        print("COURSE VALIDATION TEAM - Pipeline Complete")
        print("=" * 80)

    return consolidated_output
