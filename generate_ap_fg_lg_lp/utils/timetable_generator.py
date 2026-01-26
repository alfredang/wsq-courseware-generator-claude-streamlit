"""
File: timetable_generator.py

===============================================================================
Timetable Generator Module (OpenAI SDK Version)
===============================================================================
Description:
    This module generates a structured lesson plan timetable based on the provided course context.
    It leverages the OpenAI SDK to produce a detailed and balanced lesson plan that adheres
    strictly to WSQ course structure rules. The generated timetable ensures even distribution of topics,
    fixed sessions (such as attendance, breaks, and final assessments), and appropriate use of instructional
    methods over the specified number of days.

    This version uses the OpenAI SDK directly instead of Autogen framework.

Main Functionalities:
    • extract_unique_instructional_methods(course_context):
          Extracts and processes unique instructional method combinations from each Learning Unit in the
          course context by correcting method names and grouping them into valid pairs.
    • generate_timetable(context, num_of_days, model_choice):
          Uses OpenAI SDK to generate a complete lesson plan timetable in JSON format.
          The timetable includes fixed sessions (attendance, breaks, assessment sessions) and topic or
          activity sessions, distributed evenly across the specified number of days.

Dependencies:
    - openai (OpenAI SDK)
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

from openai import OpenAI
from common.common import parse_json_content
from settings.model_configs import get_model_config
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


def create_openai_client(model_choice: str = "GPT-4o-Mini"):
    """
    Create an OpenAI client configured with the specified model choice.

    Args:
        model_choice: Model choice string (e.g., "DeepSeek-Chat", "GPT-4o-Mini")

    Returns:
        tuple: (OpenAI client instance, model configuration dict)
    """
    autogen_config = get_model_config(model_choice)
    config_dict = autogen_config.get("config", {})

    base_url = config_dict.get("base_url", "https://openrouter.ai/api/v1")
    api_key = config_dict.get("api_key", "")
    model = config_dict.get("model", "gpt-4o-mini")
    temperature = config_dict.get("temperature", 0.2)

    client = OpenAI(
        base_url=base_url,
        api_key=api_key
    )

    model_config = {
        "model": model,
        "temperature": temperature,
        "base_url": base_url
    }

    return client, model_config


async def generate_timetable(context, num_of_days, model_choice: str = "GPT-4o-Mini"):
    """
    Generates a structured lesson plan timetable based on the provided course context using OpenAI SDK.

    This function uses OpenAI SDK to create a timetable that adheres to WSQ course structure rules.
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
    client, config = create_openai_client(model_choice)

    list_of_im = extract_unique_instructional_methods(context)

    system_message = f"""
            You are a timetable generator for WSQ courses.
            Your task is to create a **detailed and structured lesson plan timetable** for a WSQ course based on the provided course information and context. **Every generated timetable must strictly follow the rules below to maintain quality and accuracy.**

            ---

            ### **Instructions:**
            #### 1. **Course Data & Completeness**
            - **Use all provided course details**, including Learning Units (LUs), topics, Learning Outcomes (LOs), Assessment Methods (AMs), and Instructional Methods (IMs).
            - **Do not omit any topics or bullet points.**
            - **Ensure that every topic is included and each bullet point is addressed in at least one session.**
            
            #### 2. **Number of Days & Even Distribution**
            - Use **exactly {num_of_days}** day(s).
            - Distribute **topics, activities, and assessments** evenly across the day(s).
            - Ensure that each day has **exactly 9 hours** (0930hrs - 1830hrs), including breaks and assessments.
            - **Important:** The schedule for each day must start at the designated start time and end exactly at 1830hrs.

            ### **3. Instructional Methods & Resources**
            **Use ONLY these instructional methods** (extracted from the course context):  
            {list_of_im}
            DO NOT generate any IM pairs that are not in this list.
            Every session must have an instructional method pair that is in the list.
                    
            **Approved Resources:**
                - "Slide page #"
                - "TV"
                - "Whiteboard"
                - "Wi-Fi"

            ### **4. Fixed Sessions & Breaks**
            Each day must contain the following **fixed time slots**:

            #### **Day 1 First Timeslot (Mandatory)**
            - **Time:** "0930hrs - 0945hrs (15 mins)"
            - **Instructions:** 
            "Digital Attendance and Introduction to the Course"
                • Trainer Introduction
                • Learner Introduction
                • Overview of Course Structure
            - **Instructional_Methods:** "N/A"
            - **Resources:** "QR Attendance, Attendance Sheet"

            #### **Subsequent Days First Timeslot**
            - **Time:** "0930hrs - 0940hrs (10 mins)"
            - **Instructions:** "Digital Attendance (AM)"
            - **Instructional_Methods:** "N/A"
            - **Resources:** "QR Attendance, Attendance Sheet"

            #### **Mandatory Breaks**
            - **Morning Break:**  "1050hrs - 1100hrs (10 mins)"  
            - **Lunch Break:**  "1200hrs - 1245hrs (45 mins)"  
            - **Digital Attendance (PM):**  "1330hrs - 1340hrs (10 mins)"  
            - **Afternoon Break:**  "1500hrs - 1510hrs (10 mins)"  

            #### **End-of-Day Recap (All Days Except Assessment Day)**
            - **Time:** "1810hrs - 1830hrs (20 mins)"
            - **Instructions:** "Recap All Contents and Close"
            - **Instructional_Methods:** [a valid Lecture or IM Pair from the context]
            - **Resources:** "Slide page #, TV, Whiteboard"

            ---

            ### **5. Final Day Assessments**
            On the Assessment day, the following sessions must be scheduled as the **last timeslots** of the day, in the exact order given below. **No other sessions should follow these sessions.**

            1. **Digital Attendance (Assessment) (10 mins)**
            - **Time:** "[Start Time] - [End Time] (10 mins)"
            - **Instructions:** "Digital Attendance (Assessment)"
            - **Instructional_Methods:** "N/A"
            - **Resources:** "QR Attendance, Attendance Sheet"

            2. **Final Assessment Session(s)**
            - For each Assessment Method in the course details, schedule a Final Assessment session:
                - **Time:** "[Start Time] - [End Time] ([Duration])" (Duration must align with each assessment method's `Total_Delivery_Hours`.)
                - **Instructions:** "Final Assessment: [Assessment Method Full Name] ([Method Abbreviation])"
                - **Instructional_Methods:** "Assessment"
                - **Resources:** "Assessment Questions, Assessment Plan"

            3. **Final Course Feedback and TRAQOM Survey**
            - **Time:** "1810hrs - 1830hrs (20 mins)"
            - **Instructions:** "Course Feedback and TRAQOM Survey"
            - **Instructional_Methods:** "N/A"
            - **Resources:** "Feedback Forms, Survey Links"

            ---

            ### **6. Topic & Activity Session Structure**
            #### **Topic Sessions**
            - **Time:** Varies (e.g., "0945hrs - 1050hrs (65 mins)")
            - **Instructions Format:**  
            Instead of a single string, break the session instructions into:
            - **instruction_title:** e.g., "Topic X: [Topic Title] (K#, A#)"
            - **bullet_points:** A list containing each bullet point for the topic.
            
            **Important:** If there are too few topics to fill the schedule, you are allowed to split the bullet points of a single topic across multiple sessions. In that case, each session should cover a different subset of bullet points, and together they must cover all bullet points for that topic.
          
            Example:
            ```json
            "instruction_title": "Topic 1: Interpretation of a Balance Sheet (A1)",
            "bullet_points": [
                "Understanding the different components of a Balance Sheet and where to find value of any business in any Balance Sheet."
            ]
            ```
            and
            ```json
            "instruction_title": "Topic 1: Interpretation of a Balance Sheet (A1) (Cont.)",
            "bullet_points": [
                "Understanding the various types of financial ratios that can be derived from the Balance Sheet"
            ]
            ```

            #### **Activity Sessions**
            - **Duration:** Fixed at 10 minutes.
            - **Must immediately follow the corresponding topic session.**
            - **Instructions Format:**  
            - **instruction_title:** e.g., "Activity: Demonstration on [Description]" or "Activity: Case Study on [Description]"
            - **bullet_points:** **This must be an empty list.**
                **Note:** Activity timeslots must strictly have no bullet points.

            #### **7. Adjustments on Topic Allocation**
            - **If there are too many topics to fit within {num_of_days} day(s):**
            - Adjust session durations while ensuring all topics and their bullet points are covered.
            - **If there are too few topics to fill all timeslots:**
            - You may split the bullet points of a topic across multiple sessions.
            - You may add one, and only one, **Recap All Contents and Close** session per day **(if needed)**, placed immediately before the Digital Attendance (Assessment) Timeslot.  
            **Do not generate multiple Recap sessions.**
            - This Recap session is a fallback option only when there are insufficient topic sessions; it should not replace the bullet point details of the topic sessions.

            ---

            ### **8. Output Format**
            The output must strictly follow this JSON structure:

            ```json
            {{
                "lesson_plan": [
                    {{
                        "Day": "Day X",
                        "Sessions": [
                            {{
                                "Time": "Start - End (duration)",
                                "instruction_title": "Session title (e.g., Topic 1: ... or Activity: ...)",
                                "bullet_points": ["Bullet point 1", "Bullet point 2", "..."],
                                "Instructional_Methods": "Method pair",
                                "Resources": "Required resources"
                            }}
                            // Additional sessions for the day
                        ]
                    }}
                    // Additional days
                ]
            }}
            ```
            All timings must be consecutive without gaps or overlaps.
            The total number of days in the timetable must match {num_of_days}.
            """

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
    max_retries = 3
    base_delay = 30  # Start with 30 seconds

    for attempt in range(max_retries):
        try:
            completion = client.chat.completions.create(
                model=config["model"],
                temperature=config["temperature"],
                messages=[
                    {"role": "system", "content": system_message},
                    {"role": "user", "content": agent_task}
                ],
                response_format={"type": "json_object"},
                max_tokens=16384
            )
            break  # Success, exit retry loop
        except Exception as e:
            error_str = str(e)
            if "503" in error_str or "overloaded" in error_str.lower() or "unavailable" in error_str.lower():
                if attempt < max_retries - 1:  # Not the last attempt
                    delay = base_delay * (2 ** attempt)  # Exponential backoff
                    print(f"Model overloaded (503 error), retrying in {delay} seconds... (attempt {attempt + 1}/{max_retries})")
                    await asyncio.sleep(delay)
                    continue
                else:
                    raise Exception(f"Model overloaded after {max_retries} attempts. Last error: {error_str}")
            else:
                # Re-raise non-503 errors immediately
                raise e

    try:
        raw_content = completion.choices[0].message.content

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