<div align="center">

# WSQ Courseware Generator

[![Python](https://img.shields.io/badge/Python-3.13-3776AB?style=for-the-badge&logo=python&logoColor=white)](https://python.org)
[![Streamlit](https://img.shields.io/badge/Streamlit-1.30+-FF4B4B?style=for-the-badge&logo=streamlit&logoColor=white)](https://streamlit.io)
[![Claude](https://img.shields.io/badge/Claude_Agent_SDK-Anthropic-D4A574?style=for-the-badge&logo=anthropic&logoColor=white)](https://anthropic.com)
[![License](https://img.shields.io/badge/License-MIT-green?style=for-the-badge)](LICENSE)

**AI-Powered Courseware Generation Platform for WSQ Training Providers**

Built with **Claude Agent SDK** — all AI processing runs through Claude Code subscription.

![WSQ Courseware Generator](screenshot.png)

</div>

---

## About The Project

The **WSQ Courseware Generator** is an AI platform that automates the creation of Singapore Workforce Skills Qualifications (WSQ) training materials. Using Claude Agent SDK agents, it transforms Course Proposal documents into complete courseware packages.

### Key Features

| Feature | Description |
|---------|-------------|
| **Courseware Creation** | Auto-generate Assessment Plans, Facilitator Guides, and Learner Guides |
| **Lesson Plan Generation** | Generate Lesson Plans with pure Python barrier algorithm scheduling |
| **Assessment Generation** | Create 9 assessment types (SAQ, PP, CS, PRJ, ASGN, OI, DEM, RP, OQ) |
| **Slides Generation** | AI-enhanced slides with NotebookLM integration |
| **Brochure Creation** | Design marketing brochures via web scraping |
| **Courseware Audit** | Validate supporting documents with entity extraction |

---

## Tech Stack

| Category | Technology |
|----------|------------|
| **Frontend** | Streamlit 1.30+ |
| **Backend** | Python 3.13 |
| **AI Processing** | Claude Agent SDK |
| **Database** | SQLite (settings), PostgreSQL/Neon (companies) |
| **Slides** | NotebookLM MCP Server |
| **Document Processing** | python-docx, docxtpl, openpyxl, PyPDF2 |

---

## Architecture

```
┌─────────────────────────────────────────────────────────────────┐
│                      STREAMLIT UI                               │
│              (File Upload / Preview / Download)                  │
│                                                                 │
│  ┌──────────┐ ┌──────────┐ ┌──────────┐ ┌──────────┐          │
│  │ Extract  │ │Courseware │ │  Lesson  │ │Assessment│          │
│  │Course Info│ │AP/FG/LG  │ │  Plan    │ │  (9 types)│         │
│  └──────────┘ └────┬─────┘ └────┬─────┘ └────┬─────┘          │
│  ┌──────────┐ ┌──────────┐ ┌──────────┐ ┌──────────┐          │
│  │  Slides  │ │ Brochure │ │  Annex   │ │Courseware │          │
│  │(NotebookLM)││(Scraping)│ │Assessment│ │  Audit   │          │
│  └────┬─────┘ └──────────┘ └──────────┘ └────┬─────┘          │
└───────┼───────────────────────────────────────┼────────────────┘
        │                                       │
┌───────▼───────────────────────────────────────▼────────────────┐
│                  CLAUDE AGENT SDK (courseware_agents/)           │
│                                                                 │
│  ┌────────────────┐ ┌────────────────┐ ┌────────────────┐      │
│  │ CP Interpreter │ │   Assessment   │ │    Slides      │      │
│  │  (cp → JSON)   │ │   Generator    │ │    Agent       │      │
│  └────────────────┘ └────────────────┘ └────────────────┘      │
└────────────────────────────┬───────────────────────────────────┘
                             │
┌────────────────────────────▼───────────────────────────────────┐
│                  DOCUMENT GENERATION ENGINE                     │
│            (docxtpl Templates + python-docx)                   │
└────────────────────────────────────────────────────────────────┘
```

---

## Project Structure

```
courseware_claude_streamlit/
├── app.py                          # Main Streamlit application
├── pyproject.toml                  # Python project metadata
├── requirements.txt                # Python dependencies
├── .streamlit/config.toml          # Streamlit configuration
│
├── courseware_agents/               # Claude Agent SDK agents
│   ├── base.py                     # Core run_agent() wrapper
│   ├── cp_interpreter.py           # Course Proposal → JSON
│   ├── assessment_generator.py     # FG → assessment questions
│   └── slides_agent.py             # Document → slide instructions
│
├── generate_ap_fg_lg/              # Courseware generation (AP/FG/LG)
│   ├── courseware_generation.py     # AP/FG/LG Streamlit page
│   └── utils/                      # Template filling modules
│
├── generate_lp/                    # Lesson Plan generation
│   ├── lesson_plan_generation.py   # Lesson Plan Streamlit page
│   └── timetable_generator.py      # Pure Python barrier algorithm
│
├── generate_assessment/            # Assessment generation
│   └── assessment_generation.py    # Assessment Streamlit page
│
├── generate_slides/                # Slides generation
│   └── slides_generation.py        # NotebookLM integration
│
├── generate_brochure/              # Brochure generation
│   └── brochure_generation.py      # Web scraping + template
│
├── add_assessment_to_ap/           # Annex assessments to AP
│   └── annex_assessment_v2.py
│
├── courseware_audit/                # Courseware audit
│   ├── sup_doc.py                  # Entity extraction page
│   └── audit_agent.py              # Audit field extraction agent
│
├── extract_course_info/            # CP parsing (pure Python)
│   └── extract_course_info.py
│
├── settings/                       # Settings
│   └── api_database.py             # SQLite (prompt templates)
│
├── company/                        # Company management (PostgreSQL)
│   ├── company_settings.py
│   ├── company_manager.py
│   └── database.py
│
├── utils/                          # Shared utilities
│   ├── agent_runner.py             # Background agent job manager
│   ├── agent_status.py             # Agent status UI components
│   ├── helpers.py                  # File & JSON utilities
│   └── prompt_template_editor.py   # Prompt template editing UI
│
└── .claude/                        # Claude Code configuration
    ├── settings.local.json         # MCP server config (NotebookLM)
    └── skills/                     # Claude Code skill definitions
```

---

## Getting Started

### Prerequisites

- **Python 3.13+**
- **uv** (recommended) or pip
- **Claude Code** with subscription plan

### Setup

```bash
# 1. Clone the repository
git clone https://github.com/alfredang/wsq-courseware-generator-claude-streamlit.git
cd wsq-courseware-generator-claude-streamlit

# 2. Create virtual environment
uv venv && source .venv/bin/activate

# 3. Install dependencies
uv pip install -r requirements.txt

# 4. Set up environment variables
cp .env.example .env
# Edit .env with your DATABASE_URL

# 5. Authenticate NotebookLM (for slide generation)
pip install notebooklm-py[browser]
python -m notebooklm login

# 6. Run the application
streamlit run app.py
```

### Environment Variables

| Variable | Required | Description |
|----------|----------|-------------|
| `DATABASE_URL` | Yes | PostgreSQL connection string (Neon) |

---

## Agent System

All AI processing uses the **Claude Agent SDK** via the `courseware_agents/` module:

| Agent | Input | Output |
|-------|-------|--------|
| `cp_interpreter` | Parsed Course Proposal | Structured JSON context |
| `assessment_generator` | Course context + K/A statements | Assessment questions (9 types) |
| `slides_agent` | Document text | Enhanced slide instructions |

```python
import asyncio
from courseware_agents import interpret_cp, generate_assessments

# Interpret a Course Proposal
context = asyncio.run(interpret_cp("output/parsed_cp.md"))
```

---

## Skills System

Claude Code skills are defined in `.claude/skills/`:

| Skill | Description |
|-------|-------------|
| `generate_courseware` | Generate AP, FG, LG documents |
| `generate_lesson_plan` | Generate Lesson Plans with barrier algorithm |
| `generate_assessment` | Create 9 assessment types |
| `generate_slides` | Generate slides with NotebookLM MCP |
| `generate_brochure` | Create marketing brochures |
| `courseware_audit` | Verify supporting documents |

---

## Contributing

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

- [Anthropic](https://anthropic.com) — Claude Agent SDK
- [Streamlit](https://streamlit.io) — Web App Framework
- [NotebookLM](https://notebooklm.google.com) — Slide Generation
- [SkillsFuture Singapore](https://www.skillsfuture.gov.sg/) — WSQ Framework
- [Neon](https://neon.tech) — Serverless PostgreSQL

---

<div align="center">

**Made with love for Singapore's Training Providers**

</div>
