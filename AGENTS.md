# WSQ Courseware Generator — Agent Architecture

## Directory Structure

```
courseware_agents/
├── __init__.py              # Root exports (backwards-compatible)
├── base.py                  # Core: run_agent(), run_agent_json()
├── cp_interpreter.py        # Shared: CP Interpretation Agent
├── templates/               # CP Interpreter prompt templates
│   ├── cp_interpretation.md
│   └── tsc_agent.md
│
├── slides/                  # Slide Generation (5-phase pipeline)
│   ├── __init__.py
│   ├── research_agent.py    # Phase 1: Web Research
│   ├── content_generator_agent.py  # Phase 2 & 5: Content + Assembly
│   ├── editor_agent.py      # Phase 3: Slide Skeleton
│   ├── infographic_agent.py # Phase 4: AntV Infographic → PNG
│   ├── slides_agent.py      # Legacy: Document Analysis
│   └── templates/           # Slide generation templates
│       ├── slide_template.pptx          # Master PPTX template
│       ├── topic_analysis.md            # Topic analysis prompt
│       ├── source_evaluation.md         # Source evaluation prompt
│       ├── slide_instructions.md        # Slide generation prompt
│       ├── quality_validation.md        # Quality validation prompt
│       ├── infographic-item-creator_item-prompt.md
│       ├── infographic-structure-creator_structure-prompt.md
│       └── infographic-syntax-creator_prompt.md
│
├── assessment/              # Assessment Generation
│   ├── __init__.py
│   ├── assessment_generator.py  # SAQ/PP/CS/PRJ/OI/DEM questions
│   └── templates/           # Assessment prompt templates
│       ├── saq_generation.md
│       ├── case_study.md
│       ├── practical_performance.md
│       ├── project.md
│       ├── assignment.md
│       ├── demonstration.md
│       ├── oral_interview.md
│       ├── oral_questioning.md
│       └── role_play.md
│
└── audit/                   # Courseware Audit
    ├── __init__.py
    ├── audit_agent.py       # Cross-document consistency checks
    └── templates/           # Audit prompt templates
        └── audit_extraction.md
```

## Agent Overview

### 1. CP Interpreter (`cp_interpreter.py`)

| Property | Value |
|----------|-------|
| Purpose | Extract structured course data from Course Proposals |
| Tools | `Read`, `WebFetch` (conditional) |
| Model | claude-sonnet-4-20250514 |
| Called by | `extract_course_info/extract_course_info.py` |
| Output | JSON with Course_Title, Learning_Units[], K/A statements, Assessment_Methods |

Shared by all generation workflows. Runs as a background job via `agent_runner`.

---

### 2. Slide Generation Pipeline (`slides/`)

5-phase sequential pipeline orchestrated by `generate_slides/multi_agent_orchestrator.py`:

```
Phase 1: Research Agent      → Web research per topic (8 parallel)
    ↓
Phase 2: Content Generator   → Structured content blocks for infographics
    ↓
Phase 3: Editor Agent        → Slide skeleton with AntV template assignments
    ↓
Phase 4: Infographic Agent   → AntV JSON → HTML → PNG (sequential, shared browser)
    ↓
Phase 5: Assembly            → Map PNGs to slide positions → build PPTX
```

#### Phase 1: Research Agent (`slides/research_agent.py`)

| Property | Value |
|----------|-------|
| Purpose | Find 3-5 quality sources per topic via web search |
| Tools | `WebSearch` (2 searches per topic, NO WebFetch) |
| Model | Haiku (fast) |
| Parallelism | 8 concurrent topic researches |
| Output | `research_map[topic]` → sources[], key_statistics[], infographic_data |

#### Phase 2: Content Generator (`slides/content_generator_agent.py`)

| Property | Value |
|----------|-------|
| Purpose | Transform research into structured content blocks (1 block = 1 infographic slide) |
| Tools | `WebSearch` (conditional, only if research < 2 sources) |
| Model | Haiku (fast) |
| Output | `content_map[topic]` → content_blocks[] with sub_title, visualization_type, data{items[]} |

#### Phase 3: Editor Agent (`slides/editor_agent.py`)

| Property | Value |
|----------|-------|
| Purpose | Create slide skeleton mapping content blocks to AntV templates |
| Tools | None |
| Model | Haiku (fast) |
| Output | Skeleton with learning_outcomes[].learning_units[].topics[].infographic_assignments[] |

