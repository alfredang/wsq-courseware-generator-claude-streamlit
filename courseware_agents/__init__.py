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

Author: Courseware Generator Team
Date: 26 January 2026
"""

from courseware_agents.base import create_agent, get_model_for_agent, setup_openrouter

__all__ = [
    "create_agent",
    "get_model_for_agent",
    "setup_openrouter",
]
