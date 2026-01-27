# WSQ Courseware Generator with OpenAI Multi Agents

A comprehensive AI-powered courseware generation platform built with **OpenAI Agents SDK** and Streamlit. This system uses an **orchestrator-based multi-agent architecture** to automate the creation of educational documents including Course Proposals, Assessment Plans, Learning Guides, and more for workforce skills qualification (WSQ) training programs.

### 🔴 [Live Demo](https://courseware-generator-openai.streamlit.app/)
### 📖 [Official Documentation](https://alfredang.github.io/courseware_openai_agents/)

## 🚀 Quick Start for New Users

### 1. System Requirements
- **Python 3.11+** (Check with `python3 --version`)
- **macOS/Linux/Windows** supported
- **4GB+ RAM** recommended
- **Git** installed
- **uv** installed (modern Python package manager)

### 2. Download & Setup

**Option A: If you received a folder/ZIP file:**
```bash
# 1. Navigate to the downloaded project folder
cd "/path/to/courseware_openai_agents"

# 2. Initialize project with uv
uv venv
source .venv/bin/activate          # macOS/Linux
# OR
.venv\Scripts\activate             # Windows

# 3. Install dependencies (Fast)
uv pip install -r requirements.txt
```

**Option B: If downloading from Git repository:**
```bash
# 1. Clone the repository
git clone https://github.com/alfredang/courseware_openai_agents.git
cd courseware_openai_agents

# 2. Setup with uv
uv venv
source .venv/bin/activate          # macOS/Linux
uv pip install -r requirements.txt
```

### 3. Configure API Keys

**Using Settings UI (Recommended)**
1. Run the app: `streamlit run app.py`
2. Go to **Settings** → **API Keys** tab
3. Add your **OpenRouter API Key** (recommended for access to all models) or individual provider keys.

**Manual Configuration (Fallback)**
Create `.streamlit/secrets.toml`:
```toml
# API Keys - Use Settings UI instead (recommended)
OPENAI_API_KEY = "sk-your_key_here"
OPENROUTER_API_KEY = "sk-or-your_key_here"
GEMINI_API_KEY = "your-gemini-api-key"

# Database (Neon PostgreSQL for company data)
DATABASE_URL = "postgresql://user:password@host/database?sslmode=require"

# Admin Authentication (for Settings access)
ADMIN_USERNAME = "admin"
ADMIN_PASSWORD = "your-secure-password"
```

### 4. Run the Application
```bash
streamlit run app.py
```

### 5. First Use
1. Open browser to `http://localhost:8501`
2. **Set up API Keys**: Go to **Settings** → **API Keys**
3. **Select API Provider**: Choose from OpenRouter, OpenAI, or Gemini in the sidebar
4. **Select Model**: Pick from available models for the selected provider
5. Select **"Generate CP"** from sidebar
6. Upload a TSC document to test

### 💡 Model Selection & Management
The application features a flexible model management system:

- **API Provider Selection**: Choose from OpenRouter (38+ models), OpenAI (native), or Gemini
- **Dynamic Model Loading**: Models are loaded from the database based on the selected provider
- **Default Models**: Admin can set default models per provider (⭐ button in Settings)
- **Model Fetching**: Admin can fetch latest models from providers via Settings
- **Enable/Disable Models**: Admin can show/hide models from the selection dropdown

**Recommended Models:**
- **DeepSeek-Chat** (OpenRouter): Best overall performance/cost ratio
- **GPT-4o-Mini** (OpenRouter/OpenAI): Fast and cost-effective
- **Claude-3.5-Sonnet** (OpenRouter): Excellent for complex reasoning
- **Gemini-Flash** (Gemini): Very fast processing

## 🚀 Key Features

### Core Document Generation
- **Course Proposal (CP)** - Automated course proposal generation with multi-agent validation
- **Assessment Documents** - Question & Answer papers (SAQ, CS, PP formats)
- **Courseware Suite** - Assessment Plan, Learning Guide, Lesson Plan, Facilitator Guide
- **Presentation Slides** - AI-powered slide generation using NotebookLM MCP
- **Course Brochures** - Marketing materials with web scraping automation
- **Document Integration** - Assessment integration into AP annexes
- **Document Verification** - Supporting document validation and entity extraction

