"""
Slides Agent - AI-Enhanced Slide Generation

Uses Claude Agent SDK to analyze documents, evaluate sources,
craft optimal slide instructions, and validate quality before
sending to NotebookLM for slide generation.
"""

import json
import os
from typing import Optional
from courseware_agents.base import run_agent, run_agent_json


SYSTEM_PROMPT = """You are an expert educational content designer specializing in
creating presentation slides for WSQ (Workforce Skills Qualifications) training courses.

Your role is to analyze training documents and produce structured JSON that guides
slide generation. You focus on:
- Identifying key topics and learning outcomes
- Structuring content for effective presentation flow
- Ensuring alignment with WSQ competency standards
- Creating engaging, pedagogically sound slide content

Always output valid JSON matching the requested schema."""


async def analyze_document_for_slides(
    document_text: str,
    config: dict = None,
) -> dict:
    """
    Analyze a document and generate enhanced slide instructions using Claude Agent SDK.

    This replaces the old multi-agent pipeline (topic_analysis -> source_evaluator ->
    slide_instructions -> quality_validator) with a single comprehensive agent call.

    Args:
        document_text: The extracted text content from the uploaded document.
        config: Slide generation configuration dict.

    Returns:
        Dictionary with:
        - topics: List of identified key topics
        - slide_instructions: Detailed instructions for NotebookLM
        - enhanced_prompt: An enhanced prompt incorporating analysis results
        - summary: Brief analysis summary
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

2. **slide_instructions**: Detailed instructions for generating {num_slides} slides per topic, including:
   - Content structure recommendations
   - Visual layout suggestions
   - Key terminology to highlight
   - Practice exercises or discussion points
   {"- Assessment reminder slides for each major section" if include_assessment else ""}

3. **enhanced_prompt**: A single comprehensive prompt (2-3 paragraphs) that can be used
   to instruct NotebookLM to generate optimal slides from this content. This prompt should
   incorporate the topic analysis and include specific guidance about slide structure,
   content depth, and pedagogical approach.

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
        # Return a basic result if agent fails
        return {
            "topics": [],
            "slide_instructions": "",
            "enhanced_prompt": "",
            "summary": f"Agent analysis failed: {str(e)}",
            "error": str(e),
        }
