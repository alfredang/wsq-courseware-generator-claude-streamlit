"""
Slides Agent - AI-Enhanced Slide Generation

Uses Claude Agent SDK to generate structured slide content for editable PPTX creation.
Also analyzes documents for slide instructions (legacy NotebookLM flow).
"""

import asyncio
import json
import logging
import os
from typing import Optional
from courseware_agents.base import run_agent, run_agent_json

logger = logging.getLogger(__name__)

SYSTEM_PROMPT = """You are an expert educational content designer specializing in
creating presentation slides for WSQ (Workforce Skills Qualifications) training courses.

Your role is to analyze training documents and produce structured JSON that guides
slide generation. You focus on:
- Identifying key topics and learning outcomes
- Structuring content for effective presentation flow
- Ensuring alignment with WSQ competency standards
- Creating engaging, pedagogically sound slide content

Always output valid JSON matching the requested schema."""


TOPIC_SLIDES_SYSTEM = """You are an expert WSQ training slide writer. You create CONCISE,
READABLE, KNOWLEDGEABLE presentation slides — the kind a real trainer would use in class.

CONTENT RULES — KNOWLEDGE-FOCUSED:
- Slides MUST explain concepts (WHAT it is, HOW it works, WHY it matters)
- Include: definitions, frameworks, processes, comparisons, best practices
- Balance: ~50% concept explanations, ~25% real-world examples, ~25% stats/facts
- Do NOT just list cases and resources — TEACH the concept first, then give examples
- Use industry terms but explain them clearly for adult learners

SLIDE WRITING RULES:
- Each bullet: 10-20 words — concise but informative
- 4-5 bullets per slide — enough content to learn from
- Use a mix of fragments and short explanatory sentences
- Include real facts and stats from your web research
- You MUST use WebSearch to research the topic BEFORE writing slides

GOOD bullet examples:
- "AI hallucination — model generates plausible but factually incorrect information"
- "How it works: LLMs predict next token based on training patterns, not understanding"
- "Singapore PDPA: consent required before collecting personal data (Section 13)"
- "Key difference: rule-based AI follows fixed logic, GenAI learns from data patterns"
- "73% of companies now have AI governance policies (McKinsey 2024)"

BAD bullet examples:
- TOO SHORT: "AI bias" (no explanation)
- TOO LONG: "Generative AI refers to AI systems capable of creating new content including text, images, code, audio, and video based on patterns learned from training data"
- TOO VAGUE: "Important considerations for AI" (what considerations?)

Always output valid JSON only. No markdown, no explanation, just the JSON object."""


async def analyze_document_for_slides(
    document_text: str,
    config: dict = None,
) -> dict:
    """
    Analyze a document and generate enhanced slide instructions using Claude Agent SDK.

    Args:
        document_text: The extracted text content from the uploaded document.
        config: Slide generation configuration dict.

    Returns:
        Dictionary with topics, slide_instructions, enhanced_prompt, summary.
    """
    if config is None:
        config = {}

    num_slides = config.get('slides_per_topic', 5)
    include_assessment = config.get('include_assessment_reminders', True)

    prompt = f"""Analyze the following training document and produce a JSON response with:

1. **topics**: A list of 3-8 key topics identified in the document, each with:
   - "name": Topic name
   - "subtopics": List of 2-4 subtopics
   - "key_points": List of 3-5 key points to cover
   - "learning_outcomes": Related learning outcomes from the document

2. **slide_instructions**: Detailed instructions for generating {num_slides} slides per topic.

3. **enhanced_prompt**: A comprehensive prompt for NotebookLM slide generation.

4. **summary**: A brief 2-3 sentence summary of the document analysis.

Document content:
---
{document_text[:15000]}
---

Respond with ONLY valid JSON matching this schema."""

    try:
        result = await run_agent_json(
            prompt=prompt,
            system_prompt=SYSTEM_PROMPT,
            tools=["Read", "Glob", "Grep"],
            max_turns=10,
        )
        return result
    except (ValueError, Exception) as e:
        return {
            "topics": [],
            "slide_instructions": "",
            "enhanced_prompt": "",
            "summary": f"Agent analysis failed: {str(e)}",
            "error": str(e),
        }


