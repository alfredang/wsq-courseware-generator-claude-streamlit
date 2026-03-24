# Editor Agent (Slide Pipeline Phase 3) — Skills

## Purpose
Designs the complete slide deck structure and assigns AntV infographic templates to each content block.

## Skills
1. **Design Deck Structure** — Plans the full slide deck layout (intro + content + closing)
2. **Assign Templates** — Maps each content block to one of 65+ AntV infographic templates
3. **Ensure Visual Flow** — Prevents consecutive duplicate templates for variety
4. **Calculate Slide Positions** — Maps blocks to exact slide numbers in the deck
5. **Apply WSQ Standards** — Includes standard WSQ intro slides (10) and closing slides (7)

## Model
- **Claude Haiku 3.5** (`claude-3-5-haiku-20241022`)

## Input
- Course context from CP
- Research data from Phase 1
- Content blocks from Phase 2

## Output
- Complete skeleton with infographic_assignments (topic -> block -> template)
