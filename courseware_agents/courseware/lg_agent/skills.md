# Learner Guide (LG) Agent — Skills

## Purpose
Generates the Learner Guide document that trainees receive during the course.

## Skills
1. **Generate Learner Guide** — Creates the full LG document with learning content and activities
2. **Format Topic Content** — Organizes topics with bullet points per Learning Unit
3. **Include Learning Outcomes** — Documents LO and ELO statements
4. **Include K/A Statements** — Lists Knowledge and Ability competency statements per LU
5. **Course Overview** — Includes auto-generated course description

## Model
- **No AI** — Pure Python template filling using `docxtpl`

## Input
- Structured JSON context from CP Interpreter

## Output
- `LG_TGS-{ref}_{course_title}_v1.docx`
