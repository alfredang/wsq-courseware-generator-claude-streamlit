"""
OpenAI SDK-based Excel Agents.

This module replaces the Autogen-based excel_agents.py with direct OpenAI SDK implementations.
Uses JSON mode for OpenRouter compatibility (NOT beta.chat.completions.parse which OpenRouter doesn't support).

Author: Migration from Autogen to OpenAI SDK
Date: 2026-01-20
"""

import json
import sys
import re
from typing import Dict, Any
from generate_cp.utils.openai_model_client import create_openai_client
from generate_cp.schemas.excel_schemas import CourseOverviewResponse, KAAnalysisResponse, InstructionalMethodsResponse


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


async def run_course_agent(
    ensemble_output: Dict[str, Any],
    model_choice: str,
    stream_to_console: bool = True
) -> Dict[str, Any]:
    """
    Run the course overview agent using OpenAI SDK.

    Generates a course description based on course title, learning outcomes,
    and topics. Implements a two-step process: generation + validation.

    Args:
        ensemble_output: Dictionary containing course data (LOs, topics, etc.)
        model_choice: Model selection string (e.g., "DeepSeek-Chat")
        stream_to_console: Whether to stream output to console

    Returns:
        Dict containing course_overview with course_description
    """
    client, config = create_openai_client(model_choice)

    # System message from original Autogen implementation
    system_message = f"""
    As a digital marketing consultant, your primary role is to assist small business owners in optimizing their websites for SEO and improving their digital marketing strategies to enhance lead generation. You should provide clear, actionable advice tailored to the challenges and opportunities typical for small businesses. Focus on offering strategies that are feasible and effective for smaller budgets and resources. Stay abreast of the latest SEO and digital marketing trends, ensuring your advice is current and practical. When necessary, ask for clarification to understand the specific needs of each business, but also be proactive in filling in general small business scenarios. Personalize your responses to reflect an understanding of the unique dynamics and constraints small businesses face in digital marketing.
    You will do so based on the course title, learning outcomes (LOs), and the Topics found in {ensemble_output}

    Your task is to create a Course Description in 2 paragraphs for the above factors.

    An example answer is as follows: "This course equips learners with essential GitHub skills, covering version control, repository management, and collaborative workflows. Participants will learn how to create repositories, manage branches, integrate Git scripts, and leverage pull requests to streamline development. Through hands-on exercises, learners will explore GitHub features like issue tracking, code reviews, and discussions to enhance team collaboration.

    The course also covers modern GitHub tools such as GitHub Actions, Copilot, and Codespaces for automation and AI-driven development. Learners will gain expertise in security best practices, including dependency management, code scanning, and authentication protocols. By the end of the course, participants will be able to diagnose configuration issues, optimize deployment processes, and implement software improvements effectively."

    You must start your answer with "This course"
    You must take into consideration the learning outcomes and topics for the Course Description.
    Do not mention the course name in your answer.
    Do not use more than 300 words, it should be a concise summary of the course and what it has to offer.
    Do not mention the LOs in your answer.
    Do not add quotation marks in your answer.

    Provide learners with a clear overview of the course:
    Highlight the benefits your course offers including skils, competencies and needs that the course will address
    Explain how the course is relevant to the industry and how it may impact the learner's career in terms of employment/ job upgrading opportunities
    Indicate that the course is for beginner learners.
    Do not have more than 1 key value pair under "course_overview", and that key value pair must be "course_description".

    Format your response in the given JSON structure under "course_overview".
    Your output MUST be as follows, with course_description being the only key-value pair under "course_overview":
    {{
        "course_overview": {{
            "course_description": "Your course description here"
        }}
    }}
    """

    user_task = """
    1. Based on the provided data, generate your justifications.
    2. Ensure your responses are structured in JSON format.
    3. Return a full JSON object with all your answers according to the schema.
    """

    if stream_to_console:
        print("\n" + "=" * 80)
        print("COURSE AGENT - Generating Course Description")
        print("=" * 80)

    try:
        # Use standard chat.completions.create with JSON mode (OpenRouter compatible)
        completion = client.chat.completions.create(
            model=config["model"],
            temperature=config["temperature"],
            messages=[
                {"role": "system", "content": system_message},
                {"role": "user", "content": user_task}
            ],
            response_format={"type": "json_object"}
        )

        # Extract and parse JSON from response
        content = completion.choices[0].message.content
        print(f"DEBUG Course Agent - Raw response: {content[:500] if content else 'None'}...")

        parsed_json = extract_json_from_response(content)
        print(f"DEBUG Course Agent - Parsed JSON keys: {list(parsed_json.keys()) if parsed_json else 'Empty'}")

        # Handle cases where course_overview is missing or response is malformed
        if not parsed_json or "course_overview" not in parsed_json:
            print("WARNING: course_overview not in response, attempting to extract from content")
            # Try to find course_description directly in content
            if "course_description" in parsed_json:
                parsed_json = {"course_overview": parsed_json}
            elif content and "This course" in content:
                # Extract the course description from raw text
                desc_start = content.find("This course")
                desc_text = content[desc_start:desc_start + 1500] if desc_start != -1 else "Course description not available."
                # Clean up the text - remove JSON artifacts
                desc_text = re.sub(r'[{}\[\]"]', '', desc_text).strip()
                desc_text = desc_text.split("course_description")[-1].strip(": ").strip()
                if desc_text.startswith("This course"):
                    parsed_json = {"course_overview": {"course_description": desc_text[:800]}}
                else:
                    parsed_json = {"course_overview": {"course_description": "This course provides comprehensive training in the specified domain, equipping learners with essential skills and knowledge for career advancement."}}
            else:
                # Provide a default fallback
                parsed_json = {"course_overview": {"course_description": "This course provides comprehensive training in the specified domain, equipping learners with essential skills and knowledge for career advancement."}}

        # Validate with Pydantic schema
        validated = CourseOverviewResponse(**parsed_json)

        if stream_to_console:
            print("\n[Course Agent Response]")
            print(json.dumps(validated.model_dump(), indent=2))
            print("=" * 80 + "\n")

        return validated.model_dump()

    except Exception as e:
        print(f"Error in course agent: {e}", file=sys.stderr)
        # Return a fallback response instead of raising
        fallback = {"course_overview": {"course_description": "This course provides comprehensive training in the specified domain, equipping learners with essential skills and knowledge for career advancement."}}
        print(f"Returning fallback response due to error")
        return fallback


