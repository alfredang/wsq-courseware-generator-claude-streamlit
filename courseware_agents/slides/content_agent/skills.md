# Content Generator Agent (Slide Pipeline Phase 2) — Skills

## Purpose
Transforms research data into structured content blocks for infographic slides.

## Skills
1. **Generate Content Blocks** — Creates 6 content blocks per topic (default)
2. **Assign Visualization Types** — Selects the best visualization for each block:
   - overview, process, comparison, cycle, hierarchy
   - statistics, timeline, relationship, quadrant
3. **Structure Data for Infographics** — Formats items with label (2-3 words) and desc (4-8 words)
4. **Ensure Visual Variety** — No consecutive duplicate visualization types
5. **Include Statistics** — Adds statistics block if quantitative data exists
6. **Include Process Flows** — Adds process block if steps/procedures exist

## Model
- **Claude Haiku 3.5** (`claude-3-5-haiku-20241022`)

## Input
- Research data from Phase 1 (Research Agent)
- Topic title and LO description

## Output
- JSON with content blocks (title, desc, items[], visualization_type)
