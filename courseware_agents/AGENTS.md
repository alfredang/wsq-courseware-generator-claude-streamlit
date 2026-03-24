# WSQ Courseware Generator — Multi-Agent Framework

## Overview

This platform uses **Claude AI agents** to automate WSQ courseware creation. A user uploads a **Course Proposal (CP)**, and the system generates all required training materials automatically.

All agents share a common base wrapper: `courseware_agents/base.py` → `run_agent()` / `run_agent_json()` using **Claude Agent SDK**.

---

## System Architecture

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
          ┌───────────┬───────────┬───┴───┬───────────┬──────────┐
          ▼           ▼           ▼       ▼           ▼          ▼
    ┌──────────┐ ┌─────────┐ ┌──────┐ ┌──────┐ ┌──────────┐ ┌───────┐
    │ AP / ASR │ │   FG    │ │  LG  │ │  LP  │ │  Slides  │ │ Audit │
    │(Template)│ │(Template│ │(Tmpl)│ │(Tmpl)│ │(4-Agent) │ │(Agent)│
    └──────────┘ └─────────┘ └──────┘ └──────┘ └──────────┘ └───────┘
      No AI        No AI      No AI    No AI    Claude Haiku  Sonnet
```

---

## Agent Details

### 1. CP Interpreter Agent

> **Purpose:** Extracts structured course data from raw Course Proposal documents

| Property | Value |
|----------|-------|
| **File** | `courseware_agents/cp_interpreter/cp_interpreter.py` |
| **Model** | Claude Sonnet 4 (`claude-sonnet-4-20250514`) |
| **Tools** | `Read`, `WebFetch` (if course URL provided) |
| **Max Turns** | 3 (or 5 with WebFetch) |
| **Template** | `cp_interpreter/templates/cp_interpretation.md` |
| **Input** | Raw CP document (DOCX/XLSX → parsed to markdown) |
| **Output** | Structured JSON (course title, LUs, topics, K/A statements, assessment methods) |

---

### 2. Courseware Document Generators (AP / FG / LG)

> **Purpose:** Fill DOCX templates with CP data — **NO AI involved**

| Document | File | Template |
|----------|------|----------|
| **Assessment Plan (AP)** | `courseware/assessment_plan.py` | `courseware/templates/AP_TGS-Ref-No_Course-Title_v1.docx` |
| **Assessment Summary (ASR)** | `courseware/assessment_plan.py` | `courseware/templates/ASR_TGS-Ref-No_Course-Title_v1.docx` |
| **Facilitator Guide (FG)** | `courseware/facilitator_guide.py` | `courseware/templates/FG_TGS-Ref-No_Course-Title_v1.docx` |
| **Learner Guide (LG)** | `courseware/learner_guide.py` | `courseware/templates/LG_TGS-Ref-No_Course-Title_v1.docx` |

- **Technology:** `docxtpl` (Jinja2 syntax for DOCX)
- **Model:** None — pure Python template filling
- **Input:** Structured JSON from CP Interpreter
- **Output:** Completed DOCX files

---

### 3. Lesson Plan Generator (LP)

> **Purpose:** Generates timetable schedule using barrier algorithm — **NO AI involved**

| Property | Value |
|----------|-------|
| **File** | `lesson_plan/lesson_plan.py` |
| **Model** | None — pure Python |
| **Template** | `lesson_plan/templates/LP_TGS-Ref-No_Course-Title_v1.docx` |
| **Algorithm** | Barrier-based timetable scheduler |

**Schedule Rules:**
- Daily hours: 9:00 AM - 6:00 PM
- Lunch: 12:30 PM - 1:15 PM (45 mins)
- Assessment: 4:00 PM - 6:00 PM (last day only)
- Topics split across barriers with "(Cont'd)" labels

---

### 4. Assessment Generator Agent

> **Purpose:** Generates assessment questions for multiple assessment types

| Property | Value |
|----------|-------|
| **File** | `assessment/assessment_generator.py` |
| **Model** | Claude Sonnet 4 (`claude-sonnet-4-20250514`) |
| **Tools** | None (all data provided in prompt) |
| **Max Turns** | 5 |
| **Input** | FG data + K/A statements + course context |
| **Output** | JSON with questions per assessment type |

**Supported Assessment Types:**
SAQ, PP, CS, PRJ, ASGN, OI, DEM, RP, OQ

---

### 5. Slide Generation Pipeline (4 Agents + Assembly)

> **Purpose:** Generates a full PowerPoint deck with infographic slides

This is the **multi-agent pipeline** — 4 agents working sequentially, each passing output to the next.

```
┌──────────────┐    ┌───────────────────┐    ┌──────────────┐    ┌─────────────────┐    ┌──────────┐
│   Phase 1    │    │     Phase 2       │    │   Phase 3    │    │    Phase 4      │    │ Phase 5  │
│   Research   │───▶│ Content Generator │───▶│    Editor    │───▶│  Infographic    │───▶│ Assembly │
│    Agent     │    │      Agent        │    │    Agent     │    │     Agent       │    │ (Python) │
│  (Haiku)     │    │    (Haiku)        │    │   (Haiku)    │    │ (Haiku+Playwrt) │    │  No AI   │
└──────────────┘    └───────────────────┘    └──────────────┘    └─────────────────┘    └──────────┘
```

#### Phase 1: Research Agent

| Property | Value |
|----------|-------|
| **File** | `slides/research_agent.py` |
| **Model** | Claude Haiku 3.5 (`claude-3-5-haiku-20241022`) |
| **Tools** | `WebSearch` |
| **Max Turns** | 5 |
| **Input** | Topic title + bullet points |
| **Output** | Sources, key statistics, infographic-ready data |

- Performs exactly 2 WebSearch calls per topic
- Tags data for visualization: chart_data, process_steps, comparison_items, timeline_data

#### Phase 2: Content Generator Agent

| Property | Value |
|----------|-------|
| **File** | `slides/content_generator_agent.py` |
| **Model** | Claude Haiku 3.5 |
| **Tools** | `WebSearch` (supplementary only) |
| **Max Turns** | 5 |
| **Default Blocks** | 6 per topic |
| **Input** | Research data |
| **Output** | Structured content blocks with visualization types |

- Each block has: title, description, items[], visualization_type
- Visualization types: overview, process, comparison, cycle, hierarchy, statistics, timeline, relationship, quadrant

#### Phase 3: Editor Agent

| Property | Value |
|----------|-------|
| **File** | `slides/editor_agent.py` |
| **Model** | Claude Haiku 3.5 |
| **Tools** | None |
| **Max Turns** | 3 |
| **Input** | Content blocks |
| **Output** | Complete deck skeleton with template assignments |

- Maps content blocks to slide positions
- Assigns AntV infographic templates per block
- Ensures visual variety across the deck

#### Phase 4: Infographic Agent

| Property | Value |
|----------|-------|
| **File** | `slides/infographic_agent.py` |
| **Model** | Claude Haiku 3.5 |
| **Tools** | None |
| **Max Turns** | 2 |
| **Input** | Content block + template name |
| **Output** | PNG image file |

- Generates AntV DSL (with deterministic fallback)
- Renders DSL → HTML → PNG via Playwright browser
- AntV script is **inlined** (no CDN) from `slides/templates/infographic.min.js`
- 3 retries per infographic (5s/8s/12s timeouts)
- Browser restarted between topics to prevent memory exhaustion
- 65+ AntV templates available across 9 visualization types

#### Phase 5: Assembly (No AI)

- Pure Python — maps PNG images to slide positions
- Builds final PPTX using `python-pptx`
- Enforces slide count targets with padding slides

**Slide Count Targets:**

| Duration | Target Slides |
|----------|--------------|
| 1-day | 100 |
| 2-day | 160 |
| 3-day | 210 |
| 4-day | 250 |
| 5-day | 320 |

---

### 6. Audit Agent

> **Purpose:** Extracts fields from courseware documents for cross-checking against CP

| Property | Value |
|----------|-------|
| **File** | `audit/audit_agent.py` |
| **Model** | Claude Sonnet 4 (`claude-sonnet-4-20250514`) |
| **Tools** | None (text-only) |
| **Max Turns** | 5 |
| **Template** | `audit/templates/audit_extraction.md` (single source of truth) |
| **Input** | Document text + document type |
| **Output** | JSON with extracted fields |

**Audit Check Fields:**
course_title, tgs_ref_code, topics, training_hours, assessment_hours, company_name, uen, learning_outcomes, k_statements, a_statements, assessment_methods, instructional_methods, tsc_code, tsc_title

---

## Models Summary

| Model | ID | Used By |
|-------|------|---------|
| **Claude Sonnet 4** | `claude-sonnet-4-20250514` | CP Interpreter, Assessment Generator, Audit Agent |
| **Claude Haiku 3.5** | `claude-3-5-haiku-20241022` | All 4 Slide Pipeline Agents |
| **No AI** | — | AP, FG, LG, LP (template filling only) |

---

## Base Infrastructure

**File:** `courseware_agents/base.py`

| Function | Returns | Description |
|----------|---------|-------------|
| `run_agent()` | `str` | Run Claude Agent SDK, return text |
| `run_agent_json()` | `dict` | Run agent, parse result as JSON |

- Permission mode: `bypassPermissions`
- Default tools: `["Read", "Glob", "Grep"]`
- Default max turns: 30

---

## File Structure

```
courseware_agents/
├── base.py                              # Core agent wrapper (run_agent, run_agent_json)
├── __init__.py                          # Package exports
├── AGENTS.md                            # This file
│
├── cp_interpreter/                      # CP Interpreter Agent
│   ├── cp_interpreter.py                #   Main agent (Sonnet 4)
│   ├── agent/
│   │   ├── skills.md                    #   Agent skills documentation
│   │   └── tools.md                     #   Agent tools documentation
│   └── templates/
│       ├── cp_interpretation.md         #   System prompt
│       └── tsc_agent.md                 #   TSC extraction prompt
│
├── courseware/                           # Document Generators (No AI)
│   ├── assessment_plan.py               #   AP + ASR generator
│   ├── facilitator_guide.py             #   FG generator
│   ├── learner_guide.py                 #   LG generator
│   ├── ap_agent/
│   │   ├── skills.md                    #   AP agent skills
│   │   └── tools.md                     #   AP agent tools
│   ├── fg_agent/
│   │   ├── skills.md                    #   FG agent skills
│   │   └── tools.md                     #   FG agent tools
│   ├── lg_agent/
│   │   ├── skills.md                    #   LG agent skills
│   │   └── tools.md                     #   LG agent tools
│   └── templates/
│       ├── AP_TGS-Ref-No_Course-Title_v1.docx
│       ├── ASR_TGS-Ref-No_Course-Title_v1.docx
│       ├── FG_TGS-Ref-No_Course-Title_v1.docx
│       └── LG_TGS-Ref-No_Course-Title_v1.docx
│
├── lesson_plan/                         # Lesson Plan Generator (No AI)
│   ├── lesson_plan.py                   #   Barrier algorithm + template fill
│   ├── lp_agent/
│   │   ├── skills.md                    #   LP agent skills
│   │   └── tools.md                     #   LP agent tools
│   └── templates/
│       └── LP_TGS-Ref-No_Course-Title_v1.docx
│
├── assessment/                          # Assessment Generator Agent
│   ├── assessment_generator.py          #   Main agent (Sonnet 4)
│   ├── agent/
│   │   ├── skills.md                    #   Assessment agent skills
│   │   └── tools.md                     #   Assessment agent tools
│   └── templates/                       #   Assessment prompt templates
│
├── audit/                               # Audit Agent
│   ├── audit_agent.py                   #   Main agent (Sonnet 4)
│   ├── agent/
│   │   ├── skills.md                    #   Audit agent skills
│   │   └── tools.md                     #   Audit agent tools
│   └── templates/
│       └── audit_extraction.md          #   Single source of truth for audit rules
│
└── slides/                              # Slide Pipeline (4 Agents)
    ├── research_agent.py                #   Phase 1: Research (Haiku)
    ├── content_generator_agent.py       #   Phase 2: Content Gen (Haiku)
    ├── editor_agent.py                  #   Phase 3: Editor (Haiku)
    ├── infographic_agent.py             #   Phase 4: Infographic (Haiku + Playwright)
    ├── slides_agent.py                  #   Legacy agent
    ├── research_agent/
    │   ├── skills.md                    #   Research agent skills
    │   └── tools.md                     #   Research agent tools
    ├── content_agent/
    │   ├── skills.md                    #   Content generator skills
    │   └── tools.md                     #   Content generator tools
    ├── editor_agent/
    │   ├── skills.md                    #   Editor agent skills
    │   └── tools.md                     #   Editor agent tools
    ├── infographic_agent/
    │   ├── skills.md                    #   Infographic agent skills
    │   └── tools.md                     #   Infographic agent tools
    └── templates/
        └── infographic.min.js           #   AntV script (inlined, not CDN)
```
