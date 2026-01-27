# Usage Guide

Step-by-step instructions for the most common tasks.

## 1. Using the Chat Interface (Recommended)
The easiest way to use the system is through the home page chat:
1. Upload your source file (e.g., TSC document).
2. Type: *"Please generate a Course Proposal from this file."*
3. The Orchestrator will process the request and provide download links.

## 2. Manual Courseware Generation
If you prefer the modular interface:
1. Select **"Generate CP"** or **"Courseware Suite"** from the sidebar.
2. Upload the required files (facilitator guide, proposal, etc.).
3. Choose your preferred AI model in the sidebar.
4. Click **Process** and wait for the documents to be generated.

## 3. Managing Models & Settings
1. Go to **Settings** → **LLM Models**.
2. Click **Fetch Models** to get the latest list from OpenRouter.
3. Use the ⭐ icon to set your preferred default models.
4. Enable or disable specific models to keep your selection list clean.

## 4. Company Branding
1. Go to **Settings** → **Companies**.
2. Add or select your organization.
3. Upload a logo and set company details. These will be automatically injected into generated documents.

## 5. Generating Presentation Slides
1. Select **"Generate Slides"** from the sidebar.
2. Upload your course material (Facilitator Guide, Learner Guide, or Course Proposal).
3. Configure options:
   - Slides per topic
   - Include speaker notes
   - Include section summaries
4. Click **Generate Presentation Slides**.
5. Download in your preferred format (PowerPoint, PDF, or Google Slides).

**Note**: This feature requires NotebookLM MCP server. See [notebooklm-mcp](https://github.com/alfredang/notebooklm-mcp) for setup.

## 6. Using the AI Assistant
The AI Assistant at the bottom of every page helps with WSQ courseware tasks:

### Quick Navigation
Type skill commands to navigate directly to modules:
- `/generate_course_proposal` - Go to CP generation
- `/generate_assessment_plan` - Go to Assessment Plan generation
- `/generate_facilitator_guide` - Go to Facilitator Guide generation
- `/generate_learner_guide` - Go to Learner Guide generation
- `/generate_lesson_plan` - Go to Lesson Plan generation
- `/generate_assessment` - Go to Assessment generation
- `/generate_slides` - Go to Slides generation

### Getting Help
Ask questions like:
- *"What documents do I need for assessment generation?"*
- *"How do I create a learning guide?"*
- *"What are the WSQ requirements for assessments?"*

The assistant uses skill definitions to provide accurate, contextual guidance.
