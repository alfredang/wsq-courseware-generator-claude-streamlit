# WSQ Courseware Generator

[![Python](https://img.shields.io/badge/Python-3.11+-3776AB?style=for-the-badge&logo=python&logoColor=white)](https://www.python.org/)
[![Streamlit](https://img.shields.io/badge/Streamlit-1.30+-FF4B4B?style=for-the-badge&logo=streamlit&logoColor=white)](https://streamlit.io/)
[![Chainlit](https://img.shields.io/badge/Chainlit-2.9+-6366F1?style=for-the-badge&logo=chainlit&logoColor=white)](https://chainlit.io/)
[![Claude](https://img.shields.io/badge/Claude_Agent_SDK-Anthropic-D4A574?style=for-the-badge&logo=anthropic&logoColor=white)](https://docs.anthropic.com/)
[![OpenRouter](https://img.shields.io/badge/OpenRouter-38+_Models-00D4AA?style=for-the-badge)](https://openrouter.ai/)
[![License](https://img.shields.io/badge/License-Proprietary-red?style=for-the-badge)](LICENSE)

A comprehensive AI-powered courseware generation platform built with **Claude Agent SDK** and **Streamlit/Chainlit**. This system uses an **orchestrator-based multi-agent architecture** with **34 AI agents** to automate the creation of educational documents including Course Proposals, Assessment Plans, Learning Guides, Presentation Slides, and more for Workforce Skills Qualification (WSQ) training programs.

---

## What is This App?

The **WSQ Courseware Generator** is an enterprise-grade AI platform designed for training providers to:

- **Generate Course Proposals** from Training Specification Content (TSC) documents
- **Create Complete Courseware** including Assessment Plans, Facilitator Guides, Learner Guides, and Lesson Plans
- **Produce 9 Types of Assessments** (SAQ, PP, CS, PRJ, ASGN, OI, DEM, RP, OQ)
- **Generate Presentation Slides** using Google NotebookLM with AI-enhanced research
- **Create Marketing Brochures** from course data or web scraping
- **Validate Supporting Documents** with entity extraction and ACRA company verification

The platform uses a sophisticated multi-agent architecture where specialized AI agents collaborate to produce high-quality, WSQ-compliant training materials.

---

## Tech Stack

### Core Frameworks
| Technology | Purpose |
|------------|---------|
| ![Python](https://img.shields.io/badge/Python-3776AB?style=flat&logo=python&logoColor=white) | Backend runtime |
| ![Streamlit](https://img.shields.io/badge/Streamlit-FF4B4B?style=flat&logo=streamlit&logoColor=white) | Web UI (Form-based interface) |
| ![Chainlit](https://img.shields.io/badge/Chainlit-6366F1?style=flat&logoColor=white) | Chat UI (Conversation-first interface) |

### AI & LLM
| Technology | Purpose |
|------------|---------|
| ![Claude](https://img.shields.io/badge/Claude_Agent_SDK-D4A574?style=flat&logo=anthropic&logoColor=white) | Multi-agent orchestration |
| ![OpenRouter](https://img.shields.io/badge/OpenRouter-00D4AA?style=flat&logoColor=white) | Unified LLM gateway (38+ models) |
| ![OpenAI](https://img.shields.io/badge/OpenAI-412991?style=flat&logo=openai&logoColor=white) | GPT models access |
| ![Google](https://img.shields.io/badge/Gemini-4285F4?style=flat&logo=google&logoColor=white) | Gemini models & NotebookLM |
| ![Anthropic](https://img.shields.io/badge/Anthropic-D4A574?style=flat&logoColor=white) | Claude models |

### Document Processing
| Technology | Purpose |
|------------|---------|
| `python-docx` | Word document creation |
| `docxtpl` | Jinja2 DOCX templates |
| `docxcompose` | Multi-document composition |
| `PyPDF2` | PDF reading |
| `openpyxl` | Excel file handling |

### Database & Storage
| Technology | Purpose |
|------------|---------|
| ![PostgreSQL](https://img.shields.io/badge/PostgreSQL-336791?style=flat&logo=postgresql&logoColor=white) | Company data (Neon) |
| ![SQLite](https://img.shields.io/badge/SQLite-003B57?style=flat&logo=sqlite&logoColor=white) | Local config & models |

### Web & Data
| Technology | Purpose |
|------------|---------|
| `beautifulsoup4` | Web scraping |
| `pydantic` | Data validation |
| `pandas` | Data manipulation |
| `gspread` | Google Sheets integration |

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

### 2. Clone & Install

```bash
# Clone the repository
git clone https://github.com/alfredang/courseware_claude_agents.git
cd courseware_claude_agents

# Create virtual environment with uv
uv venv
source .venv/bin/activate          # macOS/Linux
# OR
.venv\Scripts\activate             # Windows

# Install dependencies
uv pip install -r requirements.txt
```

### 3. Configure Secrets

Create `.env` file in the root directory:

```bash
# API Keys
OPENAI_API_KEY=sk-your-openai-key
OPENROUTER_API_KEY=sk-or-your-openrouter-key
ANTHROPIC_API_KEY=sk-ant-your-anthropic-key
GEMINI_API_KEY=your-gemini-key

# Database (for company management)
DATABASE_URL=postgresql://user:password@host/database?sslmode=require

# Admin Authentication
ADMIN_USERNAME=admin
ADMIN_PASSWORD=your-secure-password

# Chainlit JWT Secret (generate with: chainlit create-secret)
CHAINLIT_AUTH_SECRET=your-jwt-secret
```

### 4. Run the Application

```bash
# Generate JWT secret (first time only)
chainlit create-secret

# Run the Chainlit app
chainlit run app.py
```
Open browser to `http://localhost:8000`

---

## Deployment

### Deploy to Render / Railway

1. **Create `Procfile`:**
   ```
   web: chainlit run app.py --host 0.0.0.0 --port $PORT
   ```

2. **Set Environment Variables:**
   ```
   CHAINLIT_AUTH_SECRET=your-jwt-secret
   OPENAI_API_KEY=sk-...
   OPENROUTER_API_KEY=sk-or-...
   ANTHROPIC_API_KEY=sk-ant-...
   DATABASE_URL=postgresql://...
   ADMIN_USERNAME=admin
   ADMIN_PASSWORD=your-password
   ```

3. **Deploy from GitHub**

### Deploy to Docker

1. **Create `Dockerfile`:**
   ```dockerfile
   FROM python:3.11-slim
   WORKDIR /app
   COPY requirements.txt .
   RUN pip install -r requirements.txt
   COPY . .
   EXPOSE 8000
   CMD ["chainlit", "run", "app.py", "--host", "0.0.0.0", "--port", "8000"]
   ```

2. **Build and run:**
   ```bash
   docker build -t courseware-generator .
   docker run -p 8000:8000 --env-file .env courseware-generator
   ```

---

## Key Features

### Core Document Generation (7 Modules)

| Module | Description | Agents Used |
|--------|-------------|-------------|
| **Generate CP** | Course Proposal generation from TSC documents | 10 agents |
| **Generate Courseware** | Assessment Plan, Facilitator Guide, Learner Guide, Lesson Plan | 4 agents |
| **Generate Assessment** | 9 assessment types (SAQ, PP, CS, PRJ, ASGN, OI, DEM, RP, OQ) | 9 agents |
| **Generate Slides** | Agentic slide generation with Google NotebookLM | 4 agents + NotebookLM |
| **Generate Brochure** | Marketing materials with web scraping | 1 agent |
| **Add Assessment to AP** | Integrate assessments into AP annexes | Template-based |
| **Check Documents** | Supporting document validation | Gemini API |

### Chat Interface

The application uses **Chainlit** for a conversation-first experience:
- **8 Chat Profiles** for different workflows (CP, Courseware, Assessment, etc.)
- **Natural language interaction** with AI-powered guidance
- **File upload support** for document processing
- **Real-time progress tracking** with step indicators

### Model Support

| Provider | Models Available |
|----------|------------------|
| **OpenRouter** | 38+ models (unified gateway) |
| **OpenAI** | GPT-4o, GPT-4o-Mini, o1, o3-mini |
| **Anthropic** | Claude Opus 4.5, Claude Sonnet 4 |
| **Google** | Gemini 2.5 Pro/Flash, Gemini 2.0 |
| **DeepSeek** | DeepSeek-Chat, DeepSeek-R1 |
| **Meta** | Llama 3.3 70B |

---

## Multi-Agent Architecture

The system uses an **orchestrator-based architecture** powered by the Claude Agent SDK:

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

- **Orchestrator Agents (6)**: Main coordinator, CP, Courseware, Assessment, Brochure, Document
- **Course Proposal Agents (10)**: TSC, Extraction Team (5), Research Team, Validation Team, Justification, Excel
- **Assessment Agents (9)**: SAQ, PP, CS, PRJ, ASGN, OI, DEM, RP, OQ
- **Courseware Agents (4)**: AP, FG, LG, LP
- **Slides Agents (5)**: Topic Analysis, Source Evaluator, Slide Instructions, Quality Validator, Orchestrator

---

## Project Structure

```
courseware_claude_agents/
├── app.py                          # Main Chainlit application
├── chainlit_modules/               # Chat profile handlers
│   ├── course_proposal.py
│   ├── courseware.py
│   ├── assessment.py
│   ├── slides.py
│   ├── brochure.py
│   ├── annex_assessment.py
│   ├── check_documents.py
│   └── settings.py
├── .chainlit/                      # Chainlit configuration
├── public/                         # Static assets (CSS)
├── courseware_agents/              # Claude Agent SDK agents
│   ├── orchestrator.py             # Main orchestrator
│   ├── cp_agent.py                 # Course Proposal agent
│   ├── courseware_agent.py         # Courseware agent
│   ├── assessment_agent.py         # Assessment agent
│   └── tools/                      # MCP tools
├── generate_cp/                    # Course Proposal generation
├── generate_assessment/            # Assessment generation (9 types)
├── generate_ap_fg_lg_lp/           # Courseware suite generation
├── generate_slides/                # Slide generation
├── generate_brochure/              # Brochure generation
├── settings/                       # Configuration & admin
├── company/                        # Company management
├── skills/                         # AI skill definitions
└── utils/                          # Shared utilities
```

---

## Environment Variables

| Variable | Required | Description |
|----------|----------|-------------|
| `OPENROUTER_API_KEY` | Yes* | OpenRouter API key (recommended) |
| `OPENAI_API_KEY` | Yes* | OpenAI API key |
| `ANTHROPIC_API_KEY` | No | Anthropic API key |
| `GEMINI_API_KEY` | No | Google Gemini API key |
| `DATABASE_URL` | No | PostgreSQL connection string |
| `ADMIN_USERNAME` | No | Admin login username |
| `ADMIN_PASSWORD` | No | Admin login password |
| `CHAINLIT_AUTH_SECRET` | Chainlit only | JWT secret for Chainlit auth |

*At least one LLM API key is required

---

## Security

- **No hardcoded secrets** - All API keys stored in `secrets.toml` or environment variables
- **`.gitignore` configured** - Secrets files excluded from version control
- **Admin authentication** - Protected settings access
- **Session-based storage** - NotebookLM sessions stored locally only

### Files Excluded from Git
- `.streamlit/secrets.toml`
- `.env`
- `chainlit_app/.env`
- `*-credentials.json`
- `ssg-api-calls*.json`

---

## Troubleshooting

### Import Errors
```bash
uv pip install -r requirements.txt
python3 --version  # Must be 3.11+
```

### API Key Issues
- Use **Settings → API Keys** to manage keys
- Verify key validity with your provider
- OpenRouter: one key gives access to 38+ models

### Model Selection Issues
- Go to **Settings → LLM Models → Fetch Models**
- Ensure models are enabled
- Set a default model

### Chainlit Auth Errors
```bash
cd chainlit_app
chainlit create-secret
# Add the secret to .env file
```

---

## Contributing

1. Fork the repository
2. Create a feature branch: `git checkout -b feature-name`
3. Make your changes
4. Test thoroughly
5. Submit a pull request

---

## License

This project is proprietary software developed for Tertiary Infotech. All rights reserved.

---

## Support

- [GitHub Issues](https://github.com/alfredang/courseware_claude_agents/issues)
- Check the troubleshooting section above
