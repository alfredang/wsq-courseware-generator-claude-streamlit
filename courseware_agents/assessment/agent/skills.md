# Assessment Generator Agent — Skills

## Purpose
Generates assessment questions for multiple assessment types based on course K/A statements.

## Skills
1. **Generate SAQ Questions** — Short Answer Questions mapped to K statements
2. **Generate PP Scenarios** — Practical Performance tasks mapped to A statements
3. **Generate CS Scenarios** — Case Study scenarios with analysis questions
4. **Generate PRJ Briefs** — Project-based assessment briefs
5. **Generate ASGN Tasks** — Assignment tasks with rubrics
6. **Generate OI Questions** — Oral Interview question sets
7. **Generate DEM Tasks** — Demonstration assessment criteria
8. **Generate RP Scenarios** — Role Play scenarios with evaluation criteria
9. **Generate OQ Questions** — Oral Questioning question sets
10. **Map K/A to Questions** — Links each question to specific K/A competency statements

## Model
- **Claude Sonnet 4** (`claude-sonnet-4-20250514`)

## Supported Assessment Types
| Code | Full Name |
|------|-----------|
| SAQ | Short Answer Questions |
| PP | Practical Performance |
| CS | Case Study |
| PRJ | Project |
| ASGN | Assignment |
| OI | Oral Interview |
| DEM | Demonstration |
| RP | Role Play |
| OQ | Oral Questioning |

## Input
- FG data + K/A statements + course context

## Output
- JSON with questions per assessment type (question, scenario, answer, K/A mapping)
