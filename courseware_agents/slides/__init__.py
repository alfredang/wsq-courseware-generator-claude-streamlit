"""
Slide Generation Agents — 5-Phase Multi-Agent Pipeline

Orchestrated by generate_slides/multi_agent_orchestrator.py:

    Phase 1: Research Agent      → Web research per topic (parallel)
    Phase 2: Content Generator   → Structured content blocks for infographics
    Phase 3: Editor Agent        → Slide skeleton with template assignments
    Phase 4: Infographic Agent   → AntV DSL → HTML → PNG via Playwright
    Phase 5: Assembly            → Map PNGs to slide positions → PPTX

Tools: WebSearch (Phase 1-2), Playwright + AntV Infographic (Phase 4)
Models: Configurable via generate_slides/multi_agent_config.py
"""

from courseware_agents.slides.research_agent import (
    research_topic,
    research_all_topics,
)
from courseware_agents.slides.content_generator_agent import (
    generate_content_blocks,
    generate_all_content_blocks,
    assemble_final_slides,
)
from courseware_agents.slides.editor_agent import (
    generate_skeleton,
)
from courseware_agents.slides.infographic_agent import (
    generate_single_infographic,
    generate_topic_infographics,
    generate_all_infographics,
    build_antv_dsl,
)
from courseware_agents.slides.slides_agent import (
    generate_slide_content,
    extract_slides_text,
)

__all__ = [
    # Phase 1: Research
    "research_topic",
    "research_all_topics",
    # Phase 2: Content Generation
    "generate_content_blocks",
    "generate_all_content_blocks",
    # Phase 3: Editor / Skeleton
    "generate_skeleton",
    # Phase 4: Infographic Rendering
    "generate_single_infographic",
    "generate_topic_infographics",
    "generate_all_infographics",
    "build_antv_dsl",
    # Phase 5: Assembly
    "assemble_final_slides",
    # Legacy
    "generate_slide_content",
    "extract_slides_text",
]
