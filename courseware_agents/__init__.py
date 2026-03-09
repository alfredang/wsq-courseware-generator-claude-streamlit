"""
WSQ Courseware Agents — AI-powered course material generation

Architecture:
    courseware_agents/
    ├── base.py                  # Core: run_agent(), run_agent_json()
    ├── cp_interpreter.py        # Shared: CP Interpretation Agent
    │
    ├── slides/                  # Slide Generation (5-phase pipeline)
    │   ├── research_agent.py    # Phase 1: Web Research
    │   ├── content_generator_agent.py  # Phase 2 & 5: Content + Assembly
    │   ├── editor_agent.py      # Phase 3: Slide Skeleton
    │   ├── infographic_agent.py # Phase 4: AntV → PNG
    │   └── slides_agent.py      # Legacy: Document Analysis
    │
    ├── assessment/              # Assessment Generation
    │   └── assessment_generator.py  # SAQ/PP/CS/PRJ/OI/DEM questions
    │
    └── audit/                   # Courseware Audit
        └── audit_agent.py       # Cross-document consistency checks

Agent Pipeline (Slides):
    CP Interpreter → Research → Content → Editor → Infographic → Assembly → PPTX

See AGENTS.md for full architecture documentation.
"""

# Core
from courseware_agents.base import run_agent

# Shared agent
from courseware_agents.cp_interpreter import interpret_cp

# Slide generation agents (5-phase pipeline)
from courseware_agents.slides import (
    research_topic,
    research_all_topics,
    generate_content_blocks,
    generate_all_content_blocks,
    assemble_final_slides,
    generate_skeleton,
    generate_single_infographic,
    generate_topic_infographics,
    generate_all_infographics,
    build_antv_dsl,
    generate_slide_content,
    extract_slides_text,
)

# Assessment agent
from courseware_agents.assessment import generate_assessments

# Audit agent
from courseware_agents.audit import extract_audit_fields

__all__ = [
    # Core
    "run_agent",
    # Shared
    "interpret_cp",
    # Slides pipeline
    "research_topic",
    "research_all_topics",
    "generate_content_blocks",
    "generate_all_content_blocks",
    "assemble_final_slides",
    "generate_skeleton",
    "generate_single_infographic",
    "generate_topic_infographics",
    "generate_all_infographics",
    "build_antv_dsl",
    "generate_slide_content",
    "extract_slides_text",
    # Assessment
    "generate_assessments",
    # Audit
    "extract_audit_fields",
]
