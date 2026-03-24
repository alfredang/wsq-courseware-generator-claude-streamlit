# Content Generator Agent (Slide Pipeline Phase 2) — Tools

## Tools Used

| Tool | Purpose |
|------|---------|
| **WebSearch** | Supplementary search only if research data is thin |

## Configuration
- **Model:** Claude Haiku 3.5 (`claude-3-5-haiku-20241022`)
- **Max Turns:** 5
- **Tools:** `["WebSearch"]` (supplementary only)
- **Default Blocks Per Topic:** 6

## Template
- System prompt embedded in `courseware_agents/slides/content_generator_agent.py`
