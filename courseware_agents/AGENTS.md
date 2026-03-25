# WSQ Courseware Generator — Multi-Agent Framework

## How It Works

A user uploads a **Course Proposal (CP)** → the system generates all required WSQ training materials automatically using **Claude AI agents**.

All agents use the same base wrapper: `courseware_agents/base.py` → `run_agent()` / `run_agent_json()` via **Claude Agent SDK**.

---

## System Flow

```
                      ┌──────────────────────┐
                      │  Course Proposal (CP) │
                      └──────────┬───────────┘
                                 │
                                 ▼
                      ┌──────────────────────┐
                      │   CP Interpreter      │  ← Claude Sonnet
                      │   (AI Agent)          │
                      └──────────┬───────────┘
                                 │
                      Structured JSON Output
                                 │
       ┌────────┬────────┬───────┼───────┬────────┬────────┐
       ▼        ▼        ▼       ▼       ▼        ▼        ▼
      AP       FG       LG      LP    Slides   Assess.   Audit
   (Template)(Template)(Template)(Algo) (4 AI)  (AI)     (AI)
```

---

## Features & Their Agents

### 1. Extract Course Info — CP Interpreter Agent

| | |
|---|---|
| **What it does** | Reads the CP document and extracts all course data into structured JSON |
| **Agent file** | `cp_interpreter/cp_interpreter.py` |
| **AI Model** | Claude Sonnet 4 |
| **Tools** | Read, WebFetch |
| **Prompt template** | `cp_interpreter/templates/cp_interpretation.md` |
| **Input** | Raw CP document (DOCX or XLSX) |
| **Output** | JSON — course title, learning units, topics, K/A statements, assessment methods, hours |

---

### 2. Generate AP/FG/LG — Courseware Agents (No AI)

These agents fill DOCX templates with the CP data. **No AI is used** — it's pure Python template filling using `docxtpl`.

#### AP Agent (Assessment Plan)
| | |
|---|---|
| **Agent file** | `courseware/assessment_plan.py` |
| **Template** | `courseware/templates/AP_TGS-Ref-No_Course-Title_v1.docx` |
| **Skills** | `courseware/ap_agent/skills.md` |
| **Tools** | `courseware/ap_agent/tools.md` |

#### FG Agent (Facilitator Guide)
| | |
|---|---|
| **Agent file** | `courseware/facilitator_guide.py` |
| **Template** | `courseware/templates/FG_TGS-Ref-No_Course-Title_v1.docx` |
| **Skills** | `courseware/fg_agent/skills.md` |
| **Tools** | `courseware/fg_agent/tools.md` |

#### LG Agent (Learner Guide)
| | |
|---|---|
| **Agent file** | `courseware/learner_guide.py` |
| **Template** | `courseware/templates/LG_TGS-Ref-No_Course-Title_v1.docx` |
| **Skills** | `courseware/lg_agent/skills.md` |
| **Tools** | `courseware/lg_agent/tools.md` |

#### ASR (Assessment Summary Record)
| | |
|---|---|
| **Agent file** | `courseware/assessment_plan.py` (same as AP) |
| **Template** | `courseware/templates/ASR_TGS-Ref-No_Course-Title_v1.docx` |

---

### 3. Generate Lesson Plan — LP Agent (No AI)

| | |
|---|---|
| **What it does** | Builds a timetable schedule using a barrier algorithm |
| **Agent file** | `lesson_plan/lesson_plan.py` |
| **AI Model** | None — pure Python |
| **Template** | `lesson_plan/templates/LP_TGS-Ref-No_Course-Title_v1.docx` |
| **Skills** | `lesson_plan/lp_agent/skills.md` |
| **Tools** | `lesson_plan/lp_agent/tools.md` |

**Schedule Rules:**
- 9:00 AM – 6:00 PM daily
- Lunch: 12:30 PM – 1:15 PM (45 mins)
- Assessment: 4:00 PM – 6:00 PM (last day only)
- Topics split across barriers with "(Cont'd)" labels

---

### 4. Generate Assessment — Assessment Agent

| | |
|---|---|
| **What it does** | Generates assessment questions for each assessment type |
| **Agent file** | `assessment/assessment_generator.py` |
| **AI Model** | Claude Sonnet 4 |
| **Tools** | None (all data in prompt) |
| **Skills** | `assessment/agent/skills.md` |
| **Tools doc** | `assessment/agent/tools.md` |
| **Input** | FG data + K/A statements + course context |
| **Output** | JSON with questions per assessment type |

