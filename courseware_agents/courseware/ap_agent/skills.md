# Assessment Plan (AP) Agent — Skills

## Purpose
Generates the Assessment Plan and Assessment Summary Report documents from CP data.

## Skills
1. **Generate Assessment Plan (AP)** — Creates the full AP document with assessment specifications, marking schemes, and evidence requirements
2. **Generate Assessment Summary Report (ASR)** — Creates the ASR document summarizing assessment outcomes
3. **Generate Assessment Documents** — Produces individual assessment papers per assessment method (SAQ, PP, CS, etc.)
4. **Map K/A Statements** — Maps Knowledge and Ability statements to assessment methods
5. **Format Assessment Ratios** — Formats assessor-to-candidate ratios per method

## Model
- **No AI** — Pure Python template filling using `docxtpl`

## Input
- Structured JSON context from CP Interpreter

## Output
- `AP_TGS-{ref}_{course_title}_v1.docx`
- `ASR_TGS-{ref}_{course_title}_v1.docx`
- Individual assessment papers per method
