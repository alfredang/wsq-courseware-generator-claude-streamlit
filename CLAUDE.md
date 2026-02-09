# CLAUDE.md - Project Context for Claude Code

## Project Overview

**WSQ Courseware Generator** - An AI-powered platform for generating Singapore Workforce Skills Qualifications (WSQ) training materials using Claude AI.

## Tech Stack

| Component | Technology |
|-----------|------------|
| UI Framework | Streamlit 1.30+ |
| Backend | Python 3.13 |
| LLM | Claude API (Anthropic) |
| Database | PostgreSQL (Neon), SQLite (settings) |
| Deployment | Docker, Hugging Face Spaces |

## Project Structure

```
courseware_claude_streamlit/
├── app.py                    # Main Streamlit application (sidebar, nav, routing)
├── .streamlit/               # Streamlit configuration
│   └── config.toml           # Server and theme settings
├── generate_cp/              # Course Proposal generation (10 agents)
│   ├── app.py                # Streamlit page UI
│   ├── main.py               # Orchestration pipeline
│   └── agents/               # Claude agent modules
├── generate_assessment/      # Assessment generation (9 agents)
│   ├── assessment_generation.py  # Streamlit page UI
│   └── utils/                # Claude agent modules (claude_agentic_*.py)
├── generate_ap_fg_lg_lp/     # Courseware documents (4 agents)
│   ├── courseware_generation.py  # Streamlit page UI
│   └── utils/                # Agent + template modules
├── generate_slides/          # Slides generation
│   └── slides_generation.py  # Streamlit page UI
├── generate_brochure/        # Brochure generation
│   └── brochure_generation.py  # Streamlit page UI
├── add_assessment_to_ap/     # Annex assessments to AP
│   └── annex_assessment_v2.py  # Streamlit page UI
├── check_documents/          # Document verification
│   └── sup_doc.py            # Streamlit page UI
├── courseware_agents/        # Shared agent utilities (Claude SDK)
├── settings/                 # API & model configuration
│   ├── settings.py           # Settings page UI
│   ├── admin_auth.py         # Authentication
│   ├── api_manager.py        # API key management
│   ├── api_database.py       # SQLite database
│   └── model_configs.py      # Claude model definitions
├── company/                  # Company management
│   ├── company_settings.py   # Company management UI
│   └── company_manager.py    # Company utilities
├── skills/                   # NLP skill matching
├── utils/                    # Shared utilities
├── docs/                     # Documentation
├── .claude/                  # Claude Code configuration
│   ├── settings.local.json   # Local settings
│   └── skills/               # Skill definitions (13 skills)
└── public/                   # Static assets
```

## Key Patterns

### Streamlit Patterns
- Use `st.session_state` for state management
- Use `st.sidebar` with `option_menu` for navigation
- Use `st.file_uploader()` for file uploads
- Use `st.download_button()` for file downloads
- Use `st.spinner()` for long-running operations
- Use lazy loading pattern for module pages

### Agent Pattern
Each generation module follows this pattern:
```python
# agents/<agent_name>.py
async def run_agent(input_data: dict) -> dict:
    # 1. Extract data from input
    # 2. Call Claude API with prompt
    # 3. Parse and return structured output
```

### Claude API Usage
```python
from anthropic import Anthropic

client = Anthropic()  # Uses ANTHROPIC_API_KEY from env

response = client.messages.create(
    model="claude-sonnet-4-20250514",
    max_tokens=4096,
    messages=[{"role": "user", "content": prompt}]
)
```

## Environment Variables

```bash
ANTHROPIC_API_KEY=sk-ant-...     # Required - Claude API
DATABASE_URL=postgresql://...     # Required - Neon PostgreSQL
```

## Skills System

Skills are defined in `.claude/skills/<skill_name>/`:
- `SKILL.md` - Command, keywords, response template
- `README.md` - Developer documentation
- `examples.md` - Example prompts
- `reference/` - Technical reference docs for agents

Skills use fuzzy matching via `rapidfuzz` to match user intents.

**Execution**: All skills run using **Claude Code with subscription plan** (not pay-as-you-go API).

## Document Generation

Generated documents use templates stored in `generate_ap_fg_lg_lp/utils/`:
- Assessment Plan (AP)
- Facilitator Guide (FG)
- Learner Guide (LG)
- Lesson Plan (LP)

Templates use `docxtpl` (Jinja2 syntax) for variable substitution. Slide templates are in `.claude/skills/generate_slides/templates/`.

## Coding Conventions

- Use `async/await` for all I/O operations
- Use type hints for function signatures
- Keep agents modular and single-purpose
- Store prompts in separate files under `prompts/`
- Use `st.success()` / `st.error()` for user feedback

## Common Commands

```bash
# Run locally
streamlit run app.py

# Build Docker
docker build -t wsq-courseware .

# Run Docker
docker run -p 7860:7860 --env-file .env wsq-courseware
```

## Models

| Model | ID | Use Case |
|-------|------|----------|
| Claude Sonnet 4 | `claude-sonnet-4-20250514` | Default - balanced |
| Claude Opus 4.5 | `claude-opus-4-5-20250130` | Complex reasoning |
| Claude Haiku 3.5 | `claude-3-5-haiku-20241022` | Fast tasks |