async def generate_topic_slides(
    context: dict,
    lu: dict,
    topic: dict,
    topic_idx: int,
    lu_num: str,
    num_topics: int,
    slides_per_topic: int = 10,
) -> dict:
    """Generate slides for a SINGLE topic using Claude AI with web research.

    Slide count is dynamic based on course duration:
    - 1-day course: ~5 slides/topic (60-100 total)
    - 2-day course: ~10-12 slides/topic (120-160 total)

    Args:
        context: Full extracted course info dict.
        lu: The Learning Unit dict.
        topic: The specific topic dict.
        topic_idx: Index of this topic (0-based).
        lu_num: LU number string (e.g. "LU1").
        num_topics: Total topics in this LU.
        slides_per_topic: Target number of content slides (calculated from course duration).

    Returns:
        Dict with 'title', 'ref', 'slides' list, 'activity' list.
    """
    course_title = context.get('Course_Title', 'Course')
    lu_title = lu.get('LU_Title', 'Learning Unit')
    t_title = topic.get('Topic_Title', f'Topic {topic_idx + 1}')
    t_desc = topic.get('Topic_Description', '')
    bullet_points = topic.get('Bullet_Points', []) or topic.get('Key_Points', [])
    ka_refs = topic.get('KA_References', [])
    if isinstance(ka_refs, list):
        ka_refs_str = ', '.join(ka_refs)
    else:
        ka_refs_str = str(ka_refs) if ka_refs else ''

    # Build K&A context
    k_statements = context.get('Knowledge_Statements', [])
    a_statements = context.get('Ability_Statements', [])
    ka_text = ""
    if k_statements:
        ka_text += "Knowledge Statements:\n" + "\n".join(f"  {k}" for k in k_statements[:8]) + "\n"
    if a_statements:
        ka_text += "Ability Statements:\n" + "\n".join(f"  {a}" for a in a_statements[:8]) + "\n"

    topic_detail = f"Topic: {t_title}"
    if t_desc:
        topic_detail += f"\nDescription: {t_desc}"
    if bullet_points:
        topic_detail += "\nKey Points from Course Proposal:"
        for bp in bullet_points:
            topic_detail += f"\n  - {bp}"
    if ka_refs_str:
        topic_detail += f"\nK&A References: {ka_refs_str}"

    # Build dynamic slide structure based on slides_per_topic
    if slides_per_topic <= 6:
        slide_structure = """1. Definition — WHAT is this concept? Clear definition with context (1 slide)
2. How It Works — mechanisms, processes, frameworks explained (1 slide)
3. Key Components — breakdown of sub-concepts, models, or frameworks (1 slide)
4. Real-World Application — case study or Singapore-specific example (1 slide)
5. Best Practices — do's and don'ts, practical guidelines (1 slide)
6. Key Takeaways — summary of most important points (1 slide)"""
    elif slides_per_topic <= 9:
        slide_structure = """1. Definition — WHAT is this concept? Clear definition with context (1 slide)
2. Why It Matters — importance, business impact, relevance (1 slide)
3. How It Works — mechanisms, processes, frameworks explained (1-2 slides)
4. Key Components — breakdown of sub-concepts, models, or frameworks (1-2 slides)
5. Real-World Application — case study or Singapore-specific example (1 slide)
6. Best Practices — do's and don'ts, practical guidelines (1 slide)
7. Key Takeaways — summary of most important points (1 slide)"""
    else:
        slide_structure = """1. Definition — WHAT is this concept? Clear definition with context (1 slide)
2. Why It Matters — importance, business impact, relevance (1 slide)
3. How It Works — mechanisms, processes, frameworks explained (1-2 slides)
4. Key Components — breakdown of sub-concepts, models, or frameworks (2 slides)
5. Real-World Application — case study or Singapore-specific example (1-2 slides)
6. Challenges & Risks — common pitfalls, limitations, risks (1 slide)
7. Best Practices — do's and don'ts, practical guidelines (1 slide)
8. Implementation Steps — how to apply this in workplace (1 slide)
9. Key Takeaways — summary of most important points (1 slide)"""

    prompt = f"""Generate slide content for Topic {topic_idx + 1} of {num_topics}.

Course: {course_title}
Learning Unit: {lu_num} - {lu_title}
{topic_detail}

{ka_text}

STEP 1 — RESEARCH (do this FIRST):
Use WebSearch to research this topic. Search for:
1. "{t_title} definition framework"
2. "{t_title} best practices Singapore"

STEP 2 — GENERATE EXACTLY {slides_per_topic} SLIDES (knowledge-focused):
After researching, create these slides:

{slide_structure}

STEP 3 — GENERATE A DIAGRAM for this topic:
Choose the BEST diagram type for this topic:
- "process" — for workflows, step-by-step procedures, how something works (3-6 steps)
- "comparison" — for key components, categories, types, frameworks (3-6 items with label+desc)
- "cycle" — for iterative processes, lifecycles, continuous improvement (3-6 stages)

Return a JSON object:
{{
  "title": "{t_title}",
  "ref": "",
  "slides": [
    {{
      "title": "Clear Slide Title",
      "bullets": [
        "Concept explanation — 10-20 words, informative but concise",
        "How it works — explain the mechanism or process clearly",
        "Key fact or statistic from research (with source)",
        "Comparison or contrast with related concept",
        "Practical application or Singapore-specific context"
      ]
    }},
    ... ({slides_per_topic} slides total)
  ],
  "diagram": {{
    "type": "process" or "comparison" or "cycle",
    "title": "Descriptive Diagram Title",
    "items": ["Step 1", "Step 2", "Step 3", "Step 4"]
  }},
  "activity": [
    "Activity: [Exercise Name]",
    "Scenario: [Brief scenario]",
    "Step 1: [Action]",
    "Step 2: [Action]",
    "Step 3: [Action]",
    "Expected Output: [What to produce]",
    "Duration: 15-20 minutes"
  ]
}}

DIAGRAM RULES:
- For "process": items = list of 3-6 short step names (max 30 chars each)
- For "comparison": items = list of 3-6 objects with "label" and "desc" keys
  Example: [{{"label": "Prevention", "desc": "Stop threats before they occur"}}]
- For "cycle": items = list of 3-6 stage names, center_text = optional center label
- EVERY topic MUST have a diagram — choose the type that best fits the content

CRITICAL RULES:
- EXACTLY {slides_per_topic} slides per topic — this is calculated to hit the target slide count
- 4-5 bullets per slide — concise but informative
- Each bullet: 10-20 words — explain concepts, not just list facts
- MUST include concept definitions and explanations (not just stats/cases)
- Include real stats/facts from your research (with source)
- Balance: definitions → explanations → examples → best practices
- NEVER include K/A references (K1, K2, A1, A2, etc.) in ANY slide title or topic title
- Slide titles must be CLEAN descriptive names only — no codes, no K/A tags
- The "ref" field in the JSON should always be an empty string ""
- Output ONLY valid JSON"""

    try:
        result = await run_agent_json(
            prompt=prompt,
            system_prompt=TOPIC_SLIDES_SYSTEM,
            tools=["WebSearch", "WebFetch"],
            max_turns=20,
        )
        # Validate
        slides = result.get('slides', [])
        logger.info(
            f"Generated {len(slides)} slides for {lu_num} T{topic_idx + 1}: {t_title}"
        )
        return result

    except Exception as e:
        logger.error(f"Topic slide generation failed for {lu_num} T{topic_idx + 1}: {e}")
        # Return fallback from CP data
        fallback_slides = []
        chunk_size = 5
        for j in range(0, max(len(bullet_points), 1), chunk_size):
            chunk = bullet_points[j:j + chunk_size]
            if chunk:
                fallback_slides.append({
                    "title": f"{t_title}" if j == 0 else f"{t_title} (Cont'd)",
                    "bullets": chunk,
                })
        if not fallback_slides:
            fallback_slides = [{"title": t_title, "bullets": [f"Content for {t_title}"]}]

        return {
            "title": f"T{topic_idx + 1}: {t_title}",
            "ref": ka_refs_str or "",
            "slides": fallback_slides,
            "activity": [
                f"Activity: {t_title} Practice",
                "Apply the concepts learned in this topic",
                "Step 1: Review the key concepts",
                "Step 2: Apply to a real-world scenario",
                "Step 3: Discuss findings with your group",
                "Duration: 20 minutes | Discussion: 10 minutes",
            ],
        }


