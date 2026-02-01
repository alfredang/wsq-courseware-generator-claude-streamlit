"""
Agent Base Module - Claude Agent SDK

This module provides utilities for the Claude Agent SDK integration,
including MCP server configuration and subagent definitions.

Author: Courseware Generator Team
Date: 26 January 2026
"""

import os
from typing import List, Any, Optional, Dict
from pathlib import Path

# Claude Agent SDK imports
try:
    from claude_agent_sdk import query, ClaudeAgentOptions, AgentDefinition
    CLAUDE_SDK_AVAILABLE = True
except ImportError as e:
    print(f"Warning: claude-agent-sdk package not available: {e}")
    print("Agent features will be disabled. The app will run in limited mode.")
    CLAUDE_SDK_AVAILABLE = False

    # Create stub classes for compatibility
    class ClaudeAgentOptions:
        """Stub ClaudeAgentOptions when claude-agent-sdk is not available."""
        def __init__(self, **kwargs):
            for key, value in kwargs.items():
                setattr(self, key, value)

    class AgentDefinition:
        """Stub AgentDefinition when claude-agent-sdk is not available."""
        def __init__(self, **kwargs):
            self.name = kwargs.get("name", "StubAgent")
            self.description = kwargs.get("description", "")
            self.prompt = kwargs.get("prompt", "")
            self.tools = kwargs.get("tools", [])
            print(f"Warning: Agent '{self.name}' created as stub - claude-agent-sdk not available")

    async def query(*args, **kwargs):
        """Stub query function when claude-agent-sdk is not available."""
        yield {"error": "claude-agent-sdk not available"}


def get_project_root() -> Path:
    """Get the project root directory."""
    return Path(__file__).resolve().parent.parent


def get_mcp_servers_config(
    enable_courseware_tools: bool = True,
    enable_filesystem: bool = True,
    enable_fetch: bool = True,
    custom_paths: Optional[List[str]] = None,
) -> Dict[str, Dict[str, Any]]:
    """
    Get MCP server configurations for Claude Agent SDK.

    Args:
        enable_courseware_tools: Enable the custom courseware tools MCP server
        enable_filesystem: Enable filesystem MCP server
        enable_fetch: Enable web fetch MCP server
        custom_paths: Custom paths for filesystem access

    Returns:
        Dictionary of MCP server configurations
    """
    project_root = get_project_root()
    servers = {}

    # Custom courseware tools MCP server
    if enable_courseware_tools:
        servers["courseware-tools"] = {
            "command": "python",
            "args": [str(project_root / "courseware_agents" / "run_mcp_server.py")]
        }

    # Filesystem MCP server
    if enable_filesystem:
        paths = custom_paths or [str(project_root)]
        servers["filesystem"] = {
            "command": "npx",
            "args": ["-y", "@modelcontextprotocol/server-filesystem"] + paths
        }

    # Web fetch MCP server
    if enable_fetch:
        servers["fetch"] = {
            "command": "npx",
            "args": ["-y", "@modelcontextprotocol/server-fetch"]
        }

    return servers


def create_subagent(
    name: str,
    description: str,
    prompt: str,
    tools: Optional[List[str]] = None,
) -> AgentDefinition:
    """
    Create a subagent definition for Claude Agent SDK.

    Args:
        name: Name of the subagent
        description: Brief description of the subagent's purpose
        prompt: System prompt/instructions for the subagent
        tools: List of built-in tools the subagent can use

    Returns:
        AgentDefinition instance
    """
    return AgentDefinition(
        name=name,
        description=description,
        prompt=prompt,
        tools=tools or ["Read", "Glob", "Grep"]
    )


def get_claude_model(model_name: str = "claude-sonnet-4") -> str:
    """
    Get the Claude model ID.

    Args:
        model_name: Display name or short name of the model

    Returns:
        Full model ID for Claude API
    """
    model_mapping = {
        "claude-sonnet-4": "claude-sonnet-4-20250514",
        "claude-opus-4.5": "claude-opus-4-5-20251101",
        "claude-haiku-3.5": "claude-3-5-haiku-20241022",
        "sonnet": "claude-sonnet-4-20250514",
        "opus": "claude-opus-4-5-20251101",
        "haiku": "claude-3-5-haiku-20241022",
    }

    return model_mapping.get(model_name.lower(), model_name)


def setup_anthropic_api() -> bool:
    """
    Ensure Anthropic API key is configured.

    Returns:
        True if API key is available, False otherwise
    """
    # Check environment variable first
    if os.environ.get("ANTHROPIC_API_KEY"):
        return True

    # Try to load from settings
    try:
        from settings.api_manager import load_api_keys
        api_keys = load_api_keys()
        api_key = api_keys.get("ANTHROPIC_API_KEY", "")

        if api_key:
            os.environ["ANTHROPIC_API_KEY"] = api_key
            return True
    except Exception as e:
        print(f"Warning: Could not load Anthropic API key: {e}")

    return False


def get_default_options(
    allowed_tools: Optional[List[str]] = None,
    agents: Optional[Dict[str, AgentDefinition]] = None,
    mcp_servers: Optional[Dict[str, Dict[str, Any]]] = None,
    permission_mode: str = "default",
) -> ClaudeAgentOptions:
    """
    Get default ClaudeAgentOptions with common settings.

    Args:
        allowed_tools: List of allowed built-in tools
        agents: Dictionary of subagent definitions
        mcp_servers: MCP server configurations
        permission_mode: Permission mode for tool execution

    Returns:
        Configured ClaudeAgentOptions instance
    """
    if allowed_tools is None:
        allowed_tools = ["Read", "Write", "Edit", "Bash", "Glob", "Grep", "Task"]

    if mcp_servers is None:
        mcp_servers = get_mcp_servers_config()

    return ClaudeAgentOptions(
        allowed_tools=allowed_tools,
        agents=agents or {},
        mcp_servers=mcp_servers,
        permission_mode=permission_mode,
    )


# Predefined MCP configurations for different use cases
COURSEWARE_MCP_CONFIG = {
    "enable_courseware_tools": True,
    "enable_filesystem": True,
    "enable_fetch": True,
}

DOCUMENT_AGENT_MCP_CONFIG = {
    "enable_courseware_tools": True,
    "enable_filesystem": True,
    "enable_fetch": False,
}

BROCHURE_AGENT_MCP_CONFIG = {
    "enable_courseware_tools": True,
    "enable_filesystem": True,
    "enable_fetch": True,
}

SLIDES_AGENT_MCP_CONFIG = {
    "enable_courseware_tools": True,
    "enable_filesystem": False,
    "enable_fetch": False,
}


def get_mcp_configs() -> Dict[str, Dict[str, bool]]:
    """
    Get predefined MCP server configurations.

    Returns:
        Dictionary with configuration presets
    """
    return {
        "courseware": COURSEWARE_MCP_CONFIG,
        "document": DOCUMENT_AGENT_MCP_CONFIG,
        "brochure": BROCHURE_AGENT_MCP_CONFIG,
        "slides": SLIDES_AGENT_MCP_CONFIG,
    }
