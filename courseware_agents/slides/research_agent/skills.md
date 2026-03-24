# Research Agent (Slide Pipeline Phase 1) — Skills

## Purpose
Searches the web for relevant sources and data per topic to enrich slide content.

## Skills
1. **Web Research** — Performs exactly 2 WebSearch calls per topic
2. **Source Extraction** — Extracts 3-5 credible sources from search snippets
3. **Key Statistics** — Identifies quantitative data, percentages, figures
4. **Infographic Data Tagging** — Tags data for visualization:
   - `chart_data` — Numbers suitable for charts/graphs
   - `process_steps` — Sequential steps or procedures
   - `comparison_items` — Items to compare side by side
   - `hierarchy_data` — Hierarchical/tree structures
   - `timeline_data` — Chronological events

## Model
- **Claude Haiku 3.5** (`claude-3-5-haiku-20241022`)

## Input
- Topic title + bullet points from CP
- Course title and LO description for context

## Output
- JSON with sources, summary, key_statistics, infographic_data
