"""
Courseware Agents Module

This module provides a multi-agent system for orchestrating courseware generation workflows.
The orchestrator agent coordinates specialized agents for different tasks.

Agents:
- Orchestrator: Main coordinator that routes to specialized agents
- CP Agent: Course Proposal generation
- Courseware Agent: AP/FG/LG/LP generation
- Assessment Agent: SAQ/PP/CS generation
- Brochure Agent: Brochure creation
- Document Agent: Document verification

MCP Support:
- Filesystem MCP: Document read/write operations
- PostgreSQL MCP: Company database access
- SQLite MCP: API configuration access
- Fetch MCP: Web scraping operations
- Memory MCP: Persistent agent memory

Author: Courseware Generator Team
Date: 26 January 2026
"""

from courseware_agents.base import (
    create_agent,
    get_model_for_agent,
    setup_openrouter,
    get_mcp_context,
    get_mcp_configs,
)

# Import schemas for structured outputs
from courseware_agents.schemas import (
    CPAgentResponse,
    CoursewareAgentResponse,
    AssessmentAgentResponse,
    BrochureAgentResponse,
    DocumentAgentResponse,
    OrchestratorResponse,
)

# Import MCP configuration
from courseware_agents.mcp_config import (
    mcp_context,
    MCPServerConfig,
    COURSEWARE_MCP_CONFIG,
    DOCUMENT_AGENT_MCP_CONFIG,
    BROCHURE_AGENT_MCP_CONFIG,
)

__all__ = [
    # Agent utilities
    "create_agent",
    "get_model_for_agent",
    "setup_openrouter",
    # MCP utilities
    "get_mcp_context",
    "get_mcp_configs",
    "mcp_context",
    "MCPServerConfig",
    "COURSEWARE_MCP_CONFIG",
    "DOCUMENT_AGENT_MCP_CONFIG",
    "BROCHURE_AGENT_MCP_CONFIG",
    # Schemas
    "CPAgentResponse",
    "CoursewareAgentResponse",
    "AssessmentAgentResponse",
    "BrochureAgentResponse",
    "DocumentAgentResponse",
    "OrchestratorResponse",
]
