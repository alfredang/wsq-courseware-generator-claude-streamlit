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
[![Streamlit](https://img.shields.io/badge/Streamlit-1.30+-FF4B4B?style=for-the-badge&logo=streamlit&logoColor=white)](https://streamlit.io)
[![Claude](https://img.shields.io/badge/Claude-Anthropic-D4A574?style=for-the-badge&logo=anthropic&logoColor=white)](https://anthropic.com)
[![License](https://img.shields.io/badge/License-MIT-green?style=for-the-badge)](LICENSE)
[![Docker](https://img.shields.io/badge/Docker-Ready-2496ED?style=for-the-badge&logo=docker&logoColor=white)](Dockerfile)
[![Hugging Face](https://img.shields.io/badge/HuggingFace-Spaces-yellow?style=for-the-badge&logo=huggingface&logoColor=white)](https://huggingface.co/spaces)

**AI-Powered Courseware Generation Platform for WSQ Training Providers**

[Live Demo](https://huggingface.co/spaces/tertiaryinfotech/wsq-courseware-generator) · [Report Bug](https://github.com/alfredang/wsq-courseware-generator-claude-streamlit/issues) · [Request Feature](https://github.com/alfredang/wsq-courseware-generator-claude-streamlit/discussions)

</div>

---

## About The Project

The **WSQ Courseware Generator** is an enterprise-grade AI platform that automates the creation of Singapore Workforce Skills Qualifications (WSQ) training materials. Using Claude AI agents, it transforms Training & Competency Standards (TSC) documents into complete courseware packages.

![WSQ Courseware Generator](coursewate_genertor.png)

### Key Features

| Feature | Description |
|---------|-------------|
| **Courseware Creation** | Auto-generate Assessment Plans, Facilitator Guides, Learner Guides, and Lesson Plans |
| **Assessment Generation** | Create 9 assessment types (SAQ, PP, CS, PRJ, ASGN, OI, DEM, RP, OQ) |
| **Slides Generation** | Generate presentation slides with NotebookLM integration |
| **Brochure Creation** | Design marketing brochures with web scraping |
| **Courseware Audit** | Validate supporting documents with entity extraction |

### Platform Statistics

| Metric | Count |
|--------|-------|
| AI Agents | 24 |
| Generation Modules | 6 |
| Assessment Types | 9 |
| Courseware Documents | 4 |
| Prompt Templates | 22 |
| Skills Documented | 11 |

---

## Tech Stack

| Category | Technology |
|----------|------------|
| **Frontend** | ![Streamlit](https://img.shields.io/badge/Streamlit-1.30+-FF4B4B?style=flat&logo=streamlit&logoColor=white) |
| **Backend** | ![Python](https://img.shields.io/badge/Python-3.13-3776AB?style=flat&logo=python&logoColor=white) |
| **AI/LLM** | ![Claude](https://img.shields.io/badge/Claude_API-Anthropic-D4A574?style=flat&logo=anthropic&logoColor=white) |
| **Database** | ![SQLite](https://img.shields.io/badge/SQLite-003B57?style=flat&logo=sqlite&logoColor=white) ![PostgreSQL](https://img.shields.io/badge/PostgreSQL-Neon-336791?style=flat&logo=postgresql&logoColor=white) |
| **Deployment** | ![Docker](https://img.shields.io/badge/Docker-2496ED?style=flat&logo=docker&logoColor=white) ![HuggingFace](https://img.shields.io/badge/HuggingFace-Spaces-yellow?style=flat&logo=huggingface&logoColor=white) |
| **Document Processing** | python-docx, docxtpl, openpyxl, PyPDF2 |

---

## Architecture Diagram

```
┌─────────────────────────────────────────────────────────────────────┐
│                        STREAMLIT UI                                 │
│           (Sidebar Navigation + Page Routing)                       │
│                                                                     │
│  ┌──────────┐ ┌──────────┐ ┌──────────┐ ┌──────────┐ ┌──────────┐ │
│  │   Home   │ │Courseware │ │Assessment│ │  Slides  │ │ Brochure │ │
│  │          │ │AP/FG/LG  │ │   (9)    │ │          │ │          │ │
│  └──────────┘ └────┬─────┘ └────┬─────┘ └────┬─────┘ └────┬─────┘ │
│                    │            │            │            │         │
│  ┌──────────┐ ┌──────────┐ ┌──────────┐                           │
│  │  Annex   │ │Courseware │ │ Company  │                           │
│  │Assessment│ │  Audit   │ │ Settings │                           │
│  └────┬─────┘ └────┬─────┘ └──────────┘                           │
└───────┼────────────┼────────────┼──────────────────────────────────┘
        │            │            │
┌───────▼────────────▼────────────▼──────────────────────────────────┐
│                      CLAUDE AI AGENTS (24 Total)                    │
│                                                                     │
│  ┌───────────┐ ┌───────────┐ ┌───────────┐ ┌───────────┐          │
│  │ CW Agents │ │Assessment │ │  Slides   │ │ Brochure  │          │
│  │    (4)    │ │  Agents   │ │  Agents   │ │ & Doc     │          │
│  │           │ │    (9)    │ │    (5)    │ │ Agents    │          │
│  │ -AP Agent │ │ -SAQ, PP  │ │ -Topic    │ │ -Brochure │          │
│  │ -FG Agent │ │ -CS, PRJ  │ │ -Source   │ │ -Document │          │
│  │ -LG Agent │ │ -ASGN, OI │ │ -Quality  │ │ -Entity   │          │
│  │ -LP Agent │ │ -DEM, RP  │ │ -NotebookLM││ -Verify   │          │
│  └───────────┘ └───────────┘ └───────────┘ └───────────┘          │
└─────────────────────────────┬──────────────────────────────────────┘
                              │
┌─────────────────────────────▼──────────────────────────────────────┐
│                    DOCUMENT GENERATION ENGINE                       │
│          (Templates + python-docx + docxtpl + openpyxl)            │
└────────────────────────────────────────────────────────────────────┘
```

---

## Project Structure

```
wsq-courseware-generator-claude-streamlit/
├── app.py                          # Main Streamlit application
├── Dockerfile                      # Docker configuration
├── requirements.txt                # Python dependencies
│
├── .streamlit/
│   └── config.toml                 # Streamlit configuration
│
├── generate_assessment/            # Assessment generation
│   ├── assessment_generation.py    # Assessment Streamlit page
│   └── utils/                      # 9 assessment agents
│
├── generate_ap_fg_lg_lp/           # Courseware generation
│   ├── courseware_generation.py     # Courseware Streamlit page
│   └── utils/                      # AP, FG, LG, LP agents
│
├── generate_slides/                # Slides generation
│   ├── slides_generation.py        # Slides Streamlit page
│   └── agents/                     # 5 slides agents
│
├── generate_brochure/              # Brochure generation
│   └── brochure_generation.py      # Brochure Streamlit page
│
├── add_assessment_to_ap/           # Annex assessments to AP
│   └── annex_assessment_v2.py      # Annex Streamlit page
│
├── check_documents/                # Courseware audit
│   └── sup_doc.py                  # Courseware audit Streamlit page
│
├── settings/                       # Configuration
│   ├── model_configs.py            # Model configurations
│   └── api_database.py             # SQLite database
│
├── company/                        # Company management
│   ├── company_settings.py         # Company management page
│   └── company_manager.py          # Organization utilities
│
├── .claude/                        # Claude Code configuration
│   ├── commands/                   # CLI commands
│   │   └── start-app.md            # Start Streamlit app
│   └── skills/                     # Claude Code skills (13)
│       ├── branding/
│       ├── generate_courseware/
│       ├── generate_assessment/
│       ├── generate_slides/
│       └── ...
│
└── utils/                          # Shared utilities
    └── helpers.py                  # JSON parsing, etc.
```

---

## Getting Started

### Prerequisites

- **Python 3.13+**
- **uv** (recommended) or pip
- **Docker** (optional, for containerized deployment)
- **Anthropic API Key**

### Local Development

```bash
# 1. Clone the repository
git clone https://github.com/alfredang/wsq-courseware-generator-claude-streamlit.git
cd wsq-courseware-generator-claude-streamlit

# 2. Create virtual environment with uv
uv venv && source .venv/bin/activate

# 3. Install dependencies
uv pip install -r requirements.txt

# 4. Set up environment variables
cp .env.example .env
# Edit .env with your API keys

# 5. Run the application
uv run streamlit run app.py

# 6. Open browser
# http://localhost:8501
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

---

## Environment Variables

| Variable | Required | Description |
|----------|----------|-------------|
| `ANTHROPIC_API_KEY` | Yes | Anthropic Claude API key |
| `DATABASE_URL` | No | PostgreSQL connection string (optional, for persistent storage) |

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
| `generate_courseware` | Generate AP, FG, LG, LP documents |
| `generate_assessment` | Create 9 assessment types |
| `generate_slides` | Generate slides with NotebookLM MCP |
| `generate_brochure` | Create marketing brochures |
| `courseware_audit` | Verify supporting documents |
| `add_assessment_to_ap` | Annex assessments to AP |
| `branding` | UI styling guidelines |

Skills use fuzzy matching via `rapidfuzz` to match user intents to appropriate workflows.

---

## Contributing

Contributions are welcome! Feel free to:

1. **Fork** the repository
2. **Create** a feature branch (`git checkout -b feature/AmazingFeature`)
3. **Commit** your changes (`git commit -m 'Add AmazingFeature'`)
4. **Push** to the branch (`git push origin feature/AmazingFeature`)
5. **Open** a Pull Request

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
- [Streamlit](https://streamlit.io) — Web App Framework
- [Hugging Face](https://huggingface.co) — Model Hosting & Spaces
- [SkillsFuture Singapore](https://www.skillsfuture.gov.sg/) — WSQ Framework
- [Neon](https://neon.tech) — Serverless PostgreSQL
- All contributors and testers who helped improve this project

---

<div align="center">

**Made with love for Singapore's Training Providers**

Star this repo if you find it useful!

</div>
