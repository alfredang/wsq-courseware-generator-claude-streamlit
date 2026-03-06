"""
Editor Agent (Agent 3) — Slide Structure & Infographic Assignments

Runs as Phase 3 in the 5-phase pipeline (after Research + Content Generator).
Receives content blocks from Phase 2 and structures them into the final
slide skeleton with infographic_assignments for each topic.

Tools & Skills:
  - Presentation Architecture: WSQ slide structure, section ordering
  - AntV Template Expertise: 65+ templates, template-content matching
  - Visual Flow Design: Template variety, visual storytelling sequence
  - Slide Count Optimization: Per-topic slide budget based on course hours

Determines:
- Total slide count targets
- How content blocks map to slide positions
- Which AntV template each infographic should use
- Standard WSQ intro/closing slide ordering
"""

import json
import logging
from typing import Optional
from courseware_agents.base import run_agent_json
from generate_slides.multi_agent_config import (
    EDITOR_MAX_TURNS,
    EDITOR_MODEL,
)

logger = logging.getLogger(__name__)


def _fuzzy_get_content(mapping: dict, key: str):
    """Fuzzy lookup for topic title keys (handles AI rephrasing)."""
    if not mapping or not key:
        return None
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
    return None

EDITOR_SYSTEM_PROMPT = """You are an expert WSQ training slide architect and visual flow designer.

YOUR EXPERTISE:
- Singapore WSQ presentation standards and structure
- AntV Infographic template system (65+ templates)
- Visual storytelling: sequence templates for flow, variety for engagement
- Slide budget optimization: balancing depth with presentation time

You design the complete deck structure by mapping content blocks to slide positions
with the BEST AntV template for each content type.

STANDARD WSQ SLIDE STRUCTURE (fixed, always include):
  Opening (10 slides):
    1. Cover Slide (course title, TGS code, version)
    2. Digital Attendance (Mandatory)
    3. About the Trainer (placeholder)
    4. Let's Know Each Other (icebreaker)
    5. Ground Rules
    6. Skills Framework (TSC info + all LOs)
    7. Knowledge & Ability Statements
    8. Course Outline (all topics by LU)
    9. Assessment Methods & Briefing
    10. Criteria for Funding

  Closing (7 slides):
    1. Summary & Q&A
    2. TRAQOM Survey
    3. Certificate of Accomplishment
    4. Digital Attendance (End)
    5. Final Assessment
    6. Support
    7. Thank You

DYNAMIC CONTENT (per LO → per LU → per Topic):
  For EACH Learning Outcome:
    - Section Header: "LO{n}: {LO_Description}"
    For EACH Learning Unit:
      - Section Header: "LU{n}: {LU_Title}"
      - Overview Slide (topics list)
      For EACH Topic:
        - Section Header: "T{n}: {Topic_Title}"
        - Infographic Slides (one per content block, 4-12 per topic)
        - Activity Slide

AntV TEMPLATE SELECTION (choose the BEST template per content block):
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

VISUAL FLOW RULES:
1. Map EVERY content block to a slide position — each block = one infographic slide
2. Validate that assigned_template matches the visualization_type
3. Override template if a better one exists for the specific content
4. NEVER assign the same template to consecutive slides — ensure visual variety
5. Use different template families across a topic (e.g. grid, snake, stairs, timeline)
6. Add an activity slide after each topic's infographic slides
7. First slide of each topic should use a list-grid-* or list-row-* (overview)
8. Statistical data → prefer chart-bar or chart-pie templates

Output ONLY valid JSON. No markdown, no explanation."""


