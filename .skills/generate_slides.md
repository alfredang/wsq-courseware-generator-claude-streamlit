# Generate Slides

## Command
`/generate_slides` or `generate_slides`

## Navigate
Generate Slides

## Description
Help users create PowerPoint presentation slides from course materials using NotebookLM MCP.

## Response
Taking you to **Generate Slides**. Upload your course materials and I'll generate professional presentation slides using NotebookLM.

## Instructions
When users ask about creating slides, presentations, PPT, or PowerPoint:

1. **Required Input**: Course materials (Facilitator Guide, Learner Guide, or Course Proposal)
2. **Process Using NotebookLM MCP**:
   - Create a notebook for the course content
   - Add source materials (documents, text, or URLs)
   - Use `generate_slide_deck` to create presentation
   - Download slides in presentation format
3. **MCP Tools Available**:
   - `create_notebook` - Create a new notebook for the course
   - `add_source_url` - Import web content as source
   - `add_source_text` - Add text content directly
   - `generate_slide_deck` - Generate PowerPoint-style slides
   - `ask_notebook` - Query content for specific sections
4. **Slide Generation Tips**:
   - Include clear learning objectives per section
   - Break content into digestible chunks
   - Add key points and summaries
   - Include speaker notes for facilitators
5. **Best Practices**:
   - Use Facilitator Guide for comprehensive slides
   - Structure slides by lesson/session
   - Include assessment reminders
   - Keep text minimal, focus on key points

## MCP Configuration
NotebookLM MCP server provides:
- `list_notebooks` - View existing notebooks
- `create_notebook` - Create new notebook
- `add_source_url` - Add URL sources
- `add_source_text` - Add text sources
- `generate_slide_deck` - Create presentations
- `ask_notebook` - Query notebook content
- `get_notebook_summary` - Get content summary

## Capabilities
- Generate professional presentation slides from course materials
- Create slides aligned with learning outcomes
- Structure content by sessions/lessons
- Include facilitator notes
- Support multiple input formats (FG, LG, CP)
- Uses NotebookLM MCP for AI-powered slide generation
