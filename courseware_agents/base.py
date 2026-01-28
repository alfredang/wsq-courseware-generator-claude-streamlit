"""
Agent Base Module

This module provides the agent factory function and OpenRouter configuration
for creating agents with dynamic model selection from the SQLite database.
Includes MCP (Model Context Protocol) server support for standardized tool integration.

Author: Courseware Generator Team
Date: 26 January 2026
"""

import os
from typing import List, Any, Optional, Callable, Dict

# Conditional import for openai-agents package
# This allows the app to run on Streamlit Cloud even if the package isn't fully available
AGENTS_AVAILABLE = False
Agent = None
set_default_openai_api = None

try:
    from agents import Agent, set_default_openai_api
    AGENTS_AVAILABLE = True
except ImportError as e:
    print(f"Warning: openai-agents package not available: {e}")
    print("Agent features will be disabled. The app will run in limited mode.")

    # Create a stub Agent class for compatibility
    class Agent:
        """Stub Agent class when openai-agents is not available."""
        def __init__(self, **kwargs):
            self.name = kwargs.get("name", "StubAgent")
            self.instructions = kwargs.get("instructions", "")
            self.tools = kwargs.get("tools", [])
            self.handoffs = kwargs.get("handoffs", [])
            self.model = kwargs.get("model", "")
            print(f"Warning: Agent '{self.name}' created as stub - openai-agents not available")

    def set_default_openai_api(api_type: str):
        """Stub function when openai-agents is not available."""
        pass


# Provider base URLs mapping
PROVIDER_BASE_URLS = {
    "OPENROUTER": "https://openrouter.ai/api/v1",
    "OPENAI": "https://api.openai.com/v1",
    "ANTHROPIC": "https://api.anthropic.com/v1",
    "GEMINI": "https://generativelanguage.googleapis.com/v1beta",
    "GROQ": "https://api.groq.com/openai/v1",
    "GROK": "https://api.x.ai/v1",
    "DEEPSEEK": "https://api.deepseek.com/v1",
}


def setup_api_provider(api_provider: str = "OPENROUTER") -> bool:
    """
    Configure the agents library to use the specified API provider.

    Args:
        api_provider: The API provider to use (OPENROUTER, OPENAI, ANTHROPIC, etc.)

    Returns:
        True if configuration successful, False otherwise
    """
    try:
        from settings.api_manager import load_api_keys
        from openai import AsyncOpenAI
        from agents import set_default_openai_client

        api_keys = load_api_keys()
        api_key_name = f"{api_provider}_API_KEY"
        api_key = api_keys.get(api_key_name, "")

        if not api_key:
            print(f"Warning: {api_key_name} not found in secrets")
            return False

        # Get base URL for the provider
        base_url = PROVIDER_BASE_URLS.get(api_provider, "https://openrouter.ai/api/v1")

        # Create AsyncOpenAI client configured for the provider
        client = AsyncOpenAI(
            api_key=api_key,
            base_url=base_url
        )

        # Set the custom client for the agents library
        set_default_openai_client(client, use_for_tracing=False)

        # Use chat completions API
        set_default_openai_api("chat_completions")

        # Also set environment variables as fallback
        os.environ["OPENAI_API_KEY"] = api_key
        os.environ["OPENAI_BASE_URL"] = base_url

        return True
    except Exception as e:
        print(f"Error setting up {api_provider}: {e}")
        return False