### Skills System
- **Skill-Driven AI Assistant** - Chatbot that uses skill definitions to provide contextual guidance
- **Auto-Navigation** - Type skill commands (e.g., `/generate_slides`) to navigate to modules
- **Extensible Skills** - Add new skills by creating markdown files in `.skills/` folder
- **Built-in Commands**: `/generate_course_proposal`, `/generate_assessment_plan`, `/generate_facilitator_guide`, `/generate_learner_guide`, `/generate_lesson_plan`, `/generate_assessment`, `/generate_slides`

### Model Management System
- **Multi-Provider Support** - OpenRouter (38+ models), OpenAI (native), and Gemini
- **Dynamic Model Selection** - Choose models from sidebar, applied to all generation modules
- **Default Model Configuration** - Admin can set default model per API provider
- **Model Fetching** - Fetch latest models from provider APIs
- **Enable/Disable Models** - Control which models appear in the selection dropdown
- **SQLite Database** - Persistent storage for model configurations and preferences

### Advanced AI Architecture
- **Orchestrator Agent** - Central coordinator that interacts with users and delegates to specialized agents
- **Multi-Agent Handoffs** - Seamless workflow transitions between specialized agents
- **Model Flexibility** - Support for 38+ models (DeepSeek, OpenAI, Anthropic, Google) via OpenRouter
- **Dynamic Model Selection** - Select model in sidebar, automatically applied to courseware generation
- **Content Intelligence** - Context-aware content generation with memory
- **Quality Assurance** - Multi-layer validation and error correction

## 🤖 Multi-Agent Architecture

