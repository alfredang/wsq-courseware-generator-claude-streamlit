# WSQ Courseware Generator — Multi-Agent Framework

## Overview

This platform uses **Claude AI agents** to automate WSQ courseware creation. A user uploads a **Course Proposal (CP)**, and the system generates all required training materials automatically.

All agents share a common base wrapper: `courseware_agents/base.py` → `run_agent()` / `run_agent_json()` using **Claude Agent SDK**.

```
                         ┌─────────────────────────┐
                         │   Course Proposal (CP)   │
                         └────────────┬────────────┘
                                      │
                              ┌───────▼───────┐
                              │ CP Interpreter │  Claude Sonnet
                              │    (Agent)     │
                              └───────┬───────┘
                                      │
                       Structured Course Data (JSON)
                                      │
          ┌───────────────┬───────────┼───────────┬──────────────┐
          │               │           │           │              │
          ▼               ▼           ▼           ▼              ▼
    ┌───────────┐  ┌───────────┐ ┌────────┐ ┌──────────┐ ┌───────────┐
    │ Courseware │  │  Lesson   │ │ Slides │ │Assessment│ │   Audit   │
    │  AP/FG/LG │  │   Plan    │ │Pipeline│ │Generator │ │   Agent   │
    │(Templates)│  │(Algorithm)│ │(4 AI)  │ │ (Agent)  │ │  (Agent)  │
    └───────────┘  └───────────┘ └────────┘ └──────────┘ └───────────┘
```

---

## 1. CP Interpreter Agent

> Reads the Course Proposal and extracts structured course data (title, topics, learning outcomes, K/A statements, hours, assessment methods).

```
courseware_agents/cp_interpreter/
├── cp_interpreter.py              # Main agent
└── templates/
    └── cp_interpretation.md       # System prompt
```

| Property | Value |
|----------|-------|
| **Model** | Claude Sonnet 4 |
| **Tools** | `Read`, `WebFetch` (if course URL provided) |
| **Input** | Parsed CP text file |
| **Output** | JSON: Course_Title, Learning_Units[], K/A statements, Assessment_Methods_Details[] |
| **Skill** | `/generate_courseware`, `/generate_assessment_plan`, `/generate_facilitator_guide`, `/generate_learner_guide` |

---

## 2. Courseware Document Generation (AP / FG / LG)

> Fills DOCX templates with CP data to produce courseware documents. **No AI agents** — pure Python template filling using `docxtpl` (Jinja2).

```
courseware_agents/courseware/
├── assessment_plan.py             # AP sub-agent (template filler)
├── facilitator_guide.py           # FG sub-agent (template filler)
├── learner_guide.py               # LG sub-agent (template filler)
└── templates/
    ├── AP_TGS-Ref-No_Course-Title_v1.docx
    ├── ASR_TGS-Ref-No_Course-Title_v1.docx
    ├── FG_TGS-Ref-No_Course-Title_v1.docx
    └── LG_TGS-Ref-No_Course-Title_v1.docx
```

| Property | Value |
|----------|-------|
| **Model** | N/A (pure Python) |
| **Tools** | N/A |
| **Skill** | `/generate_courseware` |

### Sub-Agents

#### AP Agent — Assessment Plan
| Property | Value |
|----------|-------|
| **File** | `courseware/assessment_plan.py` |
| **Function** | `generate_assessment_documents()` |
| **Template** | `AP_TGS-Ref-No_Course-Title_v1.docx`, `ASR_TGS-Ref-No_Course-Title_v1.docx` |
| **Output** | AP DOCX + ASR DOCX |
| **Skill** | `/generate_assessment_plan` |

#### FG Agent — Facilitator Guide
| Property | Value |
|----------|-------|
| **File** | `courseware/facilitator_guide.py` |
| **Function** | `generate_facilitators_guide()` |
| **Template** | `FG_TGS-Ref-No_Course-Title_v1.docx` |
| **Output** | FG DOCX |
| **Skill** | `/generate_facilitator_guide` |

#### LG Agent — Learner Guide
| Property | Value |
|----------|-------|
| **File** | `courseware/learner_guide.py` |
| **Function** | `generate_learning_guide()` |
| **Template** | `LG_TGS-Ref-No_Course-Title_v1.docx` |
| **Output** | LG DOCX |
| **Skill** | `/generate_learner_guide` |

