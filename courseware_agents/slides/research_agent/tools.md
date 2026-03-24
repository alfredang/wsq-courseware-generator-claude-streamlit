# Research Agent (Slide Pipeline Phase 1) — Tools

## Tools Used

| Tool | Purpose |
|------|---------|
| **WebSearch** | Search the web for topic-relevant sources and data |

## Configuration
- **Model:** Claude Haiku 3.5 (`claude-3-5-haiku-20241022`)
- **Max Turns:** 5
- **Tools:** `["WebSearch"]`
- **Note:** NO WebFetch — extracts info from search snippets only (faster)

## Template
- System prompt embedded in `courseware_agents/slides/research_agent.py`
