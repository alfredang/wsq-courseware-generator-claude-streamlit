# Create GitHub README

## Command
`/create_github_readme` or `create_github_readme`

## Keywords
readme, github readme, create readme, generate readme, project readme, documentation, readme.md, update readme, write readme

## Description
Generate a professional GitHub README.md file for the WSQ Courseware Generator project following open standards.

## Response
I'll generate a comprehensive GitHub README.md for the WSQ Courseware Generator project.

## Instructions
When this skill is invoked, generate a README.md file with the following sections:

### Template Structure

```markdown
<div align="center">

# WSQ Courseware Generator

[![Python](https://img.shields.io/badge/Python-3.13-3776AB?style=for-the-badge&logo=python&logoColor=white)](https://python.org)
[![Chainlit](https://img.shields.io/badge/Chainlit-2.0+-00ADD8?style=for-the-badge&logo=chainlit&logoColor=white)](https://chainlit.io)
[![Claude](https://img.shields.io/badge/Claude-Anthropic-orange?style=for-the-badge&logo=anthropic&logoColor=white)](https://anthropic.com)
[![License](https://img.shields.io/badge/License-MIT-green?style=for-the-badge)](LICENSE)
[![Docker](https://img.shields.io/badge/Docker-Ready-2496ED?style=for-the-badge&logo=docker&logoColor=white)](Dockerfile)

**AI-Powered Courseware Generation Platform for WSQ Training Providers**

[Demo](https://huggingface.co/spaces/YOUR_USERNAME/wsq-courseware-generator) · [Report Bug](https://github.com/alfredang/courseware_claude_agents/issues) · [Request Feature](https://github.com/alfredang/courseware_claude_agents/issues)

</div>

---

## About The Project

WSQ Courseware Generator is an AI-powered platform that automates the creation of Singapore Workforce Skills Qualifications (WSQ) training materials. Using Claude AI agents, it transforms Training & Competency Standards (TSC) documents into complete courseware packages.

### Key Features

- **Course Proposal Generation** — Extract competency units from TSC and generate structured proposals
- **Courseware Creation** — Auto-generate Assessment Plans, Facilitator Guides, Learner Guides, and Lesson Plans
- **Assessment Generation** — Create various assessment types (MCQ, case studies, practical assessments)
- **Slides Generation** — Generate presentation slides with NotebookLM integration
- **Brochure Creation** — Design marketing brochures for courses
- **Document Verification** — Check and validate courseware documents

---

## Tech Stack

| Category | Technology |
|----------|------------|
| **Frontend** | Chainlit 2.0+ |
| **Backend** | Python 3.13 |
| **AI/LLM** | Claude API (Anthropic) |
| **Database** | PostgreSQL (Neon) |
| **Deployment** | Docker, Hugging Face Spaces |
| **Document Processing** | python-docx, docxtpl, openpyxl |

---

## Architecture

```
┌─────────────────────────────────────────────────────────────────┐
│                        Chainlit UI                               │
│              (Chat Interface + File Upload)                      │
└─────────────────────────┬───────────────────────────────────────┘
                          │
┌─────────────────────────▼───────────────────────────────────────┐
│                    Chat Profiles                                 │
│  ┌──────────┐ ┌──────────┐ ┌──────────┐ ┌──────────┐           │
│  │ Course   │ │Courseware│ │Assessment│ │  Slides  │  ...      │
│  │ Proposal │ │          │ │          │ │          │           │
│  └────┬─────┘ └────┬─────┘ └────┬─────┘ └────┬─────┘           │
└───────┼────────────┼────────────┼────────────┼──────────────────┘
        │            │            │            │
┌───────▼────────────▼────────────▼────────────▼──────────────────┐
│                    Claude AI Agents                              │
│  ┌─────────────┐  ┌─────────────┐  ┌─────────────┐              │
│  │ CP Agent    │  │ CW Agent    │  │ Assessment  │   ...       │
│  │ (Extract &  │  │ (Generate   │  │ Agent       │              │
│  │  Generate)  │  │  Documents) │  │             │              │
│  └─────────────┘  └─────────────┘  └─────────────┘              │
└─────────────────────────┬───────────────────────────────────────┘
                          │
