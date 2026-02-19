# CLAUDE.md - Project Context for Claude Code

## Project Overview

**WSQ Courseware Generator** - An AI-powered platform for generating Singapore Workforce Skills Qualifications (WSQ) training materials using Claude Agent SDK.

## Architecture

All AI processing uses the **Claude Agent SDK** (`claude-agent-sdk` package). The Streamlit UI handles file upload/download and previews. Agents in `courseware_agents/` handle interpretation, content generation, and entity extraction.

## Tech Stack

| Component | Technology |
|-----------|------------|
| UI Framework | Streamlit 1.30+ |
| Backend | Python 3.13 |
| AI Processing | Claude Agent SDK |
| Database | PostgreSQL (Neon) for companies, SQLite for settings |
| Templates | docxtpl (Jinja2 DOCX) |

## Project Structure

```
courseware_claude_streamlit/
├── app.py                       # Main Streamlit app (sidebar, nav, routing)
├── .streamlit/config.toml       # Streamlit configuration
├── courseware_agents/            # Claude Agent SDK wrappers
│   ├── __init__.py              # Package exports
│   ├── base.py                  # Core run_agent() / run_agent_json()
│   ├── cp_interpreter.py        # Course Proposal interpretation agent
│   ├── assessment_generator.py  # Assessment question generation agent
│   └── slides_agent.py          # Slide generation analysis agent
├── generate_ap_fg_lg/           # Courseware documents (AP, FG, LG)
│   ├── courseware_generation.py  # Streamlit page
│   └── utils/                   # Template filling modules
├── generate_lp/                 # Lesson Plan (standalone)
│   ├── lesson_plan_generation.py # Streamlit page
│   └── timetable_generator.py   # Pure Python barrier algorithm
├── generate_assessment/         # Assessment generation
│   └── assessment_generation.py # Streamlit page
├── generate_slides/             # Slides generation (NotebookLM MCP)
│   └── slides_generation.py
├── generate_brochure/           # Brochure generation (web scraping)
│   └── brochure_generation.py
├── add_assessment_to_ap/        # Annex assessments to AP
│   └── annex_assessment_v2.py
├── courseware_audit/             # Courseware audit / entity extraction
│   └── sup_doc.py
├── extract_course_info/         # CP parsing (pure Python, no AI)
│   └── extract_course_info.py
├── settings/                    # Settings
│   └── api_database.py          # SQLite (prompt templates)
├── company/                     # Company management (PostgreSQL)
│   ├── company_settings.py      # Company management UI
│   ├── company_manager.py       # Company utilities
│   └── database.py              # PostgreSQL connection
├── utils/                       # Shared utilities
│   ├── agent_runner.py          # Background agent job manager
│   ├── agent_status.py          # Agent status UI components
│   ├── helpers.py               # File & JSON utilities
│   └── prompt_template_editor.py # Prompt template editing UI
├── Courseware/                   # Generated courseware output (gitignored)
├── .claude/skills/              # Claude Code skill definitions
└── prompt_templates/            # Prompt template markdown files
```

## Key Patterns

### Agent Pattern (Claude Agent SDK)
All AI processing uses the `courseware_agents` module:
```python
import asyncio
from courseware_agents.cp_interpreter import interpret_cp

# Run agent to interpret Course Proposal
context = asyncio.run(interpret_cp("output/parsed_cp.md"))
```

The base agent wrapper (`courseware_agents/base.py`):
```python
from claude_agent_sdk import query, ClaudeAgentOptions

async def run_agent(prompt, system_prompt=None, tools=None):
    options = ClaudeAgentOptions(
        allowed_tools=tools or ["Read", "Glob", "Grep"],
        permission_mode="bypassPermissions",
    )
    async for message in query(prompt=prompt, options=options):
        # Process messages...
```

### Streamlit Patterns
- Use `st.session_state` for state management
- Use `st.sidebar` with `option_menu` for navigation
- Use `st.file_uploader()` for file uploads
- Use `st.download_button()` for file downloads
- Use `st.spinner()` for long-running operations
- Lazy loading pattern for module pages

### Generation Workflow
Each generation page follows this pattern:
1. **Upload** - User uploads CP/FG document
2. **Parse** - Pure Python parsing (no AI)
3. **Interpret with Agent** - Claude Agent SDK interprets content → JSON context
4. **Fill Templates** - docxtpl fills DOCX templates from JSON context
5. **Download** - User downloads generated documents

## Environment Variables

```bash
DATABASE_URL=postgresql://...     # Required - Neon PostgreSQL for company data
```

## Skills System

Skills are defined in `.claude/skills/<skill_name>/`:
- `SKILL.md` - Command, keywords, response template

**Execution**: All skills run using **Claude Code with subscription plan**.

## Document Generation

Templates stored in `generate_ap_fg_lg/utils/`:
- Assessment Plan (AP)
- Facilitator Guide (FG)
- Learner Guide (LG)
- Lesson Plan (LP)

Templates use `docxtpl` (Jinja2 syntax) for variable substitution.

### Lesson Plan Schedule Rules

The Lesson Plan uses a **barrier algorithm** for schedule building:

- **Daily hours**: 9:00 AM - 6:00 PM
- **Lunch**: Fixed 45 mins at 12:30 PM - 1:15 PM
- **Assessment**: Fixed 4:00 PM - 6:00 PM on last day only
- **Topic duration**: Each topic = `instructional_hours * 60 / num_topics` minutes
- **Topic splitting**: Topics CAN split across lunch/day-end barriers. Label: "T2: Name" then "T2: Name (Cont'd)"
- **Minimum session**: 15 minutes (if remaining < 15 mins before barrier, use Break)
- **Breaks**: Fill all gaps so each day is exactly 9am-6pm
- **Styling**: DOCX uses Calibri font, steel blue (#4472C4) table headers with white text

See `.claude/skills/generate_lesson_plan/SKILL.md` for the full algorithm.

## Coding Conventions

- Use `async/await` for agent operations
- Use type hints for function signatures
- Keep agents modular and single-purpose
- Store prompts in `prompt_templates/` directory
- Use `st.success()` / `st.error()` for user feedback

## Common Commands

```bash
# Run locally
streamlit run app.py
```

## Models

| Model | ID | Use Case |
|-------|------|----------|
| Claude Sonnet 4 | `claude-sonnet-4-20250514` | Default - balanced |
| Claude Opus 4.5 | `claude-opus-4-5-20251101` | Complex reasoning |
| Claude Haiku 3.5 | `claude-3-5-haiku-20241022` | Fast tasks |