async def generate_skeleton(
    context: dict,
    content_map: dict = None,
    model: Optional[str] = None,
) -> dict:
    """Generate the slide deck skeleton with infographic assignments.

    Phase 3: Receives content blocks from Phase 2 and maps them to
    slide positions with AntV template assignments.

    Args:
        context: Parsed Course Proposal context dict with Learning_Units.
        content_map: Dict mapping topic_title → content blocks (from Phase 2).
                     If None, generates a basic skeleton without assignments.
        model: Optional model override.

    Returns:
        Skeleton dict with standard_slides, learning_outcomes (with
        infographic_assignments per topic), and closing_slides.
    """
    course_title = context.get("Course_Title", "Course")
    tgs_ref = context.get("TGS_Ref_No", "")
    total_hours_str = context.get("Total_Training_Hours", "16")
    try:
        total_hours = float(
            "".join(c for c in total_hours_str if c.isdigit() or c == ".") or "16"
        )
    except ValueError:
        total_hours = 16.0

    course_days = max(1, total_hours / 8)
    lus = context.get("Learning_Units", [])
    total_topics = sum(len(lu.get("Topics", [])) for lu in lus)
    if total_topics == 0:
        total_topics = 1

    # Build LU/Topic summary with content block info
    lu_summary_parts = []
    for lu in lus:
        lu_num = lu.get("LU_Number", "LU?")
        lu_title = lu.get("LU_Title", "")
        lo_num = lu.get("LO_Number", "LO?")
        lo_desc = lu.get("LO", "")
        topics = lu.get("Topics", [])

        part = f"\n{lo_num}: {lo_desc}\n  {lu_num}: {lu_title}\n  Topics ({len(topics)}):"
        for i, t in enumerate(topics):
            t_title = t.get("Topic_Title", f"Topic {i+1}")
            part += f"\n    T{i+1}: {t_title}"

            # Include content block summary if available
            if content_map:
                topic_content = content_map.get(t_title, {})
                blocks = topic_content.get("content_blocks", [])
                if blocks:
                    part += f" — {len(blocks)} content blocks:"
                    for bi, block in enumerate(blocks):
                        viz = block.get("visualization_type", "?")
                        template = block.get("suggested_template", "?")
                        sub = block.get("sub_title", "?")
                        part += f"\n      Block {bi}: [{viz}] {sub} → {template}"
                else:
                    bullets = t.get("Bullet_Points", [])
                    part += f" — {len(bullets)} bullet points (no content blocks)"
            else:
                bullets = t.get("Bullet_Points", [])
                part += f" — {len(bullets)} bullet points"

        lu_summary_parts.append(part)

    lu_summary = "\n".join(lu_summary_parts)

    prompt = f"""Create the slide deck skeleton with infographic assignments for this WSQ course.

COURSE INFO:
- Title: {course_title}
- TGS Reference: {tgs_ref}
- Total Training Hours: {total_hours} hours ({course_days:.0f} day(s))
- Total Topics: {total_topics}

LEARNING UNITS, TOPICS & CONTENT BLOCKS:
{lu_summary}

INSTRUCTIONS:
1. Include ALL standard WSQ opening and closing slides
2. For each topic, map content blocks to infographic slide positions
3. Validate template choices — ensure template matches visualization_type
4. Override template if a better one exists (e.g., sequence-* for process type)
5. Ensure template variety — no consecutive duplicate templates

Return this exact JSON structure:
{{
  "total_target_slides": <number>,
  "course_days": {course_days:.0f},
  "standard_intro_slides": [
    {{"type": "cover", "title": "{course_title}"}},
    {{"type": "attendance", "title": "Digital Attendance (Mandatory)"}},
    {{"type": "placeholder", "title": "About the Trainer"}},
    {{"type": "icebreaker", "title": "Let's Know Each Other"}},
    {{"type": "content", "title": "Ground Rules"}},
    {{"type": "content", "title": "Skills Framework"}},
    {{"type": "content", "title": "Knowledge & Ability Statements"}},
    {{"type": "content", "title": "Course Outline"}},
    {{"type": "content", "title": "Assessment Methods & Briefing"}},
    {{"type": "content", "title": "Criteria for Funding"}}
  ],
  "learning_outcomes": [
    {{
      "lo_number": "LO1",
      "lo_title": "...",
      "lo_description": "...",
      "learning_units": [
        {{
          "lu_number": "LU1",
          "lu_title": "...",
          "topics": [
            {{
              "topic_number": "T1",
              "topic_title": "...",
              "num_infographic_slides": 6,
              "infographic_assignments": [
                {{
                  "slide_position": 0,
                  "content_block_index": 0,
                  "sub_title": "What is Topic?",
                  "visualization_type": "overview",
                  "assigned_template": "list-grid-badge-card"
                }},
                {{
                  "slide_position": 1,
                  "content_block_index": 1,
                  "sub_title": "Process Steps",
                  "visualization_type": "process",
                  "assigned_template": "sequence-snake-steps-compact-card"
                }}
              ],
              "has_activity": true
            }}
          ]
        }}
      ]
    }}
  ],
  "standard_closing_slides": [
    {{"type": "section", "title": "Summary & Q&A"}},
    {{"type": "content", "title": "TRAQOM Survey"}},
    {{"type": "content", "title": "Certificate of Accomplishment"}},
    {{"type": "attendance", "title": "Digital Attendance"}},
    {{"type": "section", "title": "Final Assessment"}},
    {{"type": "content", "title": "Support"}},
    {{"type": "section", "title": "Thank You"}}
  ]
}}

CRITICAL:
- topic_title in output MUST be EXACTLY the same as the input topic title (no rephrasing!)
- lu_number MUST match the input LU number EXACTLY (e.g. if input says "LU 1", output "LU 1")
- infographic_assignments must have ONE entry per content block
- Each assignment: slide_position (0-indexed), content_block_index, sub_title,
  visualization_type, assigned_template (valid AntV template name)
- Validate templates match visualization types
- Vary templates — avoid repeating same template in consecutive slides
"""

    try:
        result = await run_agent_json(
            prompt=prompt,
            system_prompt=EDITOR_SYSTEM_PROMPT,
            tools=[],
            max_turns=EDITOR_MAX_TURNS,
            model=model or EDITOR_MODEL,
        )
        _validate_skeleton(result, lus, content_map)
        logger.info(
            f"Skeleton created: {result.get('total_target_slides', '?')} target slides, "
            f"{sum(len(lo.get('learning_units', [])) for lo in result.get('learning_outcomes', []))} LUs"
        )
        return result

    except Exception as e:
        logger.warning(f"Editor agent failed, generating fallback skeleton: {e}")
        return _fallback_skeleton(context, total_hours, course_days, total_topics, content_map)


