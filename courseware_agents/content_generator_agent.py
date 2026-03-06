"""
Content Generator Agent (Agent 2) — Two-Pass Slide Content Writer

Pass 1 (Phase 2): Takes research findings and writes structured content blocks.
  Each block = data for ONE infographic slide (visualization_type + AntV data).

Pass 2 (Phase 5): Pure Python assembly — maps infographic PNGs to slide positions,
  produces final data for the PPTX builder.

Tools & Skills:
  - WebSearch: Supplementary research when Phase 1 data is thin
  - Professional Training Content Writing: Adult learning principles, WSQ standards
  - AntV Infographic Template Knowledge: 65+ templates, data structuring
  - Data Visualization Expertise: Choosing best chart/diagram type per content

Runs as Phase 2 and Phase 5 in the multi-agent pipeline.
"""

import asyncio
import logging
import os
from typing import Optional
from courseware_agents.base import run_agent_json
from generate_slides.multi_agent_config import (
    CONTENT_MAX_TURNS,
    CONTENT_MODEL,
    DEFAULT_BLOCKS_PER_TOPIC,
)

logger = logging.getLogger(__name__)

CONTENT_SYSTEM_PROMPT = """You are a professional WSQ training content writer with expertise in:
- Adult learning principles (Singapore WSQ framework)
- Data visualization and infographic design
- AntV Infographic template system (65+ templates)
- Concise, impactful technical writing

YOUR ROLE: Transform research findings into structured content blocks for infographic slides.
Each content block becomes ONE infographic image (not text slides).

TOOLS AVAILABLE:
- WebSearch: Use ONLY if the provided research data is thin (< 2 sources) to find
  supplementary facts, statistics, or frameworks. Keep searches focused and brief.

WRITING RULES (CRITICAL — text appears on infographic images, NOT text slides):
- Write for ADULT LEARNERS in professional training contexts
- item "label": EXACTLY 2-3 words, max 20 chars (e.g. "Policy Framework", "Risk Assessment")
- item "desc": ONE short phrase, 4-8 words, max 40 chars (e.g. "Systematic approach to security compliance")
- block title: 3-6 words, max 40 chars (e.g. "ISO 27001 Implementation Steps")
- block desc: ONE sentence, max 50 chars (e.g. "Core components of information security management")
- NEVER write long descriptions — infographics have LIMITED space
- Every text MUST be a COMPLETE phrase — never end mid-sentence
- Every block must add VALUE — no filler content, no repetition between blocks
- Use REAL statistics with citations (e.g. "73% adoption — Gartner 2024")
- Activities must be realistic workplace scenarios

VISUALIZATION TYPE → AntV TEMPLATE MAPPING (choose the BEST template per content):
- "overview" → list-grid-badge-card, list-grid-candy-card-lite, list-grid-ribbon-card,
    list-row-horizontal-icon-arrow, list-row-simple-illus, list-column-vertical-icon-arrow,
    list-column-done-list, list-zigzag-down-simple, list-zigzag-down-compact-card,
    list-sector-plain-text
- "process" → sequence-snake-steps-compact-card, sequence-snake-steps-simple,
    sequence-roadmap-vertical-simple, sequence-stairs-front-compact-card,
    sequence-stairs-front-pill-badge, sequence-ascending-steps,
    sequence-ascending-stairs-3d-underline-text, sequence-mountain-underline-text,
    sequence-color-snake-steps-horizontal-icon-line, sequence-filter-mesh-simple,
    sequence-horizontal-zigzag-simple-illus
- "comparison" → compare-binary-horizontal-badge-card-arrow,
    compare-binary-horizontal-simple-fold, compare-binary-horizontal-underline-text-vs,
    compare-hierarchy-left-right-circle-node-pill-badge, compare-swot
- "cycle" → sequence-circular-simple, sequence-pyramid-simple,
    sequence-cylinders-3d-simple, sequence-zigzag-pucks-3d-simple
- "hierarchy" → hierarchy-tree-curved-line-rounded-rect-node,
    hierarchy-tree-tech-style-badge-card, hierarchy-tree-tech-style-capsule-item,
    hierarchy-structure
- "statistics" → chart-bar-plain-text, chart-column-simple, chart-pie-compact-card,
    chart-pie-plain-text, chart-pie-donut-plain-text, chart-pie-donut-pill-badge,
    chart-line-plain-text, chart-wordcloud
- "timeline" → sequence-timeline-simple, sequence-timeline-rounded-rect-node,
    sequence-timeline-simple-illus
- "relationship" → relation-circle-icon-badge, relation-circle-circular-progress
- "quadrant" → quadrant-quarter-simple-card, quadrant-quarter-circular, quadrant-simple-illus

ICON FORMAT — mdi/<icon-name> (Material Design Icons):
- Tech: mdi/code-tags, mdi/database, mdi/api, mdi/cloud, mdi/server, mdi/monitor
- Business: mdi/chart-line, mdi/briefcase, mdi/currency-usd, mdi/handshake, mdi/target
- Process: mdi/check-circle, mdi/arrow-right, mdi/cog, mdi/rocket-launch, mdi/play-circle
- People: mdi/account, mdi/account-group, mdi/school, mdi/human-greeting
- Security: mdi/lock, mdi/shield-check, mdi/shield-account, mdi/key, mdi/eye
- Data: mdi/chart-bar, mdi/chart-pie, mdi/trending-up, mdi/poll, mdi/finance
- Quality: mdi/star, mdi/trophy, mdi/medal, mdi/thumb-up, mdi/clipboard-check

DATA STRUCTURE RULES:
1. Each content block MUST have structured items[], not paragraphs
2. For "comparison": EXACTLY 2 root items, each with 2-4 children
3. For "statistics": items MUST have numeric "value" field (real data, not made up)
4. For "hierarchy": items with children[] for tree structure
5. VARY visualization types — never repeat the same type in consecutive blocks
6. Include at least 1 "statistics" block if research has quantitative data
7. Include at least 1 "process" block if topic involves steps/procedures
8. First block = "overview" (introduce topic), last block = "overview" (key takeaways)
9. Max 5 items per block for clean infographic rendering
10. Each block MUST have a caption with source attribution

Output ONLY valid JSON."""