---

## 3. Lesson Plan (LP)

> Builds a timetable schedule using a barrier algorithm (9am–6pm, lunch 12:30–1:15pm, assessment on last day) and fills the LP template. **No AI agent** — pure Python.

```
courseware_agents/lesson_plan/
├── lesson_plan.py                 # Barrier algorithm + template filler
└── templates/
    └── LP_TGS-Ref-No_Course-Title_v1.docx
```

| Property | Value |
|----------|-------|
| **Model** | N/A (pure Python) |
| **Tools** | N/A |
| **Function** | `generate_lesson_plan()` |
| **Template** | `LP_TGS-Ref-No_Course-Title_v1.docx` |
| **Output** | LP DOCX |
| **Skill** | `/generate_lesson_plan` |

---

## 4. Generate Slides — Multi-Agent Pipeline

> A **4-agent pipeline** that generates a PowerPoint deck with infographic image slides. This is the only true multi-agent feature in the project.

```
Research Agent → Content Generator → Editor Agent → Infographic Agent → Assembly (Python)
```

```
courseware_agents/slides/
├── research_agent.py              # Phase 1: Web research
├── content_generator_agent.py     # Phase 2: Content blocks
├── editor_agent.py                # Phase 3: Slide skeleton
├── infographic_agent.py           # Phase 4: AntV → PNG
├── slides_agent.py                # Legacy (NotebookLM V1)
└── templates/
    ├── slide_template.pptx        # Master PPTX template
    ├── infographic.min.js         # AntV JS library (inlined)
    ├── topic_analysis.md
    ├── source_evaluation.md
    ├── slide_instructions.md
    ├── quality_validation.md
    ├── infographic-item-creator_item-prompt.md
    ├── infographic-structure-creator_structure-prompt.md
    └── infographic-syntax-creator_prompt.md
```

**Configuration:** `generate_slides/multi_agent_config.py`
**PPTX Builder:** `generate_slides/build_pptx.py`
**Skill:** `/generate_slides`

**Slide Count Targets:** 1-day: 100 | 2-day: 160 | 3-day: 210 | 4-day: 250 | 5-day: 320

### Phase 1: Research Agent

> Searches the web for 3–5 quality sources per topic. Tags infographic-ready data (charts, processes, comparisons).

| Property | Value |
|----------|-------|
| **File** | `slides/research_agent.py` |
| **Model** | Claude Haiku 3.5 |
| **Tools** | `WebSearch` (2 searches per topic, no WebFetch) |
| **Max Turns** | 5 |
| **Parallelism** | 8 concurrent topic researches |
| **Output** | JSON: sources[], key_statistics[], infographic_data |

### Phase 2: Content Generator Agent

> Transforms research into structured content blocks. Each block = 1 infographic slide.

| Property | Value |
|----------|-------|
| **File** | `slides/content_generator_agent.py` |
| **Model** | Claude Haiku 3.5 |
| **Tools** | `WebSearch` (conditional — only if research has < 2 sources) |
| **Max Turns** | 5 |
| **Output** | JSON array of blocks: {visualization_type, title, items[{label, desc, icon, value}]} |
| **Viz Types** | overview, process, comparison, cycle, hierarchy, statistics, timeline, relationship, quadrant |

### Phase 3: Editor Agent

> Creates the slide skeleton — maps content blocks to AntV template types and adds WSQ standard slides (cover, section headers, activity slides, closing).

| Property | Value |
|----------|-------|
| **File** | `slides/editor_agent.py` |
| **Model** | Claude Haiku 3.5 |
| **Tools** | None |
| **Max Turns** | 3 |
| **Output** | JSON: {slides[], infographic_assignments{}} |
| **Standard Slides** | 10 opening + 7 closing + per-topic section headers + activity slides |

### Phase 4: Infographic Agent

> Generates AntV Infographic DSL from content blocks, renders to HTML, screenshots to PNG using Playwright browser.

| Property | Value |
|----------|-------|
| **File** | `slides/infographic_agent.py` |
| **Model** | Claude Haiku 3.5 (AI-first) + deterministic fallback |
| **Tools** | Playwright Chromium (browser automation) |
| **Max Turns** | 2 |
| **Rendering** | 3 retries per infographic (5s/8s/12s), browser restart between topics |
| **Canvas** | 1792 x 1024 px |
| **AntV JS** | Inlined from `templates/infographic.min.js` (no CDN) |
| **Output** | PNG images (1 per content block) |

