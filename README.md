# WSQ Courseware Generator with OpenAI Multi Agents

A comprehensive AI-powered courseware generation platform built with **OpenAI Agents SDK** and **Streamlit**. This system uses an **orchestrator-based multi-agent architecture** with **34 AI agents** to automate the creation of educational documents including Course Proposals, Assessment Plans, Learning Guides, Presentation Slides, and more for Workforce Skills Qualification (WSQ) training programs.

### [Live Demo](https://courseware-generator-openai.streamlit.app/)
### [Official Documentation](https://alfredang.github.io/courseware_openai_agents/)

---

## Platform Statistics

| Metric | Count |
|--------|-------|
| AI Agents | 34 |
| Generation Modules | 7 |
| Assessment Types | 9 |
| Courseware Documents | 4 |
| Prompt Templates | 22 (customizable) |
| Skills | 12 |
| Supported LLM Providers | 7+ |
| Available Models (via OpenRouter) | 38+ |

---

## Quick Start

### 1. System Requirements
- **Python 3.11+** (check with `python3 --version`)
- **macOS / Linux / Windows** supported
- **4GB+ RAM** recommended
- **Git** installed
- **uv** installed (modern Python package manager)
- **Node.js** (optional, for MCP servers)

### 2. Download & Setup

**Option A: From Git repository**
```bash
git clone https://github.com/alfredang/courseware_openai_agents.git
cd courseware_openai_agents
uv venv
source .venv/bin/activate          # macOS/Linux
# OR
.venv\Scripts\activate             # Windows
uv pip install -r requirements.txt
```

**Option B: From a folder/ZIP file**
```bash
cd "/path/to/courseware_openai_agents"
uv venv
source .venv/bin/activate          # macOS/Linux
# OR
.venv\Scripts\activate             # Windows
uv pip install -r requirements.txt
```

### 3. Configure API Keys

**Using Settings UI (Recommended)**
1. Run the app: `streamlit run app.py`
2. Go to **Settings** → **API Keys** tab
3. Add your **OpenRouter API Key** (recommended for access to all models) or individual provider keys

**Manual Configuration (Fallback)**

Create `.streamlit/secrets.toml`:
```toml
OPENAI_API_KEY = "sk-your_key_here"
OPENROUTER_API_KEY = "sk-or-your_key_here"
GEMINI_API_KEY = "your-gemini-api-key"
DATABASE_URL = "postgresql://user:password@host/database?sslmode=require"
ADMIN_USERNAME = "admin"
ADMIN_PASSWORD = "your-secure-password"
```

### 4. Run the Application
```bash
streamlit run app.py
```
Open browser to `http://localhost:8501`

### 5. First Use
1. **Set up API Keys**: Go to **Settings** → **API Keys**
2. **Select API Provider**: Choose from OpenRouter, OpenAI, or Gemini in the sidebar
3. **Select Model**: Pick from available models for the selected provider
4. Select a generation module from the sidebar to begin

---

## Key Features

### Core Document Generation (7 Modules)
| Module | Description | Agents Used |
|--------|-------------|-------------|
| **Generate CP** | Course Proposal generation from TSC documents | 10 agents (Extraction Team, Research Team, Validation Team) |
| **Generate Courseware** | Assessment Plan, Facilitator Guide, Learner Guide, Lesson Plan | 4 agents (AP, FG, LG, LP) |
| **Generate Assessment** | 9 assessment types (SAQ, PP, CS, PRJ, ASGN, OI, DEM, RP, OQ) | 9 agents (one per type) |
| **Generate Slides** | Agentic slide generation with Google NotebookLM + internet research | 4 agents + NotebookLM API |
| **Generate Brochure** | Marketing materials with web scraping | 1 agent |
| **Add Assessment to AP** | Integrate assessments into AP annexes | Template-based |
| **Check Documents** | Supporting document validation and entity extraction | Gemini API |

### Skills System
- **12 skill definitions** in `.skills/` folder for AI-powered chatbot guidance
- **Auto-Navigation**: Type commands like `/generate_slides` to navigate to modules
- **Extensible**: Add new skills by creating markdown files

