"""
Agent Base Module

This module provides the agent factory function and OpenRouter configuration
for creating agents with dynamic model selection from the SQLite database.

Author: Courseware Generator Team
Date: 26 January 2026
"""

import os
from typing import List, Any, Optional, Callable
from agents import Agent, set_default_openai_api


def setup_openrouter() -> bool:
    """
    Configure the agents library to use OpenRouter as the API endpoint.

    Returns:
        True if configuration successful, False otherwise
    """
    try:
        from settings.api_manager import load_api_keys
        from openai import AsyncOpenAI
        from agents import set_default_openai_client

        api_keys = load_api_keys()
        openrouter_key = api_keys.get("OPENROUTER_API_KEY", "")

        if not openrouter_key:
            print("Warning: OPENROUTER_API_KEY not found in secrets")
            return False

        # Create AsyncOpenAI client configured for OpenRouter
        client = AsyncOpenAI(
            api_key=openrouter_key,
            base_url="https://openrouter.ai/api/v1"
        )

        # Set the custom client for the agents library
        set_default_openai_client(client, use_for_tracing=False)

        # Use chat completions API (required for OpenRouter)
        set_default_openai_api("chat_completions")

        # Also set environment variables as fallback
        os.environ["OPENAI_API_KEY"] = openrouter_key
        os.environ["OPENAI_BASE_URL"] = "https://openrouter.ai/api/v1"

        return True
    except Exception as e:
        print(f"Error setting up OpenRouter: {e}")
        return False


def get_model_for_agent(model_name: str = "GPT-4o-Mini") -> str:
    """
    Get OpenRouter model ID from the SQLite database.

    Args:
        model_name: Display name of the model (e.g., "GPT-4o", "DeepSeek-Chat")

    Returns:
        OpenRouter model ID (e.g., "openai/gpt-4o", "deepseek/deepseek-chat")
    """
    try:
        from settings.api_manager import get_all_available_models

        models = get_all_available_models()
        if model_name in models:
            return models[model_name]["config"]["model"]
    except Exception as e:
        print(f"Warning: Could not load model config for '{model_name}': {e}")

    # Fallback mappings if database lookup fails
    fallback_models = {
        "GPT-4o": "openai/gpt-4o",
        "GPT-4o-Mini": "openai/gpt-4o-mini",
        "GPT-5": "openai/gpt-5",
        "DeepSeek-Chat": "deepseek/deepseek-chat",
        "DeepSeek-R1": "deepseek/deepseek-r1",
        "Claude-Sonnet-4": "anthropic/claude-sonnet-4",
        "Claude-Opus-4.5": "anthropic/claude-opus-4.5",
        "Gemini-2.5-Flash": "google/gemini-2.5-flash",
    }

    return fallback_models.get(model_name, "openai/gpt-4o-mini")


def create_agent(
    name: str,
    instructions: str,
    tools: Optional[List[Any]] = None,
    handoffs: Optional[List[Agent]] = None,
    model_name: str = "GPT-4o-Mini",
    output_type: Optional[type] = None,
    handoff_description: Optional[str] = None,
) -> Agent:
    """
    Factory function to create agents with OpenRouter configuration.

    Args:
        name: Name of the agent
        instructions: System instructions for the agent
        tools: List of tools the agent can use
        handoffs: List of agents this agent can hand off to
        model_name: Display name of the model from the database
        output_type: Optional Pydantic model for structured output
        handoff_description: Description shown when this agent is a handoff target

    Returns:
        Configured Agent instance
    """
    # Ensure OpenRouter is configured
    setup_openrouter()

    # Get the model ID from database
    model_id = get_model_for_agent(model_name)

    # Build agent kwargs
    agent_kwargs = {
        "name": name,
        "instructions": instructions,
        "model": model_id,
    }

    if tools:
        agent_kwargs["tools"] = tools

    if handoffs:
        agent_kwargs["handoffs"] = handoffs

    if output_type:
        agent_kwargs["output_type"] = output_type

    if handoff_description:
        agent_kwargs["handoff_description"] = handoff_description

    return Agent(**agent_kwargs)


def get_available_models() -> List[str]:
    """
    Get list of available model display names.

    Returns:
        List of model names that can be used with create_agent
    """
    try:
        from settings.api_manager import get_all_available_models
        models = get_all_available_models()
        return list(models.keys())
    except Exception:
        return [
            "GPT-4o",
            "GPT-4o-Mini",
            "DeepSeek-Chat",
            "Claude-Sonnet-4",
            "Gemini-2.5-Flash",
        ]