def _validate_skeleton(skeleton: dict, lus: list, content_map: dict = None) -> None:
    """Validate skeleton structure and ensure ALL content blocks have assignments.

    CRITICAL: Always rebuild assignments from content_map to guarantee 1:1 mapping
    between content blocks and infographic slides. The AI editor often produces
    fewer assignments than content blocks exist.
    """
    if "learning_outcomes" not in skeleton:
        raise ValueError("Skeleton missing 'learning_outcomes'")

    for lo in skeleton["learning_outcomes"]:
        if "learning_units" not in lo:
            raise ValueError(f"LO {lo.get('lo_number')} missing 'learning_units'")
        for lu in lo["learning_units"]:
            if "topics" not in lu:
                raise ValueError(f"LU {lu.get('lu_number')} missing 'topics'")
            for topic in lu["topics"]:
                t_title = topic.get("topic_title", "")
                matched_content = _fuzzy_get_content(content_map, t_title) if content_map else None
                blocks = matched_content.get("content_blocks", []) if matched_content else []

                existing_assignments = topic.get("infographic_assignments", [])

                # ALWAYS rebuild from content blocks if we have more blocks than assignments
                if blocks and len(blocks) > len(existing_assignments):
                    logger.info(
                        f"Rebuilding assignments for '{t_title}': "
                        f"{len(existing_assignments)} assignments → {len(blocks)} blocks"
                    )
                    new_assignments = []
                    for bi, block in enumerate(blocks):
                        # Preserve AI template choice if it exists for this position
                        ai_assignment = None
                        for ea in existing_assignments:
                            if ea.get("content_block_index") == bi:
                                ai_assignment = ea
                                break

                        new_assignments.append({
                            "slide_position": bi,
                            "content_block_index": bi,
                            "sub_title": block.get("sub_title", ""),
                            "visualization_type": block.get("visualization_type", "overview"),
                            "assigned_template": (
                                ai_assignment.get("assigned_template")
                                if ai_assignment
                                else block.get("suggested_template", "list-grid-badge-card")
                            ),
                        })
                    topic["infographic_assignments"] = new_assignments
                elif not existing_assignments and blocks:
                    # No assignments at all — generate from content blocks
                    topic["infographic_assignments"] = []
                    for bi, block in enumerate(blocks):
                        topic["infographic_assignments"].append({
                            "slide_position": bi,
                            "content_block_index": bi,
                            "sub_title": block.get("sub_title", ""),
                            "visualization_type": block.get("visualization_type", "overview"),
                            "assigned_template": block.get("suggested_template", "list-grid-badge-card"),
                        })

                topic["num_infographic_slides"] = len(topic.get("infographic_assignments", []))
                logger.info(
                    f"  Topic '{t_title}': {topic['num_infographic_slides']} infographic slides"
                )


