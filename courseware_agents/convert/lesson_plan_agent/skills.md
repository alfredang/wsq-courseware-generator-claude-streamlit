# Convert Lesson Plan Agent — Skills

## Purpose
Extracts structured lesson plan data from existing LP documents and rebuilds them using the standardised WSQ LP template.

## Skills
1. **Schedule Extraction** — Extracts full timetable with day/session structure
2. **Session Parsing** — Extracts time slots, topics, instructional methods, resources per session
3. **Metadata Extraction** — Extracts course title, TGS code, company name, hours
4. **Template Filling** — Fills standardised LP DOCX template using docxtpl (Jinja2)

## Input
- Existing Lesson Plan DOCX files (any format)

## Output
- Standardised WSQ Lesson Plan DOCX files

## Templates
- `courseware_agents/lesson_plan/templates/LP_TGS-Ref-No_Course-Title_v1.docx`
