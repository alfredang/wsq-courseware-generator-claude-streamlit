"""
File: timetable_generator.py

===============================================================================
Timetable Generator Module (Anthropic SDK Version)
===============================================================================
Description:
    This module generates a structured lesson plan timetable based on the provided course context.
    It leverages the OpenAI SDK to produce a detailed and balanced lesson plan that adheres
    strictly to WSQ course structure rules. The generated timetable ensures even distribution of topics,
    fixed sessions (such as attendance, breaks, and final assessments), and appropriate use of instructional
    methods over the specified number of days.

    This version uses the Anthropic SDK directly instead of Autogen framework.

Main Functionalities:
    • extract_unique_instructional_methods(course_context):
          Extracts and processes unique instructional method combinations from each Learning Unit in the
          course context by correcting method names and grouping them into valid pairs.
    • generate_timetable(context, num_of_days, model_choice):
          Uses Anthropic SDK to generate a complete lesson plan timetable in JSON format.
          The timetable includes fixed sessions (attendance, breaks, assessment sessions) and topic or
          activity sessions, distributed evenly across the specified number of days.

Dependencies:
    - anthropic (Anthropic SDK)
    - common.common (parse_json_content)
    - settings.model_configs (get_model_config)
    - Standard Python Libraries (built-in)

Usage:
    - Ensure the course context includes complete details such as Learning Units, Topics, Learning Outcomes,
      Assessment Methods, and Instructional Methods.
    - Specify the model choice and number of days (num_of_days) for the timetable.
    - Call generate_timetable(context, num_of_days, model_choice) to generate the lesson plan timetable.
    - The function returns a JSON dictionary with the key "lesson_plan", containing a list of daily session
      schedules formatted according to WSQ rules.

Author:
    Derrick Lim (Original), Migration to OpenAI SDK
Date:
    3 March 2025 (Original), Updated January 2026
===============================================================================
"""

from anthropic import Anthropic
from utils.helpers import parse_json_content
from settings.model_configs import get_model_config
from settings.api_manager import load_api_keys
import asyncio
import time

def extract_unique_instructional_methods(course_context):
    """
    Extracts and processes unique instructional method combinations from the provided course context.

    This function retrieves instructional methods from each Learning Unit (LU) in the course context,
    applies corrections for known replacements, and groups them into predefined valid instructional method
    pairs. If no predefined pairs exist, it generates custom pairings.

    Args:
        course_context (dict):
            A dictionary containing course details, including a list of Learning Units with instructional methods.

    Returns:
        set:
            A set of unique instructional method combinations, formatted as strings.

    Raises:
        KeyError:
            If "Learning_Units" is missing or incorrectly formatted in the course context.
    """

    unique_methods = set()

    # Define valid instructional method pairs (including "Role Play")
    valid_im_pairs = {
        ("Lecture", "Didactic Questioning"),
        ("Lecture", "Peer Sharing"),
        ("Lecture", "Group Discussion"),
        ("Demonstration", "Practice"),
        ("Demonstration", "Group Discussion"),
        ("Case Study",),
        ("Role Play",)  # Role Play is a standalone method
    }

    for lu in course_context.get("Learning_Units", []):
        extracted_methods = lu.get("Instructional_Methods", [])

        # Fix replacements BEFORE grouping
        corrected_methods = []
        for method in extracted_methods:
            if method == "Classroom":
                corrected_methods.append("Lecture")
            elif method == "Practical":
                corrected_methods.append("Practice")
            elif method == "Discussion":
                corrected_methods.append("Group Discussion")
            else:
                corrected_methods.append(method)

        # Generate valid IM pairs from the extracted methods
        method_pairs = set()
        for pair in valid_im_pairs:
            if all(method in corrected_methods for method in pair):
                method_pairs.add(", ".join(pair))  # Convert tuple to a string

        # If no valid pairs were found, create custom pairings
        if not method_pairs and corrected_methods:
            if len(corrected_methods) == 1:
                method_pairs.add(corrected_methods[0])  # Single method as standalone
            elif len(corrected_methods) == 2:
                method_pairs.add(", ".join(corrected_methods))  # Pair both together
            else:
                # Pair first two and last two methods together
                method_pairs.add(", ".join(corrected_methods[:2]))
                if len(corrected_methods) > 2:
                    method_pairs.add(", ".join(corrected_methods[-2:]))

        # Update the unique set
        unique_methods.update(method_pairs)

    return unique_methods


def create_llm_client(model_choice: str = "Claude-Sonnet-4"):
    """
    Create an Anthropic client configured with the specified model choice.

    Args:
        model_choice: Model choice string (e.g., "Claude-Sonnet-4", "Claude-Haiku-3.5")

    Returns:
        tuple: (Anthropic client instance, model configuration dict)
    """
    autogen_config = get_model_config(model_choice)
    config_dict = autogen_config.get("config", {})

    api_key = config_dict.get("api_key", "")
    model = config_dict.get("model", "claude-sonnet-4-20250514")
    temperature = config_dict.get("temperature", 0.2)

    # Fallback: If no API key in config, get it dynamically
    if not api_key:
        api_keys = load_api_keys()
        api_key = api_keys.get("ANTHROPIC_API_KEY", "")

    client = Anthropic(api_key=api_key)

    model_config = {
        "model": model,
        "temperature": temperature,
    }

    return client, model_config


