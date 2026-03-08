"""
Infographic Agent (Agent 4) — Multiple AntV Infographics per Topic

Phase 4 in the 5-phase pipeline. Generates MULTIPLE infographic images per topic
(one per content block, typically 4-6 per topic) using AntV Infographic DSL.

HYBRID APPROACH (AI-first, deterministic fallback):
  1. Claude Agent SDK generates optimized AntV DSL using the infographic-syntax-creator skill
  2. If AI fails → deterministic build_antv_dsl() produces valid DSL from structured data
  3. DSL → HTML → PNG via Playwright

Tools & Skills:
  - Claude Agent SDK with infographic-syntax-creator skill knowledge
  - Playwright (Chromium) for HTML → PNG screenshot
  - Deterministic DSL builder as fallback

AntV Infographic: https://github.com/antvis/Infographic
"""

import asyncio
import logging
import os
import tempfile
from typing import Optional
from generate_slides.multi_agent_config import (
    INFOGRAPHIC_MAX_TURNS,
    FAST_MODEL,
)

logger = logging.getLogger(__name__)

# No concurrency — sequential rendering with a single shared browser is most reliable

# ---------------------------------------------------------------------------
# AntV Infographic template mapping by visualization type
# ---------------------------------------------------------------------------
TEMPLATE_MAP = {
    "overview": [
        # Grid layouts (fill space well, best visual impact)
        "list-grid-badge-card",
        "list-grid-candy-card-lite",
        "list-grid-ribbon-card",
        # Zigzag layouts (use full canvas)
        "list-zigzag-down-compact-card",
        "list-zigzag-up-compact-card",
        "list-zigzag-down-simple",
        "list-zigzag-up-simple",
        # Row layouts (horizontal, good space usage)
        "list-row-horizontal-icon-arrow",
        "list-row-simple-illus",
        # Sector/done-list (fill space)
        "list-sector-plain-text",
        "list-column-done-list",
        # Column layouts last (can leave empty space)
        "list-column-vertical-icon-arrow",
        "list-column-simple-vertical-arrow",
    ],
    "process": [
        "sequence-snake-steps-compact-card",
        "sequence-snake-steps-simple",
        "sequence-snake-steps-underline-text",
        "sequence-roadmap-vertical-simple",
        "sequence-roadmap-vertical-plain-text",
        "sequence-stairs-front-compact-card",
        "sequence-stairs-front-pill-badge",
        "sequence-ascending-steps",
        "sequence-ascending-stairs-3d-underline-text",
        "sequence-color-snake-steps-horizontal-icon-line",
        "sequence-horizontal-zigzag-underline-text",
        "sequence-horizontal-zigzag-simple-illus",
        "sequence-zigzag-steps-underline-text",
        "sequence-mountain-underline-text",
        "sequence-filter-mesh-simple",
    ],
    "comparison": [
        "compare-binary-horizontal-badge-card-arrow",
        "compare-binary-horizontal-simple-fold",
        "compare-binary-horizontal-underline-text-vs",
        "compare-hierarchy-left-right-circle-node-pill-badge",
        "compare-swot",
    ],
    "cycle": [
        "sequence-circular-simple",
        "sequence-pyramid-simple",
        "sequence-cylinders-3d-simple",
        "sequence-zigzag-pucks-3d-simple",
    ],
    "hierarchy": [
        "hierarchy-tree-curved-line-rounded-rect-node",
        "hierarchy-tree-tech-style-badge-card",
        "hierarchy-tree-tech-style-capsule-item",
        "hierarchy-structure",
    ],
    "statistics": [
        "chart-pie-compact-card",
        "chart-pie-plain-text",
        "chart-pie-donut-plain-text",
        "chart-pie-donut-pill-badge",
        "chart-bar-plain-text",
        "chart-column-simple",
        "chart-line-plain-text",
        "chart-wordcloud",
    ],
    "timeline": [
        "sequence-timeline-simple",
        "sequence-timeline-rounded-rect-node",
        "sequence-timeline-simple-illus",
        "sequence-roadmap-vertical-simple",
    ],
    "relationship": [
        "relation-circle-icon-badge",
        "relation-circle-circular-progress",
    ],
    "quadrant": [
        "quadrant-quarter-simple-card",
        "quadrant-quarter-circular",
        "quadrant-simple-illus",
    ],
}

# Default icons for items missing icons
DEFAULT_ICONS = [
    "mdi/lightbulb", "mdi/check-circle", "mdi/star", "mdi/shield-check",
    "mdi/cog", "mdi/chart-line", "mdi/book-open", "mdi/account-group",
]


