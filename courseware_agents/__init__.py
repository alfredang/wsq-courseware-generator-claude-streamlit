"""
Courseware Agents Module

Provides agentic AI capabilities using the Claude Agent SDK.
Each agent specializes in a specific courseware generation task.

Agents:
- CP Interpreter: Extracts structured course data from Course Proposals
- Assessment Generator: Generates assessment questions from Facilitator Guides
- Slides Agent: AI-enhanced slide generation analysis
- Editor Agent: Slide skeleton with infographic assignments (Phase 3)
- Research Agent: Web research for slide content (Phase 1)
- Content Generator Agent: Structured content blocks + assembly (Phase 2 & 5)
- Infographic Agent: AntV infographic image generation (Phase 4)
"""

from courseware_agents.base import run_agent
from courseware_agents.cp_interpreter import interpret_cp
from courseware_agents.assessment_generator import generate_assessments
from courseware_agents.slides_agent import analyze_document_for_slides
from courseware_agents.editor_agent import generate_skeleton
from courseware_agents.research_agent import research_topic, research_all_topics
from courseware_agents.content_generator_agent import (
    generate_content_blocks,
    generate_all_content_blocks,
    assemble_final_slides,
)
from courseware_agents.infographic_agent import (
    build_antv_dsl,
    generate_dsl_with_ai,
    generate_single_infographic,
    generate_topic_infographics,
    generate_all_infographics,
)

__all__ = [
    "run_agent",
    "interpret_cp",
    "generate_assessments",
    "analyze_document_for_slides",
    "generate_skeleton",
    "research_topic",
    "research_all_topics",
    "generate_content_blocks",
    "generate_all_content_blocks",
    "assemble_final_slides",
    "build_antv_dsl",
    "generate_dsl_with_ai",
    "generate_single_infographic",
    "generate_topic_infographics",
    "generate_all_infographics",
]
