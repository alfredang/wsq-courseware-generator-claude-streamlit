"""
WSQ Courseware Agents — AI-powered course material generation

Architecture:
    courseware_agents/
    ├── base.py                  # Core: run_agent(), run_agent_json()
    │                            # Default tools: [Read, Glob, Grep]
    │
    ├── cp_interpreter/          # CP Interpretation Agent
    │   ├── cp_interpreter.py    # Extract structured data from Course Proposals
    │   └── templates/           # Prompt templates
    │   Model: Sonnet 4          Tools: [Read] (+[WebFetch] if URL)
    │   Skill: /generate_courseware, /generate_assessment_plan,
    │          /generate_facilitator_guide, /generate_learner_guide
    │
    ├── courseware/               # Document Generation (AP, FG, LG)
    │   ├── assessment_plan.py   # Assessment Plan + ASR
    │   ├── facilitator_guide.py # Facilitator Guide
    │   ├── learner_guide.py     # Learner Guide
    │   └── templates/           # DOCX templates (docxtpl / Jinja2)
    │   Model: N/A (pure Python) Tools: N/A (template filling only)
    │   Skill: /generate_assessment_plan, /generate_facilitator_guide,
    │          /generate_learner_guide, /generate_courseware
    │
    ├── lesson_plan/             # Lesson Plan (standalone feature)
    │   ├── lesson_plan.py       # Barrier algorithm for schedule
    │   └── templates/           # DOCX templates (docxtpl / Jinja2)
    │   Model: N/A (pure Python) Tools: N/A (template filling only)
    │   Skill: /generate_lesson_plan
    │
    ├── slides/                  # Slide Generation (5-phase pipeline)
    │   ├── research_agent.py    # Phase 1: Web Research
    │   │   Model: Haiku 3.5     Tools: [WebSearch]
    │   ├── content_generator_agent.py  # Phase 2: Content Blocks
    │   │   Model: Haiku 3.5     Tools: [WebSearch] or []
    │   ├── editor_agent.py      # Phase 3: Slide Skeleton
    │   │   Model: Haiku 3.5     Tools: []
    │   ├── infographic_agent.py # Phase 4: AntV DSL → PNG
    │   │   Model: Haiku 3.5     Tools: []
    │   ├── slides_agent.py      # Legacy: Document Analysis
    │   │   Model: Sonnet 4      Tools: [Read, Glob, Grep] / [WebSearch, WebFetch]
    │   └── templates/           # PPTX + prompt templates
    │   Skill: /generate_slides
    │
    ├── assessment/              # Assessment Generation
    │   ├── assessment_generator.py  # SAQ/PP/CS/PRJ/OI/DEM questions
    │   └── templates/           # Prompt templates
    │   Model: Sonnet 4          Tools: []
    │   Skill: /generate_assessment
    │
    └── audit/                   # Courseware Audit
        ├── audit_agent.py       # Cross-document consistency checks
        └── templates/           # Prompt templates
        Model: Sonnet 4          Tools: []
        Skill: /courseware_audit

Agent Pipeline (Slides):
    CP Interpreter → Research → Content → Editor → Infographic → Assembly → PPTX

Models:
    Sonnet 4  (claude-sonnet-4-20250514)    — Balanced, general-purpose
    Haiku 3.5 (claude-3-5-haiku-20241022)   — Fast, structured JSON/DSL
    Opus 4.5  (claude-opus-4-5-20251101)    — Complex reasoning (premium)

See AGENTS.md for full architecture documentation.
"""

# Core
from courseware_agents.base import run_agent

# Shared agent
from courseware_agents.cp_interpreter import interpret_cp

# Courseware document generators (AP, FG, LG)
from courseware_agents.courseware import (
    generate_assessment_plan,
    generate_asr_document,
    generate_assessment_documents,
    generate_facilitators_guide,
    generate_learning_guide,
)

# Lesson Plan (standalone feature)
from courseware_agents.lesson_plan import generate_lesson_plan

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
    # Courseware documents (AP, FG, LG)
    "generate_assessment_plan",
    "generate_asr_document",
    "generate_assessment_documents",
    "generate_facilitators_guide",
    "generate_learning_guide",
    # Lesson Plan
    "generate_lesson_plan",
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
