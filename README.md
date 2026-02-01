---
title: WSQ Courseware Generator
emoji: 📚
colorFrom: blue
colorTo: indigo
sdk: docker
pinned: false
app_port: 7860
---

<div align="center">

# WSQ Courseware Generator

[![Python](https://img.shields.io/badge/Python-3.13-3776AB?style=for-the-badge&logo=python&logoColor=white)](https://python.org)
[![Chainlit](https://img.shields.io/badge/Chainlit-2.0+-6366F1?style=for-the-badge&logo=chainlit&logoColor=white)](https://chainlit.io)
[![Claude](https://img.shields.io/badge/Claude-Anthropic-D4A574?style=for-the-badge&logo=anthropic&logoColor=white)](https://anthropic.com)
[![License](https://img.shields.io/badge/License-MIT-green?style=for-the-badge)](LICENSE)
[![Docker](https://img.shields.io/badge/Docker-Ready-2496ED?style=for-the-badge&logo=docker&logoColor=white)](Dockerfile)
[![Hugging Face](https://img.shields.io/badge/HuggingFace-Spaces-yellow?style=for-the-badge&logo=huggingface&logoColor=white)](https://huggingface.co/spaces)
[![Claude Code](https://img.shields.io/badge/Claude_Code-Subscription-D4A574?style=for-the-badge&logo=anthropic&logoColor=white)](https://claude.ai/claude-code)

**AI-Powered Courseware Generation Platform for WSQ Training Providers**

[Live Demo](https://huggingface.co/spaces/tertiaryinfotech/wsq-courseware-generator) · [Report Bug](https://github.com/alfredang/courseware_claude_agents/issues) · [Request Feature](https://github.com/alfredang/courseware_claude_agents/discussions)

</div>

---

## About The Project

The **WSQ Courseware Generator** is an enterprise-grade AI platform that automates the creation of Singapore Workforce Skills Qualifications (WSQ) training materials. Using Claude AI agents, it transforms Training & Competency Standards (TSC) documents into complete courseware packages.

![Course Proposal Generator](public/images/preview.png)

### Key Features

| Feature | Description |
|---------|-------------|
| **Course Proposal Generation** | Extract competency units from TSC and generate structured proposals |
| **Courseware Creation** | Auto-generate Assessment Plans, Facilitator Guides, Learner Guides, and Lesson Plans |
| **Assessment Generation** | Create 9 assessment types (SAQ, PP, CS, PRJ, ASGN, OI, DEM, RP, OQ) |
| **Slides Generation** | Generate presentation slides with NotebookLM integration |
| **Brochure Creation** | Design marketing brochures with web scraping |
| **Document Verification** | Validate supporting documents with entity extraction |

### Platform Statistics

| Metric | Count |
|--------|-------|
| AI Agents | 34 |
| Generation Modules | 7 |
| Assessment Types | 9 |
| Courseware Documents | 4 |
| Prompt Templates | 22 |
| Skills Documented | 13 |

### Execution Environment

This platform runs using **Claude Code with subscription plan**. All AI operations are executed through the Claude Code CLI environment with an active subscription, ensuring consistent and reliable performance.

---

## Tech Stack

| Category | Technology |
|----------|------------|
| **Frontend** | ![Chainlit](https://img.shields.io/badge/Chainlit-2.0+-6366F1?style=flat&logo=chainlit&logoColor=white) |
| **Backend** | ![Python](https://img.shields.io/badge/Python-3.13-3776AB?style=flat&logo=python&logoColor=white) |
| **AI/LLM** | ![Claude](https://img.shields.io/badge/Claude_API-Anthropic-D4A574?style=flat&logo=anthropic&logoColor=white) |
| **Database** | ![PostgreSQL](https://img.shields.io/badge/PostgreSQL-Neon-336791?style=flat&logo=postgresql&logoColor=white) |
| **Deployment** | ![Docker](https://img.shields.io/badge/Docker-2496ED?style=flat&logo=docker&logoColor=white) ![HuggingFace](https://img.shields.io/badge/HuggingFace-Spaces-yellow?style=flat&logo=huggingface&logoColor=white) |
| **Document Processing** | python-docx, docxtpl, openpyxl, PyPDF2 |

### Claude Models Supported

| Model | Use Case |
|-------|----------|
| **Claude Sonnet 4** | Default - Best balance of speed and capability |
| **Claude Opus 4.5** | Complex tasks requiring deep reasoning |
| **Claude Haiku 3.5** | Fast tasks requiring quick responses |

---

## Architecture Diagram

```
┌─────────────────────────────────────────────────────────────────────┐
│                         CHAINLIT UI                                  │
│                (Chat Interface + File Upload)                        │
└─────────────────────────────┬───────────────────────────────────────┘
                              │
┌─────────────────────────────▼───────────────────────────────────────┐
│                       CHAT PROFILES                                  │
│  ┌──────────┐ ┌──────────┐ ┌──────────┐ ┌──────────┐ ┌──────────┐  │
│  │ Course   │ │Courseware│ │Assessment│ │  Slides  │ │ Brochure │  │
│  │ Proposal │ │    (4)   │ │   (9)    │ │   (5)    │ │          │  │
│  └────┬─────┘ └────┬─────┘ └────┬─────┘ └────┬─────┘ └────┬─────┘  │
└───────┼────────────┼────────────┼────────────┼────────────┼─────────┘
        │            │            │            │            │
┌───────▼────────────▼────────────▼────────────▼────────────▼─────────┐
│                      CLAUDE AI AGENTS (34 Total)                     │
│                                                                      │
│  ┌─────────────────────────────────────────────────────────────┐    │
│  │                    ORCHESTRATOR AGENT                        │    │
│  │              (Routes to Specialized Agents)                  │    │
│  └───────┬─────────────┬─────────────┬─────────────┬───────────┘    │
│          │             │             │             │                 │
│  ┌───────▼───┐ ┌───────▼───┐ ┌───────▼───┐ ┌───────▼───┐           │
│  │ CP Agents │ │ CW Agents │ │Assessment │ │  Slides   │           │
│  │   (10)    │ │    (4)    │ │  Agents   │ │  Agents   │           │
│  │           │ │           │ │    (9)    │ │    (5)    │           │
│  │ -TSC      │ │ -AP Agent │ │ -SAQ, PP  │ │ -Topic    │           │
│  │ -Extract  │ │ -FG Agent │ │ -CS, PRJ  │ │ -Source   │           │
│  │ -Research │ │ -LG Agent │ │ -ASGN, OI │ │ -Quality  │           │
│  │ -Validate │ │ -LP Agent │ │ -DEM, RP  │ │ -NotebookLM│          │
│  └───────────┘ └───────────┘ └───────────┘ └───────────┘           │
└─────────────────────────────┬───────────────────────────────────────┘
                              │
┌─────────────────────────────▼───────────────────────────────────────┐
│                    DOCUMENT GENERATION ENGINE                        │
│          (Templates + python-docx + docxtpl + openpyxl)             │
└─────────────────────────────────────────────────────────────────────┘
```

---

## Project Structure

```
courseware_claude/
├── app.py                          # Main Chainlit application
├── Dockerfile                      # Docker configuration
├── requirements.txt                # Python dependencies
│
├── .chainlit/
│   └── config.toml                 # Chainlit configuration
│
├── chainlit_modules/               # Chat profile handlers
│   ├── course_proposal.py          # CP workflow
│   ├── courseware.py               # AP/FG/LG/LP workflow
│   ├── assessment.py               # Assessment workflow
│   ├── slides.py                   # Slides workflow
│   ├── brochure.py                 # Brochure workflow
│   ├── annex_assessment.py         # Add to AP workflow
│   ├── check_documents.py          # Document verification
│   └── settings.py                 # Settings panel
│
├── generate_cp/                    # Course Proposal generation
│   ├── main.py                     # Main CP pipeline
│   ├── agents/                     # CP agents (10)
│   └── utils/                      # Utilities
│
├── generate_assessment/            # Assessment generation
│   ├── agents/                     # 9 assessment agents
│   └── prompts/                    # Assessment prompts
│
├── generate_ap_fg_lg_lp/           # Courseware generation
│   ├── agents/                     # 4 courseware agents
│   └── templates/                  # Document templates
│
├── generate_slides/                # Slides generation
│   ├── agents/                     # 5 slides agents
│   └── notebooklm/                 # NotebookLM integration
│
├── generate_brochure/              # Brochure generation
│
├── settings/                       # Configuration & API
│   ├── api_manager.py              # API key management
│   ├── model_configs.py            # Model configurations
│   └── api_database.py             # SQLite database
│
├── company/                        # Company management
│   └── company_manager.py          # Organization CRUD
│
├── skills/                         # NLP skill matching
│   └── __init__.py                 # Skill definitions
│
├── .claude/                        # Claude Code configuration
│   ├── settings.local.json         # Local settings
│   └── skills/                     # Claude Code skills (13)
│       ├── branding/               # UI styling guidelines
│       ├── generate_course_proposal/   # CP generation skill
│       ├── generate_courseware/    # AP/FG/LG/LP skill
│       ├── generate_assessment/    # Assessment generation
│       ├── generate_assessment_plan/   # AP-specific skill
│       ├── generate_facilitator_guide/ # FG-specific skill
│       ├── generate_learner_guide/ # LG-specific skill
│       ├── generate_lesson_plan/   # LP-specific skill
│       ├── generate_slides/        # Slides generation
│       ├── generate_brochure/      # Brochure generation
│       ├── add_assessment_to_ap/   # Annex assessments
│       ├── check_documents/        # Document verification
│       └── create_github_readme/   # README generation
│
├── templates/                      # Document templates
│   ├── AP_template.docx
│   ├── FG_template.docx
│   ├── LG_template.docx
│   └── LP_template.docx
│
└── public/                         # Static assets
    └── custom.css                  # Dark theme styles
```

---

## Getting Started

### Prerequisites

- **Python 3.13+**
- **Docker** (optional, for containerized deployment)
- **Anthropic API Key**

### Local Development

```bash
# 1. Clone the repository
git clone https://github.com/alfredang/courseware_claude_agents.git
cd courseware_claude_agents

# 2. Create virtual environment
python -m venv venv
source venv/bin/activate  # Windows: venv\Scripts\activate

# 3. Install dependencies
pip install -r requirements.txt

# 4. Set up environment variables
cp .env.example .env
# Edit .env with your API keys

# 5. Run the application
chainlit run app.py -w

# 6. Open browser
# http://localhost:8000
```

### Docker Deployment

```bash
# Build image
docker build -t wsq-courseware .

# Run container
docker run -p 7860:7860 --env-file .env wsq-courseware
```

### Hugging Face Spaces Deployment

1. Go to [huggingface.co/spaces](https://huggingface.co/spaces)
2. Click **"Create new Space"**
3. Select **Docker** as SDK
4. Connect your GitHub repository
5. Add secrets in Settings:
   - `ANTHROPIC_API_KEY`
   - `DATABASE_URL`
   - `CHAINLIT_AUTH_SECRET`

---

## Environment Variables

| Variable | Required | Description |
|----------|----------|-------------|
| `ANTHROPIC_API_KEY` | Yes | Anthropic Claude API key |
| `DATABASE_URL` | Yes | PostgreSQL connection string |
| `CHAINLIT_AUTH_SECRET` | Yes | Session encryption secret |

---

## Skills System

The platform includes 13 documented skills in the `.claude/skills/` directory, each with:

| File | Purpose |
|------|---------|
| `SKILL.md` | Command, keywords, description, response template |
| `README.md` | Developer documentation |
| `examples.md` | Example prompts and usage |
| `reference/` | Technical reference docs for agents |

### Available Skills

| Skill | Description |
|-------|-------------|
| `generate_course_proposal` | Generate CP from TSC documents |
| `generate_courseware` | Generate AP, FG, LG, LP documents |
| `generate_assessment` | Create 9 assessment types |
| `generate_slides` | Generate slides with NotebookLM MCP |
| `generate_brochure` | Create marketing brochures |
| `check_documents` | Verify supporting documents |
| `add_assessment_to_ap` | Annex assessments to AP |
| `branding` | UI styling guidelines |
| `create_github_readme` | Generate README.md files |

Skills use fuzzy matching via `rapidfuzz` to match user intents to appropriate workflows.

---

## Contributing

Contributions are welcome! Feel free to:

1. **Fork** the repository
2. **Create** a feature branch (`git checkout -b feature/AmazingFeature`)
3. **Commit** your changes (`git commit -m 'Add AmazingFeature'`)
4. **Push** to the branch (`git push origin feature/AmazingFeature`)
5. **Open** a Pull Request

Join the discussion in [GitHub Discussions](https://github.com/alfredang/courseware_claude_agents/discussions)!

---

## License

Distributed under the MIT License. See `LICENSE` for more information.

---

## Developed By

<div align="center">

### Tertiary Infotech Academy Pte. Ltd.

**Singapore**

[Website](https://tertiaryinfotech.com) · [LinkedIn](https://linkedin.com/company/tertiary-infotech)

</div>

---

## Acknowledgements

- [Anthropic](https://anthropic.com) — Claude AI API
- [Chainlit](https://chainlit.io) — Chat UI Framework
- [Hugging Face](https://huggingface.co) — Model Hosting & Spaces
- [SkillsFuture Singapore](https://www.skillsfuture.gov.sg/) — WSQ Framework
- [Neon](https://neon.tech) — Serverless PostgreSQL
- All contributors and testers who helped improve this project

---

<div align="center">

**Made with ❤️ for Singapore's Training Providers**

⭐ Star this repo if you find it useful!

</div>
