"""
Research Agent (Agent 1) — Web Research for Slide Content

Searches the internet for 3-5 quality sources per topic (~20-30 total across course)
using WebSearch + WebFetch (built-in, no MCP needed). Tags data suitable for
infographic visualization (charts, processes, comparisons).

Runs as Phase 1 in the multi-agent pipeline.
"""

import asyncio
import logging
from typing import Optional
from courseware_agents.base import run_agent_json
from generate_slides.multi_agent_config import (
    RESEARCH_MAX_TURNS,
    RESEARCH_MODEL,
    DEFAULT_RESEARCH_DEPTH,
)

logger = logging.getLogger(__name__)

RESEARCH_SYSTEM_PROMPT = """You are a research agent for WSQ training content.
Find 3-5 quality sources per topic using 2 WebSearch calls. NO WebFetch.

CRITICAL RULES:
- Do exactly 2 WebSearch calls per topic — no more, no less
- Do NOT use WebFetch — extract all data from search result snippets
- Return JSON immediately after the 2 searches
- Research ONLY the EXACT topic title given

STRATEGY (2 searches → JSON):
1. WebSearch: "<topic title> overview guide best practices"
2. WebSearch: "<topic title> statistics framework examples"
3. Extract 3-5 sources from both search results' snippets
4. Return structured JSON — done

SOURCE QUALITY:
- PREFER: Wikipedia, government sites, academic papers, industry bodies (ISO, NIST)
- INCLUDE: McKinsey, Deloitte, Gartner, tech blogs, educational platforms
- AVOID: Personal blogs, unverified sources, content older than 2022

EXTRACT INFOGRAPHIC-READY DATA (SHORT labels, max 15 chars):
- QUANTITATIVE data (numbers, %, statistics) → chart_data (label max 2 words)
- STEP-BY-STEP processes or workflows → process_steps (step label max 3 words)
- TWO-SIDED comparisons (A vs B) → comparison_items (label max 3 words)
- HIERARCHICAL structures → hierarchy_data
- TIMELINE events → timeline_data

Output ONLY valid JSON. No markdown, no explanation."""


