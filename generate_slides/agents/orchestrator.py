"""
Slides Generation Orchestrator.

Coordinates the agentic pipeline for slide generation:
1. Topic Analysis Agent (LLM) -> research queries
2. NotebookLM: create notebook, add source
3. NotebookLM: research + Source Evaluator Agent (LLM) -> filtered sources
4. Slide Instructions Agent (LLM) -> optimal instructions
5. NotebookLM: generate slides
6. Quality Validator Agent (LLM) -> quality report
7. Adaptive retry if needed

NotebookLM operations use zero LLM tokens. LLM agents handle the
intelligence layer only.
"""

import asyncio
import json
import logging
import re
import urllib.parse
from typing import Dict, Any, List, Optional, Callable

from generate_slides.agents.topic_analysis_agent import run_topic_analysis
from generate_slides.agents.source_evaluator_agent import run_source_evaluator
from generate_slides.agents.slide_instructions_agent import run_slide_instructions
from generate_slides.agents.quality_validator_agent import run_quality_validator
from generate_slides.slides_generation import _extract_research_queries

logger = logging.getLogger(__name__)


# ---------------------------------------------------------------------------
# Helper functions (NotebookLM API operations — zero LLM tokens)
# ---------------------------------------------------------------------------

def _build_platform_urls(topics: List[str]) -> List[Dict[str, str]]:
    """
    Build Wikipedia URLs for given topics.

    Args:
        topics: List of topic name strings

    Returns:
        List of dicts with 'url' and 'title' keys
    """
    urls = []
    for topic in topics[:3]:
        clean_topic = re.sub(r'[^\w\s\-]', '', topic).strip()
        if not clean_topic:
            continue
        wiki_query = urllib.parse.quote_plus(clean_topic)
        urls.append({
            "url": f"https://en.wikipedia.org/w/index.php?search={wiki_query}",
            "title": f"Wikipedia: {clean_topic[:60]}",
        })
    return urls


async def _add_platform_sources(
    client, notebook_id: str, topic_names: List[str],
    progress_callback: Optional[Callable] = None,
) -> List[str]:
    """
    Add Wikipedia sources to the notebook.

    Args:
        client: NotebookLMClient instance (connected)
        notebook_id: Target notebook
        topic_names: List of topic name strings
        progress_callback: Optional progress callback

    Returns:
        List of successfully added source IDs
    """
    platform_urls = _build_platform_urls(topic_names)
    added_source_ids = []

    if not platform_urls:
        return added_source_ids

    if progress_callback:
        progress_callback(
            f"Adding {len(platform_urls)} Wikipedia sources...", 30
        )

    for url_info in platform_urls:
        try:
            source = await client.sources.add_url(
                notebook_id, url_info["url"], wait=False
            )
            if source and hasattr(source, 'id'):
                added_source_ids.append(source.id)
                logger.info(f"Added platform source: {url_info['title']} -> {source.id}")
        except Exception as e:
            logger.info(f"Skipped platform source {url_info['url']}: {e}")

    return added_source_ids


