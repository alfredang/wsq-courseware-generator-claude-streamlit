"""
Base Agent Runner

Wraps the Claude Agent SDK's query() function with common patterns
used across all courseware agents.
"""

import asyncio
import json
import os
from typing import Optional
from claude_agent_sdk import query, ClaudeAgentOptions, AssistantMessage, ResultMessage


async def run_agent(
    prompt: str,
    system_prompt: Optional[str] = None,
    tools: Optional[list] = None,
    working_dir: Optional[str] = None,
    max_turns: int = 30,
    model: Optional[str] = None,
) -> str:
    """
    Run a Claude agent with the given prompt and return the result text.

    Args:
        prompt: The task instruction for the agent.
        system_prompt: Optional system prompt to guide agent behavior.
        tools: List of tools the agent can use. Defaults to read-only tools.
        working_dir: Working directory for the agent. Defaults to project root.
        max_turns: Maximum number of agent turns.
        model: Optional model ID (e.g. 'claude-sonnet-4-20250514').

    Returns:
        The agent's final text output.
    """
    if tools is None:
        tools = ["Read", "Glob", "Grep"]

    if working_dir is None:
        working_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

    options = ClaudeAgentOptions(
        allowed_tools=tools,
        permission_mode="bypassPermissions",
        max_turns=max_turns,
    )

    if model:
        options.model = model

    if system_prompt:
        options.system_prompt = system_prompt

    if working_dir:
        options.cwd = working_dir

    result_text = ""

    async for message in query(prompt=prompt, options=options):
        if isinstance(message, AssistantMessage):
            for block in message.content:
                if hasattr(block, "text"):
                    result_text = block.text  # Keep last text block
        elif isinstance(message, ResultMessage):
            if hasattr(message, "result") and message.result:
                result_text = message.result

    return result_text


async def run_agent_json(
    prompt: str,
    system_prompt: Optional[str] = None,
    tools: Optional[list] = None,
    working_dir: Optional[str] = None,
    max_turns: int = 30,
    model: Optional[str] = None,
) -> dict:
    """
    Run a Claude agent and parse the result as JSON.

    Args:
        prompt: The task instruction for the agent.
        system_prompt: Optional system prompt with JSON output instructions.
        tools: List of tools the agent can use.
        working_dir: Working directory for the agent.
        max_turns: Maximum number of agent turns.
        model: Optional model ID (e.g. 'claude-sonnet-4-20250514').

    Returns:
        Parsed JSON dict from the agent's output.

    Raises:
        ValueError: If the agent's output cannot be parsed as JSON.
    """
    result = await run_agent(
        prompt=prompt,
        system_prompt=system_prompt,
        tools=tools,
        working_dir=working_dir,
        max_turns=max_turns,
        model=model,
    )

    # Try to extract JSON from the result
    json_result = _extract_json(result)
    if json_result is None:
        raise ValueError(f"Agent output is not valid JSON. Output: {result[:500]}")

    return json_result


def _extract_json(text: str) -> Optional[dict]:
    """Extract JSON from text, handling markdown code blocks."""
    if not text:
        return None

    # Try direct parse
    try:
        return json.loads(text.strip())
    except json.JSONDecodeError:
        pass

    # Try extracting from markdown code block
    import re
    json_match = re.search(r'```(?:json)?\s*\n(.*?)\n```', text, re.DOTALL)
    if json_match:
        try:
            return json.loads(json_match.group(1).strip())
        except json.JSONDecodeError:
            pass

    # Try finding JSON object in text
    brace_start = text.find('{')
    if brace_start != -1:
        depth = 0
        for i in range(brace_start, len(text)):
            if text[i] == '{':
                depth += 1
            elif text[i] == '}':
                depth -= 1
                if depth == 0:
                    try:
                        return json.loads(text[brace_start:i + 1])
                    except json.JSONDecodeError:
                        break

    return None
