# CP Interpreter Agent — Skills

## Purpose
Extracts structured course data from raw Course Proposal (CP) documents (DOCX or XLSX format).

## Skills
1. **Parse CP Document** — Reads the raw CP and identifies all course components
2. **Extract Course Metadata** — Course title, TGS reference code, TSC code/title
3. **Extract Learning Units** — LU titles, topics, bullet points per LU
4. **Extract K/A Statements** — Knowledge (K) and Ability (A) competency statements
5. **Extract Assessment Info** — Assessment methods, durations, ratios
6. **Extract Instructional Methods** — Teaching methods and trainer-to-learner ratios
7. **Generate Course Overview** — Auto-generates a course description from extracted data
8. **Web Enrichment** — Fetches additional course info from provider URL (if provided)

## Model
- **Claude Sonnet 4** (`claude-sonnet-4-20250514`)

## Input
- Raw CP document (parsed to markdown)
- Optional: Course URL for web enrichment

## Output
- Structured JSON with all course data (used by all downstream generators)
