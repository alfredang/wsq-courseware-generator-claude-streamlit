"""
OpenAI SDK-based TSC Agent.

This module replaces the Autogen-based tsc_agent.py with direct OpenAI SDK implementations.
Uses JSON mode for OpenRouter compatibility.

The TSC agent parses and corrects TSC data.

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


def tsc_agent_task(tsc_data):
    """Generate the TSC agent task prompt."""
    return f"""
    1. Parse data from the following JSON file: {tsc_data}
    2. Fix spelling errors, and missing LUs if any.
    3. Ensure that the LUs do not have the same name as the Topics.
    4. Return a full JSON object with all the extracted data according to the schema.
    """


async def run_tsc_agent(
    tsc_data: Dict[str, Any],
    model_choice: str,
    stream_to_console: bool = True
) -> Dict[str, Any]:
    """
    Run the TSC parser agent.

    Parses and corrects TSC data, fixing spelling errors and ensuring proper structure.

    Args:
        tsc_data: Raw TSC document data
        model_choice: Model selection string
        stream_to_console: Whether to stream output to console

    Returns:
        Dict containing parsed and corrected TSC data
    """
    client, config = create_openai_client(model_choice)

    system_message = f"""
        You are to parse and correct spelling mistakes from {tsc_data}:
        The requirements are as follows:
        1. If there are no LU's present, summarize a LU from each Topics and name them sequentially. The LUs should NOT have the same name as the topics. Ignore this instruction if there are LUs present.
        1.1. If there are LU's present, ensure that they are correctly mapped to the Topics. Do NOT include additional LUs if they are already present in the data.
        2. Ensure that any mention of "Topic" is followed by a number and a colon.
        2.5. Ensure that any mention of "LU" is followed by a number and a colon.
        2.6. Ensure that the A and K factors are followed by a number and a colon.
        3. Ensure that the K and A factors are correctly mapped to the LUs in brackets.
        3.1. CRITICAL: If a Topic does NOT have K and A factors in brackets in its header, you MUST add the K and A factors from its parent LU header to the Topic header. Every Topic MUST have K and A factors in brackets.
        4. Catch and amend any spelling errors to the following words:
        Instructional Methods:
        - Didactic Questioning
        - Demonstration
        - Practical
        - Peer Sharing
        - Role Play
        - Group Discussion
        - Case Study
        Assessment Methods:
        - Written Assessment
        - Practical Performance
        - Case Study
        - Oral Questioning
        - Role Play

        For example, "case studies" is WRONG, "Case Study" is CORRECT.

        An example JSON schema looks like this, with the LUs as a key-value pair:
        {{
            "Course_Proposal_Form": {{
                "null": [
                    "Title: Hands-on AI-Assisted Programming Made Simple with GitHub Copilot",
                    "Organization: Tertiary Infotech Academy Pte Ltd",
                    "Learning Outcomes:",
                    "LO1: Identify gaps in existing programming workflows and propose AI-assisted solutions using GitHub Copilot to enhance efficiency.",
                    "LO2: Explore and apply emerging AI programming tools, including GitHub Copilot, to streamline organizational coding processes.",
                    "Couse Duration: 1 days (8 hrs)",
                    "Instructional Methods:",
                    "Classroom: 3 hours",
                    "Practical: 4 hours",
                    "Didactic Questioning",
                    "Demonstration",
                    "Assessment Methods:",
                    "Written Assessment (0.5 hr)",
                    "Practical Performance (0.5 hr)",
                    "TSC Mapping:",
                    "TSC Title: Digital Technology Adoption and Innovation",
                    "TSC Code: ACC-ICT-3004-1.1",
                    "TSC Knowledge:",
                    "K1: Relevant systems and software",
                    "K2: Organisation's processes",
                    "K3: Strengths and weaknesses of existing software and systems",
                    "K4: Emerging technological trends such as block chain, machine learning, artificial intelligence,",
                    "TSC Abilities:",
                    "A1: Identify issues in the existing software and systems",
                    "A2: Seek potential IT solutions to resolve issues or for systems upgrading",
                    "A3: Propose to management on suitable IT solutions for the organisation",
                    "A4: Keep up to date with new technologies and systems",
                    "Learning Units"
                ],
                "LU1: Introduction to Copilot (K1, K3, A1, A3)": [
                    "Topic 1: Getting Started  with Github Copilot (K1, K3, A1, A3)",
                    "What is Github Copilot?",
                    "How Github Copilot enhances software development efficiency?",
                    "Install Github Copilot on Visual Studio Code",
                    "Explore Github Copilot features"
                ],
                "LU2: Coding with Github Copilot (K2, K4, A2, A4)": [
                    "Topic 2: Software Development with Github Copilot (K2, K4, A2, A4)",
                    "Github Copilot for HTML",
                    "Github Copilot for Python",
                    "Github Copilot for Javascript",
                    "Github Copilot for REST API",
                    "Other emerging AI tools for software development"
                ]
            }}
        }}

        Take note that there can be more than 1 topic per LU, if this is the case, it is already indicated in the data as LUs will already be present and defined, so there is no need for you to further formulate more LUs.
        IMPORTANT: When a Topic does not have K and A factors in its header, you MUST inherit the K and A factors from the LU header and add them to the Topic header.
        If that is the case, you are to follow the below structure for the JSON output:
        {{
            "Course_Proposal_Form": {{
                "null": [
                    "Title: Hands-on AI-Assisted Programming Made Simple with GitHub Copilot",
                    "Organization: Tertiary Infotech Academy Pte Ltd",
                    "Learning Outcomes:",
                    "LO1: Identify gaps in existing programming workflows and propose AI-assisted solutions using GitHub Copilot to enhance efficiency.",
                    "LO2: Explore and apply emerging AI programming tools, including GitHub Copilot, to streamline organizational coding processes.",
                    "Couse Duration: 1 days (8 hrs)",
                    "Instructional Methods:",
                    "Classroom: 3 hours",
                    "Practical: 4 hours",
                    "Didactic Questioning",
                    "Demonstration",
                    "Assessment Methods:",
                    "Written Assessment (0.5 hr)",
                    "Practical Performance (0.5 hr)",
                    "TSC Mapping:",
                    "TSC Title: Digital Technology Adoption and Innovation",
                    "TSC Code: ACC-ICT-3004-1.1",
                    "TSC Knowledge:",
                    "K1: Relevant systems and software",
                    "K2: Organisation's processes",
                    "K3: Strengths and weaknesses of existing software and systems",
                    "K4: Emerging technological trends such as block chain, machine learning, artificial intelligence,",
                    "TSC Abilities:",
                    "A1: Identify issues in the existing software and systems",
                    "A2: Seek potential IT solutions to resolve issues or for systems upgrading",
                    "A3: Propose to management on suitable IT solutions for the organisation",
                    "A4: Keep up to date with new technologies and systems",
                    "Learning Units"
                ],
                "LU1: Introduction to Copilot (K1, K3, A1, A3)": [
                    "Topic 1: Getting Started  with Github Copilot (K1, A1)",
                    "What is Github Copilot?",
                    "How Github Copilot enhances software development efficiency?",
                    "Install Github Copilot on Visual Studio Code",
                    "Explore Github Copilot features",
                    "Topic 2: Software Development with Github Copilot (K3, A3)",
                    "Github Copilot for HTML",
                    "Github Copilot for Python",
                    "Github Copilot for Javascript",
                    "Github Copilot for REST API",
                    "Other emerging AI tools for software development"
                ],
            }}
        }}
        """

    user_task = tsc_agent_task(tsc_data)

    if stream_to_console:
        print("\n" + "=" * 80)
        print("TSC AGENT - Parsing and Correcting TSC Data")
        print("=" * 80)

    # Retry logic for rate limits
    max_retries = 3
    retry_delay = 10  # Start with 10 seconds

    for attempt in range(max_retries):
        try:
            completion = client.chat.completions.create(
                model=config["model"],
                temperature=config["temperature"],
                max_tokens=8000,  # Limit tokens to stay within OpenRouter credit limits
                messages=[
                    {"role": "system", "content": system_message},
                    {"role": "user", "content": user_task}
                ],
                response_format={"type": "json_object"}
            )

            content = completion.choices[0].message.content
            parsed_json = extract_json_from_response(content)

            if stream_to_console:
                print("\n[TSC Agent Response]")
                print(json.dumps(parsed_json, indent=2))
                print("=" * 80 + "\n")

            return parsed_json

        except Exception as e:
            error_str = str(e).lower()
            if ("429" in str(e) or "rate" in error_str or "quota" in error_str) and attempt < max_retries - 1:
                wait_time = retry_delay * (attempt + 1)
                print(f"Rate limit hit. Waiting {wait_time} seconds before retry {attempt + 2}/{max_retries}...")
                import time
                time.sleep(wait_time)
                continue
            print(f"Error in TSC agent: {e}", file=sys.stderr)
            raise