async def run_ka_analysis_agent(
    ensemble_output: Dict[str, Any],
    instructional_methods_data: Any,
    model_choice: str,
    stream_to_console: bool = True
) -> Dict[str, Any]:
    """
    Run the Knowledge & Ability (K&A) analysis agent using OpenAI SDK.

    Analyzes K and A factors in relation to assessment methods, providing
    rationale for each K&A factor (max 50 words each).

    Args:
        ensemble_output: Dictionary containing course data
        instructional_methods_data: DataFrame with instructional methods
        model_choice: Model selection string
        stream_to_console: Whether to stream output to console

    Returns:
        Dict containing KA_Analysis with K1, K2, A1, A2, etc. mappings
    """
    client, config = create_openai_client(model_choice)

    system_message = f"""
    You are responsible for elaborating on the appropriateness of the assessment methods in relation to the K and A statements. For each LO-MoA (Learning Outcome - Method of Assessment) pair, input rationale for each on why this MoA was chosen, and specify which K&As it will assess.

    The data provided which contains the ensemble of K and A statements, and the Learning Outcomes and Methods of Assessment, is in this dataframe: {instructional_methods_data}
    For each explanation, you are to provide no more than 50 words. Do so for each A and K factor present.
    Your response should be structured in the given JSON format under "KA_Analysis".
    Full list of K factors: {ensemble_output.get('Learning Outcomes', {}).get('Knowledge', [])}
    Full list of A factors: {ensemble_output.get('Learning Outcomes', {}).get('Ability', [])}
    Ensure that ALL of the A and K factors are addressed.
    Only use the first 2 characters as the key names for your JSON output, like K1 for example. Do not use the full A and K factor description as the key name.

    Do not mention any of the Instructional Methods directly.
    K factors must address theory and knowledge, while A factors must address practical application and skills, you must reflect this in your analysis.

    Follow the suggested answer structure shown below, respective to A and K factors.
    For example:
    {{
        "KA_Analysis": {{
            "K1": "The candidate will respond to a series of [possibly scenario based] short answer questions related to: ",
            "A1": "The candidate will perform [some form of practical exercise] on this [topic] and submit [materials done] for: ",
            "K2": "explanation",
            "A2": "explanation"
        }}
    }}
    """

    user_task = """
    1. Based on the provided data, generate your justifications, ensure that ALL the A and K factors are addressed.
    2. Ensure your responses are structured in JSON format.
    3. Return a full JSON object with all your answers according to the schema.
    """

    if stream_to_console:
        print("\n" + "=" * 80)
        print("KA ANALYSIS AGENT - Analyzing Knowledge & Ability Factors")
        print("=" * 80)

    try:
        # Use standard chat.completions.create with JSON mode (OpenRouter compatible)
        completion = client.chat.completions.create(
            model=config["model"],
            temperature=config["temperature"],
            messages=[
                {"role": "system", "content": system_message},
                {"role": "user", "content": user_task}
            ],
            response_format={"type": "json_object"}
        )

        # Extract and parse JSON from response
        content = completion.choices[0].message.content
        print(f"DEBUG KA Agent - Raw response: {content[:500] if content else 'None'}...")

        parsed_json = extract_json_from_response(content)
        print(f"DEBUG KA Agent - Parsed JSON keys: {list(parsed_json.keys()) if parsed_json else 'Empty'}")

        # Handle cases where KA_Analysis is missing
        if not parsed_json or "KA_Analysis" not in parsed_json:
            print("WARNING: KA_Analysis not in response, attempting to extract")
            # Check if keys look like K1, K2, A1, A2 directly
            if parsed_json and any(k.startswith(('K', 'A')) and len(k) <= 3 for k in parsed_json.keys()):
                parsed_json = {"KA_Analysis": parsed_json}
            else:
                # Build default KA Analysis from ensemble_output
                ka_dict = {}
                knowledge = ensemble_output.get('Learning Outcomes', {}).get('Knowledge', [])
                ability = ensemble_output.get('Learning Outcomes', {}).get('Ability', [])
                for i, k in enumerate(knowledge, 1):
                    ka_dict[f"K{i}"] = f"The candidate will respond to short answer questions related to {k[:50]}..."
                for i, a in enumerate(ability, 1):
                    ka_dict[f"A{i}"] = f"The candidate will perform practical exercises demonstrating {a[:50]}..."
                parsed_json = {"KA_Analysis": ka_dict}

        # Validate with Pydantic schema
        validated = KAAnalysisResponse(**parsed_json)

        if stream_to_console:
            print("\n[KA Analysis Agent Response]")
            print(json.dumps(validated.model_dump(), indent=2))
            print("=" * 80 + "\n")

        return validated.model_dump()

    except Exception as e:
        print(f"Error in KA analysis agent: {e}", file=sys.stderr)
        # Return a fallback response
        fallback = {"KA_Analysis": {"K1": "Knowledge assessment through written questions.", "A1": "Practical assessment through demonstration."}}
        print(f"Returning fallback KA response due to error")
        return fallback