async def generate_slide_content(
    context: dict,
    lu: dict,
    lu_idx: int,
    num_lus: int,
    slides_per_topic: int = 10,
) -> dict:
    """Generate structured slide content for a Learning Unit using Claude AI.

    Generates slides per-topic in PARALLEL for speed and depth.
    Slide count per topic is dynamic based on course duration.

    Args:
        context: Full extracted course info dict.
        lu: The Learning Unit dict with Topics.
        lu_idx: Index of this LU (0-based).
        num_lus: Total number of LUs.
        slides_per_topic: Target content slides per topic (from course duration scaling).

    Returns:
        Dict with 'topics' list, each containing 'title', 'ref', 'slides', 'activity'.
    """
    lu_num = lu.get('LU_Number', f'LU{lu_idx + 1}')
    topics = lu.get('Topics', [])
    num_topics = len(topics)

    if num_topics == 0:
        return {"topics": []}

    # Generate ALL topics in parallel for speed
    tasks = [
        generate_topic_slides(
            context, lu, topic, i, lu_num, num_topics,
            slides_per_topic=slides_per_topic
        )
        for i, topic in enumerate(topics)
    ]
    results = await asyncio.gather(*tasks, return_exceptions=True)

    topic_data_list = []
    for i, result in enumerate(results):
        if isinstance(result, Exception):
            logger.error(f"[{lu_num}] Topic {i + 1} failed: {result}")
            t = topics[i]
            topic_data_list.append({
                "title": f"T{i + 1}: {t.get('Topic_Title', f'Topic {i + 1}')}",
                "ref": "",
                "slides": [{"title": t.get('Topic_Title', 'Topic'), "bullets": ["Content pending"]}],
                "activity": [f"Activity: {t.get('Topic_Title', 'Topic')} Practice"],
            })
        else:
            topic_data_list.append(result)

    total_slides = sum(len(t.get('slides', [])) for t in topic_data_list)
    logger.info(f"Generated slide content for {lu_num}: {len(topic_data_list)} topics, {total_slides} slides total")

    return {"topics": topic_data_list}


