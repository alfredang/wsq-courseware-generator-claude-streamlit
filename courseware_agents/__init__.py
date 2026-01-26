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

MCP Support (optional, requires Node.js):
- Filesystem MCP: Document read/write operations
- PostgreSQL MCP: Company database access
- SQLite MCP: API configuration access
- Fetch MCP: Web scraping operations
- Memory MCP: Persistent agent memory

Author: Courseware Generator Team
Date: 26 January 2026
"""

# Core imports with graceful fallback
try:
    from courseware_agents.base import (
        create_agent,
        get_model_for_agent,
        setup_openrouter,
        AGENTS_AVAILABLE,
    )
except ImportError as e:
    print(f"Warning: Could not import courseware_agents.base: {e}")
    AGENTS_AVAILABLE = False
    create_agent = None
    get_model_for_agent = None
    setup_openrouter = None

# MCP utilities - optional, lazy loaded
def get_mcp_context():
    """Get the MCP context manager (lazy import)."""
    try:
        from courseware_agents.mcp_config import mcp_context
        return mcp_context
    except ImportError:
        print("Warning: MCP features not available")
        return None

def get_mcp_configs():
    """Get MCP configuration presets (lazy import)."""
    try:
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
    except ImportError:
        return {}

# Import schemas for structured outputs
try:
    from courseware_agents.schemas import (
        CPAgentResponse,
        CoursewareAgentResponse,
        AssessmentAgentResponse,
        BrochureAgentResponse,
        DocumentAgentResponse,
        OrchestratorResponse,
    )
except ImportError as e:
    print(f"Warning: Could not import schemas: {e}")
    CPAgentResponse = None
    CoursewareAgentResponse = None
    AssessmentAgentResponse = None
    BrochureAgentResponse = None
    DocumentAgentResponse = None
    OrchestratorResponse = None

# MCP configuration - optional imports (don't fail if not available)
mcp_context = None
MCPServerConfig = None
COURSEWARE_MCP_CONFIG = {}
DOCUMENT_AGENT_MCP_CONFIG = {}
BROCHURE_AGENT_MCP_CONFIG = {}

try:
    from courseware_agents.mcp_config import (
        mcp_context,
        MCPServerConfig,
        COURSEWARE_MCP_CONFIG,
        DOCUMENT_AGENT_MCP_CONFIG,
        BROCHURE_AGENT_MCP_CONFIG,
    )
except ImportError:
    pass  # MCP features will be disabled

__all__ = [
    # Agent utilities
    "create_agent",
    "get_model_for_agent",
    "setup_openrouter",
    "AGENTS_AVAILABLE",
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
