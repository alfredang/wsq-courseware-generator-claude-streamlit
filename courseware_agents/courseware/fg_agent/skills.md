# Facilitator Guide (FG) Agent — Skills

## Purpose
Generates the Facilitator Guide document that trainers use to deliver the course.

## Skills
1. **Generate Facilitator Guide** — Creates the full FG document with lesson plan, session guides, and facilitation notes
2. **Map Topics to Sessions** — Organizes topics into daily sessions with timing
3. **Include Assessment Details** — Embeds assessment specifications and marking criteria
4. **Format Instructional Methods** — Documents teaching methods per topic
5. **Include K/A Statements** — Maps K/A statements to each Learning Unit

## Model
- **No AI** — Pure Python template filling using `docxtpl`

## Input
- Structured JSON context from CP Interpreter
- Lesson plan schedule data

## Output
- `FG_TGS-{ref}_{course_title}_v1.docx`
