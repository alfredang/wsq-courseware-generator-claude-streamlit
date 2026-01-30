"""
MCP (Model Context Protocol) Configuration

This module provides MCP server configurations for the courseware agents.
MCP enables standardized tool integration for database access, file operations,
and external service connections.

Author: Courseware Generator Team
Date: 26 January 2026
"""

import os
from pathlib import Path
from typing import Optional, List, Dict, Any
from contextlib import asynccontextmanager


async def create_filesystem_server(
    allowed_paths: Optional[List[str]] = None,
    name: str = "Filesystem Server"
):
    """
    Create a Filesystem MCP server for document operations.

    Args:
        allowed_paths: List of paths the server can access. Defaults to project root.
        name: Server name for identification.

    Returns:
        MCPServerStdio instance configured for filesystem access.
    """
    from agents.mcp import MCPServerStdio

    if allowed_paths is None:
        # Default to project directories
        project_root = Path(__file__).resolve().parent.parent
        allowed_paths = [
            str(project_root / "generate_cp"),
            str(project_root / "generate_assessment"),
            str(project_root / "generate_ap_fg_lg_lp"),
            str(project_root / "generate_brochure"),
            str(project_root / "check_documents"),
        ]

    return MCPServerStdio(
        name=name,
        params={
            "command": "npx",
            "args": ["-y", "@modelcontextprotocol/server-filesystem"] + allowed_paths,
        },
        cache_tools_list=True,
    )


async def create_postgres_server(
    database_url: Optional[str] = None,
    name: str = "PostgreSQL Server"
):
    """
    Create a PostgreSQL MCP server for company data access.

    Args:
        database_url: PostgreSQL connection string. Falls back to DATABASE_URL env var.
        name: Server name for identification.

    Returns:
        MCPServerStdio instance configured for PostgreSQL access.
    """
    from agents.mcp import MCPServerStdio

    if database_url is None:
        # Try to load from secrets or environment
        try:
            import streamlit as st
            database_url = st.secrets.get("DATABASE_URL", "")
        except Exception:
            database_url = os.environ.get("DATABASE_URL", "")

    if not database_url:
        raise ValueError("DATABASE_URL not configured for PostgreSQL MCP server")

    return MCPServerStdio(
        name=name,
        params={
            "command": "npx",
            "args": ["-y", "@modelcontextprotocol/server-postgres", database_url],
        },
        cache_tools_list=True,
    )


async def create_sqlite_server(
    db_path: Optional[str] = None,
    name: str = "SQLite Server"
):
    """
    Create a SQLite MCP server for API configuration access.

    Args:
        db_path: Path to SQLite database. Defaults to settings config db.
        name: Server name for identification.

    Returns:
        MCPServerStdio instance configured for SQLite access.
    """
    from agents.mcp import MCPServerStdio

    if db_path is None:
        project_root = Path(__file__).resolve().parent.parent
        db_path = str(project_root / "settings" / "config" / "api_config.db")

    return MCPServerStdio(
        name=name,
        params={
            "command": "npx",
            "args": ["-y", "@modelcontextprotocol/server-sqlite", db_path],
        },
        cache_tools_list=True,
    )


async def create_fetch_server(name: str = "Web Fetch Server"):
    """
    Create a Fetch MCP server for web scraping operations.

    Args:
        name: Server name for identification.

    Returns:
        MCPServerStdio instance configured for web fetching.
    """
    from agents.mcp import MCPServerStdio

    return MCPServerStdio(
        name=name,
        params={
            "command": "npx",
            "args": ["-y", "@modelcontextprotocol/server-fetch"],
        },
        cache_tools_list=True,
    )