def _fuzzy_get_topic(mapping: dict, key: str) -> dict:
    """Fuzzy lookup for topic title keys (handles AI rephrasing)."""
    if not mapping or not key:
        return {}
    if key in mapping:
        return mapping[key]
    def _norm(s):
        return s.lower().replace(" ", "").replace("_", "").replace("-", "").strip()
    norm_key = _norm(key)
    for k, v in mapping.items():
        if _norm(k) == norm_key:
            return v
    key_lower = key.lower().strip()
    for k, v in mapping.items():
        k_lower = k.lower().strip()
        if key_lower in k_lower or k_lower in key_lower:
            return v
    return {}


# ---------------------------------------------------------------------------
# Deterministic AntV DSL builder (no agent call needed)
# ---------------------------------------------------------------------------

def _truncate(text: str, max_len: int) -> str:
    """Truncate text at word boundary without adding '..' markers.

    If text exceeds max_len, cuts at the last complete word that fits.
    Never leaves partial words or '..' — content looks complete.
    """
    if not text:
        return ""
    text = text.strip()
    if len(text) <= max_len:
        return text
    # Cut at last space before max_len to keep complete words
    cut = text[:max_len]
    last_space = cut.rfind(" ")
    if last_space > max_len // 2:
        return cut[:last_space].rstrip(".,;:-")
    # No good word boundary — just use the full cut
    return cut.rstrip(".,;:-")


def _safe_dsl_value(text: str) -> str:
    """Clean a text value for AntV DSL (remove newlines, backticks, etc.)."""
    if not text:
        return ""
    return text.replace("\n", " ").replace("`", "'").replace("\\", "").strip()


def _enforce_dsl_text_limits(dsl: str) -> str:
    """Post-process AI-generated DSL to enforce text length limits.

    Truncates labels, descriptions, and titles that exceed safe limits
    to prevent overflow/overlap in rendered infographics.
    Applies stricter limits for chart/sequence templates.
    """
    lines = dsl.split("\n")
    result = []

    # Detect template type from first line
    first_line = dsl.strip().split("\n")[0] if dsl.strip() else ""
    is_chart = "chart-" in first_line
    is_sequence = ("sequence-" in first_line or "zigzag" in first_line)
    is_horizontal = ("horizontal" in first_line or "snake" in first_line
                     or "color-snake" in first_line or "ascending" in first_line
                     or "stairs" in first_line)

    # Template-specific limits — generous to avoid mid-word truncation
    is_list = "list-" in first_line
    is_grid = "grid" in first_line
    is_column = "column" in first_line or "done-list" in first_line
    is_row = "row" in first_line

    if is_chart:
        label_max = 18       # Charts: labels under bars
        item_desc_max = 0    # NO descriptions for chart items — causes cutoff
        title_max = 45
        top_desc_max = 60
    elif is_sequence and is_horizontal:
        label_max = 20       # Horizontal process
        item_desc_max = 35   # Moderate descriptions
        title_max = 45
        top_desc_max = 55
    elif is_sequence:
        label_max = 22       # Vertical sequence
        item_desc_max = 45
        title_max = 45
        top_desc_max = 60
    elif is_list or is_grid or is_column or is_row:
        label_max = 28       # Lists/grids: plenty of room
        item_desc_max = 55   # Full descriptions OK
        title_max = 50
        top_desc_max = 65
    else:
        label_max = 25       # Default: generous
        item_desc_max = 50
        title_max = 45
        top_desc_max = 60

    item_count = 0
    max_items = 3 if (is_sequence and is_horizontal) else (4 if is_sequence else 5)
    in_items = False

    for line in lines:
        stripped = line.lstrip()
        indent_len = len(line) - len(stripped)
        indent = line[:indent_len]

        # Track items section
        if stripped == "items":
            in_items = True
            item_count = 0
            result.append(line)
            continue

        # Track sections that end items
        if stripped in ("theme", "data") and indent_len == 0:
            in_items = False

        # Count and limit items
        if in_items and stripped.startswith("- label "):
            item_count += 1
            if item_count > max_items:
                # Skip this item and all its children until next item or section end
                continue

        # Skip lines belonging to excess items
        if in_items and item_count > max_items and indent_len >= 4 and not stripped.startswith("- label "):
            if stripped in ("theme",):
                in_items = False
            else:
                continue

        # Truncate title lines
        if stripped.startswith("title "):
            value = _truncate(stripped[6:], title_max)
            result.append(f"{indent}title {value}")
        # Truncate desc lines — different limits for top-level vs item-level
        elif stripped.startswith("desc "):
            if indent_len >= 4 and in_items:
                # Item-level description
                if item_desc_max <= 0:
                    continue  # Skip desc entirely for charts
                value = _truncate(stripped[5:], item_desc_max)
            else:
                # Top-level description
                value = _truncate(stripped[5:], top_desc_max)
            result.append(f"{indent}desc {value}")
        # Truncate label lines
        elif stripped.startswith("- label "):
            value = _truncate(stripped[8:], label_max)
            result.append(f"{indent}- label {value}")
        elif stripped.startswith("label ") and indent_len >= 4:
            value = _truncate(stripped[6:], label_max)
            result.append(f"{indent}label {value}")
        else:
            result.append(line)
    return "\n".join(result)