async def _research_single_query(
    client, notebook_id: str, query: str,
    idx: int, total: int,
    progress_callback: Optional[Callable] = None,
) -> List[Dict[str, str]]:
    """
    Run a single deep web research query via NotebookLM Research API.

    Args:
        client: NotebookLMClient instance (connected)
        notebook_id: Target notebook
        query: Research query string
        idx: Query index (0-based)
        total: Total number of queries
        progress_callback: Optional progress callback

    Returns:
        List of found source dicts with 'url', 'title', 'summary' keys.
        Also includes '_task_id' for later import_sources call.
    """
    query_num = idx + 1
    logger.info(f"Starting research query {query_num}/{total}: {query}")

    if progress_callback:
        progress_callback(
            f"Researching topic {query_num}/{total}: {query[:60]}...",
            35 + (idx * 8),
        )

    try:
        task = await client.research.start(notebook_id, query, source="web", mode="fast")
        task_id = task.get("task_id") or task.get("report_id", "")
        logger.info(f"Research started: task_id={task_id}")

        # Poll until complete (timeout 120s)
        poll_timeout = 120
        elapsed = 0
        poll_interval = 5
        research_result = None

        while elapsed < poll_timeout:
            await asyncio.sleep(poll_interval)
            elapsed += poll_interval

            result = await client.research.poll(notebook_id)
            status = result.get("status", "")
            logger.info(f"Research poll: status={status}, elapsed={elapsed}s")

            if status == "completed":
                research_result = result
                break
            elif status == "no_research":
                logger.warning(f"Research returned no_research for query: {query}")
                break

        if not research_result:
            logger.warning(f"Research timed out or failed for query: {query}")
            return []

        found_sources = research_result.get("sources", [])
        logger.info(f"Research found {len(found_sources)} sources for query: {query[:60]}")

        # Attach task_id so orchestrator can import later
        for s in found_sources:
            s["_task_id"] = task_id

        return found_sources[:5]  # Cap at 5 per query

    except Exception as e:
        logger.warning(f"Research failed for query '{query}': {e}")
        return []


async def _import_approved_sources(
    client, notebook_id: str, task_id: str,
    approved_sources: List[Dict[str, Any]],
) -> List[str]:
    """
    Import evaluator-approved sources into the notebook.

    Args:
        client: NotebookLMClient instance (connected)
        notebook_id: Target notebook
        task_id: Research task ID for import_sources
        approved_sources: List of source dicts (must have 'url')

    Returns:
        List of imported source IDs
    """
    imported_ids = []

    if not approved_sources:
        return imported_ids

    sources_to_import = [s for s in approved_sources if s.get("url")]

    if not sources_to_import:
        return imported_ids

    try:
        imported = await client.research.import_sources(
            notebook_id, task_id, sources_to_import
        )
        for src in imported:
            src_id = src.get("id") or src.get("source_id", "")
            if src_id:
                imported_ids.append(src_id)
        logger.info(f"Imported {len(imported_ids)} approved sources")
    except Exception as e:
        logger.warning(f"Failed to import approved sources: {e}")

    return imported_ids


async def _generate_with_retry(
    client, notebook_id: str, source_ids: List[str], instructions: str,
) -> tuple:
    """
    Generate slide deck with up to 3 retry attempts.

    Args:
        client: NotebookLMClient instance (connected)
        notebook_id: Target notebook
        source_ids: All source IDs to include
        instructions: Slide generation instructions

    Returns:
        Tuple of (gen_result, task_id)
    """
    gen_result = None
    task_id = None

    for attempt in range(3):
        try:
            gen_result = await client.artifacts.generate_slide_deck(
                notebook_id,
                source_ids=source_ids,
                instructions=instructions,
            )
            task_id = gen_result.task_id if hasattr(gen_result, 'task_id') else str(gen_result)
            logger.info(f"Slide generation triggered: task_id={task_id}, sources={len(source_ids)}")
            break
        except Exception as e:
            logger.warning(f"Slide generation attempt {attempt + 1} failed: {e}")
            if attempt < 2:
                await asyncio.sleep(8)
            else:
                raise

    return gen_result, task_id


async def _wait_for_slides(client, notebook_id: str, task_id: str) -> str:
    """
    Wait for slide generation to complete.

    Args:
        client: NotebookLMClient instance (connected)
        notebook_id: Target notebook
        task_id: Generation task ID

    Returns:
        Status string: "completed", "timeout", or "wait_error: ..."
    """
    if not task_id:
        return "no_task_id"

    try:
        final_status = await client.artifacts.wait_for_completion(
            notebook_id, task_id, timeout=300.0
        )
        logger.info(f"Slide generation completed: {final_status}")
        return "completed"
    except TimeoutError:
        logger.warning("Slide generation timed out after 300s")
        return "timeout"
    except Exception as e:
        logger.warning(f"Wait for completion error: {e}")
        return f"wait_error: {e}"