**Supported types:** WA-SAQ, PP, CS, OQ, OI, DEM, RP, PRJ, ASGN

---

### 5. Generate Slides — 4-Agent Pipeline

This is the **multi-agent pipeline** — 4 agents work sequentially, each passing output to the next.

```
  Research Agent  →  Content Agent  →  Editor Agent  →  Infographic Agent  →  Assembly
    (Haiku)           (Haiku)           (Haiku)        (Haiku + Playwright)   (Python)
```

#### Research Agent (Phase 1)
| | |
|---|---|
| **What it does** | Searches the web for sources and data per topic |
| **Agent file** | `slides/research_agent.py` |
| **AI Model** | Claude Haiku 3.5 |
| **Tools** | WebSearch (2 searches per topic) |
| **Skills** | `slides/research_agent/skills.md` |
| **Tools doc** | `slides/research_agent/tools.md` |
| **Output** | Sources, statistics, infographic-ready data |

#### Content Generator Agent (Phase 2)
| | |
|---|---|
| **What it does** | Transforms research into structured content blocks |
| **Agent file** | `slides/content_generator_agent.py` |
| **AI Model** | Claude Haiku 3.5 |
| **Tools** | WebSearch (supplementary) |
| **Skills** | `slides/content_agent/skills.md` |
| **Tools doc** | `slides/content_agent/tools.md` |
| **Output** | Content blocks with title, description, items, visualization type |

#### Editor Agent (Phase 3)
| | |
|---|---|
| **What it does** | Creates slide skeleton with template assignments |
| **Agent file** | `slides/editor_agent.py` |
| **AI Model** | Claude Haiku 3.5 |
| **Tools** | None |
| **Skills** | `slides/editor_agent/skills.md` |
| **Tools doc** | `slides/editor_agent/tools.md` |
| **Output** | Complete deck skeleton with AntV template assignments |

#### Infographic Agent (Phase 4)
| | |
|---|---|
| **What it does** | Renders content blocks into PNG infographic images |
| **Agent file** | `slides/infographic_agent.py` |
| **AI Model** | Claude Haiku 3.5 |
| **Tools** | None (uses Playwright browser for rendering) |
| **Skills** | `slides/infographic_agent/skills.md` |
| **Tools doc** | `slides/infographic_agent/tools.md` |
| **Output** | PNG image files |

**Key details:**
- AntV script inlined from `slides/templates/infographic.min.js` (no CDN)
- 3 retries per infographic (5s / 8s / 12s timeouts)
- Browser restarted between topics to prevent memory issues
- 65+ AntV templates across 9 visualization types

#### Assembly (Phase 5 — No AI)
- Builds final PPTX using `python-pptx`
- Maps PNG images to slide positions
- Enforces slide count targets with padding slides

**Slide Targets:**
| Course Duration | Target Slides |
|----------------|---------------|
| 1-day | 100 |
| 2-day | 160 |
| 3-day | 210 |
| 4-day | 250 |
| 5-day | 320 |

---

### 6. Courseware Audit — Audit Agent

| | |
|---|---|
| **What it does** | Extracts fields from courseware documents and cross-checks against CP |
| **Agent file** | `audit/audit_agent.py` |
| **AI Model** | Claude Sonnet 4 |
| **Tools** | None (text-only extraction) |
| **Skills** | `audit/agent/skills.md` |
| **Tools doc** | `audit/agent/tools.md` |
| **Rules file** | `audit/templates/audit_extraction.md` (single source of truth) |
| **Input** | Document text + document type |
| **Output** | JSON with extracted fields for comparison |

**Fields checked:** Course Title, TGS Ref No, Topics, Training Hours, Assessment Hours, Company Name, UEN, Learning Outcomes, K Statements, A Statements, Assessment Methods, Instructional Methods, TSC Code, TSC Title

---

### 7. Convert Documents — Conversion Agents

Three sub-agents for converting existing documents into standardised WSQ format.

#### Convert Assessment Agent
| | |
|---|---|
| **What it does** | Extracts questions from existing assessments and rebuilds in WSQ format |
| **Agent file** | `convert_assessment/convert_assessment.py` |
| **AI Model** | Claude Sonnet 4 |
| **Skills** | `convert/assessment_agent/skills.md` |
| **Tools doc** | `convert/assessment_agent/tools.md` |

#### Convert Courseware Agent
| | |
|---|---|
| **What it does** | Extracts data from existing AP/FG/LG/ASR and fills WSQ templates |
| **Agent file** | `convert_assessment/convert_assessment.py` |
| **AI Model** | Claude Sonnet 4 |
| **Skills** | `convert/courseware_agent/skills.md` |
| **Tools doc** | `convert/courseware_agent/tools.md` |