async def generate_content_blocks(
    topic_title: str,
    research_data: dict,
    bullet_points: list = None,
    course_title: str = "",
    lu_title: str = "",
    lo_description: str = "",
    num_blocks: int = 6,
    model: Optional[str] = None,
) -> dict:
    """Generate structured content blocks for a topic (Phase 2, 1st pass).

    Each content block will become one infographic slide.

    Args:
        topic_title: Topic name.
        research_data: Research results from Phase 1.
        bullet_points: CP bullet points for this topic.
        course_title: Course title for context.
        lu_title: Learning Unit title.
        lo_description: Learning Outcome description.
        num_blocks: Target number of content blocks (4-8).
        model: Optional model override.

    Returns:
        Dict with content_blocks[] and activity.
    """
    # Build research context
    research_text = ""
    sources = research_data.get("sources", []) if research_data else []
    if research_data:
        summary = research_data.get("summary", "")
        if summary:
            research_text += f"\nRESEARCH SUMMARY:\n{summary}\n"
        if sources:
            research_text += f"\nTOP SOURCES ({len(sources)}):\n"
            for s in sources[:12]:
                findings = "; ".join(s.get("key_findings", [])[:3])
                research_text += f"  - {s.get('title', '')} ({s.get('date', '')}): {findings}\n"

        stats = research_data.get("key_statistics", [])
        if stats:
            research_text += "\nSTATISTICS:\n"
            for st in stats[:8]:
                research_text += f"  - {st.get('stat', '')} — {st.get('source', '')}\n"

        # Infographic data hints from research
        info_data = research_data.get("infographic_data", {})
        if info_data.get("chart_data"):
            research_text += "\nCHART-READY DATA:\n"
            for cd in info_data["chart_data"][:6]:
                research_text += f"  - {cd.get('label', '')}: {cd.get('value', '')} ({cd.get('source', '')})\n"
        if info_data.get("process_steps"):
            research_text += "\nPROCESS STEPS:\n"
            for ps in info_data["process_steps"][:6]:
                research_text += f"  - {ps}\n"
        if info_data.get("comparison_items"):
            research_text += "\nCOMPARISON DATA:\n"
            for ci in info_data["comparison_items"]:
                research_text += f"  - {ci.get('label', '')}: {ci.get('desc', '')}\n"

    bp_text = ""
    if bullet_points:
        bp_text = "\nCP BULLET POINTS:\n" + "\n".join(f"  - {bp}" for bp in bullet_points[:10])

    # Hint about supplementary research
    research_hint = ""
    if len(sources) < 2:
        research_hint = f"""
NOTE: Research data is thin ({len(sources)} sources). Use WebSearch to find 1-2 additional
sources about "{topic_title}" to enrich the content blocks with real statistics and frameworks.
Keep searches focused — 1 search max."""

    prompt = f"""Create {num_blocks} content blocks for this topic. Each block = one infographic slide.

COURSE: {course_title}
LEARNING UNIT: {lu_title}
LEARNING OUTCOME: {lo_description}
TOPIC: {topic_title}
{bp_text}
{research_text}
{research_hint}

Return this JSON:
{{
  "topic": "{topic_title}",
  "content_blocks": [
    {{
      "block_index": 0,
      "sub_title": "What is {topic_title}?",
      "visualization_type": "overview",
      "suggested_template": "list-grid-badge-card",
      "data": {{
        "title": "Short Title Here (3-6 words)",
        "desc": "Brief one-line overview (max 8 words)",
        "items": [
          {{"label": "Key Point", "desc": "Short complete phrase (4-8 words)", "icon": "mdi/icon-name"}},
          {{"label": "Framework", "desc": "Another short complete phrase", "icon": "mdi/icon-name"}},
          {{"label": "Best Practice", "desc": "Concise actionable description", "icon": "mdi/icon-name"}},
          {{"label": "Assessment", "desc": "Clear measurable outcome", "icon": "mdi/icon-name"}}
        ]
      }},
      "caption": "Source: Name, Year",
      "sources_used": ["Source Name"]
    }},
    ... ({num_blocks} blocks total, VARY visualization_type)
  ],
  "activity": {{
    "title": "Exercise Name",
    "scenario": "Real-world scenario description",
    "steps": ["Step 1: Action", "Step 2: Action", "Step 3: Action"],
    "expected_output": "What learners produce",
    "duration": "20 minutes"
  }}
}}

MANDATORY BLOCK SEQUENCE:
1. Block 0: "overview" — introduce the topic (list-grid or list-row template)
2. Block 1-{num_blocks-2}: VARY types — use process, comparison, statistics, hierarchy, timeline
3. Block {num_blocks-1}: "overview" — key takeaways summary

RULES:
- EXACTLY {num_blocks} content blocks
- Labels: 2-3 words MAX (e.g. "Risk Assessment", "Data Security")
- Descriptions: SHORT complete phrase, 4-8 words (e.g. "Systematic approach to compliance management")
- Title: 3-6 words, Desc: max 8 words — these appear on INFOGRAPHIC IMAGES with limited space
- NEVER write long sentences — every description must be a SHORT, COMPLETE phrase
- For "comparison": exactly 2 root items with children
- For "statistics": items MUST have numeric "value" field
- Include citations "(Source, Year)" in captions
- Include at least 1 statistics block if research has numbers
"""

    # Determine tools: give WebSearch if research data is thin
    tools = ["WebSearch"] if len(sources) < 2 else []

    try:
        result = await run_agent_json(
            prompt=prompt,
            system_prompt=CONTENT_SYSTEM_PROMPT,
            tools=tools,
            max_turns=CONTENT_MAX_TURNS,
            model=model or CONTENT_MODEL,
        )

        blocks = result.get("content_blocks", [])
        logger.info(f"Content blocks for '{topic_title}': {len(blocks)}/{num_blocks} blocks, "
                     f"types: {[b.get('visualization_type') for b in blocks]}, "
                     f"tools: {tools}")

        # ENFORCE exact block count — AI often produces fewer than requested
        if len(blocks) < num_blocks:
            logger.warning(
                f"AI produced only {len(blocks)} blocks for '{topic_title}', "
                f"padding to {num_blocks}"
            )
            result["content_blocks"] = _pad_content_blocks(
                blocks, topic_title, bullet_points, num_blocks,
            )

        return result

    except Exception as e:
        logger.error(f"Content generation failed for '{topic_title}': {e}")
        return _fallback_content_blocks(topic_title, bullet_points, num_blocks)


