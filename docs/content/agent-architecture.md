# Multi-Agent Architecture

The WSQ Courseware Generator is powered by a sophisticated multi-agent system built on the **OpenAI Agents SDK**.

## Orchestrator Pattern

The system uses an **Orchestrator Agent** as the central brain. It interacts with the user via a chat interface and intelligently routes requests to specialized agents.

### Specialized Agents

| Agent | Responsibility |
|-------|----------------|
| **CP Agent** | Handles TSC parsing and CP generation. |
| **Courseware Agent** | Manages LG, FG, LP, and AP creation. |
| **Assessment Agent** | Focused on generating assessment papers. |
| **Brochure Agent** | Specialized in web scraping and marketing content. |
| **Document Agent** | Performs verification and entity extraction. |

## Agent Handoffs

When a user asks "Generate a course proposal for this file," the Orchestrator identifies the intent and **hands off** the conversation thread to the CP Agent. This ensures that the agent with the specific tools and prompts for the task is the one executing it.

## MCP (Model Context Protocol)

The agents are equipped with tools connected via MCP servers:
- **Filesystem**: Reading and writing local files.
- **PostgreSQL**: Accessing company and training data.
- **Fetch**: Navigating the web for brochure data.
- **Memory**: Retaining context across different parts of the workflow.