#### Convert Lesson Plan Agent
| | |
|---|---|
| **What it does** | Extracts schedule from existing LP and fills WSQ LP template |
| **Agent file** | `convert_assessment/convert_assessment.py` |
| **AI Model** | Claude Sonnet 4 |
| **Skills** | `convert/lesson_plan_agent/skills.md` |
| **Tools doc** | `convert/lesson_plan_agent/tools.md` |

---

## AI Models Used

| Model | ID | Where Used |
|-------|-----|------------|
| **Claude Sonnet 4** | `claude-sonnet-4-20250514` | CP Interpreter, Assessment, Audit, Convert Agents |
| **Claude Haiku 3.5** | `claude-3-5-haiku-20241022` | All 4 Slide Pipeline Agents |
| **No AI** | — | AP, FG, LG, LP, ASR (template filling only) |

---

## Folder Structure

```
courseware_agents/
├── base.py                                    # Core wrapper (run_agent, run_agent_json)
├── __init__.py                                # Package exports
├── AGENTS.md                                  # This file
│
├── cp_interpreter/                            # Feature: Extract Course Info
│   ├── cp_interpreter.py                      #   Agent (Sonnet)
│   ├── agent/
│   │   ├── skills.md
│   │   └── tools.md
│   └── templates/
│       ├── cp_interpretation.md
│       └── tsc_agent.md
│
├── courseware/                                 # Feature: Generate AP/FG/LG
│   ├── assessment_plan.py                     #   AP + ASR generator
│   ├── facilitator_guide.py                   #   FG generator
│   ├── learner_guide.py                       #   LG generator
│   ├── ap_agent/
│   │   ├── skills.md
│   │   └── tools.md
│   ├── fg_agent/
│   │   ├── skills.md
│   │   └── tools.md
│   ├── lg_agent/
│   │   ├── skills.md
│   │   └── tools.md
│   └── templates/
│       ├── AP_TGS-Ref-No_Course-Title_v1.docx
│       ├── ASR_TGS-Ref-No_Course-Title_v1.docx
│       ├── FG_TGS-Ref-No_Course-Title_v1.docx
│       └── LG_TGS-Ref-No_Course-Title_v1.docx
│
├── lesson_plan/                               # Feature: Generate Lesson Plan
│   ├── lesson_plan.py                         #   Barrier algorithm + template fill
│   ├── lp_agent/
│   │   ├── skills.md
│   │   └── tools.md
│   └── templates/
│       └── LP_TGS-Ref-No_Course-Title_v1.docx
│
├── assessment/                                # Feature: Generate Assessment
│   ├── assessment_generator.py                #   Agent (Sonnet)
│   ├── agent/
│   │   ├── skills.md
│   │   └── tools.md
│   └── templates/                             #   Prompt templates per type
│       ├── saq_generation.md
│       ├── practical_performance.md
│       ├── case_study.md
│       └── ... (9 assessment types)
│
├── audit/                                     # Feature: Courseware Audit
│   ├── audit_agent.py                         #   Agent (Sonnet)
│   ├── agent/
│   │   ├── skills.md
│   │   └── tools.md
│   └── templates/
│       └── audit_extraction.md                #   Single source of truth
│
├── convert/                                   # Feature: Convert Documents
│   ├── assessment_agent/
│   │   ├── skills.md
│   │   └── tools.md
│   ├── courseware_agent/
│   │   ├── skills.md
│   │   └── tools.md
│   └── lesson_plan_agent/
│       ├── skills.md
│       └── tools.md
│
└── slides/                                    # Feature: Generate Slides (4-Agent Pipeline)
    ├── research_agent.py                      #   Phase 1: Research (Haiku)
    ├── content_generator_agent.py             #   Phase 2: Content (Haiku)
    ├── editor_agent.py                        #   Phase 3: Editor (Haiku)
    ├── infographic_agent.py                   #   Phase 4: Infographic (Haiku + Playwright)
    ├── research_agent/
    │   ├── skills.md
    │   └── tools.md
    ├── content_agent/
    │   ├── skills.md
    │   └── tools.md
    ├── editor_agent/
    │   ├── skills.md
    │   └── tools.md
    ├── infographic_agent/
    │   ├── skills.md
    │   └── tools.md
    └── templates/
        └── infographic.min.js                 #   AntV script (inlined)
```