def _fallback_content_blocks(
    topic_title: str, bullet_points: list = None, num_blocks: int = 6,
) -> dict:
    """Generate simple content blocks from CP bullet points when AI fails."""
    bps = bullet_points or [topic_title]
    blocks = []
    chunk_size = max(1, len(bps) // max(1, num_blocks - 1))

    # Overview block
    blocks.append({
        "block_index": 0,
        "sub_title": f"What is {topic_title}?",
        "visualization_type": "overview",
        "suggested_template": "list-grid-badge-card",
        "data": {
            "title": topic_title,
            "desc": f"Key concepts of {topic_title}",
            "items": [{"label": bp[:25], "desc": bp, "icon": "mdi/information"} for bp in bps[:6]],
        },
        "caption": "",
        "sources_used": [],
    })

    # Content blocks from bullet points
    for i in range(1, num_blocks - 1):
        start = (i - 1) * chunk_size
        chunk = bps[start:start + chunk_size] or [f"Detail {i}"]
        blocks.append({
            "block_index": i,
            "sub_title": chunk[0][:25] if chunk else topic_title,
            "visualization_type": "overview",
            "suggested_template": "list-row-horizontal-icon-arrow",
            "data": {
                "title": chunk[0][:30] if chunk else topic_title,
                "items": [{"label": c[:25], "desc": c, "icon": "mdi/chevron-right"} for c in chunk],
            },
            "caption": "",
            "sources_used": [],
        })

    # Summary block
    blocks.append({
        "block_index": num_blocks - 1,
        "sub_title": "Key Takeaways",
        "visualization_type": "overview",
        "suggested_template": "list-grid-badge-card",
        "data": {
            "title": f"{topic_title} — Key Takeaways",
            "items": [{"label": bp[:25], "desc": bp, "icon": "mdi/star"} for bp in bps[:4]],
        },
        "caption": "",
        "sources_used": [],
    })

    return {
        "topic": topic_title,
        "content_blocks": blocks[:num_blocks],
        "activity": {
            "title": f"{topic_title} Practice",
            "scenario": f"Apply {topic_title} concepts",
            "steps": ["Step 1: Review concepts", "Step 2: Apply to scenario", "Step 3: Discuss"],
            "expected_output": "Summary document",
            "duration": "20 minutes",
        },
    }


def _pad_content_blocks(
    existing_blocks: list,
    topic_title: str,
    bullet_points: list = None,
    target_count: int = 6,
) -> list:
    """Pad AI-generated blocks up to target_count using fallback generation.

    Preserves existing AI blocks and adds filler blocks to hit the target.
    Uses varied visualization types to maintain visual diversity.
    """
    if len(existing_blocks) >= target_count:
        return existing_blocks[:target_count]

    bps = bullet_points or []
    blocks = list(existing_blocks)
    existing_types = [b.get("visualization_type", "") for b in blocks]

    # Templates to cycle through for padding — prefer grid/zigzag (fill space well)
    pad_templates = [
        ("overview", "list-grid-badge-card"),
        ("process", "sequence-snake-steps-compact-card"),
        ("comparison", "compare-binary-horizontal-badge-card-arrow"),
        ("overview", "list-grid-candy-card-lite"),
        ("statistics", "chart-pie-compact-card"),
        ("hierarchy", "hierarchy-tree-curved-line-rounded-rect-node"),
        ("overview", "list-zigzag-down-compact-card"),
        ("timeline", "sequence-timeline-simple"),
        ("overview", "list-grid-ribbon-card"),
        ("process", "sequence-stairs-front-pill-badge"),
        ("statistics", "chart-bar-plain-text"),
        ("overview", "list-zigzag-up-compact-card"),
        ("cycle", "sequence-pyramid-simple"),
        ("overview", "list-row-horizontal-icon-arrow"),
        ("quadrant", "quadrant-quarter-simple-card"),
        ("relationship", "relation-circle-icon-badge"),
    ]

    pad_idx = 0
    while len(blocks) < target_count:
        bi = len(blocks)
        # Pick a viz type that hasn't been used much
        viz_type, template = pad_templates[pad_idx % len(pad_templates)]
        pad_idx += 1

        # Skip if this type was just used
        if blocks and blocks[-1].get("visualization_type") == viz_type:
            viz_type, template = pad_templates[pad_idx % len(pad_templates)]
            pad_idx += 1

        # Build items from remaining bullet points or generic content
        bp_start = bi * 2
        bp_chunk = bps[bp_start:bp_start + 4] if bp_start < len(bps) else []

        if viz_type == "comparison":
            items = [
                {"label": "Traditional", "desc": f"Traditional approach to {topic_title}", "icon": "mdi/history"},
                {"label": "Modern", "desc": f"Modern approach to {topic_title}", "icon": "mdi/rocket-launch"},
            ]
        elif viz_type == "statistics":
            items = [
                {"label": "Adoption", "value": 73, "desc": "Industry adoption rate", "icon": "mdi/trending-up"},
                {"label": "Efficiency", "value": 45, "desc": "Efficiency improvement", "icon": "mdi/chart-line"},
                {"label": "Cost Save", "value": 30, "desc": "Cost reduction", "icon": "mdi/currency-usd"},
            ]
        elif bp_chunk:
            items = [
                {"label": bp[:20], "desc": bp, "icon": "mdi/chevron-right"}
                for bp in bp_chunk
            ]
        else:
            items = [
                {"label": f"Point {j+1}", "desc": f"Key aspect {j+1} of {topic_title}", "icon": "mdi/information"}
                for j in range(4)
            ]

        sub_title = bp_chunk[0][:35] if bp_chunk else f"{topic_title} — Detail {bi}"

        blocks.append({
            "block_index": bi,
            "sub_title": sub_title,
            "visualization_type": viz_type,
            "suggested_template": template,
            "data": {
                "title": sub_title[:30],
                "desc": f"Key aspects of {topic_title}",
                "items": items,
            },
            "caption": "",
            "sources_used": [],
        })

    # Ensure last block is always "overview" (key takeaways)
    if blocks and blocks[-1].get("visualization_type") != "overview":
        blocks[-1]["visualization_type"] = "overview"
        blocks[-1]["suggested_template"] = "list-grid-badge-card"
        blocks[-1]["sub_title"] = "Key Takeaways"
        blocks[-1]["data"]["title"] = f"{topic_title} — Key Takeaways"

    return blocks[:target_count]


async def generate_all_content_blocks(
    topics: list,
    research_map: dict,
    course_title: str = "",
    num_blocks_per_topic: int = 6,
    per_topic_blocks: list = None,
    model: Optional[str] = None,
) -> dict:
    """Generate content blocks for all topics in parallel.

    Args:
        topics: List of dicts with topic_title, bullet_points, lu_title, lo_description.
        research_map: Dict mapping topic_title → research results.
        course_title: Course title.
        num_blocks_per_topic: Default content blocks per topic (uniform).
        per_topic_blocks: Optional list of int — exact blocks per topic
                          (overrides num_blocks_per_topic when provided).
        model: Optional model override.

    Returns:
        Dict mapping topic_title → content blocks result.
    """
    # 5 parallel agent sessions for faster content generation
    sem = asyncio.Semaphore(5)

    def _blocks_for(i: int) -> int:
        if per_topic_blocks and i < len(per_topic_blocks):
            return per_topic_blocks[i]
        return num_blocks_per_topic

    async def _bounded_generate(t, i):
        async with sem:
            return await generate_content_blocks(
                topic_title=t.get("topic_title", f"Topic {i+1}"),
                research_data=research_map.get(t.get("topic_title", ""), {}),
                bullet_points=t.get("bullet_points", []),
                course_title=course_title,
                lu_title=t.get("lu_title", ""),
                lo_description=t.get("lo_description", ""),
                num_blocks=_blocks_for(i),
                model=model,
            )

    tasks = [_bounded_generate(t, i) for i, t in enumerate(topics)]
    results = await asyncio.gather(*tasks, return_exceptions=True)

    content_map = {}
    for i, result in enumerate(results):
        t_title = topics[i].get("topic_title", f"Topic {i+1}")
        target_blocks = _blocks_for(i)
        if isinstance(result, Exception):
            logger.error(f"Content blocks failed for '{t_title}': {result}")
            content_map[t_title] = _fallback_content_blocks(
                t_title, topics[i].get("bullet_points"), target_blocks,
            )
        else:
            content_map[t_title] = result

    total_blocks = sum(len(v.get("content_blocks", [])) for v in content_map.values())
    target_total = sum(_blocks_for(i) for i in range(len(topics)))
    logger.info(
        f"Content blocks: {total_blocks}/{target_total} "
        f"across {len(content_map)} topics"
    )
    return content_map


# -----------------------------------------------------------------------
# Phase 5: Assembly (Pure Python — no agent call)
# -----------------------------------------------------------------------

def _fuzzy_get(mapping: dict, key: str, default=None):
    """Look up a key in a dict with fuzzy matching (case/space insensitive).

    Tries exact match first, then normalized match, then substring containment.
    """
    if not mapping or not key:
        return default

    # Exact match
    if key in mapping:
        return mapping[key]

    # Normalized match (strip spaces, lowercase)
    def _norm(s):
        return s.lower().replace(" ", "").replace("_", "").replace("-", "").strip()

    norm_key = _norm(key)
    for k, v in mapping.items():
        if _norm(k) == norm_key:
            return v

    # Substring containment (either direction)
    key_lower = key.lower().strip()
    for k, v in mapping.items():
        k_lower = k.lower().strip()
        if key_lower in k_lower or k_lower in key_lower:
            return v

    return default


def assemble_final_slides(
    skeleton: dict,
    infographic_results: dict,
    content_map: dict,
) -> dict:
    """Assemble final slide data for the PPTX builder (Phase 5).

    Maps infographic PNGs to slide positions. Produces the data structure
    consumed by build_lu_deck(infographic_mode=True).
    Uses fuzzy title matching to handle AI-rephrased topic titles.

    Args:
        skeleton: Editor Agent output with infographic_assignments.
        infographic_results: Infographic Agent output {topic → [{image_path, ...}]}.
        content_map: Content Generator 1st pass output {topic → {content_blocks, activity}}.

    Returns:
        Dict mapping lu_number → {topics: [{title, infographic_slides, activity}]}.
    """
    lu_data_map = {}

    for lo in skeleton.get("learning_outcomes", []):
        lo_num = lo.get("lo_number", "LO?")
        lo_title = lo.get("lo_title", "")
        for lu in lo.get("learning_units", []):
            lu_num = lu.get("lu_number", "LU?")
            lu_title = lu.get("lu_title", "")
            topics_data = []

            for topic in lu.get("topics", []):
                t_title = topic.get("topic_title", "Topic")
                t_num = topic.get("topic_number", "T?")

                # Get infographic images for this topic (fuzzy match)
                topic_infographics = _fuzzy_get(infographic_results, t_title, [])

                # Get content blocks for fallback (fuzzy match)
                topic_content = _fuzzy_get(content_map, t_title, {})
                content_blocks = topic_content.get("content_blocks", [])

                # Get activity
                activity_data = topic_content.get("activity", {})
                activity_lines = _format_activity(activity_data)

                # Map infographic assignments to final slides
                assignments = topic.get("infographic_assignments", [])
                infographic_slides = []

                for assignment in assignments:
                    pos = assignment.get("slide_position", len(infographic_slides))
                    block_idx = assignment.get("content_block_index")

                    # Find matching infographic result
                    matching_infographic = None
                    for info in topic_infographics:
                        if info.get("slide_position") == pos:
                            matching_infographic = info
                            break

                    # Get caption from content block
                    caption = ""
                    fallback_bullets = []
                    if block_idx is not None and block_idx < len(content_blocks):
                        block = content_blocks[block_idx]
                        caption = block.get("caption", "")
                        # Build fallback bullets from block data
                        items = block.get("data", {}).get("items", [])
                        fallback_bullets = [
                            f"{it.get('label', '')}: {it.get('desc', '')}"
                            for it in items[:5]
                        ]
                    elif assignment.get("generated_data"):
                        items = assignment["generated_data"].get("items", [])
                        fallback_bullets = [
                            f"{it.get('label', '')}: {it.get('desc', '')}"
                            for it in items[:5]
                        ]

                    slide_title = assignment.get("sub_title", "") or (
                        content_blocks[block_idx].get("sub_title", t_title)
                        if block_idx is not None and block_idx < len(content_blocks)
                        else t_title
                    )

                    infographic_slides.append({
                        "position": pos,
                        "title": slide_title,
                        "image_path": (
                            matching_infographic.get("image_path")
                            if matching_infographic and matching_infographic.get("generated")
                            else None
                        ),
                        "caption": caption,
                        "fallback_bullets": fallback_bullets,
                    })

                topics_data.append({
                    "title": t_title,
                    "topic_number": t_num,
                    "lo_number": lo_num,
                    "lo_title": lo_title,
                    "lu_number": lu_num,
                    "lu_title": lu_title,
                    "ref": "",
                    "infographic_slides": infographic_slides,
                    "activity": activity_lines,
                })

            lu_data_map[lu_num] = {
                "topics": topics_data,
                "lo_number": lo_num,
                "lo_title": lo_title,
                "lu_number": lu_num,
                "lu_title": lu_title,
            }

    return lu_data_map


def _format_activity(activity_data: dict) -> list:
    """Format activity dict into string list for PPTX builder."""
    if not activity_data:
        return []

    if isinstance(activity_data, list):
        return activity_data

    lines = []
    if activity_data.get("title"):
        lines.append(f"Activity: {activity_data['title']}")
    if activity_data.get("scenario"):
        lines.append(f"Scenario: {activity_data['scenario']}")
    for step in activity_data.get("steps", []):
        lines.append(step)
    if activity_data.get("expected_output"):
        lines.append(f"Expected Output: {activity_data['expected_output']}")
    if activity_data.get("duration"):
        lines.append(f"Duration: {activity_data['duration']}")
    return lines
