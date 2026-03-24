# Infographic Agent (Slide Pipeline Phase 4) — Skills

## Purpose
Renders content blocks into PNG infographic images using AntV visualization library and Playwright browser.

## Skills
1. **Generate AntV DSL** — Creates AntV chart specification from content block data
2. **Deterministic Fallback** — Uses `build_antv_dsl()` if AI-generated DSL fails
3. **Render HTML to PNG** — Converts AntV HTML to PNG via Playwright browser
4. **Template Selection** — Supports 65+ AntV templates across 9 visualization types:
   - overview (12 templates), process (14), comparison (5), cycle (4)
   - hierarchy (4), statistics (8), timeline (4), relationship (2), quadrant (3)
5. **Retry Logic** — 3 retries per infographic (5s/8s/12s timeouts)
6. **Memory Management** — Browser restarted between topics to prevent memory exhaustion
7. **Icon Loading** — 3s AbortController timeout for external icon fetching

## Model
- **Claude Haiku 3.5** (`claude-3-5-haiku-20241022`)

## Rendering Pipeline
```
Content Block + Template Name
        │
        ▼
  AI generates AntV DSL (or deterministic fallback)
        │
        ▼
  DSL embedded in HTML with INLINED AntV script
        │
        ▼
  Playwright browser renders HTML → PNG (1792x1024)
```

## Input
- Content block (title, desc, items)
- Template name (from Editor Agent)
- Course title for context

## Output
- PNG image file (1792x1024 pixels)
