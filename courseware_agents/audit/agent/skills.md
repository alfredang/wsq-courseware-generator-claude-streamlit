# Audit Agent — Skills

## Purpose
Extracts fields from courseware documents and cross-checks them against the Course Proposal (CP).

## Skills
1. **Extract Course Title** — Identifies the course title from any document type
2. **Extract TGS Reference** — Finds TGS reference code
3. **Extract Topics** — Lists all topics/learning units found in the document
4. **Extract Duration Fields** — Training hours, assessment hours
5. **Extract Company Info** — Company name, UEN
6. **Extract Learning Outcomes** — LO/ELO statements
7. **Extract K/A Statements** — Knowledge and Ability competency statements
8. **Extract Assessment Methods** — Assessment types and durations
9. **Extract Instructional Methods** — Teaching methods used
10. **Extract TSC Info** — TSC code and title
11. **Cross-Check Against CP** — Compares extracted values with CP source of truth

## Model
- **Claude Sonnet 4** (`claude-sonnet-4-20250514`)

## Audit Rules
All audit check items and extraction rules are defined in a single source of truth:
`courseware_agents/audit/templates/audit_extraction.md`

No hardcoded rules in Python — edit the .md file to add/remove/change audit fields.

## Input
- Document text (any courseware type: AP, FG, LG, LP)
- Document type identifier

## Output
- JSON with extracted field values per document