async def extract_slides_text(image_dir: str) -> list:
    """Extract text from slide images using Claude Agent SDK (Read tool).

    The Read tool in Claude Agent SDK supports reading images — it presents
    them visually to the multimodal LLM. This means we can extract text
    from NotebookLM slide images using just the Claude Code subscription,
    no separate API key needed.

    Args:
        image_dir: Directory containing slide images (slide_000.png, slide_001.png, ...).

    Returns:
        List of dicts: [{"title": "...", "bullets": [...], "is_section_header": bool,
                          "has_diagram": bool, "layout": "text-full|..."}, ...]
    """
    # Use forward slashes for consistency in agent prompts
    safe_dir = image_dir.replace("\\", "/")

    prompt = f"""Extract text from ALL presentation slide images in this directory: {safe_dir}

INSTRUCTIONS:
1. First, use Glob to find all .png files matching "{safe_dir}/*.png"
2. Read EVERY image file found (they are numbered: slide_000.png, slide_001.png, etc.)
3. For each slide image, extract:
   - title: The main heading/title (usually at the top in larger font)
   - bullets: All bullet points and body text as a list of strings
   - is_section_header: true if slide is just a big centered title with no bullets
   - has_diagram: true if the slide contains diagrams, flowcharts, or images
   - layout: "text-full" (text spans width), "text-left" (text on left half),
             "text-right" (text on right half), "title-only" (just a title),
             "image-full" (mostly image/diagram)

Return ONLY a JSON object with this structure:
{{
  "slides": [
    {{
      "title": "Exact Title From Slide",
      "bullets": ["First bullet point text", "Second bullet point", ...],
      "is_section_header": false,
      "has_diagram": false,
      "layout": "text-full"
    }},
    ... (one entry per slide image, in order)
  ]
}}

IMPORTANT RULES:
- Process EVERY .png image in the directory — do not skip any
- Preserve the EXACT text visible on each slide (don't paraphrase or summarize)
- Section header slides (big centered title) should have empty bullets []
- Include ALL visible text, even small footnotes or labels
- Output ONLY the JSON object, nothing else"""

    try:
        result = await run_agent_json(
            prompt=prompt,
            system_prompt=(
                "You are an expert at reading presentation slide images and extracting text. "
                "Read each image carefully with the Read tool and extract all visible text. "
                "Organize the text into a title and bullet points. Be thorough — capture every "
                "piece of text on each slide. Return structured JSON only."
            ),
            tools=["Read", "Glob"],
            max_turns=50,
        )
        slides = result.get("slides", [])
        if isinstance(slides, list):
            logger.info(f"Extracted text from {len(slides)} slide images in {image_dir}")
            return slides
        return []
    except Exception as e:
        logger.error(f"Slide text extraction via SDK failed: {e}")
        return []