async def create_notebooklm_server(
    server_path: Optional[str] = None,
    name: str = "NotebookLM Server"
):
    """
    Create a NotebookLM MCP server for AI-powered content processing.

    Provides tools for creating notebooks, adding sources, and generating
    slide decks, summaries, quizzes, and more via Google NotebookLM.

    Available tools:
        - list_notebooks: List all notebooks
        - create_notebook: Create a new notebook
        - add_source_url: Add a URL as source
        - add_source_text: Add raw text as source
        - ask_notebook: Query notebook content
        - get_notebook_summary: Get summary and insights
        - generate_slide_deck: Generate PowerPoint-style slides
        - generate_quiz: Generate quiz questions
        - generate_summary_report: Generate a briefing document

    Args:
        server_path: Path to the notebooklm-mcp server directory.
                     Defaults to sibling directory of project root.
        name: Server name for identification.

    Returns:
        MCPServerStdio instance configured for NotebookLM access.
    """
    from agents.mcp import MCPServerStdio

    if server_path is None:
        # Try common locations
        project_root = Path(__file__).resolve().parent.parent
        possible_paths = [
            project_root / "notebooklm-mcp",
            project_root.parent / "notebooklm-mcp",
            Path.home() / "notebooklm-mcp",
        ]
        for p in possible_paths:
            if (p / "server.py").exists():
                server_path = str(p)
                break

    if not server_path:
        raise ValueError(
            "NotebookLM MCP server not found. Clone it from "
            "https://github.com/alfredang/notebooklm-mcp and set the path."
        )

    return MCPServerStdio(
        name=name,
        params={
            "command": "uv",
            "args": ["run", "python", "server.py"],
            "cwd": server_path,
        },
        cache_tools_list=True,
    )


async def create_memory_server(name: str = "Memory Server"):
    """
    Create a Memory MCP server for persistent knowledge storage.

    This provides a knowledge graph-based memory system for agents
    to store and retrieve information across sessions.

    Args:
        name: Server name for identification.

    Returns:
        MCPServerStdio instance configured for memory operations.
    """
    from agents.mcp import MCPServerStdio

    return MCPServerStdio(
        name=name,
        params={
            "command": "npx",
            "args": ["-y", "@modelcontextprotocol/server-memory"],
        },
        cache_tools_list=True,
    )


class MCPServerConfig:
    """
    Configuration class for MCP servers used by courseware agents.

    This class provides a centralized way to manage MCP server instances
    and their lifecycle.
    """

    def __init__(self):
        self._servers: Dict[str, Any] = {}
        self._active = False

    async def initialize(
        self,
        enable_filesystem: bool = True,
        enable_postgres: bool = False,
        enable_sqlite: bool = False,
        enable_fetch: bool = True,
        enable_memory: bool = False,
        enable_notebooklm: bool = False,
        custom_paths: Optional[List[str]] = None,
        notebooklm_path: Optional[str] = None,
    ):
        """
        Initialize MCP servers based on configuration.

        Args:
            enable_filesystem: Enable filesystem MCP server.
            enable_postgres: Enable PostgreSQL MCP server.
            enable_sqlite: Enable SQLite MCP server.
            enable_fetch: Enable web fetch MCP server.
            enable_memory: Enable memory MCP server.
            enable_notebooklm: Enable NotebookLM MCP server.
            custom_paths: Custom paths for filesystem server.
            notebooklm_path: Path to notebooklm-mcp server directory.
        """
        if enable_filesystem:
            self._servers["filesystem"] = await create_filesystem_server(custom_paths)

        if enable_postgres:
            try:
                self._servers["postgres"] = await create_postgres_server()
            except ValueError as e:
                print(f"Warning: PostgreSQL MCP not available: {e}")

        if enable_sqlite:
            self._servers["sqlite"] = await create_sqlite_server()

        if enable_fetch:
            self._servers["fetch"] = await create_fetch_server()

        if enable_memory:
            self._servers["memory"] = await create_memory_server()

        if enable_notebooklm:
            try:
                self._servers["notebooklm"] = await create_notebooklm_server(notebooklm_path)
            except ValueError as e:
                print(f"Warning: NotebookLM MCP not available: {e}")

    async def start_all(self):
        """Start all configured MCP servers."""
        for name, server in self._servers.items():
            try:
                await server.__aenter__()
                print(f"Started MCP server: {name}")
            except Exception as e:
                print(f"Failed to start MCP server {name}: {e}")
        self._active = True

    async def stop_all(self):
        """Stop all running MCP servers."""
        for name, server in self._servers.items():
            try:
                await server.__aexit__(None, None, None)
                print(f"Stopped MCP server: {name}")
            except Exception as e:
                print(f"Error stopping MCP server {name}: {e}")
        self._active = False
        self._servers.clear()

    @property
    def servers(self) -> List[Any]:
        """Get list of active MCP servers."""
        return list(self._servers.values())

    @property
    def is_active(self) -> bool:
        """Check if servers are active."""
        return self._active

    def get_server(self, name: str) -> Optional[Any]:
        """Get a specific MCP server by name."""
        return self._servers.get(name)


