# CP Interpreter Agent — Tools

## Tools Used

| Tool | Purpose | When Used |
|------|---------|-----------|
| **Read** | Read the parsed CP markdown file | Always |
| **WebFetch** | Fetch course info from provider website | Only when course URL is provided |

## Configuration
- **Max Turns:** 3 (or 5 when WebFetch is enabled)
- **Permission Mode:** bypassPermissions

## Template
- `courseware_agents/cp_interpreter/templates/cp_interpretation.md` — System prompt for extraction
- `courseware_agents/cp_interpreter/templates/tsc_agent.md` — TSC code extraction prompt