async def run_im_agent(
    ensemble_output: Dict[str, Any],
    instructional_methods_json: Dict[str, Any],
    model_choice: str,
    stream_to_console: bool = True
) -> Dict[str, Any]:
    """
    Run the instructional methods agent using OpenAI SDK.

    Contextualizes template explanations of instructional methods to fit
    the specific course context.

    Args:
        ensemble_output: Dictionary containing course data
        instructional_methods_json: Template explanations for IMs
        model_choice: Model selection string
        stream_to_console: Whether to stream output to console

    Returns:
        Dict containing Instructional_Methods with method names as keys
    """
    client, config = create_openai_client(model_choice)

    system_message = f"""
    You are responsible for contextualising the explanations of the chosen instructional methods to fit the context of the course.
    You will take the template explanations and provide a customised explanation for each instructional method.
    Your response must be structured in the given JSON format under "Instructional_Methods".
    Focus on explaining why each of the IM is appropriate and not just on what will be done using the particular IM.
    Do not mention any A and K factors directly.
    Do not mention any topics directly.
    Do not mention the course name directly.

    Your response should be structured in the given JSON format under "Instructional_Methods".
    The following JSON output details the course, and the full list of chosen instructional methods can be found under the Instructional Methods key: {ensemble_output}
    Full list of template answers for the chosen instructional methods: {instructional_methods_json}

    Do not miss out on any of the chosen instructional methods.
    The key names must be the exact name of the instructional method, and the value must be the explanation.

    For example:
    {{
        "Instructional_Methods": {{
            "Lecture": "",
            "Didactic Questioning": ""
        }}
    }}
    """

    user_task = """
    1. Based on the provided data, generate your justifications, ensure that the instructional methods are addressed.
    2. Ensure your responses are structured in JSON format.
    3. Return a full JSON object with all your answers according to the schema.
    """

    if stream_to_console:
        print("\n" + "=" * 80)
        print("INSTRUCTIONAL METHODS AGENT - Contextualizing IMs")
        print("=" * 80)

    try:
        # Use standard chat.completions.create with JSON mode (OpenRouter compatible)
        completion = client.chat.completions.create(
            model=config["model"],
            temperature=config["temperature"],
            messages=[
                {"role": "system", "content": system_message},
                {"role": "user", "content": user_task}
            ],
            response_format={"type": "json_object"}
        )

        # Extract and parse JSON from response
        content = completion.choices[0].message.content
        print(f"DEBUG IM Agent - Raw response: {content[:500] if content else 'None'}...")

        parsed_json = extract_json_from_response(content)
        print(f"DEBUG IM Agent - Parsed JSON keys: {list(parsed_json.keys()) if parsed_json else 'Empty'}")

        # Handle cases where Instructional_Methods is missing
        if not parsed_json or "Instructional_Methods" not in parsed_json:
            print("WARNING: Instructional_Methods not in response, attempting to extract")
            # Check if keys look like method names directly
            common_methods = ["Lecture", "Demonstration", "Practice", "Discussion", "Case Study", "Role Play"]
            if parsed_json and any(k in common_methods or "Lecture" in k or "Discussion" in k for k in parsed_json.keys()):
                parsed_json = {"Instructional_Methods": parsed_json}
            else:
                # Build default from instructional_methods_json
                im_dict = {}
                if instructional_methods_json:
                    for method in instructional_methods_json:
                        if isinstance(method, dict):
                            name = method.get('name', method.get('method', 'Unknown'))
                            im_dict[name] = f"This method is appropriate for delivering course content effectively."
                        elif isinstance(method, str):
                            im_dict[method] = f"This method is appropriate for delivering course content effectively."
                if not im_dict:
                    im_dict = {"Lecture": "This method is appropriate for delivering theoretical content."}
                parsed_json = {"Instructional_Methods": im_dict}

        # Validate with Pydantic schema
        validated = InstructionalMethodsResponse(**parsed_json)

        if stream_to_console:
            print("\n[Instructional Methods Agent Response]")
            print(json.dumps(validated.model_dump(), indent=2))
            print("=" * 80 + "\n")

        return validated.model_dump()

    except Exception as e:
        print(f"Error in instructional methods agent: {e}", file=sys.stderr)
        # Return a fallback response
        fallback = {"Instructional_Methods": {"Lecture": "This method is appropriate for delivering theoretical content."}}
        print(f"Returning fallback IM response due to error")
        return fallback