@asynccontextmanager
async def mcp_context(
    enable_filesystem: bool = True,
    enable_postgres: bool = False,
    enable_sqlite: bool = False,
    enable_fetch: bool = True,
    enable_memory: bool = False,
    enable_notebooklm: bool = False,
    custom_paths: Optional[List[str]] = None,
    notebooklm_path: Optional[str] = None,
):
    """
    Context manager for MCP server lifecycle.

    Usage:
        async with mcp_context(enable_notebooklm=True) as servers:
            agent = Agent(name="Slides Agent", mcp_servers=servers)
            result = await Runner.run(agent, "Generate slides")

    Args:
        enable_filesystem: Enable filesystem MCP server.
        enable_postgres: Enable PostgreSQL MCP server.
        enable_sqlite: Enable SQLite MCP server.
        enable_fetch: Enable web fetch MCP server.
        enable_memory: Enable memory MCP server.
        enable_notebooklm: Enable NotebookLM MCP server.
        custom_paths: Custom paths for filesystem server.
        notebooklm_path: Path to notebooklm-mcp server directory.

    Yields:
        List of active MCP servers.
    """
    config = MCPServerConfig()
    await config.initialize(
        enable_filesystem=enable_filesystem,
        enable_postgres=enable_postgres,
        enable_sqlite=enable_sqlite,
        enable_fetch=enable_fetch,
        enable_memory=enable_memory,
        enable_notebooklm=enable_notebooklm,
        custom_paths=custom_paths,
        notebooklm_path=notebooklm_path,
    )
    await config.start_all()

    try:
        yield config.servers
    finally:
        await config.stop_all()


# Predefined server configurations for common use cases
COURSEWARE_MCP_CONFIG = {
    "enable_filesystem": True,
    "enable_postgres": False,  # Enable when company data access needed
    "enable_sqlite": False,    # Enable when API config access needed
    "enable_fetch": True,      # For web scraping in brochure generation
    "enable_memory": False,    # Enable for persistent agent memory
}

DOCUMENT_AGENT_MCP_CONFIG = {
    "enable_filesystem": True,
    "enable_postgres": True,   # For training records verification
    "enable_sqlite": False,
    "enable_fetch": False,
    "enable_memory": False,
}

BROCHURE_AGENT_MCP_CONFIG = {
    "enable_filesystem": True,
    "enable_postgres": False,
    "enable_sqlite": False,
    "enable_fetch": True,      # For course info scraping
    "enable_memory": False,
    "enable_notebooklm": False,
}

SLIDES_AGENT_MCP_CONFIG = {
    "enable_filesystem": False,
    "enable_postgres": False,
    "enable_sqlite": False,
    "enable_fetch": False,
    "enable_memory": False,
    "enable_notebooklm": True,  # NotebookLM for slide generation
}


__all__ = [
    "create_filesystem_server",
    "create_postgres_server",
    "create_sqlite_server",
    "create_fetch_server",
    "create_memory_server",
    "create_notebooklm_server",
    "MCPServerConfig",
    "mcp_context",
    "COURSEWARE_MCP_CONFIG",
    "DOCUMENT_AGENT_MCP_CONFIG",
    "BROCHURE_AGENT_MCP_CONFIG",
    "SLIDES_AGENT_MCP_CONFIG",
]
