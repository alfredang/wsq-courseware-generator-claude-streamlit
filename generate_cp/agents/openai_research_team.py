"""
OpenAI SDK-based Research Team.

This module replaces the Autogen-based research_team.py with direct OpenAI SDK implementations.
Uses JSON mode for OpenRouter compatibility.

The research team consists of 4 sequential agents:
1. Background Analyst - Analyzes targeted sector background and needs
2. Performance Gap Analyst - Identifies performance gaps and post-training benefits
3. Sequencing Rationale Agent - Justifies curriculum sequencing
4. Editor - Consolidates all findings into structured JSON

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


def research_task(ensemble_output):
    """Generate the research task prompt."""
    return f"""
    1. Based on the extracted data from {ensemble_output}, generate your justifications.
    2. Ensure your responses are structured in JSON format.
    3. Return a full JSON object with all your answers according to the schema.
    """


async def run_background_analyst(
    ensemble_output: Dict[str, Any],
    model_choice: str,
    stream_to_console: bool = True
) -> Dict[str, Any]:
    """
    Run the background analyst agent.

    Analyzes the targeted sector background and needs for training.

    Args:
        ensemble_output: Dictionary containing course data
        model_choice: Model selection string
        stream_to_console: Whether to stream output to console

    Returns:
        Dict containing Background Analysis
    """
    client, config = create_openai_client(model_choice)

    system_message = f"""
    As a training consultant focusing on analyzing performance gaps and training needs based on course learning outcomes,
    your task is to assess the targeted sector(s) background and needs for the training. Your analysis should be structured
    clearly and based on the provided course title and industry.
    Do not use any control characters such as newlines.
    Do not mention the course name in your answer.
    Do not mention the specific industry as well, give a general answer like simply "the industry" or "the sector".

    Answer the following question based on the extracted data from the first agent in {ensemble_output}:
    (i) Targeted sector(s) background and needs for the training: Using the Course Title, and the Industry from {ensemble_output.get('Course Information', [])}.

    This portion must be at least 600 words long with each point consisting of at least 200 words, and structured into three paragraphs:
    1. Challenges and performance gaps in the industry related to the course.
    2. Training needs necessary to address these gaps.
    3. Job roles that would benefit from the training.

    Format your response in the given JSON structure under "Background Information".
    "Background Analysis": {{
            "Challenges and performance gaps in the industry related to the course": "",
            "Training needs necessary to address these gaps": "",
            "Job roles that would benefit from the training": ""
        }}
    """

    user_task = research_task(ensemble_output)

    if stream_to_console:
        print("\n" + "=" * 80)
        print("BACKGROUND ANALYST - Analyzing Sector Background and Needs")
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
            print("\n[Background Analyst Response]")
            print(json.dumps(parsed_json, indent=2))
            print("=" * 80 + "\n")

        return parsed_json

    except Exception as e:
        print(f"Error in background analyst: {e}", file=sys.stderr)
        raise


async def run_performance_gap_analyst(
    ensemble_output: Dict[str, Any],
    model_choice: str,
    stream_to_console: bool = True
) -> Dict[str, Any]:
    """
    Run the performance gap analyst agent.

    Identifies performance gaps and post-training benefits.

    Args:
        ensemble_output: Dictionary containing course data
        model_choice: Model selection string
        stream_to_console: Whether to stream output to console

    Returns:
        Dict containing Performance Gaps, Attributes Gained, Post-Training Benefits
    """
    client, config = create_openai_client(model_choice)

    system_message = f"""
    You are responsible for identifying the performance gaps and post-training benefits to learners that the course will address.
    Based on the extracted data, answer the following question:
    (ii) Performance gaps that the course will address for the given course title and learning outcomes: {ensemble_output.get('Course Information', {}).get('Course Title', [])}, {ensemble_output.get('Learning Outcomes', {}).get('Learning Outcomes', [])}.
    Do not use any control characters such as newlines.

    Your task is to perform the following:
    1. For each Learning Outcome (LO), provide one unique performance gap, one corresponding attribute gained, and one post-training benefit to learners. Do not repeat performance gaps or attributes across different LOs.
    2. However, in the event that there are only 2 Learning Outcomes, you are to provide 3 unique performance gaps and corresponding attributes gained.
    3. However, in the event that there are more than 5 Learning Outcomes, your answers are to be limited to 5 unique performance gaps and corresponding attributes gained.

    Format your response in the given JSON structure under "Performance Gaps".
    Your answer for (ii.) is to be given in a point format with three distinct sections, appended together as one list element with new line separators, this is an example with only 3 Learning Outcomes, hence 3 points each:
    {{

    Performance gaps:
    Learners are unclear with [specific skill or knowledge gap].
    (perform this analysis for the LOs)

    Attributes gained:
    Ability/Proficiency to [specific skill or knowledge learned].
    (perform this analysis for the LOs)

    Post training benefits:
    (perform this analysis for the LOs)

    }}

    An example output is as follows, you must follow the key names and structure:
    {{
    "Performance Gaps": [
      "Learners are unclear with establishing high-level structures and frameworks for Kubernetes solutions.",
      "Learners struggle to align technical, functional, and service requirements within Kubernetes-based solution architectures.",
      "Learners lack the ability to coordinate multiple Kubernetes solution components effectively.",
      "Learners find it challenging to articulate the value of Kubernetes solutions, particularly regarding coding standards and scalability.",
      "Learners do not have robust processes for monitoring and testing Kubernetes architectures against business requirements."
    ],
    "Attributes Gained": [
      "Ability to establish high-level structures and frameworks to guide the development of Kubernetes solutions.",
      "Proficiency in aligning various stakeholder requirements within a Kubernetes architecture.",
      "Skill in coordinating multiple solution components to ensure compatibility and meet design goals.",
      "Capability to articulate the value added by Kubernetes solutions to business needs.",
      "Competence in establishing processes to monitor and validate Kubernetes architectures."
    ],
    "Post-Training Benefits to Learners": [
      "Enhanced ability to design and implement effective Kubernetes solutions that meet organizational needs.",
      "Improved communication and collaboration among teams due to aligned requirements.",
      "Increased efficiency in managing Kubernetes components, leading to better application performance.",
      "Greater understanding of the importance of coding standards and scalability in Kubernetes implementations.",
      "Reduced risk of application performance issues through established monitoring and testing processes."
    ]
  }}

    """

    user_task = research_task(ensemble_output)

    if stream_to_console:
        print("\n" + "=" * 80)
        print("PERFORMANCE GAP ANALYST - Identifying Performance Gaps")
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
            print("\n[Performance Gap Analyst Response]")
            print(json.dumps(parsed_json, indent=2))
            print("=" * 80 + "\n")

        return parsed_json

    except Exception as e:
        print(f"Error in performance gap analyst: {e}", file=sys.stderr)
        raise


async def run_sequencing_rationale_agent(
    ensemble_output: Dict[str, Any],
    model_choice: str,
    stream_to_console: bool = True
) -> Dict[str, Any]:
    """
    Run the sequencing rationale agent.

    Justifies the rationale of curriculum sequencing.

    Args:
        ensemble_output: Dictionary containing course data
        model_choice: Model selection string
        stream_to_console: Whether to stream output to console

    Returns:
        Dict containing Sequencing Analysis
    """
    client, config = create_openai_client(model_choice)

    system_message = f"""
    You are an experienced course developer. Your task is to justify the rationale of sequencing
    using a step-by-step curriculum framework for the course titled: {ensemble_output.get('Course Information', {}).get('Course Title', [])}.
    Have one pointer within Performance Gaps and Attributes Gained for each Learning Outcome
    Do not use any control characters such as newlines.
    Do not mention any course names in your analysis.
    Ensure that all Learning Units are accounted for in your analysis.

    Reference the following JSON variables in your response:
    1. Learning outcomes: {ensemble_output.get('Learning Outcomes', {}).get('Learning Outcomes', [])}
    2. Learning units: {ensemble_output.get('TSC and Topics', {}).get('Learning Units', [])}
    3. Course outline: {ensemble_output.get('Assessment Methods', {}).get('Course Outline', [])}

    Output your response for (iii.) in the following format, for example:
    {{
        Sequencing Explanation: For this course, the step-by-step sequencing is employed to scaffold the learners' comprehension and application of video marketing strategies using AI tools. The methodology is crucial as it system-atically breaks down the intricate facets of video marketing, inbound marketing strategies, and AI tools into digestible units. This aids in gradually building the learners' knowledge and skills from fundamental to more complex concepts, ensuring a solid foundation before advancing to the next topic. The progression is designed to foster a deeper understanding and the ability to effectively apply the learned concepts in real-world marketing scenarios.

        LU1:
            Title: Translating Strategy into Action and Fostering a Customer-Centric Culture
            Description: LU1 lays the foundational knowledge by introducing learners to the organization's inbound marketing strategies and how they align with the overall marketing strategy. The facilitator will guide learners through translating these strategies into actionable plans and understanding the customer decision journey. This unit sets the stage for fostering a customer-centric culture with a particular focus on adhering to organizational policies and guidelines. The integration of AI tools in these processes is introduced, giving learners a glimpse into the technological aspects they will delve deeper into in subsequent units.

        LU2:
            Title: Improving Inbound Marketing Strategies and Content Management
            Description: Building on the foundational knowledge, LU2 dives into the practical aspects of content creation and curation and how AI tools can be utilized for strategy improvement. Learners will be led through exercises to recommend improvements and manage content across various platforms. The hands-on activities in this unit are designed to enhance learners' ability to manage and optimize video content, crucial skills in video marketing with AI tools.

        LU3:
            Title: Leading Customer Decision Processes and Monitoring Inbound Marketing Effectiveness
            Description: LU3 escalates to a higher level of complexity where learners delve into lead conversion processes, leading customers through decision processes, and evaluating marketing strategy effectiveness. Under the guidance of the facilitator, learners will engage in monitoring and reviewing inbound marketing strategies, thereby aligning theoretical knowledge with practical skills in a real-world context. The synthesis of previous knowledge with advanced concepts in this unit culminates in a comprehensive understanding of video marketing with AI tools, equipping learners with the requisite skills to excel in the modern marketing landscape.

        Conclusion: "Overall, the structured sequencing of these learning units is designed to address the performance gaps identified in the retail industry while equipping learners with the necessary attributes to excel in their roles as machine learning professionals."

    }}

    """

    user_task = research_task(ensemble_output)

    if stream_to_console:
        print("\n" + "=" * 80)
        print("SEQUENCING RATIONALE AGENT - Justifying Curriculum Sequencing")
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
            print("\n[Sequencing Rationale Agent Response]")
            print(json.dumps(parsed_json, indent=2))
            print("=" * 80 + "\n")

        return parsed_json

    except Exception as e:
        print(f"Error in sequencing rationale agent: {e}", file=sys.stderr)
        raise


async def run_editor_agent(
    background_data: Dict[str, Any],
    performance_data: Dict[str, Any],
    sequencing_data: Dict[str, Any],
    model_choice: str,
    stream_to_console: bool = True
) -> Dict[str, Any]:
    """
    Run the editor agent to consolidate all research findings.

    Args:
        background_data: Output from background analyst
        performance_data: Output from performance gap analyst
        sequencing_data: Output from sequencing rationale agent
        model_choice: Model selection string
        stream_to_console: Whether to stream output to console

    Returns:
        Dict containing consolidated research output
    """
    client, config = create_openai_client(model_choice)

    system_message = f"""
    You are to consolidate the findings without amending any of the output, mapping each agent's output to these terms accordingly.

    Only 3 keys are present, Background Analysis, Performance Analysis, Sequencing Analysis. Do not aggregate any of the Validator's output, only the researching agents. Do not aggregate validator comments, those are not essential.
    Your response will only be the consolidated mapped json findings, do not include any additional comments, completion notices such as "Here is the JSON mapping based on the provided context:" is not needed.

    The json mapping guideline list is as follows:
    {{
        "Background Analysis": {{

        }},
        "Performance Analysis": {{
            "Performance Gaps": [

            ],
            "Attributes Gained": [

            ],
            "Post-Training Benefits to Learners": [

            ]
        }},
        "Sequencing Analysis": {{

        "Sequencing Explanation": "",

        "LU1": {{
            "Title": "",
            "Description": ""
        }},

        "LU2": {{
            "Title": "",
            "Description": ""
        }},

        "LU3": {{
            "Title": "",
            "Description": ""
        }},

        "LU4": {{
            "Title": "",
            "Description": ""
        }},

        "Conclusion": "",

        }}
    }}
    """

    user_task = f"""
    Consolidate the following research findings into the required JSON format:

    Background Analysis Data:
    {json.dumps(background_data, indent=2)}

    Performance Analysis Data:
    {json.dumps(performance_data, indent=2)}

    Sequencing Analysis Data:
    {json.dumps(sequencing_data, indent=2)}

    Return only the consolidated JSON output.
    """

    if stream_to_console:
        print("\n" + "=" * 80)
        print("EDITOR AGENT - Consolidating Research Findings")
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
            print("\n[Editor Agent Response]")
            print(json.dumps(parsed_json, indent=2))
            print("=" * 80 + "\n")

        return parsed_json

    except Exception as e:
        print(f"Error in editor agent: {e}", file=sys.stderr)
        raise


async def run_research_team(
    ensemble_output: Dict[str, Any],
    model_choice: str,
    stream_to_console: bool = True
) -> Dict[str, Any]:
    """
    Run the full research team pipeline.

    This replaces the Autogen RoundRobinGroupChat with sequential OpenAI API calls.
    Executes: Background Analyst -> Performance Gap Analyst -> Sequencing Rationale -> Editor

    Args:
        ensemble_output: Dictionary containing course data
        model_choice: Model selection string
        stream_to_console: Whether to stream output to console

    Returns:
        Dict containing consolidated research output
    """
    if stream_to_console:
        print("\n" + "=" * 80)
        print("RESEARCH TEAM - Starting Research Pipeline")
        print("=" * 80)

    # Run agents sequentially (mimics RoundRobinGroupChat with max_turns=4)
    background_data = await run_background_analyst(
        ensemble_output=ensemble_output,
        model_choice=model_choice,
        stream_to_console=stream_to_console
    )

    performance_data = await run_performance_gap_analyst(
        ensemble_output=ensemble_output,
        model_choice=model_choice,
        stream_to_console=stream_to_console
    )

    sequencing_data = await run_sequencing_rationale_agent(
        ensemble_output=ensemble_output,
        model_choice=model_choice,
        stream_to_console=stream_to_console
    )

    # Editor consolidates all findings
    consolidated_output = await run_editor_agent(
        background_data=background_data,
        performance_data=performance_data,
        sequencing_data=sequencing_data,
        model_choice=model_choice,
        stream_to_console=stream_to_console
    )

    if stream_to_console:
        print("\n" + "=" * 80)
        print("RESEARCH TEAM - Pipeline Complete")
        print("=" * 80)

    return consolidated_output