async def generate_timetable(context, num_of_days, model_choice: str = "GPT-4o-Mini"):
    """
    Generates a structured lesson plan timetable based on the provided course context using OpenAI SDK.

    This function uses Anthropic SDK to create a timetable that adheres to WSQ course structure rules.
    It ensures balanced topic distribution across the specified number of days, maintains session timing integrity,
    and applies predefined instructional methods.

    Args:
        context (dict):
            A dictionary containing course details, including Learning Units, Learning Outcomes,
            and Assessment Methods.
        num_of_days (int):
            The number of days over which the course timetable should be distributed.
        model_choice (str):
            The model choice string for selecting the AI model.

    Returns:
        dict:
            A dictionary containing the generated lesson plan under the key `"lesson_plan"`,
            structured as a list of sessions for each day.

    Raises:
        Exception:
            If the generated timetable response is missing the required `"lesson_plan"` key or
            fails to parse correctly.
    """
    client, config = create_llm_client(model_choice)

    list_of_im = extract_unique_instructional_methods(context)

    system_message = f"""You are a WSQ timetable generator. Create a lesson plan for {num_of_days} day(s), 0930-1830hrs daily.

**RULES:**
1. Use ONLY these instructional methods: {list_of_im}
2. Resources: "Slide page #", "TV", "Whiteboard", "Wi-Fi"
3. Include ALL topics and bullet points from the course

**FIXED SESSIONS:**
- Day 1 Start: 0930-0945 (15min) - "Digital Attendance and Introduction" (N/A)
- Other Days Start: 0930-0940 (10min) - "Digital Attendance (AM)" (N/A)
- Morning Break: 1050-1100 (10min)
- Lunch: 1200-1245 (45min)
- PM Attendance: 1330-1340 (10min) - "Digital Attendance (PM)" (N/A)
- Afternoon Break: 1500-1510 (10min)
- End of Day: 1810-1830 (20min) - "Recap All Contents and Close" or "Course Feedback and TRAQOM Survey" (last day)

**FINAL DAY ASSESSMENTS** (schedule at end):
- Digital Attendance (Assessment) - 10min
- Final Assessment sessions (use Assessment_Methods_Details for durations)
- Course Feedback and TRAQOM Survey - 1810-1830

**SESSION FORMAT:**
- Topic: instruction_title="Topic X: [Title] (K#, A#)", bullet_points=[list of points]
- Activity: instruction_title="Activity: [Description]", bullet_points=[] (empty)

**OUTPUT JSON:**
{{"lesson_plan": [{{"Day": "Day 1", "Sessions": [{{"Time": "0930hrs - 0945hrs (15 mins)", "instruction_title": "...", "bullet_points": [...], "Instructional_Methods": "...", "Resources": "..."}}]}}]}}"""

    agent_task = f"""
        1. Take the complete dictionary provided:
        {context}
        2. Use the provided JSON dictionary, which includes all the course information, to generate the lesson plan timetable.

        **Instructions:**
        1. Adhere to all the rules and guidelines.
        2. Include the timetable data under the key 'lesson_plan' within a JSON dictionary.
        3. Return the JSON dictionary containing the 'lesson_plan' key.
    """

    # Process sample input with retry logic
    max_retries = 2
    base_delay = 5  # Reduced delay

    for attempt in range(max_retries):
        try:
            completion = client.messages.create(
                model=config["model"],
                temperature=0.3,
                system=system_message,
                messages=[
                    {"role": "user", "content": agent_task}
                ],
                max_tokens=8192
            )
            break  # Success, exit retry loop
        except Exception as e:
            error_str = str(e)
            if "overloaded" in error_str.lower() or "unavailable" in error_str.lower() or "529" in error_str:
                if attempt < max_retries - 1:  # Not the last attempt
                    delay = base_delay * (2 ** attempt)  # Exponential backoff
                    print(f"Model overloaded, retrying in {delay} seconds... (attempt {attempt + 1}/{max_retries})")
                    await asyncio.sleep(delay)
                    continue
                else:
                    raise Exception(f"Model overloaded after {max_retries} attempts. Last error: {error_str}")
            else:
                # Re-raise non-overload errors immediately
                raise e

    try:
        raw_content = completion.content[0].text

        if not raw_content:
            raise Exception("No content in response from timetable generator")

        # Log the raw content for debugging (first 500 chars)
        print(f"DEBUG: Raw timetable response (first 500 chars): {raw_content[:500]}")

        # Parse the JSON content
        timetable_response = parse_json_content(raw_content)

        # Check if response is valid
        if not timetable_response:
            raise Exception(f"Failed to parse JSON content - parse_json_content returned None. Raw content was: {raw_content[:200]}...")

        if not isinstance(timetable_response, dict):
            raise Exception(f"Invalid response format - expected dict, got {type(timetable_response)}. Content: {timetable_response}")

        if 'lesson_plan' not in timetable_response:
            available_keys = list(timetable_response.keys()) if isinstance(timetable_response, dict) else "N/A"
            raise Exception(f"No lesson_plan key found in timetable data. Available keys: {available_keys}")

        # Validate lesson_plan structure
        lesson_plan = timetable_response['lesson_plan']
        if not isinstance(lesson_plan, list):
            raise Exception(f"lesson_plan should be a list, got {type(lesson_plan)}")

        return timetable_response

    except Exception as e:
        # Provide more context in the error message
        error_context = f"Context info - num_days: {num_of_days}, context keys: {list(context.keys()) if isinstance(context, dict) else 'Not a dict'}"
        raise Exception(f"Failed to parse timetable JSON: {str(e)}. {error_context}")