async def _chat_review_slides(client, notebook_id: str) -> str:
    """
    Use NotebookLM chat to ask about generated slides for quality validation.

    Args:
        client: NotebookLMClient instance (connected)
        notebook_id: Target notebook

    Returns:
        Text description of the slides from NotebookLM chat
    """
    try:
        review_question = (
            "Summarize the slide deck you generated. List all section titles, "
            "the key topics covered in each section, and whether speaker notes "
            "are included. Also note any learning outcomes or assessment points covered."
        )
        result = await client.chat.ask(notebook_id, review_question)
        answer = result.answer if hasattr(result, 'answer') else str(result)
        logger.info(f"Chat review received: {len(answer)} chars")
        return answer
    except Exception as e:
        logger.warning(f"Chat review failed: {e}")
        return f"Unable to review slides via chat: {e}"


def _build_fallback_instructions(config: Dict[str, Any], research_sources_count: int) -> str:
    """
    Build fallback hardcoded instructions (used when instructions agent fails).

    Args:
        config: Slide configuration dict
        research_sources_count: Number of research sources available

    Returns:
        Instruction string for NotebookLM
    """
    slides_per_topic = config.get('slides_per_topic', 3)
    include_notes = config.get('include_notes', True)
    include_summaries = config.get('include_summaries', True)
    slide_style = config.get('slide_style', 'Professional')

    instructions = (
        f"Create a {slide_style.lower()} slide deck for this WSQ course material. "
        f"Target approximately {slides_per_topic} slides per topic/learning unit. "
        "Structure the presentation so each major topic or learning unit has its own "
        "clearly separated section with a section title slide. "
        "Use a logical flow: start with an overview/agenda slide, then dedicate "
        "separate sections for each topic, and end with a conclusion/summary. "
    )
    if include_notes:
        instructions += "Include detailed speaker/facilitator notes for each slide. "
    if include_summaries:
        instructions += "Add a summary slide at the end of each section before moving to the next topic. "
    if research_sources_count > 0:
        instructions += (
            "Incorporate the latest research findings and industry best practices "
            "from the web research sources provided. "
        )
    instructions += "Ensure all key learning outcomes and competencies are covered."
    return instructions


# ---------------------------------------------------------------------------
# Main orchestrator pipeline
# ---------------------------------------------------------------------------

