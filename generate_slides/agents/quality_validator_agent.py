"""
Quality Validation Agent for Slides Generation.

Post-generation quality assessment using NotebookLM chat review data.
Scores the generated slides and recommends whether to accept or retry.

Uses JSON mode for structured output via OpenRouter-compatible models.
"""

import json
import logging
from typing import Dict, Any, List

from generate_cp.utils.openai_model_client import create_openai_client
from utils.prompt_loader import load_prompt

logger = logging.getLogger(__name__)


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

    if "{" in content:
        start = content.find("{")
        depth = 0
        end = start
        for i in range(start, len(content)):
            if content[i] == "{":
                depth += 1
            elif content[i] == "}":
                depth -= 1
                if depth == 0:
                    end = i + 1
                    break
        try:
            return json.loads(content[start:end])
        except json.JSONDecodeError:
            pass

    try:
        return json.loads(content)
    except json.JSONDecodeError:
        logger.warning("Failed to parse JSON from quality validator response")
        return {}


async def run_quality_validator(
    slide_review_data: str,
    expected_topics: List[str],
    expected_structure: List[str],
    material_type: str,
    model_choice: str,
) -> Dict[str, Any]:
    """
    Validate quality of generated slides based on NotebookLM chat review.

    Args:
        slide_review_data: Text response from NotebookLM chat about the slides
        expected_topics: Topic names that should be covered
        expected_structure: Expected structure outline from instructions agent
        material_type: Document type
        model_choice: Model selection string for create_openai_client

    Returns:
        Dict with overall_score, per-criterion scores (1-10),
        recommendation (pass/retry_with_modifications/retry_full),
        retry_suggestions, strengths, weaknesses
    """
    client, config = create_openai_client(model_choice)

    topics_str = json.dumps(expected_topics, indent=2)
    structure_str = json.dumps(expected_structure, indent=2)

    system_message = load_prompt(
        "slides/quality_validation",
        material_type=material_type,
        expected_topics=topics_str,
        expected_structure=structure_str,
        slide_review_data=slide_review_data,
    )

    user_task = (
        "Evaluate the slide deck quality based on the information provided. "
        "Return as JSON."
    )

    logger.info(f"Running quality validator: {len(expected_topics)} expected topics, "
                f"review data length={len(slide_review_data)}")

    completion = client.chat.completions.create(
        model=config["model"],
        temperature=config["temperature"],
        max_tokens=4000,
        messages=[
            {"role": "system", "content": system_message},
            {"role": "user", "content": user_task},
        ],
        response_format={"type": "json_object"},
    )

    result = extract_json_from_response(completion.choices[0].message.content)

    overall = result.get("overall_score", 0)
    recommendation = result.get("recommendation", "pass")
    logger.info(f"Quality validation complete: score={overall}/10, recommendation={recommendation}")

    return result
