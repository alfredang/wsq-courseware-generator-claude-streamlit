"""
Courseware Agents Module - Claude Agent SDK

This module provides a multi-agent system for orchestrating courseware generation workflows.
The orchestrator agent coordinates specialized subagents for different tasks.

Built on the Claude Agent SDK with MCP (Model Context Protocol) support.

Agents:
- Orchestrator: Main coordinator that routes to specialized agents
- CP Agent: Course Proposal generation
- Courseware Agent: AP/FG/LG/LP generation
- Assessment Agent: SAQ/PP/CS generation
- Brochure Agent: Brochure creation
- Document Agent: Document verification

MCP Support:
- Courseware Tools MCP: Custom courseware generation tools
- Filesystem MCP: Document read/write operations
- Fetch MCP: Web scraping operations
- PostgreSQL MCP: Company database access (optional)
- NotebookLM MCP: Slide generation (optional)

Author: Courseware Generator Team
Date: 26 January 2026
"""

# Core imports - Claude Agent SDK base utilities
try:
    from courseware_agents.base import (
        CLAUDE_SDK_AVAILABLE,
        get_mcp_servers_config,
        create_subagent,
        get_claude_model,
        setup_anthropic_api,
        get_default_options,
        COURSEWARE_MCP_CONFIG,
        DOCUMENT_AGENT_MCP_CONFIG,
        BROCHURE_AGENT_MCP_CONFIG,
        SLIDES_AGENT_MCP_CONFIG,
    )
except ImportError as e:
    print(f"Warning: Could not import courseware_agents.base: {e}")
    CLAUDE_SDK_AVAILABLE = False
    get_mcp_servers_config = None
    create_subagent = None
    get_claude_model = None
    setup_anthropic_api = None
    get_default_options = None
    COURSEWARE_MCP_CONFIG = {}
    DOCUMENT_AGENT_MCP_CONFIG = {}
    BROCHURE_AGENT_MCP_CONFIG = {}
    SLIDES_AGENT_MCP_CONFIG = {}

# Orchestrator and agent definitions
try:
    from courseware_agents.orchestrator import (
        run_orchestrator,
        run_orchestrator_simple,
        get_orchestrator_options,
        ORCHESTRATOR_INSTRUCTIONS,
        CP_AGENT,
        COURSEWARE_AGENT,
        ASSESSMENT_AGENT,
        BROCHURE_AGENT,
        DOCUMENT_AGENT,
        get_cp_agent,
        get_courseware_agent,
        get_assessment_agent,
        get_brochure_agent,
        get_document_agent,
    )
except ImportError as e:
    print(f"Warning: Could not import orchestrator: {e}")
    run_orchestrator = None
    run_orchestrator_simple = None
    get_orchestrator_options = None
    ORCHESTRATOR_INSTRUCTIONS = None
    CP_AGENT = None
    COURSEWARE_AGENT = None
    ASSESSMENT_AGENT = None
    BROCHURE_AGENT = None
    DOCUMENT_AGENT = None
    get_cp_agent = None
    get_courseware_agent = None
    get_assessment_agent = None
    get_brochure_agent = None
    get_document_agent = None

# Agent instructions
try:
    from courseware_agents.cp_agent import CP_AGENT_INSTRUCTIONS
    from courseware_agents.courseware_agent import COURSEWARE_AGENT_INSTRUCTIONS
    from courseware_agents.assessment_agent import ASSESSMENT_AGENT_INSTRUCTIONS
    from courseware_agents.brochure_agent import BROCHURE_AGENT_INSTRUCTIONS
    from courseware_agents.document_agent import DOCUMENT_AGENT_INSTRUCTIONS
except ImportError as e:
    print(f"Warning: Could not import agent instructions: {e}")
    CP_AGENT_INSTRUCTIONS = None
    COURSEWARE_AGENT_INSTRUCTIONS = None
    ASSESSMENT_AGENT_INSTRUCTIONS = None
    BROCHURE_AGENT_INSTRUCTIONS = None
    DOCUMENT_AGENT_INSTRUCTIONS = None

# MCP configuration utilities
try:
    from courseware_agents.mcp_config import (
        get_mcp_servers,
        get_mcp_server_config,
        get_project_root,
    )
except ImportError:
    get_mcp_servers = None
    get_mcp_server_config = None
    get_project_root = None

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


__all__ = [
    # SDK availability
    "CLAUDE_SDK_AVAILABLE",
    # Base utilities
    "get_mcp_servers_config",
    "create_subagent",
    "get_claude_model",
    "setup_anthropic_api",
    "get_default_options",
    # Orchestrator
    "run_orchestrator",
    "run_orchestrator_simple",
    "get_orchestrator_options",
    "ORCHESTRATOR_INSTRUCTIONS",
    # Agent definitions
    "CP_AGENT",
    "COURSEWARE_AGENT",
    "ASSESSMENT_AGENT",
    "BROCHURE_AGENT",
    "DOCUMENT_AGENT",
    # Agent getters
    "get_cp_agent",
    "get_courseware_agent",
    "get_assessment_agent",
    "get_brochure_agent",
    "get_document_agent",
    # Agent instructions
    "CP_AGENT_INSTRUCTIONS",
    "COURSEWARE_AGENT_INSTRUCTIONS",
    "ASSESSMENT_AGENT_INSTRUCTIONS",
    "BROCHURE_AGENT_INSTRUCTIONS",
    "DOCUMENT_AGENT_INSTRUCTIONS",
    # MCP configuration
    "get_mcp_servers",
    "get_mcp_server_config",
    "get_project_root",
    "COURSEWARE_MCP_CONFIG",
    "DOCUMENT_AGENT_MCP_CONFIG",
    "BROCHURE_AGENT_MCP_CONFIG",
    "SLIDES_AGENT_MCP_CONFIG",
    # Schemas
    "CPAgentResponse",
    "CoursewareAgentResponse",
    "AssessmentAgentResponse",
    "BrochureAgentResponse",
    "DocumentAgentResponse",
    "OrchestratorResponse",
]