def _fallback_skeleton(
    context: dict, total_hours: float, course_days: float,
    total_topics: int, content_map: dict = None,
) -> dict:
    """Generate a skeleton algorithmically when the agent fails."""
    from generate_slides.multi_agent_config import compute_slides_per_topic

    slides_per = compute_slides_per_topic(total_hours, total_topics)
    lus = context.get("Learning_Units", [])
    course_title = context.get("Course_Title", "Course")

    learning_outcomes = []
    for lu in lus:
        lo_num = lu.get("LO_Number", "LO?")
        lu_num = lu.get("LU_Number", "LU?")
        topics = lu.get("Topics", [])
        topic_entries = []

        for i, t in enumerate(topics):
            t_title = t.get("Topic_Title", f"Topic {i+1}")

            # Build infographic_assignments from content blocks
            assignments = []
            if content_map and t_title in content_map:
                blocks = content_map[t_title].get("content_blocks", [])
                for bi, block in enumerate(blocks):
                    assignments.append({
                        "slide_position": bi,
                        "content_block_index": bi,
                        "sub_title": block.get("sub_title", ""),
                        "visualization_type": block.get("visualization_type", "overview"),
                        "assigned_template": block.get("suggested_template", "list-grid-badge-card"),
                    })
            else:
                # No content blocks — create placeholder assignments
                bps = t.get("Bullet_Points", [])
                num_slides = min(slides_per, max(4, len(bps)))
                for si in range(num_slides):
                    assignments.append({
                        "slide_position": si,
                        "content_block_index": si,
                        "sub_title": bps[si] if si < len(bps) else f"Slide {si+1}",
                        "visualization_type": "overview",
                        "assigned_template": "list-grid-badge-card",
                    })

            topic_entries.append({
                "topic_number": f"T{i+1}",
                "topic_title": t_title,
                "num_infographic_slides": len(assignments),
                "infographic_assignments": assignments,
                "has_activity": True,
            })

        # Group by LO
        existing_lo = None
        for lo in learning_outcomes:
            if lo["lo_number"] == lo_num:
                existing_lo = lo
                break

        lu_entry = {
            "lu_number": lu_num,
            "lu_title": lu.get("LU_Title", ""),
            "topics": topic_entries,
        }

        if existing_lo:
            existing_lo["learning_units"].append(lu_entry)
        else:
            learning_outcomes.append({
                "lo_number": lo_num,
                "lo_title": lu.get("LO", ""),
                "lo_description": lu.get("LO", ""),
                "learning_units": [lu_entry],
            })

    return {
        "total_target_slides": int(course_days * 80),
        "course_days": int(course_days),
        "standard_intro_slides": [
            {"type": "cover", "title": course_title},
            {"type": "attendance", "title": "Digital Attendance (Mandatory)"},
            {"type": "placeholder", "title": "About the Trainer"},
            {"type": "icebreaker", "title": "Let's Know Each Other"},
            {"type": "content", "title": "Ground Rules"},
            {"type": "content", "title": "Skills Framework"},
            {"type": "content", "title": "Knowledge & Ability Statements"},
            {"type": "content", "title": "Course Outline"},
            {"type": "content", "title": "Assessment Methods & Briefing"},
            {"type": "content", "title": "Criteria for Funding"},
        ],
        "learning_outcomes": learning_outcomes,
        "standard_closing_slides": [
            {"type": "section", "title": "Summary & Q&A"},
            {"type": "content", "title": "TRAQOM Survey"},
            {"type": "content", "title": "Certificate of Accomplishment"},
            {"type": "attendance", "title": "Digital Attendance"},
            {"type": "section", "title": "Final Assessment"},
            {"type": "content", "title": "Support"},
            {"type": "section", "title": "Thank You"},
        ],
    }
