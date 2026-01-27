# Core Features

The system is packed with features designed to handle every aspect of courseware development.

## 📄 Course Proposal (CP) Generation
Automatically extract information from **TSC (Training Specification Content)** documents to generate professional Course Proposals in Excel or Word formats.

## 📝 Assessment Materials
Generate a complete set of assessment tools:
- **SAQ**: Short Answer Questions
- **CS**: Case Study scenarios
- **PP**: Practical Performance checklists

## 📚 Courseware Suite
Generate the full pedagogical package for a course:
- **Learning Guide (LG)**: Comprehensive material for learners.
- **Facilitator Guide (FG)**: Detailed instructions for trainers.
- **Lesson Plan (LP)**: Minute-by-minute breakdown of the training.
- **Assessment Plan (AP)**: Mapping of outcomes to assessment methods.

## 🎯 Presentation Slides
Generate professional presentation slides from course materials using **NotebookLM MCP**:
- Upload Facilitator Guide, Learner Guide, or Course Proposal
- Configure slides per topic and speaker notes
- Export to PowerPoint, PDF, or Google Slides format

## 🎨 Marketing Brochures
Scrape course information from websites or parse existing documents to create sleek, print-ready HTML and PDF brochures.

## 🔍 Document Verification
An AI agent capable of verifying company UENs, checking document completeness, and extracting key entities from supporting documents.

## 💬 Skills System
A skill-driven AI assistant available on every page:
- **Skill Commands**: Type `/generate_slides` or other commands to navigate
- **Contextual Help**: The assistant uses skill definitions to provide guidance
- **Extensible**: Add new skills by creating markdown files in `.skills/` folder

### Available Skill Commands
| Command | Description |
|---------|-------------|
| `/generate_course_proposal` | Navigate to Course Proposal generation |
| `/generate_assessment_plan` | Navigate to Assessment Plan generation |
| `/generate_facilitator_guide` | Navigate to Facilitator Guide generation |
| `/generate_learner_guide` | Navigate to Learner Guide generation |
| `/generate_lesson_plan` | Navigate to Lesson Plan generation |
| `/generate_assessment` | Navigate to Assessment generation |
| `/generate_slides` | Navigate to Slides generation |
