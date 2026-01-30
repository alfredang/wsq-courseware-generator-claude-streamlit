"""
Topic Analysis Agent for Slides Generation.

Replaces regex-based _extract_research_queries() with LLM-based
intelligent topic extraction. Analyzes document content to identify
research-worthy topics with relevance scoring.

Uses JSON mode for structured output via OpenRouter-compatible models.
"""

import json
import logging
from typing import Dict, Any

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

    # Last resort: try parsing the whole string
    try:
        return json.loads(content)
    except json.JSONDecodeError:
        logger.warning("Failed to parse JSON from topic analysis response")
        return {}


async def run_topic_analysis(
    content: str,
    filename: str,
    material_type: str,
    num_queries: int,
    model_choice: str,
) -> Dict[str, Any]:
    """
    Analyze document content and extract research-worthy topics using LLM.

    Args:
        content: Extracted text from document
        filename: Original filename
        material_type: Type (FG, LG, CP, Other)
        num_queries: Maximum number of topics to return
        model_choice: Model selection string for create_openai_client

    Returns:
        Dict with keys: document_domain, document_type_detected,
        topics (list with name, research_query, relevance_score, rationale),
        total_topics_found
    """
    client, config = create_openai_client(model_choice)

    system_message = load_prompt(
        "slides/topic_analysis",
        material_type=material_type,
        filename=filename,
    )

    # Truncate content to fit in context window of smaller models
    truncated_content = content[:15000]

    user_task = (
        f"Analyze the following document content and identify the top {num_queries} "
        f"most research-worthy topics.\n\n"
        f"---\n{truncated_content}\n---\n\n"
        f"Return your analysis as a JSON object."
    )

    logger.info(f"Running topic analysis agent with model={config['model']}, "
                f"content_length={len(truncated_content)}, num_queries={num_queries}")

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

    # Sort by relevance and cap at num_queries
    if "topics" in result:
        result["topics"] = sorted(
            result["topics"],
            key=lambda t: t.get("relevance_score", 0),
            reverse=True,
        )[:num_queries]

    logger.info(f"Topic analysis complete: {len(result.get('topics', []))} topics extracted, "
                f"domain={result.get('document_domain', 'unknown')}")

    return result
