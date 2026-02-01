"""
Orchestrator Agent - Claude Agent SDK

This is the main coordinator agent that interacts with users and
delegates tasks to specialized subagents.

Supports MCP (Model Context Protocol) servers for enhanced tool integration
including custom courseware tools, filesystem operations, and web fetching.

Author: Courseware Generator Team
Date: 26 January 2026
"""

from typing import Optional, List, Any, Dict, AsyncGenerator

try:
    from claude_agent_sdk import query, ClaudeAgentOptions, AgentDefinition
except ImportError:
    from courseware_agents.base import ClaudeAgentOptions, AgentDefinition, query

from courseware_agents.base import (
    get_mcp_servers_config,
    create_subagent,
    setup_anthropic_api,
    COURSEWARE_MCP_CONFIG,
)


# System instructions for the Orchestrator
ORCHESTRATOR_INSTRUCTIONS = """You are the Courseware Generator Orchestrator, the main coordinator for WSQ courseware generation.

## Your Role

You help users create WSQ (Workforce Skills Qualifications) courseware materials by:
1. Understanding their needs
2. Routing to the appropriate specialized agent
3. Coordinating multi-step workflows
4. Reporting results

## Available Specialized Agents

You can delegate to these specialized agents using the Task tool:

### 1. CP Agent (Course Proposal)
- **Use when**: User wants to generate a Course Proposal from TSC file
- **Capabilities**: Parse TSC documents, extract course info, research job roles
- **Needs**: TSC document (DOCX)
- **Outputs**: CP JSON data, CP Word document

### 2. Courseware Agent (AP/FG/LG/LP)
- **Use when**: User wants to generate courseware documents
- **Capabilities**: Generate Assessment Plans, Facilitator Guides, Learner Guides, Lesson Plans
- **Needs**: Course Proposal data (JSON)
- **Outputs**: AP, FG, LG, LP documents

### 3. Assessment Agent (SAQ/PP/CS)
- **Use when**: User wants to generate assessment materials
- **Capabilities**: Create Short Answer Questions, Practical Performance, Case Studies
- **Needs**: Facilitator Guide or course content
- **Outputs**: Assessment question papers and answer keys

### 4. Brochure Agent
- **Use when**: User wants to create a marketing brochure
- **Capabilities**: Scrape course info, generate marketing content, create brochures
- **Needs**: Course URL or Course Proposal data
- **Outputs**: HTML and PDF brochures

### 5. Document Agent
- **Use when**: User wants to verify supporting documents
- **Capabilities**: Extract entities, verify against training records, check completeness
- **Needs**: Documents to verify (PDF, images)
- **Outputs**: Verification reports

## Available MCP Tools

You have access to custom courseware tools via MCP:
- parse_tsc_document: Parse TSC documents
- run_extraction_pipeline: Extract course information
- generate_assessment_plan: Generate AP documents
- generate_facilitator_guide: Generate FG documents
- generate_learner_guide: Generate LG documents
- generate_lesson_plan: Generate LP documents
- generate_saq_questions: Generate SAQ assessments
- generate_practical_performance: Generate PP assessments
- generate_case_study: Generate CS assessments
- scrape_course_info: Scrape course information from URLs
- generate_brochure_html: Generate HTML brochures
- extract_document_entities: Extract entities from documents
- verify_company_uen: Verify UEN against ACRA
- And more...

## Typical Workflows

### Full Course Generation
1. User provides TSC document
2. Use CP tools → generates Course Proposal
3. Use Courseware tools → generates AP, FG, LG, LP
4. Use Assessment tools → generates assessments
5. Use Brochure tools → creates marketing brochure

### Assessment Only
1. User provides Facilitator Guide
2. Use Assessment tools → generates SAQ, PP, or CS

### Document Verification
1. User provides supporting documents
2. Use Document tools → verifies and reports

## How to Interact

1. **Greet the user** and ask what they need
2. **Clarify requirements** if unclear
3. **Use appropriate tools** with context
4. **Report back** results when complete

## Important Guidelines

- Always explain what you're doing
- Ask for clarification when needed
- Provide helpful suggestions
- Report any errors clearly
- Guide users through the process step by step

## Example Interactions

**User**: "I want to create courseware for a new AI course"
**You**: "I'll help you create courseware! To get started, I need the TSC (Training Standards and Competencies) document for the course. Do you have the TSC file ready to upload?"

**User**: "Generate assessments for this course"
**You**: "I'll help you generate assessments. I can create:
- SAQ (Short Answer Questions)
- PP (Practical Performance assessments)
- CS (Case Studies)

Do you have a Facilitator Guide I can use as source material? And which assessment types would you like?"

**User**: "Check these documents"
**You**: "I'll verify your documents against our training records. Please upload the documents you want to check, and I'll extract the relevant information and verify them."
"""


# Import agent instructions from individual agent files
def _get_cp_agent_instructions() -> str:
    """Get CP Agent instructions."""
    from courseware_agents.cp_agent import CP_AGENT_INSTRUCTIONS
    return CP_AGENT_INSTRUCTIONS