### Model Management
- **7+ API Providers**: OpenRouter, OpenAI, Gemini, Anthropic, DeepSeek, Groq, Grok
- **38+ Models** available via OpenRouter
- **Dynamic Model Selection**: Choose model in sidebar, applied to all modules
- **SQLite Database**: Persistent storage for model configs, API keys, prompt templates
- **Admin Settings UI**: Fetch, enable/disable, set defaults for models

### Prompt Template System
- **22 customizable prompt templates** across 5 categories
- Templates stored in SQLite database and editable via Settings UI
- Categories: Assessment (9), Courseware (6), Course Proposal (2), Brochure (1), Slides (4)

---

## Multi-Agent Architecture

The system uses an **orchestrator-based architecture** powered by the [OpenAI Agents SDK](https://github.com/openai/openai-agents-python). The orchestrator agent coordinates specialized agents via handoffs.

```
                    ┌─────────────────────────┐
                    │   Orchestrator Agent    │
                    │  (User Interaction)     │
                    └───────────┬─────────────┘
                                │ handoffs
        ┌───────────┬───────────┼───────────┬───────────┐
        ▼           ▼           ▼           ▼           ▼
   ┌─────────┐ ┌─────────┐ ┌─────────┐ ┌─────────┐ ┌─────────┐
   │CP Agent │ │Courseware│ │Assessment│ │Brochure │ │Document │
   │         │ │  Agent   │ │  Agent   │ │  Agent  │ │  Agent  │
   └─────────┘ └─────────┘ └─────────┘ └─────────┘ └─────────┘
```

### All 34 Agents

#### Orchestrator Agents (6)
| Agent | File | Purpose |
|-------|------|---------|
| Orchestrator | `courseware_agents/orchestrator.py` | Main coordinator, routes user requests |
| CP Agent | `courseware_agents/cp_agent.py` | Course Proposal generation |
| Courseware Agent | `courseware_agents/courseware_agent.py` | AP/FG/LG/LP generation |
| Assessment Agent | `courseware_agents/assessment_agent.py` | Assessment generation |
| Brochure Agent | `courseware_agents/brochure_agent.py` | Brochure creation |
| Document Agent | `courseware_agents/document_agent.py` | Document verification |

#### Course Proposal Agents (6)
| Agent | File | Purpose |
|-------|------|---------|
| TSC Agent | `generate_cp/agents/openai_tsc_agent.py` | Parse & correct TSC documents |
| Course Info Extractor | `generate_cp/agents/openai_extraction_team.py` | Extract course metadata |
| Learning Outcomes Extractor | `generate_cp/agents/openai_extraction_team.py` | Extract learning outcomes |
| TSC/Topics Extractor | `generate_cp/agents/openai_extraction_team.py` | Extract TSC structure |
| Assessment Methods Extractor | `generate_cp/agents/openai_extraction_team.py` | Extract assessment info |
| Aggregator | `generate_cp/agents/openai_extraction_team.py` | Combine all extracted data |

#### Additional CP Pipeline Agents (4)
| Agent | File | Purpose |
|-------|------|---------|
| Research Team | `generate_cp/agents/openai_research_team.py` | Job role analysis & research |
| Validation Team | `generate_cp/agents/openai_course_validation_team.py` | Validation surveys |
| Justification Agent | `generate_cp/agents/openai_justification_agent.py` | Assessment justifications |
| Excel Agents | `generate_cp/agents/openai_excel_agents.py` | Excel document generation |

#### Assessment Agents (9)
| Agent | File | Assessment Type |
|-------|------|----------------|
| SAQ Agent | `generate_assessment/utils/openai_agentic_SAQ.py` | Short Answer Questions |
| PP Agent | `generate_assessment/utils/openai_agentic_PP.py` | Practical Performance |
| CS Agent | `generate_assessment/utils/openai_agentic_CS.py` | Case Studies |
| PRJ Agent | `generate_assessment/utils/openai_agentic_PRJ.py` | Project Briefs |
| ASGN Agent | `generate_assessment/utils/openai_agentic_ASGN.py` | Written Assignments |
| OI Agent | `generate_assessment/utils/openai_agentic_OI.py` | Oral Interview |
| DEM Agent | `generate_assessment/utils/openai_agentic_DEM.py` | Demonstration |
| RP Agent | `generate_assessment/utils/openai_agentic_RP.py` | Role Play |
| OQ Agent | `generate_assessment/utils/openai_agentic_OQ.py` | Oral Questioning |

#### Courseware Agents (4)
| Agent | File | Document |
|-------|------|----------|
| AP Agent | `generate_ap_fg_lg_lp/utils/agentic_AP.py` | Assessment Plan + Summary Report |
| FG Agent | `generate_ap_fg_lg_lp/utils/agentic_FG.py` | Facilitator Guide |
| LG Agent | `generate_ap_fg_lg_lp/utils/agentic_LG.py` | Learner Guide |
| LP Agent | `generate_ap_fg_lg_lp/utils/agentic_LP.py` | Lesson Plan |

#### Slides Agents (5)
| Agent | File | Purpose |
|-------|------|---------|
| Topic Analysis | `generate_slides/agents/topic_analysis_agent.py` | Extract research-worthy topics from document |
| Source Evaluator | `generate_slides/agents/source_evaluator_agent.py` | Score & filter research sources |
| Slide Instructions | `generate_slides/agents/slide_instructions_agent.py` | Craft optimal generation instructions |
| Quality Validator | `generate_slides/agents/quality_validator_agent.py` | Score slides (1-10) on 5 criteria |
| Orchestrator | `generate_slides/agents/orchestrator.py` | Coordinate 10-step pipeline |

---

## Slides Generation — 3-Layer Architecture

The **Generate Slides** module uses a unique architecture combining a Streamlit UI, AI agents, and Google NotebookLM:

```
┌─────────────────────────────────────────────────────────────┐
│  LAYER 1: STREAMLIT UI                                      │
│  generate_slides/slides_generation.py                       │
│                                                             │
│  - User uploads a document (FG, LG, CP)                     │
│  - Configures options (slides per topic, style, research)    │
│  - Toggles Agentic Mode & Quality Validation                │
│  - Clicks "Generate" → triggers the pipeline                │
└──────────────────────────┬──────────────────────────────────┘
                           │
                           ▼
┌─────────────────────────────────────────────────────────────┐
│  LAYER 2: AI AGENTS (LLM via OpenRouter/Gemini)             │
│  generate_slides/agents/orchestrator.py                     │
│                                                             │
│  Agent 1: Topic Analysis                                    │
│    → Analyzes document, extracts research-worthy topics      │
│                                                             │
│  Agent 2: Source Evaluator                                  │
│    → Scores research sources on relevance & quality          │
│    → Filters out low-quality sources before import           │
│                                                             │
│  Agent 3: Slide Instructions                                │
│    → Crafts optimal instructions tailored to content         │
│                                                             │
│  Agent 4: Quality Validator                                 │
│    → Scores generated slides (1-10) on 5 criteria            │
│    → Triggers adaptive retry if quality is low               │
└──────────────────────────┬──────────────────────────────────┘
                           │
                           ▼
┌─────────────────────────────────────────────────────────────┐
│  LAYER 3: GOOGLE NOTEBOOKLM (No LLM tokens needed)         │
│  notebooklm-py library → Google NotebookLM API              │
│                                                             │
│  - Creates notebook in your Google account                   │
│  - Adds course content as source                            │
│  - Searches the web for latest information on key topics     │
│  - Adds Wikipedia sources for academic references            │
│  - Imports approved research sources                         │
│  - Generates slide deck with all sources                     │
│  - Returns slides in NotebookLM Studio                      │
└─────────────────────────────────────────────────────────────┘
```

**10-Step Agentic Pipeline:**

| Step | Action | Layer |
|------|--------|-------|
| 1 | Analyze document topics with AI | Agent (LLM) |
| 2 | Connect to NotebookLM | NotebookLM |
| 3 | Create notebook | NotebookLM |
| 4 | Upload course content | NotebookLM |
| 5 | Add Wikipedia sources | NotebookLM |
| 6 | Web research + AI source evaluation | NotebookLM + Agent (LLM) |
| 7 | Craft optimal slide instructions | Agent (LLM) |
| 8 | Generate slides | NotebookLM |
| 9 | Wait for completion | NotebookLM |
| 10 | Validate quality + adaptive retry | Agent (LLM) |

**Two Modes:**
- **Agentic Mode** (AI-Enhanced): Uses 4 LLM agents for intelligent topic analysis, source evaluation, instruction crafting, and quality validation. Requires an API key (Gemini 2.0 Flash is free via OpenRouter).
- **Non-Agentic Mode**: NotebookLM handles everything directly. No LLM API tokens needed.

**Internet Research** enriches slides with external sources:
- The slider (1–3 topics) controls how many key topics are researched on the web
- Each topic search can return up to 5 web sources + 1 Wikipedia reference
- Sources are evaluated by the AI Source Evaluator agent before import

---

## Data Flow

### Course Proposal Generation
```
TSC Document (DOCX/PDF)
    → Parse Document
    → TSC Agent (correct & structure)
    → Extraction Team (5 agents: Course Info, Learning Outcomes, TSC/Topics, Assessment Methods, Aggregator)
    → Research Team (job role analysis)
    → Validation Team (validation surveys)
    → Excel Agents (Excel export)
    → Output: CP JSON + CP DOCX + Validation DOCX + Excel files
```

### Courseware Generation
```
Course Proposal (JSON/DOCX)
    → Parse CP data
    → 4 parallel agents:
        ├→ AP Agent → Assessment Plan DOCX + Summary Report
        ├→ FG Agent → Facilitator Guide DOCX
        ├→ LG Agent → Learner Guide DOCX
        └→ LP Agent → Lesson Plan DOCX
    → Apply company branding/logo
    → Output: ZIP with all documents
```

### Assessment Generation
```
Facilitator Guide (DOCX)
    → Parse FG → Extract Learning Units, Topics, K/A Statements
    → Select assessment types (up to 9 types)
    → Per type agent generates questions:
        SAQ | PP | CS | PRJ | ASGN | OI | DEM | RP | OQ
    → Populate DOCX templates
    → Output: Q&A Papers (ZIP)
```

### Slides Generation
```
Course Document (FG, LG, or CP)
    → Extract text
    → Topic Analysis Agent (identify topics + research queries)
    → NotebookLM: Create notebook + upload source (zero tokens)
    → NotebookLM: Add Wikipedia sources (zero tokens)
    → NotebookLM: Web research per topic (zero tokens)
    → Source Evaluator Agent (filter low-quality sources)
    → NotebookLM: Import approved sources (zero tokens)
    → Slide Instructions Agent (craft optimal instructions)
    → NotebookLM: Generate slide deck (zero tokens)
    → Quality Validator Agent (score & adaptive retry)
    → Output: Slides in NotebookLM Studio
```

---

## Project Structure

```
courseware_openai_agents/
├── app.py                          # Main Streamlit application (1,387 lines)
│
├── .skills/                        # Skill definitions (12 markdown files)
│   ├── generate_course_proposal.md
│   ├── generate_assessment_plan.md
│   ├── generate_facilitator_guide.md
│   ├── generate_learner_guide.md
│   ├── generate_lesson_plan.md
│   ├── generate_assessment.md
│   ├── generate_slides.md
│   ├── generate_brochure.md
│   ├── generate_courseware.md
│   ├── add_assessment_to_ap.md
│   ├── check_documents.md
│   └── branding.md
│
├── skills/                         # Skills loader module
│   └── __init__.py                 # Skill parser, keyword matcher, system message builder
│
├── courseware_agents/               # Multi-Agent System (OpenAI Agents SDK)
│   ├── base.py                     # Agent factory & model configuration
│   ├── schemas.py                  # Pydantic schemas for structured outputs
│   ├── mcp_config.py               # MCP server configurations
│   ├── orchestrator.py             # Main orchestrator with handoffs
│   ├── cp_agent.py                 # Course Proposal agent
│   ├── courseware_agent.py         # AP/FG/LG/LP agent
│   ├── assessment_agent.py         # Assessment agent
│   ├── brochure_agent.py           # Brochure agent
│   └── document_agent.py           # Document verification agent
│
├── generate_cp/                    # Course Proposal generation
│   ├── main.py                     # CP orchestration pipeline
│   ├── app.py                      # Streamlit UI
│   ├── cv_main.py                  # Course validation
│   ├── agents/                     # 6 CP-specific agents
│   │   ├── openai_tsc_agent.py
│   │   ├── openai_extraction_team.py
│   │   ├── openai_research_team.py
│   │   ├── openai_course_validation_team.py
│   │   ├── openai_justification_agent.py
│   │   └── openai_excel_agents.py
│   ├── utils/                      # Helpers, parsers, templates
│   ├── models/                     # Pydantic schemas
│   └── schemas/                    # Excel data structures
│
├── generate_assessment/            # Assessment generation (9 types)
│   ├── assessment_generation.py    # Streamlit UI (1,171 lines)
│   └── utils/                      # 9 assessment agents + templates
│       ├── openai_agentic_SAQ.py
│       ├── openai_agentic_PP.py
│       ├── openai_agentic_CS.py
│       ├── openai_agentic_PRJ.py
│       ├── openai_agentic_ASGN.py
│       ├── openai_agentic_OI.py
│       ├── openai_agentic_DEM.py
│       ├── openai_agentic_RP.py
│       ├── openai_agentic_OQ.py
│       └── Templates/             # DOCX templates for Q&A papers
│
├── generate_ap_fg_lg_lp/          # Courseware suite generation
│   ├── courseware_generation.py    # Streamlit UI (1,071 lines)
│   └── utils/                      # 4 courseware agents + helpers
│       ├── agentic_AP.py
│       ├── agentic_FG.py
│       ├── agentic_LG.py
│       ├── agentic_LP.py
│       ├── helper.py
│       ├── organization_utils.py
│       └── timetable_generator.py
│
├── generate_slides/                # Slide generation (Agentic + NotebookLM)
│   ├── slides_generation.py        # Streamlit UI + NotebookLM pipeline (1,078 lines)
│   └── agents/                     # 5 slides agents
│       ├── orchestrator.py         # 10-step agentic pipeline coordinator
│       ├── topic_analysis_agent.py
│       ├── source_evaluator_agent.py
│       ├── slide_instructions_agent.py
│       └── quality_validator_agent.py
│
├── generate_brochure/              # Marketing brochure generation
│   ├── brochure_generation.py      # Streamlit UI + scraping (2,150 lines)
│   └── brochure_template/          # HTML/CSS templates
│
├── add_assessment_to_ap/           # Assessment integration into AP
│   └── annex_assessment_v2.py
│
├── check_documents/                # Document validation
│   ├── sup_doc.py                  # Validation UI
│   ├── gemini_processor.py         # Gemini-based entity extraction
│   └── acra_call.py                # ACRA company registry lookup
│
├── settings/                       # Configuration & admin
│   ├── settings.py                 # Settings UI (API Keys, Models, Templates)
│   ├── api_manager.py              # API key management
│   ├── api_database.py             # SQLite database (models, keys, templates)
│   ├── admin_auth.py               # Admin authentication
│   └── model_configs.py            # Model configuration presets
│
├── company/                        # Company/organization management
│   ├── company_settings.py         # Company management UI
│   ├── company_manager.py          # Branding & selection
│   ├── database.py                 # PostgreSQL storage
│   └── logo/                       # Company logos
│
├── utils/                          # Shared utilities
│   ├── prompt_loader.py            # Load prompt templates from DB/files
│   ├── helpers.py                  # Common helpers
│   └── prompt_templates/           # 22 markdown prompt templates
│       ├── assessment/             # 9 templates (SAQ, PP, CS, PRJ, ASGN, OI, DEM, RP, OQ)
│       ├── courseware/             # 6 templates (AP, FG, LG, LP, timetable, CP interpretation)
│       ├── course_proposal/        # 2 templates (CP interpretation, TSC agent)
│       ├── brochure/               # 1 template
│       └── slides/                 # 4 templates (topic analysis, source evaluation, instructions, quality)
│
├── docs/                           # Documentation site
│   ├── index.html                  # Landing page
│   └── content/                    # 6 markdown pages
│       ├── introduction.md
│       ├── getting-started.md
│       ├── core-features.md
│       ├── agent-architecture.md
│       ├── usage-guide.md
│       └── troubleshooting.md
│
├── notebooklm-mcp/                # NotebookLM MCP server + login scripts
├── requirements.txt                # Python dependencies (24 packages)
└── pyproject.toml                  # Project metadata
```

---

## AI Assistant & Skills System

### AI Assistant
Every page includes an **AI Assistant** at the bottom that provides contextual help. The assistant is skill-driven and can answer questions, navigate you to modules, and provide step-by-step guidance.

### Skill Commands

| Command | Action |
|---------|--------|
| `/generate_course_proposal` | Navigate to Course Proposal generation |
| `/generate_assessment_plan` | Navigate to Assessment Plan generation |
| `/generate_facilitator_guide` | Navigate to Facilitator Guide generation |
| `/generate_learner_guide` | Navigate to Learner Guide generation |
| `/generate_lesson_plan` | Navigate to Lesson Plan generation |
| `/generate_assessment` | Navigate to Assessment generation |
| `/generate_slides` | Navigate to Slides generation |
| `/generate_brochure` | Navigate to Brochure generation |
| `/generate_courseware` | Navigate to full Courseware Suite |
| `/add_assessment_to_ap` | Navigate to Assessment Integration |
| `/check_documents` | Navigate to Document Validation |
| `/branding` | Navigate to Company Branding settings |

### Adding New Skills
Create a markdown file in `.skills/` folder with this structure:
```markdown
# Skill Name

## Command
`/skill_command`

## Navigate
Page Name (must match sidebar menu)

## Description
Brief description of what this skill does.

## Response
Message shown when skill command is invoked.

## Instructions
Detailed instructions for the AI to follow...

## Capabilities
- Capability 1
- Capability 2
```

---

## Usage Guide

### 1. Generate Course Proposal
1. Upload TSC (Training Specification Content) document
2. Select AI model
3. Choose CP type (Excel CP or Legacy DOCX)
4. Process and download generated documents

### 2. Generate Assessment Documents
1. Upload Facilitator Guide
2. Select assessment types (SAQ, PP, CS, PRJ, ASGN, OI, DEM, RP, OQ)
3. Generate and download Q&A papers as ZIP

### 3. Generate Courseware Suite
1. Upload Course Proposal document
2. Select required documents (AP/FG/LG/LP)
3. Configure organization details
4. Generate complete courseware package

### 4. Generate Presentation Slides
1. Upload course materials (FG, LG, or CP)
2. Configure slide options (slides per topic, speaker notes, style)
3. Enable **AI-Enhanced (Agentic) Mode** for intelligent topic analysis and quality validation
4. Enable **Internet Research** to enrich slides with web sources and Wikipedia references
5. Generate slides — opens directly in NotebookLM Studio

**Agentic Mode** uses 4 AI agents:
- **Topic Analysis Agent** — Extracts research-worthy topics from your document
- **Source Evaluator Agent** — Filters research sources by relevance and quality
- **Slide Instructions Agent** — Crafts optimal instructions tailored to your content
- **Quality Validator Agent** — Scores generated slides and triggers adaptive retry if needed

**Setup Required**: See [NotebookLM Setup](#notebooklm-setup-for-slides-generation) below.

### 5. Generate Brochure
1. Upload course materials or enter course URL
2. Configure brochure details (course topics, entry requirements, certification)
3. Generate HTML brochure with company branding
4. Download as HTML or PDF

### 6. Add Assessment to AP
1. Upload Assessment Plan (DOCX)
2. Upload assessment Q&A papers
3. Integrate assessments into AP annexes
4. Download updated AP

### 7. Check Documents
1. Upload supporting documents
2. Run entity extraction (names, addresses, dates)
3. Validate company information via ACRA lookup
4. Review compliance results

---

## Configuration

### API Provider & Model Management

#### Supported API Providers
| Provider | Description | Key |
|----------|-------------|-----|
| **OpenRouter** | Unified gateway to 38+ models | `OPENROUTER_API_KEY` |
| **OpenAI** | Native OpenAI models (GPT-4o, etc.) | `OPENAI_API_KEY` |
| **Gemini** | Google Gemini models | `GEMINI_API_KEY` |
| **DeepSeek** | DeepSeek models | Via OpenRouter |
| **Anthropic** | Claude models | Via OpenRouter |
| **Groq** | Fast inference | `GROQ_API_KEY` |
| **Grok** | xAI models | Via OpenRouter |

#### Available Models via OpenRouter
| Provider | Models |
|----------|--------|
| **OpenAI** | GPT-4o, GPT-4o-Mini, GPT-4-Turbo, o1, o1-mini, o3-mini |
| **Anthropic** | Claude Opus 4.5, Claude Sonnet 4, Claude 3.5 Sonnet |
| **Google** | Gemini 2.5 Pro/Flash, Gemini 2.0 Flash |
| **DeepSeek** | DeepSeek-Chat, DeepSeek-R1 |
| **Meta** | Llama 3.3 70B, Llama 3.1 405B |
| **Qwen** | Qwen 2.5 72B, QwQ 32B |
| **Mistral** | Mistral Large, Codestral |

#### Recommended Models
- **DeepSeek-Chat**: Best performance/cost ratio (recommended default)
- **GPT-4o-Mini**: Fast and cost-effective for simple tasks
- **Claude Sonnet 4**: Excellent for complex reasoning
- **Gemini 2.0 Flash**: Very fast, free tier available via OpenRouter

#### Admin Model Management (Settings → LLM Models)
| Feature | Description |
|---------|-------------|
| **Set Default** | Mark a model as default for the selected API provider |
| **Enable/Disable** | Show/hide models in the selection dropdown |
| **Fetch Models** | Retrieve latest available models from the provider API |
| **Add Models** | Manually add new model configurations |
| **Delete Models** | Remove unused model configurations |

### Prompt Template Management
All 22 prompt templates are stored in SQLite and can be customized via **Settings → Prompt Templates**:
- View, edit, and restore built-in templates
- Create custom templates for specific use cases
- Templates use `{variable}` placeholders for dynamic substitution

### Document Templates
| Module | Template Location |
|--------|-------------------|
| Course Proposal | `generate_cp/templates/` |
| Courseware | `generate_ap_fg_lg_lp/input/Template/` |
| Assessment | `generate_assessment/utils/Templates/` |
| Brochure | `generate_brochure/brochure_template/` |

### Company Data Storage
Company/organization data is stored in **PostgreSQL** (Neon recommended):
- Managed via Settings → Companies
- Supports multi-company branding with logos
- Requires `DATABASE_URL` in environment or Streamlit secrets

---

## MCP (Model Context Protocol) Support

The system supports MCP servers for standardized tool integration:

| Server | Purpose | Use Case |
|--------|---------|----------|
| **Filesystem** | Document read/write | Reading TSC documents, writing courseware |
| **PostgreSQL** | Company database access | Training records, company data |
| **SQLite** | API configuration access | Model config, API key metadata |
| **Fetch** | Web scraping | Course info scraping for brochures |
| **Memory** | Persistent agent memory | Cross-session knowledge retention |

MCP servers require **Node.js** (optional feature).

---

## TSC Document Requirements

For optimal Course Proposal generation, ensure TSC documents follow these conventions:

**Learning Unit Format:**
```
LU1: Introduction to Data Analytics (K1, K2, A1)
```

**Topic Format:**
```
Topic 1: Data Collection Methods (K1, A1)
```

**Key Requirements:**
- Include colon (`:`) after LU/Topic labels
- Use proper Knowledge (K) and Ability (A) factor notation
- Ensure LUs appear before their associated topics

---

## NotebookLM Setup (For Slides Generation)

The **Generate Slides** module uses Google NotebookLM to create AI-powered slide decks. This requires a one-time login per user.

### Step 1: Install NotebookLM Library
```bash
pip install notebooklm-py[browser]
```

### Step 2: Run the Login Script
```bash
python notebooklm-mcp/login_windows.py
```
This opens a Chromium browser window and navigates to NotebookLM.

### Step 3: Sign In with Your Google Account
1. Complete the Google login in the browser window
2. Wait until you see the NotebookLM homepage
3. Press **Enter** in the terminal to save your session

Your session is saved locally at `~/.notebooklm/storage_state.json`. This file is **not** pushed to GitHub — each user logs in on their own machine.

### Important Notes
- **Any Google account** works (personal or workspace Gmail)
- Login only needs to be done **once** per machine
- If your session expires, run the login script again
- **Non-agentic mode**: No LLM API tokens needed (NotebookLM handles everything)
- **Agentic mode**: Requires an OpenRouter or Gemini API key in Settings (Gemini 2.0 Flash is free)

---

## Dependencies

### Core Framework
| Package | Purpose |
|---------|---------|
| `streamlit` >= 1.30.0 | Web UI framework |
| `openai` >= 1.12.0 | OpenAI SDK |
| `openai-agents` >= 0.0.7 | Agent orchestration framework |

### Document Processing
| Package | Purpose |
|---------|---------|
| `python-docx` | Word document creation |
| `docxtpl` | Jinja2 DOCX templates |
| `docxcompose` | Compose multiple DOCX files |
| `PyPDF2` | PDF reading |
| `openpyxl` | Excel file handling |
| `jinja2` | Template rendering |

### Data & Web
| Package | Purpose |
|---------|---------|
| `pydantic` >= 2.0.0 | Data validation |
| `pandas` | Data manipulation |
| `beautifulsoup4` | Web scraping |
| `lxml` | XML processing |
| `rapidfuzz` | Fuzzy string matching |
| `requests` | HTTP requests |

### Google Integration
| Package | Purpose |
|---------|---------|
| `google-api-python-client` | Google API |
| `google-auth-httplib2` | Authentication |
| `google-auth-oauthlib` | OAuth 2.0 |
| `gspread` | Google Sheets |

### Database & Auth
| Package | Purpose |
|---------|---------|
| `psycopg2-binary` | PostgreSQL |
| `python-dotenv` | Environment variables |
| `Pillow` | Image processing |

---

## Troubleshooting

### Import Errors
- Ensure all dependencies: `uv pip install -r requirements.txt`
- Check Python version: 3.11+ required
- Verify virtual environment is activated

### API Key Issues
- Use **Settings → API Keys** to manage keys
- Verify key validity and quotas with your provider
- For OpenRouter: one key gives access to 38+ models

### Model Selection Issues
- If no models appear, use **Settings → LLM Models → Fetch Models**
- Check that models are enabled (not disabled)
- Verify a default model is set

### NotebookLM Issues
- **Authentication expired**: Re-run `python notebooklm-mcp/login_windows.py`
- **Daily limit reached**: NotebookLM has Google-imposed daily usage limits; wait until the next day
- **Sources not importing**: Ensure internet research is enabled in slide configuration

### Document Processing Errors
- Ensure uploaded documents follow TSC formatting requirements
- Check file formats (DOCX for most uploads)

---

## Security Notes

- Never commit API keys to version control
- Use Streamlit secrets management for production
- Regularly rotate API keys
- Monitor API usage and costs
- NotebookLM sessions are stored locally and never committed to Git
- Admin authentication required for Settings access

---

## Contributing

1. Fork the repository
2. Create a feature branch: `git checkout -b feature-name`
3. Make your changes following the existing code style
4. Test thoroughly with sample documents
5. Submit a pull request

---

## License

This project is proprietary software developed for Tertiary Infotech. All rights reserved.

---

## Support

For technical support or questions:
- Check the troubleshooting section above
- Review the [GitHub repository issues](https://github.com/alfredang/courseware_openai_agents/issues)
- Contact the development team