The system uses an **orchestrator-based architecture** powered by the [OpenAI Agents SDK](https://github.com/openai/openai-agents-python). The orchestrator agent coordinates specialized agents via handoffs:

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

### Agent Descriptions

| Agent | Purpose | Default Model |
|-------|---------|---------------|
| **Orchestrator** | User interaction, task routing, workflow coordination | GPT-4o |
| **CP Agent** | Course Proposal generation from TSC documents | DeepSeek-Chat |
| **Courseware Agent** | Assessment Plan, Facilitator Guide, Learner Guide, Lesson Plan | DeepSeek-Chat |
| **Assessment Agent** | SAQ, Practical Performance, Case Study generation | DeepSeek-Chat |
| **Brochure Agent** | Marketing brochure creation with web scraping | GPT-4o-Mini |
| **Document Agent** | Supporting document verification and entity extraction | GPT-4o-Mini |

### How It Works

1. **User chats** with the Orchestrator on the homepage
2. **Orchestrator analyzes** the request and identifies the appropriate specialized agent
3. **Handoff occurs** - control transfers to the specialized agent with context
4. **Specialized agent** executes using its tools (document parsing, AI generation, web scraping)
5. **Results returned** to user through the orchestrator

### Key Features

- **Natural Language Interface**: Chat with the orchestrator to generate any document
- **Automatic Agent Selection**: The orchestrator routes requests to the right agent
- **Tool-Equipped Agents**: Each agent has specialized function tools
- **Configurable Models**: Change models per agent via Settings UI
- **OpenRouter Integration**: Unified access to 38+ models from multiple providers

### Agent Tools

Each agent is equipped with specialized function tools:

**CP Agent Tools:**
- `parse_tsc_document` - Parse TSC DOCX files
- `run_extraction_pipeline` - Extract course info, learning outcomes
- `run_research_pipeline` - Job role analysis
- `generate_cp_document` - Create final Word document

**Courseware Agent Tools:**
- `generate_assessment_plan` - Create AP document
- `generate_facilitator_guide` - Create FG document
- `generate_learner_guide` - Create LG document
- `generate_lesson_plan` - Create LP document
- `generate_timetable` - Create course schedule

**Assessment Agent Tools:**
- `generate_saq_questions` - Short Answer Questions
- `generate_practical_performance` - PP assessments
- `generate_case_study` - Case study scenarios
- `parse_facilitator_guide` - Extract FG structure

**Brochure Agent Tools:**
- `scrape_course_info` - Web scrape course details
- `generate_brochure_html` - Create HTML brochure
- `generate_brochure_pdf` - Convert to PDF
- `generate_marketing_content` - AI-enhanced copy

**Document Agent Tools:**
- `extract_document_entities` - Entity extraction
- `verify_company_uen` - UEN validation
- `check_document_completeness` - Completeness check

### MCP (Model Context Protocol) Support

The system supports **MCP servers** for standardized tool integration, enabling agents to access external data sources and services through a unified protocol.

#### Available MCP Servers

| Server | Purpose | Use Case |
|--------|---------|----------|
| **Filesystem** | Document read/write operations | Reading TSC documents, writing generated courseware |
| **PostgreSQL** | Company database access | Training records verification, company data |
| **SQLite** | API configuration access | Model configuration, API key metadata |
| **Fetch** | Web scraping operations | Course info scraping for brochures |
| **Memory** | Persistent agent memory | Cross-session knowledge retention |

#### Usage Example

```python
from courseware_agents import mcp_context, COURSEWARE_MCP_CONFIG
from courseware_agents.orchestrator import create_orchestrator_with_mcp
from agents import Runner

async def run_with_mcp():
    # Initialize MCP servers with context manager
    async with mcp_context(**COURSEWARE_MCP_CONFIG) as servers:
        # Create orchestrator with MCP support
        orchestrator = create_orchestrator_with_mcp(mcp_servers=servers)

        # Run the agent
        result = await Runner.run(orchestrator, "Generate courseware")
        print(result.final_output)
```

#### Predefined Configurations

- **COURSEWARE_MCP_CONFIG**: General courseware generation (filesystem + fetch)
- **DOCUMENT_AGENT_MCP_CONFIG**: Document verification (filesystem + postgres)
- **BROCHURE_AGENT_MCP_CONFIG**: Brochure generation (filesystem + fetch)

#### Requirements for MCP

MCP servers require Node.js/npm for the official MCP server implementations:
```bash
# Install Node.js (required for MCP servers)
# macOS
brew install node

# Or using nvm
curl -o- https://raw.githubusercontent.com/nvm-sh/nvm/v0.39.0/install.sh | bash
nvm install node
```

## 📋 Prerequisites

- Python 3.11+
- Streamlit account (for deployment)
- **OpenRouter API Key** (recommended - single key for 38+ models)
- Or **OpenAI API Key** (for native OpenAI models only)

### Key Dependencies
- `openai-agents` - OpenAI Agents SDK for multi-agent orchestration
- `openai` - OpenAI Python client (used with OpenRouter)
- `streamlit` - Web UI framework
- `python-docx` - Word document generation
- `jinja2` - Template rendering

## 🛠 Installation

### Recommended Method (UV)

1. **Install UV (if not installed):**
   ```bash
   curl -LsSf https://astral.sh/uv/install.sh | sh
   ```
   *Windows users: `powershell -c "irm https://astral.sh/uv/install.ps1 | iex"`*

2. **Clone and Setup:**
   ```bash
   git clone https://github.com/alfredang/courseware_openai_agents.git
   cd courseware_openai_agents
   uv venv
   source .venv/bin/activate
   uv pip install -r requirements.txt
   ```

### Legacy Method (pip)

1. **Clone the repository:**
   ```bash
   git clone https://github.com/alfredang/courseware_openai_agents.git
   cd courseware_openai_agents
   ```

2. **Create virtual environment:**
   ```bash
   python -m venv venv
   source venv/bin/activate
   pip install -r requirements.txt
   ```

## 🚀 Quick Start

### Local Development
```bash
streamlit run app.py
```

### Streamlit Cloud Deployment
1. Push your code to GitHub
2. Connect to [Streamlit Cloud](https://streamlit.io/cloud)
3. Add your secrets in the Streamlit Cloud dashboard
4. Deploy your app

## 📁 Project Structure

```
courseware_openai_agents/
├── app.py                      # Main Streamlit application with AI assistant
├── .skills/                    # 🎯 Skill definitions (markdown files)
│   ├── generate_course_proposal.md  # CP skill with instructions
│   ├── generate_assessment_plan.md  # Assessment Plan skill
│   ├── generate_facilitator_guide.md # Facilitator Guide skill
│   ├── generate_learner_guide.md    # Learner Guide skill
│   ├── generate_lesson_plan.md      # Lesson Plan skill
│   ├── generate_assessment.md       # Assessment skill
│   ├── generate_slides.md           # Slides skill (NotebookLM MCP)
│   └── branding.md                  # Branding guidelines
├── skills/                     # Skills loader module
│   └── __init__.py            # Parse skill files, extract commands
├── courseware_agents/          # 🤖 Multi-Agent System (OpenAI Agents SDK)
│   ├── __init__.py            # Package exports
│   ├── base.py                # Agent factory & OpenRouter configuration
│   ├── schemas.py             # Pydantic schemas for structured outputs
│   ├── mcp_config.py          # MCP server configurations
│   ├── orchestrator.py        # Main orchestrator with handoffs to all agents
│   ├── cp_agent.py            # Course Proposal generation agent
│   ├── courseware_agent.py    # AP/FG/LG/LP generation agent
│   ├── assessment_agent.py    # SAQ/PP/Case Study generation agent
│   ├── brochure_agent.py      # Marketing brochure agent
│   └── document_agent.py      # Document verification agent
├── settings/                   # API and model configuration
│   ├── settings.py            # API Keys & LLM Models UI (Admin)
│   ├── api_manager.py         # API key management (SQLite storage)
│   ├── api_database.py        # Model database operations (SQLite)
│   └── model_configs.py       # AI model configurations (38+ models)
├── company/                    # Company/organization management
│   ├── company_settings.py    # Company management UI
│   ├── company_manager.py     # Company selection & branding utilities
│   ├── database.py            # Neon PostgreSQL database operations
│   └── logo/                  # Company logos storage
├── utils/                      # Shared utilities
│   ├── helpers.py             # Common helper functions (parse_json, etc.)
│   ├── prompt_loader.py       # AI prompt loading utilities
│   └── prompts/               # AI prompt templates
├── generate_cp/               # Course Proposal generation
│   ├── app.py                 # Streamlit interface
│   ├── agents/                # Legacy multi-agent implementations
│   └── utils/                 # CP-specific utilities
├── generate_assessment/       # Assessment generation (SAQ, CS, PP)
│   ├── assessment_generation.py
│   └── utils/                 # Assessment utilities & templates
├── generate_ap_fg_lg_lp/      # Courseware document generation
│   ├── courseware_generation.py  # AP, FG, LG, LP generation
│   └── utils/                 # Document generators, templates & organizations
├── generate_slides/           # 🆕 Presentation slide generation
│   └── slides_generation.py   # NotebookLM MCP integration
├── generate_brochure/         # Marketing brochure generation
│   ├── brochure_generation.py
│   └── brochure_template/     # HTML brochure templates
├── add_assessment_to_ap/      # Assessment integration into AP
│   └── annex_assessment_v2.py # Annex assessment tools
├── check_documents/           # Supporting document tools
│   └── sup_doc.py            # Document verification & extraction
└── requirements.txt           # Python dependencies
```

## 💬 AI Assistant & Skills System

### AI Assistant
Every page includes an **AI Assistant** at the bottom that provides contextual help for WSQ courseware tasks. The assistant is skill-driven and can:
- Answer questions about document generation
- Navigate you to the right module
- Provide step-by-step guidance based on skill instructions

### Skill Commands
Type these commands in the AI Assistant to navigate and get help:

| Command | Action |
|---------|--------|
| `/generate_course_proposal` | Navigate to Course Proposal generation |
| `/generate_assessment_plan` | Navigate to Assessment Plan generation |
| `/generate_facilitator_guide` | Navigate to Facilitator Guide generation |
| `/generate_learner_guide` | Navigate to Learner Guide generation |
| `/generate_lesson_plan` | Navigate to Lesson Plan generation |
| `/generate_assessment` | Navigate to Assessment generation |
| `/generate_slides` | Navigate to Slides generation |

### Adding New Skills
Create a markdown file in `.skills/` folder with this structure:

```markdown
# Skill Name

## Command
`/skill_command` or `skill_command`

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

## 💡 Usage Guide

### Chat with the Orchestrator (Recommended)
The homepage features a **chat interface** powered by the Orchestrator Agent. Simply describe what you need:

```
"I want to generate a Course Proposal from my TSC document"
"Create assessment materials for my course"
"Generate a marketing brochure"
"Verify my supporting documents"
```

The orchestrator will automatically route your request to the appropriate specialized agent.

### 1. Generate Course Proposal
1. Upload TSC (Training Specification Content) document
2. Select AI model (GPT-4o-Mini recommended)
3. Choose CP type (Excel CP or Legacy DOCX)
4. Process and download generated documents

### 2. Generate Assessment Documents
1. Upload Facilitator Guide and Slide Deck
2. Select assessment types (SAQ/CS/PP)
3. Generate and download question-answer sets

### 3. Generate Courseware Suite
1. Upload Course Proposal document
2. Select required documents (AP/FG/LG/LP)
3. Configure organization details
4. Generate complete courseware package

### 4. Generate Presentation Slides
1. Upload course materials (FG, LG, or CP)
2. Configure slide options (slides per topic, speaker notes)
3. Generate slides using NotebookLM MCP
4. Download in PowerPoint, PDF, or Google Slides format

**Note**: Requires NotebookLM MCP server configuration. See [notebooklm-mcp](https://github.com/alfredang/notebooklm-mcp) for setup.

### 5. Additional Features
- **Brochure Generation**: Automated marketing material creation
- **Document Verification**: Entity extraction and validation
- **Assessment Integration**: Merge assessments into AP documents

## 🔧 Configuration

### API Provider & Model Management

The application supports multiple AI providers with dynamic model selection:

#### Supported API Providers
| Provider | Description | Key Configuration |
|----------|-------------|-------------------|
| **OpenRouter** | Unified gateway to 38+ models from various providers | `OPENROUTER_API_KEY` |
| **OpenAI** | Native OpenAI models (GPT-4o, GPT-4-Turbo, etc.) | `OPENAI_API_KEY` |
| **Gemini** | Google's Gemini models | `GEMINI_API_KEY` |

#### Model Selection Workflow
1. **Select API Provider** in the sidebar (defaults to OpenRouter)
2. **Choose Model** from the dropdown (shows enabled models for that provider)
3. **Generate Documents** - selected model is applied to all generation modules

#### Admin Model Management (Settings → LLM Models)
| Feature | Description |
|---------|-------------|
| **Set Default (⭐)** | Mark a model as default for the selected API provider |
| **Enable/Disable** | Show/hide models in the selection dropdown |
| **Fetch Models** | Retrieve latest available models from the provider's API |
| **Add Models** | Manually add new model configurations |
| **Delete Models** | Remove unused model configurations |

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

### Recommended Models
- **DeepSeek-Chat**: Best performance/cost ratio (recommended default)
- **GPT-4o-Mini**: Fast and cost-effective for simple tasks
- **Claude Sonnet 4**: Excellent for complex reasoning
- **Gemini 2.5 Flash**: Very fast, good for bulk operations

### Document Templates
All document templates are located in respective module directories:
- Course Proposal: `generate_cp/templates/`
- Courseware: `generate_ap_fg_lg_lp/input/Template/`
- Assessment: `generate_assessment/utils/Templates/`
- Brochure: `generate_brochure/brochure_template/`

### Company Data Storage
Company/organization data is stored in a **Neon PostgreSQL database**:
- Managed via Settings → Companies in the UI
- Database operations in `settings/database.py`
- Requires `DATABASE_URL` in environment variables or Streamlit secrets

## 🔍 TSC Document Requirements

For optimal results, ensure your TSC documents follow these conventions:

**Learning Unit Format:**
```
LU1: Introduction to Data Analytics (K1, K2, A1)
```

**Topic Format:**
```
Topic 1: Data Collection Methods (K1, A1)
```

**Key Requirements:**
- Include colon (:) after LU/Topic labels
- Use proper Knowledge (K) and Ability (A) factor notation
- Ensure LUs appear before their associated topics

## 🚨 Troubleshooting

### Common Issues

**Import Errors:**
- Ensure all dependencies are installed: `pip install -r requirements.txt`
- For UV users: `uv pip install -r requirements.txt` (much faster)
- Check Python version compatibility (3.11+)
- Verify virtual environment is activated

**API Key Issues:**
- Use **Settings → API Keys** tab to manage API keys (recommended)
- Ensure you have the API key for your selected provider:
  - OpenRouter: `OPENROUTER_API_KEY`
  - OpenAI: `OPENAI_API_KEY`
  - Gemini: `GEMINI_API_KEY`
- For fallback: verify API keys are set in `.streamlit/secrets.toml`
- Check API key validity and quotas with your provider
- The system will automatically use the API key matching the selected provider

**Model Selection Issues:**
- If no models appear, ensure the API provider has models in the database
- Use **Settings → LLM Models → Fetch Models** to retrieve available models
- Check that models are enabled (not disabled in Settings)
- Verify a default model is set for the provider (⭐ button)

**Document Processing Errors:**
- Ensure uploaded documents follow TSC formatting requirements
- Check file formats (DOCX for most uploads)

**Memory Issues:**
- Large document processing may require additional memory
- Consider using lighter models for development

## 🔐 Security Notes

- Never commit API keys to version control
- Use Streamlit secrets management for production
- Regularly rotate API keys
- Monitor API usage and costs

## 🤝 Contributing

1. Fork the repository
2. Create a feature branch: `git checkout -b feature-name`
3. Make your changes following the existing code style
4. Test thoroughly with sample documents
5. Submit a pull request

## 📝 License

This project is proprietary software developed for Tertiary Infotech. All rights reserved.

## 📞 Support

For technical support or questions:
- Check the troubleshooting section above
- Review the GitHub repository issues
- Contact the development team

