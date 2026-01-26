"""
Orchestrator Agent

This is the main coordinator agent that interacts with users and
delegates tasks to specialized agents via handoffs.

Author: Courseware Generator Team
Date: 26 January 2026
"""

from agents import Agent, handoff
from courseware_agents.base import create_agent, setup_openrouter, get_model_for_agent
from typing import Optional


# System instructions for the Orchestrator
ORCHESTRATOR_INSTRUCTIONS = """You are the Courseware Generator Orchestrator, the main coordinator for WSQ courseware generation.

## Your Role

You help users create WSQ (Workforce Skills Qualifications) courseware materials by:
1. Understanding their needs
2. Routing to the appropriate specialized agent
3. Coordinating multi-step workflows
4. Reporting results

## Available Specialized Agents

You can hand off to these specialized agents:

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

## Typical Workflows

### Full Course Generation
1. User provides TSC document
2. Hand off to CP Agent → generates Course Proposal
3. Hand off to Courseware Agent → generates AP, FG, LG, LP
4. Hand off to Assessment Agent → generates assessments
5. Hand off to Brochure Agent → creates marketing brochure

### Assessment Only
1. User provides Facilitator Guide
2. Hand off to Assessment Agent → generates SAQ, PP, or CS

### Document Verification
1. User provides supporting documents
2. Hand off to Document Agent → verifies and reports

## How to Interact

1. **Greet the user** and ask what they need
2. **Clarify requirements** if unclear
3. **Hand off** to the appropriate agent with context
4. **Report back** results when agent completes

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


def create_orchestrator(model_name: str = "GPT-4o") -> Agent:
    """
    Create the main orchestrator agent with handoffs to all specialized agents.

    The orchestrator is created lazily to avoid circular imports.

    Args:
        model_name: Model to use for the orchestrator (default: GPT-4o)

    Returns:
        Configured orchestrator Agent with handoffs
    """
    # Ensure OpenRouter is configured
    setup_openrouter()

    # Import agents here to avoid circular imports
    from courseware_agents.cp_agent import cp_agent
    from courseware_agents.courseware_agent import courseware_agent
    from courseware_agents.assessment_agent import assessment_agent
    from courseware_agents.brochure_agent import brochure_agent
    from courseware_agents.document_agent import document_agent

    # Get model ID
    model_id = get_model_for_agent(model_name)

    # Create orchestrator with handoffs
    orchestrator = Agent(
        name="Courseware Orchestrator",
        instructions=ORCHESTRATOR_INSTRUCTIONS,
        model=model_id,
        handoffs=[
            handoff(
                cp_agent,
                tool_name_override="transfer_to_cp_agent",
                tool_description_override="Transfer to CP Agent for Course Proposal generation from TSC documents"
            ),
            handoff(
                courseware_agent,
                tool_name_override="transfer_to_courseware_agent",
                tool_description_override="Transfer to Courseware Agent for AP/FG/LG/LP document generation"
            ),
            handoff(
                assessment_agent,
                tool_name_override="transfer_to_assessment_agent",
                tool_description_override="Transfer to Assessment Agent for SAQ/PP/CS assessment generation"
            ),
            handoff(
                brochure_agent,
                tool_name_override="transfer_to_brochure_agent",
                tool_description_override="Transfer to Brochure Agent for course brochure creation"
            ),
            handoff(
                document_agent,
                tool_name_override="transfer_to_document_agent",
                tool_description_override="Transfer to Document Agent for document verification and validation"
            ),
        ],
    )

    return orchestrator


# For convenience, also provide the individual agents
def get_cp_agent():
    """Get the CP Agent instance"""
    from courseware_agents.cp_agent import cp_agent
    return cp_agent


def get_courseware_agent():
    """Get the Courseware Agent instance"""
    from courseware_agents.courseware_agent import courseware_agent
    return courseware_agent


def get_assessment_agent():
    """Get the Assessment Agent instance"""
    from courseware_agents.assessment_agent import assessment_agent
    return assessment_agent


def get_brochure_agent():
    """Get the Brochure Agent instance"""
    from courseware_agents.brochure_agent import brochure_agent
    return brochure_agent


def get_document_agent():
    """Get the Document Agent instance"""
    from courseware_agents.document_agent import document_agent
    return document_agent