def setup_openrouter() -> bool:
    """
    Configure the agents library to use OpenRouter as the API endpoint.
    This is a convenience wrapper around setup_api_provider for backward compatibility.

    Returns:
        True if configuration successful, False otherwise
    """
    return setup_api_provider("OPENROUTER")


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
    mcp_servers: Optional[List[Any]] = None,
    api_provider: str = "OPENROUTER",
) -> Agent:
    """
    Factory function to create agents with dynamic API provider configuration.

    Args:
        name: Name of the agent
        instructions: System instructions for the agent
        tools: List of tools the agent can use
        handoffs: List of agents this agent can hand off to
        model_name: Display name of the model from the database
        output_type: Optional Pydantic model for structured output
        handoff_description: Description shown when this agent is a handoff target
        mcp_servers: Optional list of MCP servers the agent can use
        api_provider: API provider to use (OPENROUTER, OPENAI, ANTHROPIC, etc.)

    Returns:
        Configured Agent instance
    """
    # Configure the API provider
    setup_api_provider(api_provider)

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

    if mcp_servers:
        agent_kwargs["mcp_servers"] = mcp_servers

    return Agent(**agent_kwargs)


async def create_agent_with_mcp(
    name: str,
    instructions: str,
    tools: Optional[List[Any]] = None,
    handoffs: Optional[List[Agent]] = None,
    model_name: str = "GPT-4o-Mini",
    output_type: Optional[type] = None,
    handoff_description: Optional[str] = None,
    mcp_config: Optional[Dict[str, bool]] = None,
) -> Agent:
    """
    Factory function to create agents with MCP server support.

    This async function initializes MCP servers based on the config and
    creates an agent with those servers attached.

    Args:
        name: Name of the agent
        instructions: System instructions for the agent
        tools: List of tools the agent can use
        handoffs: List of agents this agent can hand off to
        model_name: Display name of the model from the database
        output_type: Optional Pydantic model for structured output
        handoff_description: Description shown when this agent is a handoff target
        mcp_config: MCP server configuration dict with keys:
            - enable_filesystem: Enable filesystem MCP server
            - enable_postgres: Enable PostgreSQL MCP server
            - enable_sqlite: Enable SQLite MCP server
            - enable_fetch: Enable web fetch MCP server
            - enable_memory: Enable memory MCP server

    Returns:
        Configured Agent instance with MCP servers

    Example:
        async with mcp_context(**COURSEWARE_MCP_CONFIG) as mcp_servers:
            agent = create_agent(
                name="My Agent",
                instructions="...",
                mcp_servers=mcp_servers
            )
    """
    from courseware_agents.mcp_config import mcp_context, COURSEWARE_MCP_CONFIG

    # Use default config if not provided
    if mcp_config is None:
        mcp_config = COURSEWARE_MCP_CONFIG

    # Note: MCP servers require async context management
    # This function is for reference - use mcp_context directly
    return create_agent(
        name=name,
        instructions=instructions,
        tools=tools,
        handoffs=handoffs,
        model_name=model_name,
        output_type=output_type,
        handoff_description=handoff_description,
    )


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


# Re-export MCP utilities for convenience
def get_mcp_context():
    """
    Get the MCP context manager for initializing MCP servers.

    Usage:
        from courseware_agents.base import get_mcp_context

        async with get_mcp_context()(enable_postgres=True) as servers:
            agent = create_agent(name="Agent", instructions="...", mcp_servers=servers)
            result = await Runner.run(agent, "Query")

    Returns:
        mcp_context async context manager function
    """
    from courseware_agents.mcp_config import mcp_context
    return mcp_context


def get_mcp_configs() -> Dict[str, Dict[str, bool]]:
    """
    Get predefined MCP server configurations.

    Returns:
        Dictionary with configuration presets:
        - COURSEWARE_MCP_CONFIG: General courseware generation
        - DOCUMENT_AGENT_MCP_CONFIG: Document verification
        - BROCHURE_AGENT_MCP_CONFIG: Brochure generation
    """
    from courseware_agents.mcp_config import (
        COURSEWARE_MCP_CONFIG,
        DOCUMENT_AGENT_MCP_CONFIG,
        BROCHURE_AGENT_MCP_CONFIG,
    )
    return {
        "courseware": COURSEWARE_MCP_CONFIG,
        "document": DOCUMENT_AGENT_MCP_CONFIG,
        "brochure": BROCHURE_AGENT_MCP_CONFIG,
    }
