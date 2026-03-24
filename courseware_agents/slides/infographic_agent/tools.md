# Infographic Agent (Slide Pipeline Phase 4) — Tools

## Tools Used

| Tool | Purpose |
|------|---------|
| *None (AI)* | AntV DSL generation uses no Claude tools |
| **Playwright** | Headless browser for HTML → PNG rendering |
| **AntV Script** | Inlined JavaScript for infographic rendering |

## Configuration
- **Model:** Claude Haiku 3.5 (`claude-3-5-haiku-20241022`)
- **Max Turns:** 2
- **Canvas Size:** 1792 x 1024 pixels
- **Retry Strategy:** 3 attempts (5s / 8s / 12s timeouts)
- **Browser Flags:** `--disable-gpu --no-sandbox --disable-dev-shm-usage --disable-web-security --allow-file-access-from-files`

## Critical Rule
AntV script MUST be **inlined** into HTML from `courseware_agents/slides/templates/infographic.min.js`.
NEVER use `<script src="...">` — Windows file:// cross-origin blocks CDN and local file references.

## Templates
- `courseware_agents/slides/templates/infographic.min.js` — AntV script (cached in `_ANTV_SCRIPT_CACHE`)
- 65+ AntV visualization templates mapped in `infographic_agent.py`