#### Phase 4: Infographic Agent (`slides/infographic_agent.py`)

| Property | Value |
|----------|-------|
| Purpose | Render AntV Infographic PNGs from content blocks |
| Tools | Playwright (browser automation), AntV Infographic v0.2.15 |
| Model | N/A (deterministic DSL builder) |
| Strategy | ONE shared Chromium browser, sequential rendering, 3s render wait |
| Output | `infographic_map[topic]` → [{image_path, generated, slide_position}] |

Key functions:
- `build_antv_dsl()` — Deterministic JSON builder (no AI)
- `_write_antv_html()` — Generates self-contained HTML with AntV `setOptions() + performRender()`
- `_html_to_png()` — Playwright screenshot with size validation + retry

#### Phase 5: Assembly (`slides/content_generator_agent.py`)

| Property | Value |
|----------|-------|
| Purpose | Map infographic PNGs to slide positions, build final PPTX |
| Tools | None (pure Python) |
| Function | `assemble_final_slides()` |
| Output | `lu_data_map[lu_number]` → topics[] with infographic_slides[{image_path}] |

#### Legacy: Slides Agent (`slides/slides_agent.py`)

| Property | Value |
|----------|-------|
| Purpose | Generate slide content via Claude + WebSearch (used by NotebookLM V1 flow) |
| Tools | `WebSearch`, `WebFetch`, `Read`, `Glob` |
| Functions | `generate_slide_content()`, `extract_slides_text()` |

---

### 3. Assessment Agent (`assessment/assessment_generator.py`)

| Property | Value |
|----------|-------|
| Purpose | Generate WSQ assessment questions from course context |
| Tools | None (all data in prompt) |
| Model | claude-sonnet-4-20250514 |
| Called by | `generate_assessment/assessment_generation.py` |
| Types | SAQ, PP, CS, PRJ, ASGN, OI, DEM, RP, OQ |
| Output | assessment_types[] with questions[] (scenario, question_statement, K/A mapping, answer points) |

---

### 4. Audit Agent (`audit/audit_agent.py`)

| Property | Value |
|----------|-------|
| Purpose | Extract fields from AP/FG/LG/LP for cross-document consistency validation |
| Tools | None (document text in prompt) |
| Model | claude-sonnet-4-20250514 |
| Called by | `courseware_audit/sup_doc.py` |
| Output | tgs_ref_code, course_title, learning_outcomes[], durations, topics[], assessment_methods[] |

---

## Document Generation (Non-Agent)

These use `docxtpl` templates + pure Python, fed by CP Interpreter output:

| Document | Module | Template |
|----------|--------|----------|
| Assessment Plan (AP) | `generate_ap_fg_lg/utils/agentic_AP.py` | `AP_*.docx` |
| Facilitator Guide (FG) | `generate_ap_fg_lg/utils/agentic_FG.py` | `FG_*.docx` |
| Learner Guide (LG) | `generate_ap_fg_lg/utils/agentic_LG.py` | `LG_*.docx` |
| Lesson Plan (LP) | `generate_ap_fg_lg/utils/agentic_LP.py` | `LP_*.docx` (barrier algorithm) |

---

## Configuration

Slide pipeline config: `generate_slides/multi_agent_config.py`

| Setting | Value | Purpose |
|---------|-------|---------|
| SLIDE_TARGETS | 1d:60-100, 2d:130-140, 3d:195-210, 4d:230-250 | Slide count targets |
| MAX_SLIDES_PER_TOPIC | 16 | Cap infographics per topic |
| RESEARCH_MODEL | Haiku | Fast web search |
| CONTENT_MODEL | Haiku | Fast content generation |
| EDITOR_MODEL | Haiku | Fast skeleton generation |

---

## Core Infrastructure

| File | Purpose |
|------|---------|
| `courseware_agents/base.py` | `run_agent()` / `run_agent_json()` — Claude Agent SDK wrappers |
| `utils/agent_runner.py` | Background async job manager for long-running agents |
| `utils/agent_status.py` | Streamlit UI components for agent progress display |
| `generate_slides/multi_agent_orchestrator.py` | 5-phase pipeline coordinator |
| `generate_slides/build_pptx.py` | python-pptx PPTX builder with company branding |