async def run_agentic_pipeline(
    content: str,
    filename: str,
    config: Dict[str, Any],
    model_choice: str,
    progress_callback: Optional[Callable] = None,
    max_retries: int = 1,
) -> Dict[str, Any]:
    """
    Full agentic slides generation pipeline.

    Coordinates 4 LLM agents with NotebookLM API operations:
    - Topic Analysis Agent: intelligent research query extraction
    - Source Evaluator Agent: filters low-quality research sources
    - Slide Instructions Agent: crafts optimal generation instructions
    - Quality Validator Agent: scores output and triggers adaptive retry

    Args:
        content: Extracted document text
        filename: Original filename
        config: UI configuration dict (all slide options)
        model_choice: LLM model choice for agents
        progress_callback: Callback(message, percent) for UI progress
        max_retries: Max quality-based retries (0 = no validation)

    Returns:
        Dict with success, message, notebook_id, quality_report, etc.
    """
    try:
        from notebooklm import NotebookLMClient
    except ImportError:
        return {
            "success": False,
            "message": ("**notebooklm-py is not installed.**\n\n"
                        "Run: `pip install notebooklm-py[browser]`\n\n"
                        "Then authenticate: `python -m notebooklm login`"),
        }

    enable_research = config.get('enable_research', True)
    num_queries = config.get('num_queries', 2)
    material_type = config.get('material_type', 'Course Material')
    total_steps = 10

    try:
        # =================================================================
        # PHASE 1: Topic Analysis (LLM Agent)
        # =================================================================
        topics = []
        document_domain = ""
        research_queries = []
        topic_result = {}

        if enable_research:
            if progress_callback:
                progress_callback(f"Step 1/{total_steps}: Analyzing document topics with AI...", 5)

            try:
                topic_result = await run_topic_analysis(
                    content=content,
                    filename=filename,
                    material_type=material_type,
                    num_queries=num_queries,
                    model_choice=model_choice,
                )
                topics = topic_result.get("topics", [])
                document_domain = topic_result.get("document_domain", "")
                research_queries = [t.get("research_query", "") for t in topics if t.get("research_query")]
                logger.info(f"Topic analysis: {len(topics)} topics, domain='{document_domain}'")
            except Exception as e:
                logger.warning(f"Topic analysis agent failed, falling back to regex extraction: {e}")
                topics = []
                research_queries = []

            # Fallback: if LLM produced no queries, use regex-based extraction
            if not research_queries:
                logger.info("Using regex-based topic extraction as fallback")
                if progress_callback:
                    progress_callback(f"Step 1/{total_steps}: Extracting topics from document text...", 8)
                research_queries = _extract_research_queries(content, filename, material_type, num_queries)
                # Build basic topic dicts for Wikipedia sources
                if not topics and research_queries:
                    topics = [{"name": re.sub(r'\s+(training|best practices|latest|industry|standards|developments|course content).*$',
                                              '', q, flags=re.IGNORECASE).strip(),
                               "research_query": q} for q in research_queries]
                logger.info(f"Regex fallback produced {len(research_queries)} queries: {research_queries}")
        else:
            if progress_callback:
                progress_callback(f"Step 1/{total_steps}: Skipping topic analysis (research disabled)...", 5)

        # =================================================================
        # PHASE 2: NotebookLM Setup (No LLM tokens)
        # =================================================================
        if progress_callback:
            progress_callback(f"Step 2/{total_steps}: Connecting to NotebookLM...", 10)

        client = await NotebookLMClient.from_storage()

        async with client:
            # Step 3: Create notebook
            if progress_callback:
                progress_callback(f"Step 3/{total_steps}: Creating notebook...", 15)

            notebook_title = f"{filename} - {material_type} Slides"
            notebook = await client.notebooks.create(notebook_title)
            notebook_id = notebook.id
            logger.info(f"Created notebook: {notebook_id} - {notebook_title}")

            # Step 4: Add source document
            if progress_callback:
                progress_callback(f"Step 4/{total_steps}: Uploading course content...", 20)

            source_title = f"{filename} ({material_type})"
            source_text = content[:100000]
            source = await client.sources.add_text(notebook_id, source_title, source_text)
            source_id = source.id
            logger.info(f"Added source: {source_id} - {source.title}")

            # Wait for source processing
            wait_time = min(15, max(8, len(source_text) // 10000))
            logger.info(f"Waiting {wait_time}s for source processing ({len(source_text)} chars)")
            await asyncio.sleep(wait_time)

            # Verify source is available
            try:
                sources_list = await client.sources.list(notebook_id)
                source_ready = any(s.id == source_id for s in sources_list)
                if source_ready:
                    logger.info(f"Source {source_id} confirmed available")
                else:
                    logger.warning(f"Source {source_id} not yet visible — waiting 10 more seconds")
                    await asyncio.sleep(10)
            except Exception as e:
                logger.warning(f"Could not verify source readiness: {e}")
                await asyncio.sleep(5)

            all_source_ids = [source_id]
            research_sources_count = 0
            platform_sources_count = 0
            source_evaluation_results = []

            # =================================================================
            # PHASE 3: Research + Source Evaluation
            # =================================================================
            if enable_research and research_queries:
                # Step 5: Add Wikipedia sources (using search URLs for reliability)
                if progress_callback:
                    progress_callback(f"Step 5/{total_steps}: Adding Wikipedia sources...", 28)

                topic_names = [t.get("name", "") for t in topics if t.get("name")]
                platform_source_ids = await _add_platform_sources(
                    client, notebook_id, topic_names, progress_callback
                )
                all_source_ids.extend(platform_source_ids)
                platform_sources_count = len(platform_source_ids)
                logger.info(f"Added {platform_sources_count} Wikipedia sources")

                # Step 6: Web research per query + Source Evaluation
                if progress_callback:
                    progress_callback(f"Step 6/{total_steps}: Researching topics on the web...", 35)

                for idx, query in enumerate(research_queries):
                    # Run NotebookLM research (no LLM tokens)
                    found_sources = await _research_single_query(
                        client, notebook_id, query, idx, len(research_queries),
                        progress_callback,
                    )

                    if found_sources:
                        # Evaluate sources with LLM agent
                        if progress_callback:
                            progress_callback(
                                f"Step 6/{total_steps}: Evaluating source quality for topic {idx + 1}...",
                                40 + (idx * 8),
                            )

                        # Prepare sources for evaluation (strip internal fields)
                        eval_sources = [
                            {"url": s.get("url", ""), "title": s.get("title", ""), "summary": s.get("summary", "")}
                            for s in found_sources
                        ]
                        task_id_for_import = found_sources[0].get("_task_id", "") if found_sources else ""

                        try:
                            eval_result = await run_source_evaluator(
                                sources=eval_sources,
                                document_domain=document_domain,
                                research_query=query,
                                material_type=material_type,
                                model_choice=model_choice,
                            )
                            source_evaluation_results.append(eval_result)

                            # Only import approved sources
                            approved = [
                                s for s in eval_result.get("evaluated_sources", [])
                                if s.get("approved", False)
                            ]

                            if approved and task_id_for_import:
                                imported_ids = await _import_approved_sources(
                                    client, notebook_id, task_id_for_import, approved
                                )
                                all_source_ids.extend(imported_ids)
                                research_sources_count += len(imported_ids)
                        except Exception as e:
                            logger.warning(f"Source evaluation failed for query '{query}': {e}")
                            # Fallback: import all found sources without evaluation
                            if task_id_for_import:
                                imported_ids = await _import_approved_sources(
                                    client, notebook_id, task_id_for_import, eval_sources
                                )
                                all_source_ids.extend(imported_ids)
                                research_sources_count += len(imported_ids)

                # Wait for platform sources to finish processing
                if platform_source_ids:
                    try:
                        await client.sources.wait_for_sources(
                            notebook_id, platform_source_ids, timeout=60.0
                        )
                    except Exception as e:
                        logger.warning(f"Some Wikipedia sources may not be ready: {e}")

                # Wait for research sources
                research_ids_only = [sid for sid in all_source_ids if sid != source_id and sid not in platform_source_ids]
                if research_ids_only:
                    try:
                        await client.sources.wait_for_sources(
                            notebook_id, research_ids_only, timeout=120.0
                        )
                    except Exception as e:
                        logger.warning(f"Some research sources may not be ready: {e}")

                logger.info(
                    f"Research complete: {research_sources_count} web + "
                    f"{platform_sources_count} Wikipedia. Total: {len(all_source_ids)}"
                )

            # =================================================================
            # PHASE 4: Generate Slide Instructions (LLM Agent)
            # =================================================================
            if progress_callback:
                progress_callback(f"Step 7/{total_steps}: Crafting optimal slide instructions with AI...", 60)

            instructions = ""
            expected_structure = []

            try:
                instructions_result = await run_slide_instructions(
                    content=content,
                    topics=topics,
                    config=config,
                    research_sources_count=research_sources_count,
                    model_choice=model_choice,
                )
                instructions = instructions_result.get("instructions", "")
                expected_structure = instructions_result.get("structure_outline", [])
            except Exception as e:
                logger.warning(f"Slide instructions agent failed, using fallback: {e}")

            # Fallback if agent produced empty instructions
            if not instructions:
                instructions = _build_fallback_instructions(config, research_sources_count)
                logger.info("Using fallback instructions")

            # =================================================================
            # PHASE 5: Generate Slides (NotebookLM, no LLM tokens)
            # =================================================================
            if progress_callback:
                progress_callback(f"Step 8/{total_steps}: Generating slides in NotebookLM...", 65)

            gen_result, task_id = await _generate_with_retry(
                client, notebook_id, all_source_ids, instructions
            )

            # Step 9: Wait for completion
            if progress_callback:
                progress_callback(
                    f"Step 9/{total_steps}: Waiting for slides to be generated...", 75
                )

            generation_status = await _wait_for_slides(client, notebook_id, task_id)

            # =================================================================
            # PHASE 6: Quality Validation (LLM Agent) + Adaptive Retry
            # =================================================================
            quality_report = None

            if max_retries > 0 and generation_status == "completed":
                if progress_callback:
                    progress_callback(f"Step 10/{total_steps}: Validating slide quality with AI...", 85)

                # Use NotebookLM chat to gather slide info (no LLM tokens)
                slide_review_data = await _chat_review_slides(client, notebook_id)

                expected_topic_names = [t.get("name", "") for t in topics if t.get("name")]

                try:
                    quality_report = await run_quality_validator(
                        slide_review_data=slide_review_data,
                        expected_topics=expected_topic_names,
                        expected_structure=expected_structure,
                        material_type=material_type,
                        model_choice=model_choice,
                    )

                    # Adaptive retry
                    recommendation = quality_report.get("recommendation", "pass")
                    if recommendation == "retry_with_modifications" and max_retries > 0:
                        if progress_callback:
                            progress_callback(
                                "Quality check suggests improvements. Retrying with enhanced instructions...",
                                88,
                            )

                        retry_suggestions = quality_report.get("retry_suggestions", "")
                        modified_instructions = (
                            instructions +
                            f"\n\nADDITIONAL REQUIREMENTS: {retry_suggestions}"
                        )

                        gen_result2, task_id2 = await _generate_with_retry(
                            client, notebook_id, all_source_ids, modified_instructions
                        )
                        generation_status = await _wait_for_slides(
                            client, notebook_id, task_id2
                        )
                        task_id = task_id2
                        logger.info("Adaptive retry completed")

                except Exception as e:
                    logger.warning(f"Quality validation failed: {e}")
                    # Continue without quality report

            if progress_callback:
                progress_callback("Slides generated successfully!", 95)

            return {
                "success": True,
                "message": "Slide deck generated successfully!",
                "notebook_id": notebook_id,
                "notebook_title": notebook_title,
                "task_id": task_id,
                "source_id": source_id,
                "source_title": source.title,
                "generation_status": generation_status,
                "research_enabled": enable_research,
                "research_queries": research_queries,
                "research_sources_count": research_sources_count,
                "platform_sources_count": platform_sources_count,
                "total_sources": len(all_source_ids),
                "topic_analysis": topic_result if enable_research else None,
                "source_evaluations": source_evaluation_results,
                "quality_report": quality_report,
                "instructions_used": instructions[:200] + "..." if len(instructions) > 200 else instructions,
            }

    except FileNotFoundError:
        return {
            "success": False,
            "message": ("**NotebookLM authentication not found.**\n\n"
                        "You need to log in first. Run this in your terminal:\n"
                        "```\n"
                        "cd notebooklm-mcp\n"
                        "uv run notebooklm login\n"
                        "```\n"
                        "This will open a browser to authenticate with your Google account."),
        }
    except Exception as e:
        error_msg = str(e)
        if "auth" in error_msg.lower() or "login" in error_msg.lower() or "credential" in error_msg.lower():
            return {
                "success": False,
                "message": ("**NotebookLM authentication error.**\n\n"
                            f"Error: {error_msg}\n\n"
                            "Please re-authenticate:\n"
                            "```\n"
                            "cd notebooklm-mcp\n"
                            "uv run notebooklm login\n"
                            "```"),
            }
        return {
            "success": False,
            "message": f"**Error generating slides:** {error_msg}",
        }