┌─────────────────────────▼───────────────────────────────────────┐
│                Document Generation Engine                        │
│        (Templates + python-docx + docxtpl)                      │
└─────────────────────────────────────────────────────────────────┘
```

---

## Project Structure

```
courseware_claude/
├── app.py                      # Main Chainlit application
├── Dockerfile                  # Docker configuration
├── requirements.txt            # Python dependencies
├── .chainlit/
│   └── config.toml            # Chainlit configuration
├── chainlit_modules/          # Chainlit module handlers
│   ├── course_proposal.py
│   ├── courseware.py
│   ├── assessment.py
│   ├── slides.py
│   └── ...
├── generate_cp/               # Course Proposal generation
│   ├── main.py
│   └── utils/
├── generate_ap_fg_lg_lp/      # Courseware generation
├── generate_assessment/       # Assessment generation
├── generate_slides/           # Slides generation
├── generate_brochure/         # Brochure generation
├── settings/                  # Configuration & API management
├── company/                   # Company/organization management
├── skills/                    # NLP skill matching
├── templates/                 # Document templates
└── public/                    # Static assets (CSS, images)
```

---

## Getting Started

### Prerequisites

- Python 3.13+
- Docker (optional, for containerized deployment)
- Anthropic API Key

### Local Development

1. **Clone the repository**
   ```bash
   git clone https://github.com/alfredang/courseware_claude_agents.git
   cd courseware_claude_agents
   ```

2. **Create virtual environment**
   ```bash
   python -m venv venv
   source venv/bin/activate  # On Windows: venv\Scripts\activate
   ```

3. **Install dependencies**
   ```bash
   pip install -r requirements.txt
   ```

4. **Set up environment variables**
   ```bash
   cp .env.example .env
   # Edit .env with your API keys
   ```

5. **Run the application**
   ```bash
   chainlit run app.py -w
   ```

6. **Open in browser**
   ```
   http://localhost:8000
   ```

### Docker Deployment

```bash
docker build -t wsq-courseware .
docker run -p 7860:7860 --env-file .env wsq-courseware
```

### Hugging Face Spaces Deployment

1. Create a new Space at [huggingface.co/spaces](https://huggingface.co/spaces)
2. Select **Docker** as SDK
3. Connect your GitHub repository
4. Add secrets in Settings:
   - `ANTHROPIC_API_KEY`
   - `DATABASE_URL`
   - `CHAINLIT_AUTH_SECRET`

---

## Environment Variables

| Variable | Description | Required |
|----------|-------------|----------|
| `ANTHROPIC_API_KEY` | Anthropic Claude API key | Yes |
| `DATABASE_URL` | PostgreSQL connection string | Yes |
| `CHAINLIT_AUTH_SECRET` | Session encryption secret | Yes |

---

## Contributing

Contributions are welcome! Feel free to:

- Fork the repository
- Create a feature branch (`git checkout -b feature/AmazingFeature`)
- Commit your changes (`git commit -m 'Add some AmazingFeature'`)
- Push to the branch (`git push origin feature/AmazingFeature`)
- Open a Pull Request

Join the discussion in [GitHub Discussions](https://github.com/alfredang/courseware_claude_agents/discussions).

---

## License

Distributed under the MIT License. See `LICENSE` for more information.

---

## Developed By

<div align="center">

**Tertiary Infotech Academy Pte. Ltd.**

Singapore

</div>

---

## Acknowledgements

- [Anthropic](https://anthropic.com) — Claude AI API
- [Chainlit](https://chainlit.io) — Chat UI Framework
- [Hugging Face](https://huggingface.co) — Model Hosting & Spaces
- [SkillsFuture Singapore](https://www.skillsfuture.gov.sg/) — WSQ Framework
- All contributors and testers who helped improve this project

---

<div align="center">

Made with ❤️ for Singapore's Training Providers

</div>
```

## Capabilities
- Generate complete README.md following GitHub best practices
- Include all standard sections (About, Tech Stack, Setup, etc.)
- Add technology badges
- Create architecture diagrams using ASCII art
- Document file structure
- Provide deployment instructions

## Next Steps
After generating the README:
1. Review and customize the content
2. Update placeholder URLs and usernames
3. Add screenshots if available
4. Commit to repository
