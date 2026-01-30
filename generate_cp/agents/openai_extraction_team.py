"""
OpenAI SDK-based Extraction Team.

This module replaces the Autogen-based extraction_team.py with direct OpenAI SDK implementations.
Uses JSON mode for OpenRouter compatibility.

The extraction team consists of 5 sequential agents:
1. Course Info Extractor - Extracts course metadata
2. Learning Outcomes Extractor - Extracts LOs, K and A statements
3. TSC and Topics Extractor - Extracts TSC info and topics
4. Assessment Methods Extractor - Extracts assessment methods and course outline
5. Aggregator - Combines all extracted data into single JSON

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


def extraction_task(data):
    """Generate the extraction task prompt."""
    return f"""
    1. Extract data from the following JSON file: {data}
    2. Map the extracted data according to the schemas.
    3. Return a full JSON object with all the extracted data according to the schema.
    """


async def run_course_info_extractor(
    data: Dict[str, Any],
    model_choice: str,
    stream_to_console: bool = True
) -> Dict[str, Any]:
    """
    Run the course info extractor agent.

    Extracts course metadata like title, organization, hours, etc.

    Args:
        data: Raw TSC document data
        model_choice: Model selection string
        stream_to_console: Whether to stream output to console

    Returns:
        Dict containing Course Information
    """
    client, config = create_openai_client(model_choice)

    system_message = f"""
    You are to extract the following variables from {data}:
        1) Course Title
        2) Name of Organisation
        3) Classroom Hours (can be found under Instructional Duration: xxxx)
        4) Practical Hours (if none found, insert 0)
        5) Number of Assessment Hours (can be found under Assessment Duration: xxxx)
        6) Course Duration (Number of Hours)
        7) Industry

        Use the term_library below for "Industry", based on the front 3 letters of the TSC code:
        term_library = {{
            'ACC': 'Accountancy',
            'RET': 'Retail',
            'MED': 'Media',
            'ICT': 'Infocomm Technology',
            'BEV': 'Built Environment',
            'DSN': 'Design',
            'DNS': 'Design',
            'AGR': 'Agriculture',
            'ELE': 'Electronics',
            'LOG': 'Logistics',
            'STP': 'Sea Transport',
            'TOU': 'Tourism',
            'AER': 'Aerospace',
            'ATP': 'Air Transport',
            'BPM': 'BioPharmaceuticals Manufacturing',
            'ECM': 'Energy and Chemicals',
            'EGS': 'Engineering Services',
            'EPW': 'Energy and Power',
            'EVS': 'Environmental Services',
            'FMF': 'Food Manufacturing',
            'FSE': 'Financial Services',
            'FSS': 'Food Services',
            'HAS': 'Hotel and Accommodation Services',
            'HCE': 'Healthcare',
            'HRS': 'Human Resource',
            'INP': 'Intellectual Property',
            'LNS': 'Landscape',
            'MAR': 'Marine and Offshore',
            'PRE': 'Precision Engineering',
            'PTP': 'Public Transport',
            'SEC': 'Security',
            'SSC': 'Social Service',
            'TAE': 'Training and Adult Education',
            'WPH': 'Workplace Safety and Health',
            'WST': 'Wholesale Trade',
            'ECC': 'Early Childhood Care and Education',
            'ART': 'Arts'
        }}
        Format the extracted data in JSON format, with this structure, do NOT change the key names or add unnecessary spaces:
            "Course Information": {{
            "Course Title": "",
            "Name of Organisation": "",
            "Classroom Hours": ,
            "Practical Hours": ,
            "Number of Assessment Hours": ,
            "Course Duration (Number of Hours)": ,
            "Industry": ""
        }}
        Extra emphasis on following the JSON format provided, do NOT change the names of the keys, never use "course_info" as the key name.
    """

    user_task = extraction_task(data)

    if stream_to_console:
        print("\n" + "=" * 80)
        print("COURSE INFO EXTRACTOR - Extracting Course Metadata")
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
            print("\n[Course Info Extractor Response]")
            print(json.dumps(parsed_json, indent=2))
            print("=" * 80 + "\n")

        return parsed_json

    except Exception as e:
        print(f"Error in course info extractor: {e}", file=sys.stderr)
        raise


async def run_learning_outcomes_extractor(
    data: Dict[str, Any],
    model_choice: str,
    stream_to_console: bool = True
) -> Dict[str, Any]:
    """
    Run the learning outcomes extractor agent.

    Extracts Learning Outcomes, Knowledge, and Ability statements.

    Args:
        data: Raw TSC document data
        model_choice: Model selection string
        stream_to_console: Whether to stream output to console

    Returns:
        Dict containing Learning Outcomes
    """
    client, config = create_openai_client(model_choice)

    system_message = f"""
    You are to extract the following variables from {data}:
        1) Learning Outcomes - include the terms LO1:, LO2:, etc. in front of each learning outcome
        2) Knowledge statements - MUST extract ALL K# statements from the TSC document
        3) Ability statements - MUST extract ALL A# statements from the TSC document

        CRITICAL INSTRUCTIONS:
        - Find ALL text blocks that start with "K1:", "K2:", "K3:", etc. - these are Knowledge statements
        - Find ALL text blocks that start with "A1:", "A2:", "A3:", etc. - these are Ability statements
        - Each statement should be a SEPARATE item in the array
        - Do NOT combine multiple statements into one string
        - Include the complete description after the colon

        Format the extracted data in JSON format with this EXACT structure:
            "Learning Outcomes": {{
                "Learning Outcomes": [
                    "LO1: First learning outcome description",
                    "LO2: Second learning outcome description"
                ],
                "Knowledge": [
                    "K1: First knowledge statement description",
                    "K2: Second knowledge statement description",
                    "K3: Third knowledge statement description"
                ],
                "Ability": [
                    "A1: First ability statement description",
                    "A2: Second ability statement description"
                ]
            }}

        CRITICAL: Extract EVERY K# and A# statement found in the document. Do not skip any.
        CRITICAL: Each K# and A# must be a separate array item, not combined with newlines.
    """

    user_task = extraction_task(data)

    if stream_to_console:
        print("\n" + "=" * 80)
        print("LEARNING OUTCOMES EXTRACTOR - Extracting LOs, K and A Statements")
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
            print("\n[Learning Outcomes Extractor Response]")
            print(json.dumps(parsed_json, indent=2))
            print("=" * 80 + "\n")

        return parsed_json

    except Exception as e:
        print(f"Error in learning outcomes extractor: {e}", file=sys.stderr)
        raise


async def run_tsc_and_topics_extractor(
    data: Dict[str, Any],
    model_choice: str,
    stream_to_console: bool = True
) -> Dict[str, Any]:
    """
    Run the TSC and topics extractor agent.

    Extracts TSC title, code, topics, and learning units.

    Args:
        data: Raw TSC document data
        model_choice: Model selection string
        stream_to_console: Whether to stream output to console

    Returns:
        Dict containing TSC and Topics
    """
    client, config = create_openai_client(model_choice)

    system_message = f"""
    You are to extract the following variables from {data}:
        1) TSC Title - the full title of the TSC
        2) TSC Code - the code in format XXX-XXX-XXXX-X.X
        3) Topics - MUST extract ALL topics from ALL Learning Units
        4) Learning Units - extract all LU titles WITHOUT K/A codes

        CRITICAL INSTRUCTIONS FOR TOPICS:
        - Extract EVERY topic from the document that starts with "Topic 1:", "Topic 2:", etc.
        - Include the FULL topic name INCLUDING the K# and A# codes in parentheses
        - Topics appear under each Learning Unit in the "Course Outline" section
        - You must extract topics from ALL Learning Units, not just one
        - Format: "Topic X: Topic Name (K#, A#)"

        CRITICAL INSTRUCTIONS FOR LEARNING UNITS:
        - Extract all Learning Unit titles (LU1:, LU2:, LU3:, etc.)
        - Format: "LU1: Learning Unit Title"
        - Do NOT include the (K#, A#) codes in Learning Units
        - Only the LU number and title

        Format the extracted data in JSON format, with this structure:
            "TSC and Topics": {{
            "TSC Title": ["Generative AI Model Development and Fine Tuning"],
            "TSC Code": ["ICT-BAS-0048-1.1"],
            "Topics": [
                "Topic 1: Probability Theory and Statistics (K1)",
                "Topic 2: Deep Learning Theory and Algorithms (K9)",
                "Topic 3: Machine Learning Libraries (K10)"
            ],
            "Learning Units": [
                "LU1: Foundations of Generative AI",
                "LU2: Data Preparation for Generative AI"
            ]
        }}

        CRITICAL: Extract ALL Topics from ALL Learning Units in the document.
    """

    user_task = extraction_task(data)

    if stream_to_console:
        print("\n" + "=" * 80)
        print("TSC AND TOPICS EXTRACTOR - Extracting TSC Info and Topics")
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
            print("\n[TSC and Topics Extractor Response]")
            print(json.dumps(parsed_json, indent=2))
            print("=" * 80 + "\n")

        return parsed_json

    except Exception as e:
        print(f"Error in TSC and topics extractor: {e}", file=sys.stderr)
        raise


async def run_assessment_methods_extractor(
    data: Dict[str, Any],
    model_choice: str,
    stream_to_console: bool = True
) -> Dict[str, Any]:
    """
    Run the assessment methods extractor agent.

    Extracts assessment methods, instructional methods, and course outline.

    Args:
        data: Raw TSC document data
        model_choice: Model selection string
        stream_to_console: Whether to stream output to console

    Returns:
        Dict containing Assessment Methods
    """
    client, config = create_openai_client(model_choice)

    system_message = f"""
    You are to extract the following variables from {data}:
        1) Assessment Methods (remove the brackets and time values at the end of each string)
        2) Instructional Methods (extract the full string as-is from the TSC document)
        3) Amount of Practice Hours (insert "N.A." if not found)
        4) Course Outline - MUST extract ALL Learning Units with their Topics and Details

        CRITICAL INSTRUCTIONS FOR COURSE OUTLINE:
        - Find the "Course Outline:" section in the TSC document
        - Each Learning Unit (LU1, LU2, etc.) will list topics underneath it
        - Each topic will have a title in format "Topic X: Name (K#, A#)"
        - You MUST extract topic details/descriptions that appear under each topic
        - If no details are explicitly listed, leave Details as empty array []
        - INCLUDE THE FULL TOPIC TITLE with K and A factors in parentheses

        Format the extracted data in JSON format with this EXACT structure:
            "Assessment Methods": {{
                "Assessment Methods": ["Written Assessment", "Practical Performance"],
                "Amount of Practice Hours": "N.A.",
                "Course Outline": {{
                    "Learning Units": {{
                        "LU1": {{
                            "Description": [
                                {{
                                    "Topic": "Topic 1: Full Topic Name (K1, A1)",
                                    "Details": ["Detail point 1", "Detail point 2"]
                                }},
                                {{
                                    "Topic": "Topic 2: Another Topic (K2, A2)",
                                    "Details": []
                                }}
                            ]
                        }},
                        "LU2": {{
                            "Description": [
                                {{
                                    "Topic": "Topic 1: Topic Title (K3)",
                                    "Details": ["Detail 1"]
                                }}
                            ]
                        }}
                    }}
                }},
                "Instructional Methods": "Interactive Presentation, Demonstration, Practical"
            }}

        CRITICAL: You MUST extract Course Outline. It is mandatory. Look for the "Course Outline:" section in the document.
        CRITICAL: Extract ALL Learning Units and ALL Topics listed under each LU.
        CRITICAL: Instructional Methods should be a STRING, not an array.
    """

    user_task = extraction_task(data)

    if stream_to_console:
        print("\n" + "=" * 80)
        print("ASSESSMENT METHODS EXTRACTOR - Extracting Assessment Methods and Course Outline")
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
            print("\n[Assessment Methods Extractor Response]")
            print(json.dumps(parsed_json, indent=2))
            print("=" * 80 + "\n")

        return parsed_json

    except Exception as e:
        print(f"Error in assessment methods extractor: {e}", file=sys.stderr)
        raise


async def run_aggregator_agent(
    course_info: Dict[str, Any],
    learning_outcomes: Dict[str, Any],
    tsc_and_topics: Dict[str, Any],
    assessment_methods: Dict[str, Any],
    model_choice: str,
    stream_to_console: bool = True
) -> Dict[str, Any]:
    """
    Run the aggregator agent to combine all extracted data.

    Args:
        course_info: Output from course info extractor
        learning_outcomes: Output from learning outcomes extractor
        tsc_and_topics: Output from TSC and topics extractor
        assessment_methods: Output from assessment methods extractor
        model_choice: Model selection string
        stream_to_console: Whether to stream output to console

    Returns:
        Dict containing combined extraction output
    """
    client, config = create_openai_client(model_choice)

    system_message = """
    You are to combine the outputs from the following agents into a single JSON object, do NOT aggregate output from the validator agent:
        1) course_info_extractor
        2) learning_outcomes_extractor
        3) tsc_and_topics_extractor
        4) assessment_methods_extractor
    Return the combined output into a single JSON file, do not alter the keys in any way, do not add or nest any keys. Ensure that the following is adhered to:
    1. **Strict JSON Formatting:**
    - The output must be a valid JSON object with proper syntax (keys in double quotes, commas separating elements, arrays enclosed in square brackets, objects enclosed in curly braces).

    2. **Schema Compliance:**
    The JSON must include the following top-level keys:
    - `"Course Information"`
    - `"Learning Outcomes"`
    - `"TSC and Topics"`
    - `"Assessment Methods"`

    3. **No Trailing Commas or Missing Brackets:**
    - Ensure that each array (`[...]`) and object (`{...}`) is closed properly.
    - Do not leave trailing commas.

    4. **Consistent Key Names:**
    - Use consistent and properly spelled keys as specified.

    5. **Always Validate Before Output:**
    - Run a JSON lint check (or a `json.loads()` equivalent if you are simulating code) before returning the final JSON.

    6. **Error Handling:**
    If you detect an issue in the JSON (e.g., missing commas, brackets, or improper formatting), correct it immediately before providing the output.

    7. **Output Format:**
    Return only the JSON object and no additional commentary.
    """

    user_task = f"""
    Combine the following extracted data into a single JSON object:

    Course Information:
    {json.dumps(course_info, indent=2)}

    Learning Outcomes:
    {json.dumps(learning_outcomes, indent=2)}

    TSC and Topics:
    {json.dumps(tsc_and_topics, indent=2)}

    Assessment Methods:
    {json.dumps(assessment_methods, indent=2)}

    Return only the combined JSON object.
    """

    if stream_to_console:
        print("\n" + "=" * 80)
        print("AGGREGATOR AGENT - Combining All Extracted Data")
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
            print("\n[Aggregator Agent Response]")
            print(json.dumps(parsed_json, indent=2))
            print("=" * 80 + "\n")

        return parsed_json

    except Exception as e:
        print(f"Error in aggregator agent: {e}", file=sys.stderr)
        raise


async def run_extraction_team(
    data: Dict[str, Any],
    model_choice: str,
    stream_to_console: bool = True
) -> Dict[str, Any]:
    """
    Run the full extraction team pipeline.

    This replaces the Autogen RoundRobinGroupChat with sequential OpenAI API calls.
    Executes: Course Info -> Learning Outcomes -> TSC/Topics -> Assessment Methods -> Aggregator

    Args:
        data: Raw TSC document data
        model_choice: Model selection string
        stream_to_console: Whether to stream output to console

    Returns:
        Dict containing combined extraction output
    """
    if stream_to_console:
        print("\n" + "=" * 80)
        print("EXTRACTION TEAM - Starting Extraction Pipeline")
        print("=" * 80)

    # Run agents sequentially (mimics RoundRobinGroupChat with max_turns=5)
    course_info = await run_course_info_extractor(
        data=data,
        model_choice=model_choice,
        stream_to_console=stream_to_console
    )

    learning_outcomes = await run_learning_outcomes_extractor(
        data=data,
        model_choice=model_choice,
        stream_to_console=stream_to_console
    )

    tsc_and_topics = await run_tsc_and_topics_extractor(
        data=data,
        model_choice=model_choice,
        stream_to_console=stream_to_console
    )

    assessment_methods = await run_assessment_methods_extractor(
        data=data,
        model_choice=model_choice,
        stream_to_console=stream_to_console
    )

    # Aggregator combines all findings
    combined_output = await run_aggregator_agent(
        course_info=course_info,
        learning_outcomes=learning_outcomes,
        tsc_and_topics=tsc_and_topics,
        assessment_methods=assessment_methods,
        model_choice=model_choice,
        stream_to_console=stream_to_console
    )

    if stream_to_console:
        print("\n" + "=" * 80)
        print("EXTRACTION TEAM - Pipeline Complete")
        print("=" * 80)

    return combined_output