### Phase 5: Assembly (No AI)

> Maps infographic PNG images to slide positions, enforces slide count targets, builds final editable PPTX.

| Property | Value |
|----------|-------|
| **File** | `generate_slides/build_pptx.py` |
| **Model** | N/A (pure Python) |
| **Tools** | N/A |
| **Library** | python-pptx |
| **Output** | Editable PPTX file |
| **Enforcement** | Padding slides added if content count < target |

---

## 5. Assessment Generation

> Generates WSQ assessment questions (9 types) from course context data.

```
courseware_agents/assessment/
├── assessment_generator.py        # Main agent
└── templates/
    ├── saq_generation.md          # Short Answer Questions
    ├── case_study.md              # Case Study
    ├── practical_performance.md   # Practical Performance
    ├── project.md                 # Project
    ├── assignment.md              # Assignment
    ├── demonstration.md           # Demonstration
    ├── oral_interview.md          # Oral Interview
    ├── oral_questioning.md        # Oral Questioning
    └── role_play.md               # Role Play
```

| Property | Value |
|----------|-------|
| **Model** | Claude Sonnet 4 |
| **Tools** | None (all data passed in prompt) |
| **Function** | `generate_assessments()` |
| **Question Types** | SAQ, PP, CS, PRJ, ASGN, OI, DEM, RP, OQ |
| **Output** | JSON: assessment_types[] with questions[] (scenario, question, K/A mapping, answer) |
| **Skill** | `/generate_assessment` |

---

## 6. Courseware Audit

> Extracts fields from uploaded courseware documents (AP, FG, LG, LP) and cross-checks them against the CP for consistency.

```
courseware_agents/audit/
├── audit_agent.py                 # Main agent
└── templates/
    └── audit_extraction.md        # System prompt + audit check items (single source of truth)
```

| Property | Value |
|----------|-------|
| **Model** | Claude Sonnet 4 |
| **Tools** | None (document text passed in prompt) |
| **Function** | `extract_audit_fields()` |
| **Check Items** | Course Title, TGS Ref, Topics, Training Hours, Assessment Hours, Company Name, UEN, Learning Outcomes, K/A Statements, Assessment Methods, Instructional Methods, TSC Code/Title |
| **Output** | Per-document checklist: green tick (match) / red X (mismatch) / N/A (not applicable) |
| **Skill** | `/courseware_audit` |

---

## Model Usage Summary

| Agent | Model | Reason |
|-------|-------|--------|
| CP Interpreter | Sonnet 4 | Complex JSON extraction from structured documents |
| AP / FG / LG | N/A | Pure Python template filling |
| Lesson Plan (LP) | N/A | Pure Python barrier algorithm |
| Research Agent | Haiku 3.5 | Fast web search |
| Content Generator | Haiku 3.5 | Fast structured JSON generation |
| Editor Agent | Haiku 3.5 | Fast slide skeleton generation |
| Infographic Agent | Haiku 3.5 | Fast DSL generation |
| PPTX Builder | N/A | Pure Python (python-pptx) |
| Assessment Generator | Sonnet 4 | Complex question generation |
| Audit Agent | Sonnet 4 | Multi-field extraction |

## Tool Usage Summary

| Agent | Tools |
|-------|-------|
| CP Interpreter | `Read`, `WebFetch` (optional) |
| Research Agent | `WebSearch` |
| Content Generator | `WebSearch` (conditional) |
| Editor Agent | None |
| Infographic Agent | Playwright browser |
| Assessment Generator | None |
| Audit Agent | None |

---

## Core Infrastructure

| File | Purpose |
|------|---------|
| `courseware_agents/base.py` | `run_agent()` / `run_agent_json()` — Claude Agent SDK wrappers |
| `utils/agent_runner.py` | Background async job manager for long-running agents |
| `utils/agent_status.py` | Streamlit UI components for agent progress display |
| `generate_slides/multi_agent_orchestrator.py` | 5-phase slide pipeline coordinator |
| `generate_slides/multi_agent_config.py` | Slide pipeline configuration (models, targets, limits) |
| `generate_slides/build_pptx.py` | PPTX builder with company branding |
