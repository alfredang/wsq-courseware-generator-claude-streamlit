"""
MCP (Model Context Protocol) Configuration - Claude Agent SDK

This module provides MCP server configurations for the Claude Agent SDK.
MCP enables standardized tool integration for custom tools, database access,
file operations, and external service connections.

Author: Courseware Generator Team
Date: 26 January 2026
"""

import os
from pathlib import Path
from typing import Optional, List, Dict, Any


def get_project_root() -> Path:
    """Get the project root directory."""
    return Path(__file__).resolve().parent.parent


def get_mcp_server_config(
    server_type: str,
    **kwargs
) -> Dict[str, Any]:
    """
    Get MCP server configuration for Claude Agent SDK.

    Args:
        server_type: Type of MCP server (courseware-tools, filesystem, fetch, etc.)
        **kwargs: Additional configuration options

    Returns:
        Dictionary with command and args for the MCP server
    """
    project_root = get_project_root()

    configs = {
        "courseware-tools": {
            "command": "python",
            "args": [str(project_root / "courseware_agents" / "run_mcp_server.py")]
        },
        "filesystem": {
            "command": "npx",
            "args": ["-y", "@modelcontextprotocol/server-filesystem"] + kwargs.get("paths", [str(project_root)])
        },
        "fetch": {
            "command": "npx",
            "args": ["-y", "@modelcontextprotocol/server-fetch"]
        },
        "postgres": {
            "command": "npx",
            "args": ["-y", "@modelcontextprotocol/server-postgres", kwargs.get("database_url", os.environ.get("DATABASE_URL", ""))]
        },
        "sqlite": {
            "command": "npx",
            "args": ["-y", "@modelcontextprotocol/server-sqlite", kwargs.get("db_path", str(project_root / "settings" / "config" / "api_config.db"))]
        },
        "memory": {
            "command": "npx",
            "args": ["-y", "@modelcontextprotocol/server-memory"]
        },
        "notebooklm": {
            "command": "uv",
            "args": ["run", "python", "server.py"],
            "cwd": kwargs.get("server_path", str(project_root / "notebooklm-mcp"))
        },
    }

    return configs.get(server_type, {})


def get_mcp_servers(
    enable_courseware_tools: bool = True,
    enable_filesystem: bool = True,
    enable_fetch: bool = True,
    enable_postgres: bool = False,
    enable_sqlite: bool = False,
    enable_memory: bool = False,
    enable_notebooklm: bool = False,
    custom_paths: Optional[List[str]] = None,
    database_url: Optional[str] = None,
    notebooklm_path: Optional[str] = None,
) -> Dict[str, Dict[str, Any]]:
    """
    Get MCP server configurations for Claude Agent SDK.

    This function returns a dictionary of MCP server configurations
    that can be passed directly to ClaudeAgentOptions.mcp_servers.

    Args:
        enable_courseware_tools: Enable custom courseware tools MCP server
        enable_filesystem: Enable filesystem MCP server
        enable_fetch: Enable web fetch MCP server
        enable_postgres: Enable PostgreSQL MCP server
        enable_sqlite: Enable SQLite MCP server
        enable_memory: Enable memory MCP server
        enable_notebooklm: Enable NotebookLM MCP server
        custom_paths: Custom paths for filesystem server
        database_url: PostgreSQL connection string
        notebooklm_path: Path to notebooklm-mcp server directory

    Returns:
        Dictionary of MCP server configurations

    Example:
        from claude_agent_sdk import query, ClaudeAgentOptions

        servers = get_mcp_servers(
            enable_courseware_tools=True,
            enable_filesystem=True,
        )

        options = ClaudeAgentOptions(
            mcp_servers=servers,
            allowed_tools=["Read", "Write", "Task"]
        )

        async for msg in query("Generate courseware", options):
            print(msg)
    """
    servers = {}

    if enable_courseware_tools:
        servers["courseware-tools"] = get_mcp_server_config("courseware-tools")

    if enable_filesystem:
        paths = custom_paths or [str(get_project_root())]
        servers["filesystem"] = get_mcp_server_config("filesystem", paths=paths)

    if enable_fetch:
        servers["fetch"] = get_mcp_server_config("fetch")

    if enable_postgres:
        db_url = database_url or os.environ.get("DATABASE_URL", "")
        if db_url:
            servers["postgres"] = get_mcp_server_config("postgres", database_url=db_url)

    if enable_sqlite:
        servers["sqlite"] = get_mcp_server_config("sqlite")

    if enable_memory:
        servers["memory"] = get_mcp_server_config("memory")

    if enable_notebooklm:
        server_path = notebooklm_path
        if not server_path:
            # Try common locations
            possible_paths = [
                get_project_root() / "notebooklm-mcp",
                get_project_root().parent / "notebooklm-mcp",
                Path.home() / "notebooklm-mcp",
            ]
            for p in possible_paths:
                if (p / "server.py").exists():
                    server_path = str(p)
                    break

        if server_path:
            servers["notebooklm"] = get_mcp_server_config("notebooklm", server_path=server_path)

    return servers


# Predefined server configurations for common use cases
COURSEWARE_MCP_CONFIG = {
    "enable_courseware_tools": True,
    "enable_filesystem": True,
    "enable_fetch": True,
    "enable_postgres": False,
    "enable_sqlite": False,
    "enable_memory": False,
    "enable_notebooklm": False,
}

DOCUMENT_AGENT_MCP_CONFIG = {
    "enable_courseware_tools": True,
    "enable_filesystem": True,
    "enable_fetch": False,
    "enable_postgres": True,
    "enable_sqlite": False,
    "enable_memory": False,
    "enable_notebooklm": False,
}

BROCHURE_AGENT_MCP_CONFIG = {
    "enable_courseware_tools": True,
    "enable_filesystem": True,
    "enable_fetch": True,
    "enable_postgres": False,
    "enable_sqlite": False,
    "enable_memory": False,
    "enable_notebooklm": False,
}

SLIDES_AGENT_MCP_CONFIG = {
    "enable_courseware_tools": True,
    "enable_filesystem": False,
    "enable_fetch": False,
    "enable_postgres": False,
    "enable_sqlite": False,
    "enable_memory": False,
    "enable_notebooklm": True,
}


__all__ = [
    "get_project_root",
    "get_mcp_server_config",
    "get_mcp_servers",
    "COURSEWARE_MCP_CONFIG",
    "DOCUMENT_AGENT_MCP_CONFIG",
    "BROCHURE_AGENT_MCP_CONFIG",
    "SLIDES_AGENT_MCP_CONFIG",
]
