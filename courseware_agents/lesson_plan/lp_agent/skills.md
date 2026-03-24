# Lesson Plan (LP) Agent — Skills

## Purpose
Generates the Lesson Plan document with a timetable schedule using a barrier algorithm.

## Skills
1. **Generate Timetable** — Creates daily schedule using barrier-based algorithm
2. **Split Topics Across Barriers** — Handles topic splitting across lunch/day-end with "(Cont'd)" labels
3. **Schedule Assessment** — Places assessment session on last day (4:00 PM - 6:00 PM)
4. **Fill Breaks** — Ensures each day is exactly 9:00 AM - 6:00 PM with break fillers
5. **Map Instructional Methods** — Assigns teaching methods and resources per session

## Model
- **No AI** — Pure Python barrier algorithm + `docxtpl` template filling

## Schedule Rules
- Daily hours: 9:00 AM - 6:00 PM
- Lunch: 12:30 PM - 1:15 PM (45 mins, fixed)
- Assessment: 4:00 PM - 6:00 PM (last day only)
- Minimum session: 15 minutes
- Topic duration: `instructional_hours * 60 / num_topics` minutes

## Input
- Structured JSON context from CP Interpreter
- Organisation name

## Output
- `LP_TGS-{ref}_{course_title}_v1.docx`