def build_antv_dsl(content_block: dict, assigned_template: str) -> str:
    """Build AntV Infographic JSON options from a structured content block.

    Uses setOptions() API (v0.2.15 compatible) instead of legacy DSL syntax.
    Returns a JSON string with {template, title, data:{items}}.
    """
    import json as _json
    block_data = content_block.get("data", {})
    title = _truncate(block_data.get("title", ""), 50)
    items = block_data.get("items", [])

    # Limit items based on template type
    is_chart = assigned_template.startswith("chart-")
    is_sequence = (assigned_template.startswith("sequence-") or
                   assigned_template.startswith("list-zigzag"))
    is_horizontal = ("horizontal" in assigned_template or "snake" in assigned_template
                     or "ascending" in assigned_template or "stairs" in assigned_template)
    is_compare = assigned_template.startswith("compare-")

    if is_sequence and is_horizontal:
        items = items[:3]
    elif is_sequence:
        items = items[:4]
    elif is_chart:
        items = items[:4]
    elif is_compare:
        items = items[:4]
    else:
        items = items[:6]

    # Build items list
    json_items = []
    for i, item in enumerate(items):
        entry = {
            "label": _truncate(item.get("label", f"Point {i + 1}"), 28),
        }
        desc = item.get("desc", "")
        if desc and not is_chart:
            entry["desc"] = _truncate(desc, 55)
        icon = item.get("icon", DEFAULT_ICONS[i % len(DEFAULT_ICONS)])
        if icon and icon.startswith("mdi/"):
            entry["icon"] = icon
        else:
            entry["icon"] = DEFAULT_ICONS[i % len(DEFAULT_ICONS)]

        # Charts need numeric values
        if is_chart:
            value = item.get("value")
            if value is None or not isinstance(value, (int, float)):
                try:
                    value = int(value) if value else (i + 1) * 20
                except (ValueError, TypeError):
                    value = (i + 1) * 20
            entry["value"] = value

        # Handle children for compare/hierarchy
        children = item.get("children", [])
        if children:
            entry["children"] = []
            for ci, child in enumerate(children[:3]):
                child_entry = {
                    "label": _truncate(child.get("label", f"Sub {ci + 1}"), 25),
                    "icon": child.get("icon", DEFAULT_ICONS[ci % len(DEFAULT_ICONS)]),
                }
                child_desc = child.get("desc", "")
                if child_desc:
                    child_entry["desc"] = _truncate(child_desc, 40)
                entry["children"].append(child_entry)

        json_items.append(entry)

    # For compare templates, ensure exactly 2 root items with children
    if is_compare and len(json_items) >= 2:
        mid = max(1, len(json_items) // 2)
        group_a = json_items[:mid]
        group_b = json_items[mid:]
        root_a = group_a[0].copy()
        if len(group_a) > 1:
            root_a["children"] = group_a[1:]
        root_b = group_b[0].copy()
        if len(group_b) > 1:
            root_b["children"] = group_b[1:]
        json_items = [root_a, root_b]

    options = {
        "template": assigned_template,
        "title": {"text": title or "Infographic"},
        "data": {"items": json_items},
    }
    return _json.dumps(options)


# ---------------------------------------------------------------------------
# AI-powered DSL generation (Claude Agent SDK) with deterministic fallback
# ---------------------------------------------------------------------------

# AI DSL concurrency limit — max 2 concurrent agent calls for DSL
_DSL_AI_SEMAPHORE = asyncio.Semaphore(2)

INFOGRAPHIC_DSL_SYSTEM_PROMPT = """You are an AntV Infographic DSL expert. Output ONLY valid AntV Infographic syntax — NO markdown, NO code blocks, NO explanation.

SYNTAX RULES:
- First line: `infographic <template-name>`
- Blocks: `data` / `theme`, two-space indentation
- Key-value: `key value` (space separated)
- Arrays: `-` prefix for items
- data fields: title(string), desc(string), items(array)
- items fields: label(string), value(number), desc(string), icon(string), children(array)
- compare-* templates: EXACTLY 2 root nodes, comparison items as children
- chart-* templates: items MUST have numeric `value` field
- Icons: `mdi/<icon-name>` (e.g. mdi/rocket-launch, mdi/shield-check, mdi/chart-line)

CRITICAL WRITING RULES — content must be COMPLETE (never cut off mid-sentence):
- Write SHORT, COMPLETE phrases that FIT the space. NEVER write long sentences.
- Labels: 2-3 words max (e.g. "Policy Framework", "Risk Assessment", "Data Security")
- Descriptions: ONE short phrase, 4-8 words max (e.g. "Comprehensive security policy development")
- Title: 3-6 words (e.g. "GDPR Control Analysis Process")
- Top desc: ONE sentence, max 8-10 words
- chart-* items: NO desc field — only label + value + icon
- EVERY piece of text must be a COMPLETE phrase — no partial sentences

ITEM COUNT LIMITS:
- horizontal sequence/snake/stairs templates: MAX 4 items
- vertical sequence/roadmap/timeline: MAX 4 items
- hierarchy-* templates: MAX 4 items (max 3 children each)
- compare-* templates: EXACTLY 2 root items with max 3 children each
- list/grid templates: MAX 5 items
- chart-* templates: MAX 4 items (NO desc on chart items)

AVAILABLE TEMPLATES:
Sequence (process/steps): sequence-snake-steps-compact-card, sequence-roadmap-vertical-simple,
  sequence-timeline-simple, sequence-timeline-rounded-rect-node, sequence-ascending-steps,
  sequence-stairs-front-compact-card, sequence-circular-simple, sequence-pyramid-simple,
  sequence-color-snake-steps-horizontal-icon-line, sequence-zigzag-steps-underline-text,
  sequence-horizontal-zigzag-underline-text, sequence-snake-steps-simple,
  sequence-snake-steps-underline-text, sequence-filter-mesh-simple,
  sequence-mountain-underline-text, sequence-cylinders-3d-simple,
  sequence-stairs-front-pill-badge, sequence-zigzag-pucks-3d-simple,
  sequence-ascending-stairs-3d-underline-text, sequence-roadmap-vertical-plain-text
Compare (A vs B): compare-binary-horizontal-badge-card-arrow,
  compare-binary-horizontal-simple-fold, compare-binary-horizontal-underline-text-vs,
  compare-hierarchy-left-right-circle-node-pill-badge, compare-swot
List (bullet points): list-grid-badge-card, list-grid-candy-card-lite, list-grid-ribbon-card,
  list-row-horizontal-icon-arrow, list-column-vertical-icon-arrow,
  list-column-simple-vertical-arrow, list-zigzag-down-compact-card, list-zigzag-down-simple,
  list-zigzag-up-compact-card, list-zigzag-up-simple, list-sector-plain-text,
  list-column-done-list, list-row-simple-illus
Hierarchy (tree): hierarchy-tree-curved-line-rounded-rect-node,
  hierarchy-tree-tech-style-badge-card, hierarchy-tree-tech-style-capsule-item,
  hierarchy-structure
Chart (data): chart-bar-plain-text, chart-column-simple, chart-line-plain-text,
  chart-pie-plain-text, chart-pie-compact-card, chart-pie-donut-plain-text,
  chart-pie-donut-pill-badge, chart-wordcloud
Quadrant: quadrant-quarter-simple-card, quadrant-quarter-circular, quadrant-simple-illus
Relation: relation-circle-icon-badge, relation-circle-circular-progress

TEMPLATE SELECTION:
- List/overview → list-grid-* or list-row-*
- Process/steps → sequence-snake-* or sequence-roadmap-*
- Comparison → compare-binary-* (2 root nodes + children)
- SWOT → compare-swot
- Hierarchy → hierarchy-tree-*
- Data/stats → chart-* (items need value field)
- Timeline → sequence-timeline-*
- Relationship → relation-circle-*
- Quadrant → quadrant-*

Output ONLY the DSL. No markdown fences. No explanation."""


async def generate_dsl_with_ai(
    content_block: dict,
    assigned_template: str,
    topic_title: str,
    model: Optional[str] = None,
) -> Optional[str]:
    """Generate AntV DSL using Claude Agent SDK (AI-powered).

    Uses the agent's knowledge of AntV Infographic syntax to produce
    optimized DSL that takes advantage of template-specific features.

    Falls back to None if AI fails — caller should use build_antv_dsl() instead.

    Args:
        content_block: Content block with data, visualization_type, etc.
        assigned_template: AntV template name.
        topic_title: Topic title for context.
        model: Optional model override.

    Returns:
        AntV DSL string, or None if AI generation fails.
    """
    from courseware_agents.base import run_agent

    block_data = content_block.get("data", {})
    title = block_data.get("title", topic_title)
    desc = block_data.get("desc", "")
    items = block_data.get("items", [])
    viz_type = content_block.get("visualization_type", "overview")
    sub_title = content_block.get("sub_title", "")
    caption = content_block.get("caption", "")

    # Format items for the prompt
    items_text = ""
    for i, item in enumerate(items[:6]):
        label = item.get("label", f"Item {i+1}")
        item_desc = item.get("desc", "")
        icon = item.get("icon", "")
        value = item.get("value", "")
        children = item.get("children", [])
        items_text += f"\n  {i+1}. {label}: {item_desc}"
        if icon:
            items_text += f" (icon: {icon})"
        if value:
            items_text += f" (value: {value})"
        if children:
            for ci, child in enumerate(children[:3]):
                c_label = child.get("label", f"Sub {ci+1}")
                c_desc = child.get("desc", "")
                items_text += f"\n     - {c_label}: {c_desc}"

    prompt = f"""Generate AntV Infographic DSL for this content:

TEMPLATE: {assigned_template}
VISUALIZATION TYPE: {viz_type}
TITLE: {title}
DESCRIPTION: {desc}
ITEMS:{items_text}

Generate ONLY the AntV DSL syntax using template "{assigned_template}".
CRITICAL — every text must be SHORT and COMPLETE (never cut off):
- Labels: 2-3 words (e.g. "Policy Framework", "Risk Assessment")
- Descriptions: 4-8 words, ONE complete phrase (e.g. "Systematic security policy development process")
- Title: 3-6 words, Desc: ONE short sentence (max 10 words)
- chart items: only label + value + icon (NO desc field)
- sequence/hierarchy: MAX 4 items, list/grid: MAX 5 items, chart: MAX 4 items
- NEVER write long text that might get cut off — keep everything SHORT and COMPLETE
Output ONLY the DSL — no markdown, no explanation."""

    try:
        async with _DSL_AI_SEMAPHORE:
            result = await run_agent(
                prompt=prompt,
                system_prompt=INFOGRAPHIC_DSL_SYSTEM_PROMPT,
                tools=[],  # No tools needed — pure text generation
                max_turns=INFOGRAPHIC_MAX_TURNS,
                model=model or FAST_MODEL,
            )

        if not result:
            return None

        # Clean the result — strip markdown fences if any
        dsl = result.strip()
        if dsl.startswith("```"):
            lines = dsl.split("\n")
            lines = [l for l in lines if not l.strip().startswith("```")]
            dsl = "\n".join(lines).strip()

        # Validate: must start with "infographic"
        if not dsl.startswith("infographic"):
            logger.warning(f"AI DSL invalid (doesn't start with 'infographic'): {dsl[:80]}")
            return None

        # Validate: must have data section
        if "data" not in dsl:
            logger.warning(f"AI DSL invalid (no 'data' section): {dsl[:80]}")
            return None

        # Post-process: enforce text length limits on AI output
        dsl = _enforce_dsl_text_limits(dsl)

        logger.info(f"AI DSL generated for '{sub_title}' ({len(dsl)} chars)")
        return dsl

    except Exception as e:
        logger.warning(f"AI DSL generation failed for '{sub_title}': {e}")
        return None


# ---------------------------------------------------------------------------
# Single infographic generation (DSL → HTML → PNG)
# ---------------------------------------------------------------------------

async def generate_single_infographic(
    content_block: dict,
    assigned_template: str,
    topic_title: str,
    slide_position: int,
    output_dir: str,
    model: Optional[str] = None,
    browser=None,
) -> dict:
    """Generate ONE infographic from a content block.

    Builds AntV DSL deterministically from content block data,
    renders HTML, and converts to PNG via Playwright.
    """
    sub_title = content_block.get("sub_title", f"Slide {slide_position + 1}")
    viz_type = content_block.get("visualization_type", "overview")
    caption = content_block.get("caption", "")

    try:
        # FAST MODE: Use deterministic DSL builder (no AI call needed)
        # The deterministic builder is reliable and avoids ~5s per infographic
        # from AI DSL generation. Content blocks already have structured data.
        antv_syntax = None
        dsl_source = "deterministic"

        if False:  # AI DSL disabled for speed — deterministic builder is sufficient
            try:
                antv_syntax = await generate_dsl_with_ai(
                    content_block=content_block,
                    assigned_template=assigned_template,
                    topic_title=topic_title,
                    model=model,
                )
                if antv_syntax:
                    dsl_source = "ai"
            except Exception as ai_err:
                logger.debug(f"AI DSL skipped for '{sub_title}': {ai_err}")

        # Deterministic fallback
        if not antv_syntax:
            antv_syntax = build_antv_dsl(content_block, assigned_template)
            dsl_source = "deterministic"

        if not antv_syntax:
            raise ValueError(f"Empty DSL/JSON generated for '{sub_title}'")

        # Write HTML
        safe_title = _safe_filename(topic_title)
        html_filename = f"infographic_{safe_title}_pos{slide_position}.html"
        html_path = os.path.join(output_dir, html_filename)
        _write_antv_html(html_path, antv_syntax, f"{topic_title} — {sub_title}")

        # Convert to PNG (with browser semaphore)
        png_filename = f"infographic_{safe_title}_pos{slide_position}.png"
        png_path = os.path.join(output_dir, png_filename)

        png_ok = await _html_to_png(html_path, png_path, browser=browser)

        result = {
            "topic": topic_title,
            "slide_position": slide_position,
            "sub_title": sub_title,
            "visualization_type": viz_type,
            "template_used": assigned_template,
            "html_path": html_path,
            "caption": caption,
        }

        if png_ok and os.path.exists(png_path):
            result["image_path"] = png_path
            result["generated"] = True
            result["dsl_source"] = dsl_source
            logger.info(
                f"Infographic [{slide_position}] '{sub_title}': "
                f"template={assigned_template}, dsl={dsl_source}, PNG={os.path.getsize(png_path)}B"
            )
        else:
            result["image_path"] = None
            result["generated"] = False
            result["error"] = "PNG conversion failed"
            logger.warning(
                f"Infographic [{slide_position}] '{sub_title}': PNG failed"
            )

        return result

    except Exception as e:
        logger.error(f"Infographic failed for '{sub_title}' (pos {slide_position}): {e}")
        return {
            "topic": topic_title,
            "slide_position": slide_position,
            "sub_title": sub_title,
            "visualization_type": viz_type,
            "template_used": assigned_template,
            "generated": False,
            "error": str(e),
            "caption": caption,
        }


async def generate_topic_infographics(
    topic_title: str,
    content_blocks: list,
    infographic_assignments: list,
    output_dir: str,
    model: Optional[str] = None,
    browser=None,
) -> list:
    """Generate ALL infographics for a single topic SEQUENTIALLY.

    Uses a shared browser instance passed from generate_all_infographics().
    Sequential processing is the most reliable approach on Windows.
    """
    _FALLBACK_TEMPLATES = [
        "list-grid-badge-card",
        "list-grid-candy-card-lite",
        "list-row-horizontal-icon-arrow",
        "list-column-done-list",
    ]

    infographic_list = []

    for assignment in infographic_assignments:
        block_idx = assignment.get("content_block_index", 0)
        slide_pos = assignment.get("slide_position", 0)
        assigned_template = assignment.get("assigned_template", "list-grid-badge-card")

        if block_idx < len(content_blocks):
            block = content_blocks[block_idx]
        else:
            block = {
                "sub_title": assignment.get("sub_title", f"Slide {slide_pos + 1}"),
                "visualization_type": assignment.get("visualization_type", "overview"),
                "data": {
                    "title": assignment.get("sub_title", topic_title),
                    "items": [{"label": topic_title[:15], "desc": "Key content", "icon": "mdi/information"}],
                },
            }

        result = None
        try:
            result = await generate_single_infographic(
                content_block=block,
                assigned_template=assigned_template,
                topic_title=topic_title,
                slide_position=slide_pos,
                output_dir=output_dir,
                model=model,
                browser=browser,
            )
        except Exception as e:
            logger.error(f"Infographic exception for '{topic_title}' pos {slide_pos}: {e}")

        # Retry with fallback if failed
        if not result or not result.get("generated"):
            fallback = _FALLBACK_TEMPLATES[slide_pos % len(_FALLBACK_TEMPLATES)]
            if fallback != assigned_template:
                try:
                    result = await generate_single_infographic(
                        content_block=block,
                        assigned_template=fallback,
                        topic_title=topic_title,
                        slide_position=slide_pos,
                        output_dir=output_dir,
                        model=model,
                        browser=browser,
                    )
                except Exception as e2:
                    logger.error(f"Fallback failed for pos {slide_pos}: {e2}")

        infographic_list.append(result or {
            "topic": topic_title,
            "slide_position": slide_pos,
            "generated": False,
            "error": "All attempts failed",
        })

    generated = sum(1 for r in infographic_list if r.get("generated"))
    logger.info(f"Topic '{topic_title}': {generated}/{len(infographic_list)} infographics generated")
    return infographic_list


async def generate_all_infographics(
    skeleton: dict,
    content_map: dict,
    output_dir: str = None,
    model: Optional[str] = None,
) -> dict:
    """Generate infographics for ALL topics using ONE shared browser.

    Creates a single Playwright browser at the start, processes all topics
    sequentially, and closes the browser at the end. This is the most
    reliable approach — no concurrency issues, no resource exhaustion.
    """
    if output_dir is None:
        output_dir = tempfile.mkdtemp(prefix="multi_agent_infographics_")
    os.makedirs(output_dir, exist_ok=True)

    # Collect topic tasks
    topic_tasks = []

    for lo in skeleton.get("learning_outcomes", []):
        for lu in lo.get("learning_units", []):
            for topic in lu.get("topics", []):
                t_title = topic.get("topic_title", "Topic")
                assignments = topic.get("infographic_assignments", [])
                topic_content = _fuzzy_get_topic(content_map, t_title)
                blocks = topic_content.get("content_blocks", [])

                if not assignments and blocks:
                    import random
                    assignments = []
                    used_templates = set()
                    for bi, b in enumerate(blocks):
                        viz_type = b.get("visualization_type", "overview")
                        suggested = b.get("suggested_template", "")
                        if not suggested or suggested in used_templates:
                            candidates = TEMPLATE_MAP.get(viz_type, TEMPLATE_MAP["overview"])
                            available = [t for t in candidates if t not in used_templates]
                            if not available:
                                available = candidates
                            suggested = random.choice(available)
                        used_templates.add(suggested)
                        assignments.append({
                            "slide_position": bi,
                            "content_block_index": bi,
                            "sub_title": b.get("sub_title", ""),
                            "visualization_type": viz_type,
                            "assigned_template": suggested,
                        })
                    # Write back to skeleton so assemble_final_slides can find them
                    topic["infographic_assignments"] = assignments

                if not assignments:
                    logger.warning(f"No assignments or blocks for topic '{t_title}' — skipping")
                    continue

                safe_title = _safe_filename(t_title)
                topic_dir = os.path.join(output_dir, safe_title)
                os.makedirs(topic_dir, exist_ok=True)

                topic_tasks.append({
                    "title": t_title,
                    "blocks": blocks,
                    "assignments": assignments,
                    "dir": topic_dir,
                })

    total_infographics = sum(len(t['assignments']) for t in topic_tasks)
    logger.info(
        f"Generating infographics for {len(topic_tasks)} topics, "
        f"{total_infographics} total infographics"
    )

    # Launch ONE browser for ALL infographics
    infographic_map = {}
    total_generated = 0
    total_attempted = 0

    try:
        from playwright.async_api import async_playwright
        pw = await async_playwright().start()
        browser = await pw.chromium.launch(headless=True)
        logger.info("Playwright browser launched for infographic generation")
    except Exception as e:
        logger.error(f"Failed to launch Playwright: {e}")
        # Return empty map — all topics will get text fallback
        for task in topic_tasks:
            infographic_map[task["title"]] = []
        return infographic_map

    try:
        # Process topics SEQUENTIALLY with the shared browser
        for ti, task in enumerate(topic_tasks):
            logger.info(f"Rendering topic {ti + 1}/{len(topic_tasks)}: '{task['title']}' ({len(task['assignments'])} infographics)")
            try:
                result = await generate_topic_infographics(
                    topic_title=task["title"],
                    content_blocks=task["blocks"],
                    infographic_assignments=task["assignments"],
                    output_dir=task["dir"],
                    model=model,
                    browser=browser,
                )
                infographic_map[task["title"]] = result
                gen = sum(1 for r in result if r.get("generated"))
                total_generated += gen
                total_attempted += len(result)
            except Exception as e:
                logger.error(f"All infographics failed for '{task['title']}': {e}")
                infographic_map[task["title"]] = []
    finally:
        # Always close browser and playwright
        try:
            await browser.close()
        except Exception:
            pass
        try:
            await pw.stop()
        except Exception:
            pass
        logger.info("Playwright browser closed")

    logger.info(
        f"Infographics complete: {total_generated}/{total_attempted} generated "
        f"across {len(infographic_map)} topics"
    )
    return infographic_map


# ---------------------------------------------------------------------------
# Utilities
# ---------------------------------------------------------------------------

def _safe_filename(title: str) -> str:
    """Create a filesystem-safe filename from a title."""
    safe = title.replace(" ", "_").replace("/", "-").replace("\\", "-")
    safe = "".join(c for c in safe if c.isalnum() or c in "_-")
    return safe[:30]


def _write_antv_html(html_path: str, syntax: str, title: str) -> None:
    """Write a self-contained HTML file that renders an AntV Infographic.

    Uses setOptions() + performRender() API (compatible with v0.2.15+).
    The `syntax` param is now a JSON string with {template, title, data:{items}}.
    Falls back to DSL string if syntax doesn't start with '{'.
    """
    import json as _json
    safe_title = title.replace("<", "&lt;").replace(">", "&gt;")

    # Convert DSL syntax to JSON options if needed
    if syntax.strip().startswith("{"):
        options_json = syntax
    else:
        # Legacy DSL string — convert to JSON options
        options_json = _dsl_to_json_options(syntax)

    html_content = f"""<!DOCTYPE html>
<html lang="en">
<head>
  <meta charset="utf-8">
  <title>{safe_title} - Infographic</title>
  <style>
    * {{ margin: 0; padding: 0; box-sizing: border-box; }}
    body {{ background: #FFFFFF; }}
    #container {{ width: 1792px; min-height: 1024px; }}
  </style>
</head>
<body>
  <div id="container"></div>
  <script src="https://unpkg.com/@antv/infographic@0.2.15/dist/infographic.min.js"></script>
  <script>
    AntVInfographic.registerResourceLoader(async (config) => {{
      const {{ data, scene }} = config;
      try {{
        let url;
        if (scene === 'icon') url = `https://api.iconify.design/${{data}}.svg`;
        else if (scene === 'illus') url = `https://raw.githubusercontent.com/balazser/undraw-svg-collection/refs/heads/main/svgs/${{data}}.svg`;
        else return null;
        const r = await fetch(url, {{ referrerPolicy: 'no-referrer' }});
        if (!r.ok) return null;
        const text = await r.text();
        if (!text || !text.trim().startsWith('<svg')) return null;
        return AntVInfographic.loadSVGResource(text);
      }} catch (e) {{ return null; }}
    }});
  </script>
  <script>
    const ig = new AntVInfographic.Infographic({{
      container: '#container',
      width: 1792,
      height: 1024,
    }});
    const opts = {options_json};
    ig.setOptions(opts);
    ig.performRender();
    setTimeout(() => ig.performRender(), 1500);
    setTimeout(() => ig.performRender(), 3000);
  </script>
</body>
</html>"""

    with open(html_path, "w", encoding="utf-8") as f:
        f.write(html_content)
    logger.debug(f"AntV HTML written: {html_path}")


def _dsl_to_json_options(dsl: str) -> str:
    """Convert legacy AntV DSL syntax string to JSON options for setOptions() API."""
    import json as _json
    lines = dsl.strip().split("\n")
    template = "list-grid-badge-card"
    title_text = ""
    desc_text = ""
    items = []

    # Parse first line for template
    if lines and lines[0].startswith("infographic "):
        template = lines[0].replace("infographic ", "").strip()

    current_item = None
    for line in lines[1:]:
        stripped = line.strip()
        if stripped.startswith("title =") or stripped.startswith("title="):
            title_text = stripped.split("=", 1)[1].strip()
        elif stripped.startswith("desc =") or stripped.startswith("desc="):
            desc_text = stripped.split("=", 1)[1].strip()
        elif stripped.startswith("- label:"):
            if current_item:
                items.append(current_item)
            current_item = {"label": stripped.replace("- label:", "").strip()}
        elif stripped.startswith("desc:") and current_item is not None:
            current_item["desc"] = stripped.replace("desc:", "").strip()
        elif stripped.startswith("icon:") and current_item is not None:
            current_item["icon"] = stripped.replace("icon:", "").strip()
        elif stripped.startswith("value:") and current_item is not None:
            current_item["value"] = stripped.replace("value:", "").strip()

    if current_item:
        items.append(current_item)

    options = {
        "template": template,
        "title": {"text": title_text or "Infographic"},
        "data": {"items": items},
    }
    return _json.dumps(options)


async def _html_to_png(html_path: str, png_path: str, browser=None) -> bool:
    """Convert HTML to PNG using a provided browser instance.

    Uses a single long-lived browser — just opens a new page/tab for each screenshot.
    The browser is created once in generate_all_infographics() and reused for ALL screenshots.
    """
    MIN_PNG_SIZE = 10000

    try:
        from pathlib import Path
        file_url = Path(html_path).as_uri()

        if browser is None:
            logger.error("No browser provided to _html_to_png")
            return False

        async def _do_screenshot(wait_ms=5000):
            page = await browser.new_page(viewport={"width": 1792, "height": 1024})
            try:
                page.set_default_timeout(30000)
                await page.goto(file_url, wait_until="domcontentloaded")
                await page.wait_for_timeout(wait_ms)
                await page.screenshot(path=png_path, full_page=True)
            finally:
                await page.close()

        # First attempt (3s wait — AntV renders fast with performRender())
        await asyncio.wait_for(_do_screenshot(3000), timeout=30)

        # Validate PNG size — retry once if too small
        if os.path.exists(png_path):
            png_size = os.path.getsize(png_path)
            if png_size < MIN_PNG_SIZE:
                logger.warning(f"PNG small ({png_size}B), retrying with longer wait")
                await asyncio.wait_for(_do_screenshot(5000), timeout=30)
                if os.path.exists(png_path):
                    png_size = os.path.getsize(png_path)
                    if png_size < MIN_PNG_SIZE:
                        logger.warning(f"PNG still small ({png_size}B) after retry")
                        return True

        if os.path.exists(png_path):
            logger.debug(f"PNG: {png_path} ({os.path.getsize(png_path)}B)")
            return True

        return False

    except ImportError:
        logger.error("Playwright not installed — cannot generate PNGs")
        return False
    except asyncio.TimeoutError:
        logger.warning(f"Playwright timed out for {html_path}")
        if os.path.exists(png_path) and os.path.getsize(png_path) > 5000:
            return True
        return False
    except Exception as e:
        logger.warning(f"Playwright failed for {html_path}: {e}")
        return False