async def research_topic(
    topic_title: str,
    bullet_points: list = None,
    course_title: str = "",
    lo_description: str = "",
    research_depth: int = 20,
    model: Optional[str] = None,
) -> dict:
    """Research a single topic using WebSearch + WebFetch.

    Args:
        topic_title: The topic to research.
        bullet_points: Key points from the CP for this topic.
        course_title: Parent course title for context.
        lo_description: Learning outcome description.
        research_depth: Target number of sources (10/20/30).
        model: Optional model override.

    Returns:
        Dict with sources, summary, key_statistics, infographic_data, etc.
    """
    bp_text = ""
    if bullet_points:
        bp_text = "\nKey points to cover:\n" + "\n".join(f"  - {bp}" for bp in bullet_points[:10])

    lo_text = ""
    if lo_description:
        lo_text = f"\nLearning Outcome: {lo_description}"

    prompt = f"""Research the following topic for a WSQ training course.

COURSE: {course_title}
TOPIC (from Course Proposal — research EXACTLY this): {topic_title}
{lo_text}
{bp_text}

IMPORTANT: Research ONLY "{topic_title}" — do NOT drift to related but different topics.

SEARCH PLAN (2 searches, NO WebFetch):
1. WebSearch for "{topic_title} overview guide best practices"
2. WebSearch for "{topic_title} statistics framework examples"
3. Extract 3-5 sources from search result snippets — do NOT call WebFetch
4. Return JSON immediately

Return this JSON structure:
{{
  "topic": "{topic_title}",
  "search_queries_used": ["query 1", "query 2", ...],
  "sources": [
    {{
      "url": "https://...",
      "title": "Source Title",
      "type": "article",
      "key_findings": ["Finding 1 with specific data", "Finding 2"],
      "relevance_score": 0.95,
      "date": "2024"
    }}
  ],
  "summary": "2-3 paragraph synthesis of research findings",
  "key_statistics": [
    {{"stat": "73% of companies...", "source": "McKinsey 2024", "chart_type": "pie"}}
  ],
  "recommended_frameworks": ["Framework 1", "Framework 2"],
  "infographic_data": {{
    "chart_data": [
      {{"label": "Category A", "value": 73, "source": "McKinsey 2024"}},
      {{"label": "Category B", "value": 27, "source": "McKinsey 2024"}}
    ],
    "process_steps": [
      "Step 1: Identify data assets",
      "Step 2: Classify and categorize",
      "Step 3: Implement controls",
      "Step 4: Monitor and review"
    ],
    "comparison_items": [
      {{"label": "Traditional Approach", "desc": "Manual processes, paper-based"}},
      {{"label": "Modern Approach", "desc": "Automated, AI-driven analytics"}}
    ],
    "hierarchy_data": {{
      "root": "Main Concept",
      "children": ["Sub-concept 1", "Sub-concept 2", "Sub-concept 3"]
    }},
    "timeline_data": [
      {{"year": "2020", "event": "Initial adoption"}},
      {{"year": "2023", "event": "Mainstream adoption"}}
    ]
  }}
}}

IMPORTANT:
- Each source MUST have a real URL and specific key_findings
- key_statistics should include chart_type (pie/bar/line) for visualization
- infographic_data is CRITICAL — extract ALL visualizable data
- At least 3 entries in chart_data, 3-6 in process_steps, 2 in comparison_items
"""

    try:
        result = await run_agent_json(
            prompt=prompt,
            system_prompt=RESEARCH_SYSTEM_PROMPT,
            tools=["WebSearch"],
            max_turns=4,
            model=model or RESEARCH_MODEL,
        )
        source_count = len(result.get("sources", []))
        logger.info(f"Research complete for '{topic_title}': {source_count} sources")
        return result

    except Exception as e:
        logger.error(f"Research failed for '{topic_title}': {e}")
        return {
            "topic": topic_title,
            "search_queries_used": [],
            "sources": [],
            "summary": f"Research unavailable for {topic_title}.",
            "key_statistics": [],
            "recommended_frameworks": [],
            "infographic_data": {
                "chart_data": [],
                "process_steps": [],
                "comparison_items": [],
                "hierarchy_data": {},
                "timeline_data": [],
            },
        }


async def research_all_topics(
    topics: list,
    course_title: str = "",
    research_depth: int = 20,
    model: Optional[str] = None,
) -> dict:
    """Research all topics in parallel.

    Args:
        topics: List of dicts with topic_title, bullet_points, lo_description.
        course_title: Parent course title.
        research_depth: Sources per topic.
        model: Optional model override.

    Returns:
        Dict mapping topic_title → research results.
    """
    # 8 parallel agent sessions for faster research
    sem = asyncio.Semaphore(8)

    async def _bounded_research(t, i):
        async with sem:
            return await research_topic(
                topic_title=t.get("topic_title", f"Topic {i+1}"),
                bullet_points=t.get("bullet_points", []),
                course_title=course_title,
                lo_description=t.get("lo_description", ""),
                research_depth=research_depth,
                model=model,
            )

    tasks = [_bounded_research(t, i) for i, t in enumerate(topics)]
    results = await asyncio.gather(*tasks, return_exceptions=True)

    research_map = {}
    for i, result in enumerate(results):
        t_title = topics[i].get("topic_title", f"Topic {i+1}")
        if isinstance(result, Exception):
            logger.error(f"Research failed for '{t_title}': {result}")
            research_map[t_title] = {
                "topic": t_title, "sources": [], "summary": "Research unavailable.",
                "key_statistics": [],
                "recommended_frameworks": [],
                "infographic_data": {"chart_data": [], "process_steps": [],
                                     "comparison_items": [], "hierarchy_data": {},
                                     "timeline_data": []},
            }
        else:
            research_map[t_title] = result

    total_sources = sum(len(v.get("sources", [])) for v in research_map.values())
    logger.info(f"Research complete: {len(research_map)} topics, {total_sources} total sources")
    return research_map