def _get_courseware_agent_instructions() -> str:
    """Get Courseware Agent instructions."""
    from courseware_agents.courseware_agent import COURSEWARE_AGENT_INSTRUCTIONS
    return COURSEWARE_AGENT_INSTRUCTIONS


def _get_assessment_agent_instructions() -> str:
    """Get Assessment Agent instructions."""
    from courseware_agents.assessment_agent import ASSESSMENT_AGENT_INSTRUCTIONS
    return ASSESSMENT_AGENT_INSTRUCTIONS


def _get_brochure_agent_instructions() -> str:
    """Get Brochure Agent instructions."""
    from courseware_agents.brochure_agent import BROCHURE_AGENT_INSTRUCTIONS
    return BROCHURE_AGENT_INSTRUCTIONS


def _get_document_agent_instructions() -> str:
    """Get Document Agent instructions."""
    from courseware_agents.document_agent import DOCUMENT_AGENT_INSTRUCTIONS
    return DOCUMENT_AGENT_INSTRUCTIONS


# Define subagents
CP_AGENT = AgentDefinition(
    name="cp_agent",
    description="Course Proposal generation from TSC documents. Use for parsing TSC files and generating CP data.",
    prompt=_get_cp_agent_instructions() if 'courseware_agents.cp_agent' in __builtins__ else "CP Agent for Course Proposal generation.",
)

COURSEWARE_AGENT = AgentDefinition(
    name="courseware_agent",
    description="AP/FG/LG/LP document generation. Use for generating Assessment Plans, Facilitator Guides, Learner Guides, and Lesson Plans.",
    prompt="Courseware Agent for document generation.",
)

ASSESSMENT_AGENT = AgentDefinition(
    name="assessment_agent",
    description="SAQ/PP/CS assessment generation. Use for generating Short Answer Questions, Practical Performance, and Case Studies.",
    prompt="Assessment Agent for assessment generation.",
)

BROCHURE_AGENT = AgentDefinition(
    name="brochure_agent",
    description="Course brochure creation. Use for generating marketing brochures from course data or URLs.",
    prompt="Brochure Agent for brochure creation.",
)

DOCUMENT_AGENT = AgentDefinition(
    name="document_agent",
    description="Document verification and validation. Use for extracting entities and verifying documents.",
    prompt="Document Agent for document verification.",
)


def get_orchestrator_options(
    mcp_config: Optional[Dict[str, bool]] = None,
) -> ClaudeAgentOptions:
    """
    Get ClaudeAgentOptions for the orchestrator.

    Args:
        mcp_config: MCP server configuration

    Returns:
        Configured ClaudeAgentOptions
    """
    if mcp_config is None:
        mcp_config = COURSEWARE_MCP_CONFIG

    mcp_servers = get_mcp_servers_config(**mcp_config)

    return ClaudeAgentOptions(
        allowed_tools=["Read", "Write", "Edit", "Bash", "Glob", "Grep", "Task", "WebFetch"],
        agents={
            "cp_agent": CP_AGENT,
            "courseware_agent": COURSEWARE_AGENT,
            "assessment_agent": ASSESSMENT_AGENT,
            "brochure_agent": BROCHURE_AGENT,
            "document_agent": DOCUMENT_AGENT,
        },
        mcp_servers=mcp_servers,
    )


async def run_orchestrator(
    prompt: str,
    mcp_config: Optional[Dict[str, bool]] = None,
) -> AsyncGenerator[Any, None]:
    """
    Run the orchestrator with Claude Agent SDK.

    Args:
        prompt: User prompt to process
        mcp_config: MCP server configuration

    Yields:
        Messages from the orchestrator

    Example:
        async for message in run_orchestrator("Generate a Course Proposal"):
            print(message)
    """
    setup_anthropic_api()

    options = get_orchestrator_options(mcp_config)

    async for message in query(
        prompt=prompt,
        options=options,
    ):
        yield message


async def run_orchestrator_simple(
    prompt: str,
    mcp_config: Optional[Dict[str, bool]] = None,
) -> str:
    """
    Run the orchestrator and return the final result.

    Args:
        prompt: User prompt to process
        mcp_config: MCP server configuration

    Returns:
        Final result as string
    """
    result = ""
    async for message in run_orchestrator(prompt, mcp_config):
        if hasattr(message, "result"):
            result = message.result
        elif hasattr(message, "content"):
            result = message.content
    return result


# Convenience functions to get individual agent definitions
def get_cp_agent() -> AgentDefinition:
    """Get the CP Agent definition."""
    return CP_AGENT


def get_courseware_agent() -> AgentDefinition:
    """Get the Courseware Agent definition."""
    return COURSEWARE_AGENT


def get_assessment_agent() -> AgentDefinition:
    """Get the Assessment Agent definition."""
    return ASSESSMENT_AGENT


def get_brochure_agent() -> AgentDefinition:
    """Get the Brochure Agent definition."""
    return BROCHURE_AGENT


def get_document_agent() -> AgentDefinition:
    """Get the Document Agent definition."""
    return DOCUMENT_AGENT
