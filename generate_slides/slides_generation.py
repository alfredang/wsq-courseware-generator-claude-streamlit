"""
Slides Generation Module

Generates presentation slides from extracted course info using NotebookLM.
No file upload needed — uses course context from Extract Course Info page.

Flow:
1. User extracts course info on the Extract Course Info page
2. App formats the structured context as source text
3. App calls NotebookLM directly:
   - create notebook
   - add course content as source text
   - research internet for key topics (optional)
   - import research sources into notebook
   - generate slide deck with all sources
4. User gets slides in NotebookLM Studio

Dependencies:
    - streamlit
    - notebooklm-py[browser] (pip install notebooklm-py[browser])
"""

import streamlit as st
import asyncio
import logging
import re
import urllib.parse
from typing import Optional, Dict, Any, List

logger = logging.getLogger(__name__)


# =============================================================================
# Format course info as text for NotebookLM
# =============================================================================

def _format_course_info_as_text(context: dict) -> str:
    """
    Convert extracted course info dict to structured text for NotebookLM.

    Args:
        context: Course context dict from Extract Course Info page.

    Returns:
        Formatted text document suitable as a NotebookLM source.
    """
    lines = []

    course_title = context.get('Course_Title', 'Course')
    lines.append(f"# {course_title}")
    lines.append("")

    # Course metadata
    if context.get('TGS_Ref_No'):
        lines.append(f"**Course Reference:** {context['TGS_Ref_No']}")
    if context.get('TSC_Title'):
        lines.append(f"**TSC Title:** {context['TSC_Title']}")
    if context.get('Total_Course_Duration_Hours'):
        lines.append(f"**Course Duration:** {context['Total_Course_Duration_Hours']}")
    if context.get('Total_Training_Hours'):
        lines.append(f"**Training Hours:** {context['Total_Training_Hours']}")
    lines.append("")

    # Course description
    description = context.get('TSC_Description') or context.get('Proficiency_Description')
    if description:
        lines.append("## Course Description")
        lines.append(description)
        lines.append("")

    # Learning Units with Topics
    for lu in context.get('Learning_Units', []):
        lu_title = lu.get('LU_Title', 'Learning Unit')
        lines.append(f"## {lu_title}")

        if lu.get('LO'):
            lines.append(f"**Learning Outcome:** {lu['LO']}")
        lines.append("")

        for topic in lu.get('Topics', []):
            lines.append(f"### {topic.get('Topic_Title', 'Topic')}")
            for bp in topic.get('Bullet_Points', []):
                lines.append(f"- {bp}")
            lines.append("")

        # Knowledge statements
        k_statements = lu.get('K_numbering_description', [])
        if k_statements:
            lines.append("**Knowledge Statements:**")
            for k in k_statements:
                lines.append(f"- **{k.get('K_number', '')}:** {k.get('Description', '')}")
            lines.append("")

        # Ability statements
        a_statements = lu.get('A_numbering_description', [])
        if a_statements:
            lines.append("**Ability Statements:**")
            for a in a_statements:
                lines.append(f"- **{a.get('A_number', '')}:** {a.get('Description', '')}")
            lines.append("")

        # Instructional methods
        methods = lu.get('Instructional_Methods', [])
        if methods:
            lines.append(f"**Instructional Methods:** {', '.join(methods)}")
            lines.append("")

    # Assessment methods
    assessment_details = context.get('Assessment_Methods_Details', [])
    if assessment_details:
        lines.append("## Assessment Methods")
        for am in assessment_details:
            method = am.get('Assessment_Method', '')
            duration = am.get('Total_Delivery_Hours', '')
            lines.append(f"- **{method}** ({duration})")
        lines.append("")

    return "\n".join(lines)


# =============================================================================
# NotebookLM helpers
# =============================================================================

def _check_notebooklm_available() -> bool:
    """Check if notebooklm-py library is installed."""
    try:
        from notebooklm import NotebookLMClient  # noqa: F401
        return True
    except ImportError:
        return False


def _extract_research_queries(content: str, course_title: str,
                               num_queries: int = 2) -> List[str]:
    """
    Extract research queries from document content by finding key topics.
    Pure text parsing — no LLM needed.
    """
    queries = []
    lines = content.split('\n')

    topic_candidates = []
    for line in lines:
        stripped = line.strip()
        if not stripped or len(stripped) < 5:
            continue

        if re.match(r'^#{2,3}\s+\w', stripped) and len(stripped) < 120:
            topic_candidates.append(re.sub(r'^#{2,3}\s+', '', stripped))
        elif re.match(r'^\d+\.?\d*\s+\w', stripped) and len(stripped) < 120:
            topic_candidates.append(re.sub(r'^\d+\.?\d*\s+', '', stripped))

    seen = set()
    unique_topics = []
    for t in topic_candidates:
        normalized = t.lower().strip()
        if normalized in seen or normalized in ('introduction', 'conclusion', 'summary',
                                                  'references', 'appendix', 'course description',
                                                  'assessment methods'):
            continue
        seen.add(normalized)
        unique_topics.append(t)

    for topic in unique_topics[:num_queries]:
        query = f"{topic} training best practices and latest industry standards"
        queries.append(query)

    if len(queries) < num_queries:
        queries.append(f"{course_title} course content latest developments and best practices")

    return queries[:num_queries]


def _build_platform_urls(topics: List[str]) -> List[Dict[str, str]]:
    """Build Wikipedia search URLs for the given topics."""
    urls = []
    for topic in topics[:3]:
        clean_topic = re.sub(r'[^\w\s\-]', '', topic).strip()
        if not clean_topic:
            continue
        wiki_query = urllib.parse.quote_plus(clean_topic)
        urls.append({
            "url": f"https://en.wikipedia.org/w/index.php?search={wiki_query}",
            "title": f"Wikipedia: {clean_topic[:60]}"
        })
    return urls


async def _add_platform_sources(client, notebook_id: str, topics: List[str],
                                 progress_callback=None) -> List[str]:
    """Add sources from Wikipedia to the notebook."""
    platform_urls = _build_platform_urls(topics)
    added_source_ids = []

    if not platform_urls:
        return added_source_ids

    if progress_callback:
        progress_callback(
            f"Adding {len(platform_urls)} Wikipedia sources...",
            30
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


async def _do_internet_research(client, notebook_id: str, queries: List[str],
                                 progress_callback=None) -> List[str]:
    """Perform web research using NotebookLM's Research API and import sources."""
    all_imported_source_ids = []
    total_queries = len(queries)

    for idx, query in enumerate(queries):
        query_num = idx + 1
        logger.info(f"Starting research query {query_num}/{total_queries}: {query}")

        if progress_callback:
            progress_callback(
                f"Step 5/8: Researching topic {query_num}/{total_queries}: {query[:60]}...",
                35 + (idx * 10)
            )

        try:
            task = await client.research.start(notebook_id, query, source="web", mode="fast")
            task_id = task.get("task_id") or task.get("report_id", "")

            poll_timeout = 120
            elapsed = 0
            poll_interval = 5
            research_result = None

            while elapsed < poll_timeout:
                await asyncio.sleep(poll_interval)
                elapsed += poll_interval

                result = await client.research.poll(notebook_id)
                status = result.get("status", "")

                if status == "completed":
                    research_result = result
                    break
                elif status == "no_research":
                    break

            if not research_result:
                continue

            found_sources = research_result.get("sources", [])
            sources_to_import = [s for s in found_sources if s.get("url")][:5]

            if progress_callback:
                progress_callback(
                    f"Step 6/8: Importing {len(sources_to_import)} research sources...",
                    45 + (idx * 10)
                )

            if sources_to_import:
                try:
                    imported = await client.research.import_sources(
                        notebook_id, task_id, sources_to_import
                    )
                    for src in imported:
                        src_id = src.get("id") or src.get("source_id", "")
                        if src_id:
                            all_imported_source_ids.append(src_id)
                except Exception as e:
                    logger.warning(f"Failed to import sources for query '{query}': {e}")

        except Exception as e:
            logger.warning(f"Research failed for query '{query}': {e}")
            continue

    if all_imported_source_ids:
        if progress_callback:
            progress_callback(
                f"Waiting for {len(all_imported_source_ids)} research sources to process...",
                55
            )
        try:
            await client.sources.wait_for_sources(
                notebook_id, all_imported_source_ids, timeout=120.0
            )
        except Exception as e:
            logger.warning(f"Some research sources may not be ready: {e}")

    return all_imported_source_ids


async def _generate_slides_direct(content: str, course_title: str, config: Dict[str, Any],
                                   progress_callback=None) -> Dict[str, Any]:
    """
    Generate slides by calling NotebookLM directly.

    Args:
        content: Formatted course text for NotebookLM source
        course_title: Course title for the notebook name
        config: Slide configuration options
        progress_callback: Optional callback to update progress
    """
    try:
        from notebooklm import NotebookLMClient
    except ImportError:
        return {
            "success": False,
            "message": ("**notebooklm-py is not installed.**\n\n"
                        "Run: `pip install notebooklm-py[browser]`\n\n"
                        "Then authenticate: `python -m notebooklm login`")
        }

    enable_research = config.get('enable_research', True)
    num_queries = config.get('num_queries', 2)
    total_steps = 8 if enable_research else 5

    try:
        if progress_callback:
            progress_callback(f"Step 1/{total_steps}: Connecting to NotebookLM...", 5)

        client = await NotebookLMClient.from_storage()

        async with client:
            if progress_callback:
                progress_callback(f"Step 2/{total_steps}: Creating notebook...", 10)

            notebook_title = f"{course_title} - Slides"
            notebook = await client.notebooks.create(notebook_title)
            notebook_id = notebook.id

            if progress_callback:
                progress_callback(f"Step 3/{total_steps}: Uploading course content...", 15)

            source_title = f"{course_title} (Course Material)"
            source_text = content[:100000]
            source = await client.sources.add_text(notebook_id, source_title, source_text)
            source_id = source.id

            if progress_callback:
                progress_callback(f"Step 3/{total_steps}: Waiting for source processing...", 20)

            wait_time = min(15, max(8, len(source_text) // 10000))
            await asyncio.sleep(wait_time)

            try:
                sources_list = await client.sources.list(notebook_id)
                source_ready = any(s.id == source_id for s in sources_list)
                if not source_ready:
                    await asyncio.sleep(10)
            except Exception:
                await asyncio.sleep(5)

            all_source_ids = [source_id]
            research_sources_count = 0
            platform_sources_count = 0

            if enable_research:
                if progress_callback:
                    progress_callback(f"Step 4/{total_steps}: Extracting research topics...", 25)

                queries = _extract_research_queries(content, course_title, num_queries)

                if queries:
                    if progress_callback:
                        progress_callback(f"Step 4/{total_steps}: Adding Wikipedia sources...", 28)

                    topic_names = []
                    for q in queries:
                        core = re.sub(
                            r'\s+(training|best practices|latest|industry|standards|developments|course content).*$',
                            '', q, flags=re.IGNORECASE
                        ).strip()
                        if core:
                            topic_names.append(core)

                    platform_source_ids = await _add_platform_sources(
                        client, notebook_id, topic_names, progress_callback
                    )
                    all_source_ids.extend(platform_source_ids)
                    platform_sources_count = len(platform_source_ids)

                    research_source_ids = await _do_internet_research(
                        client, notebook_id, queries, progress_callback
                    )
                    all_source_ids.extend(research_source_ids)
                    research_sources_count = len(research_source_ids)

                    if platform_source_ids:
                        try:
                            await client.sources.wait_for_sources(
                                notebook_id, platform_source_ids, timeout=60.0
                            )
                        except Exception:
                            pass

            slide_step = 7 if enable_research else 4
            if progress_callback:
                progress_callback(f"Step {slide_step}/{total_steps}: Generating slide deck...", 65)

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
                instructions += "Add a summary slide at the end of each section. "
            if enable_research and research_sources_count > 0:
                instructions += (
                    "Incorporate the latest research findings and industry best practices "
                    "from the web research sources provided. "
                )
            instructions += "Ensure all key learning outcomes and competencies are covered."

            gen_result = None
            task_id = None
            for attempt in range(3):
                try:
                    if progress_callback and attempt > 0:
                        progress_callback(
                            f"Step {slide_step}/{total_steps}: Retrying (attempt {attempt + 1}/3)...",
                            70
                        )
                    gen_result = await client.artifacts.generate_slide_deck(
                        notebook_id,
                        source_ids=all_source_ids,
                        instructions=instructions,
                    )
                    task_id = gen_result.task_id if hasattr(gen_result, 'task_id') else str(gen_result)
                    break
                except Exception as e:
                    logger.warning(f"Slide generation attempt {attempt + 1} failed: {e}")
                    if attempt < 2:
                        await asyncio.sleep(8)
                    else:
                        raise

            wait_step = 8 if enable_research else 5
            if progress_callback:
                progress_callback(
                    f"Step {wait_step}/{total_steps}: Waiting for slides (1-3 min)...",
                    80
                )

            generation_status = "triggered"
            if task_id:
                try:
                    await client.artifacts.wait_for_completion(
                        notebook_id, task_id, timeout=300.0
                    )
                    generation_status = "completed"
                except TimeoutError:
                    generation_status = "timeout"
                except Exception as e:
                    generation_status = f"wait_error: {e}"

            if progress_callback:
                progress_callback("Slides generated successfully!", 95)

            return {
                "success": True,
                "message": "Slide deck generated successfully!",
                "notebook_id": notebook_id,
                "notebook_title": notebook_title,
                "task_id": task_id,
                "generation_status": generation_status,
                "research_enabled": enable_research,
                "research_sources_count": research_sources_count,
                "platform_sources_count": platform_sources_count,
                "total_sources": len(all_source_ids),
            }

    except FileNotFoundError:
        return {
            "success": False,
            "message": ("**NotebookLM authentication not found.**\n\n"
                        "Run in your terminal:\n"
                        "```\ncd notebooklm-mcp\nuv run notebooklm login\n```")
        }
    except Exception as e:
        error_msg = str(e)
        if "auth" in error_msg.lower() or "login" in error_msg.lower():
            return {
                "success": False,
                "message": (f"**NotebookLM authentication error:** {error_msg}\n\n"
                            "Please re-authenticate:\n"
                            "```\ncd notebooklm-mcp\nuv run notebooklm login\n```")
            }
        return {
            "success": False,
            "message": f"**Error generating slides:** {error_msg}"
        }


# =============================================================================
# Streamlit App
# =============================================================================

def app():
    """Streamlit page for Slides Generation."""
    st.title("Generate Slides")
    st.write("Generate presentation slides from course info using NotebookLM.")

    # Check dependencies
    nlm_available = _check_notebooklm_available()
    if not nlm_available:
        st.error(
            "**notebooklm-py library not installed.**\n\n"
            "Run: `pip install notebooklm-py[browser]`\n\n"
            "Then authenticate: `python -m notebooklm login`"
        )
        return

    # Prompt Templates (editable, collapsed)
    from utils.prompt_template_editor import render_prompt_templates
    render_prompt_templates("slides", "Prompt Templates (Slides)")

    # Check for extracted course info
    extracted_info = st.session_state.get('extracted_course_info')
    if not extracted_info:
        st.warning("Please extract course info first on the **Extract Course Info** page.")
        return

    # Show course info summary
    course_title = extracted_info.get('Course_Title', 'Course')
    num_topics = sum(
        len(lu.get('Topics', []))
        for lu in extracted_info.get('Learning_Units', [])
    )
    st.caption(f"**{course_title}** | {num_topics} topics")

    # Dependency check
    from utils.agent_runner import submit_agent_job
    from utils.agent_status import render_page_job_status

    # Generate Slides
    if st.button("Generate Slides", type="primary"):
        # Format course info as text for NotebookLM
        content = _format_course_info_as_text(extracted_info)
        config = {
            'enable_research': True,
            'num_queries': 2,
            'slides_per_topic': 3,
            'include_notes': True,
            'include_summaries': True,
            'slide_style': 'Professional',
        }

        _content = content
        _course_title = course_title
        _config = config

        async def _generate_slides():
            """Run the full slide generation pipeline."""
            try:
                from courseware_agents.slides_agent import analyze_document_for_slides
                analysis = await analyze_document_for_slides(_content, _config)
                if analysis.get("enhanced_prompt"):
                    _config['enhanced_prompt'] = analysis['enhanced_prompt']
            except Exception as e:
                logger.warning(f"Slides analysis skipped: {e}")

            result = await _generate_slides_direct(
                _content, _course_title, _config
            )
            return result

        job = submit_agent_job(
            key="generate_slides",
            label="Generate Slides",
            async_fn=_generate_slides,
        )

        if job is None:
            st.warning("Slide generation is already running.")
        else:
            st.rerun()

    # Agent Status
    def _on_slides_complete(job):
        result = job.get("result")
        if result:
            st.session_state['slides_result'] = result

    job_status = render_page_job_status(
        "generate_slides",
        on_complete=_on_slides_complete,
        running_message="Generating slides via NotebookLM... (approximately 2-5 minutes)",
    )

    if job_status == "running":
        st.stop()

    # Display Results
    result = st.session_state.get('slides_result')
    if result:
        if result.get("success"):
            notebook_id = result.get('notebook_id', '')
            direct_link = f"https://notebooklm.google.com/notebook/{notebook_id}" if notebook_id else "https://notebooklm.google.com"

            st.link_button("Open Slides in NotebookLM", direct_link, type="primary")
            st.caption("Your slide deck is in the Studio panel on the right side of NotebookLM.")

            with st.expander("Generation Details"):
                total_src = result.get('total_sources', 1)
                research_src = result.get('research_sources_count', 0)
                st.markdown(
                    f"- **Notebook:** {result.get('notebook_title', 'N/A')}\n"
                    f"- **Sources:** {total_src} total ({research_src} from web research)\n"
                    f"- **Status:** {result.get('generation_status', 'N/A')}"
                )
        else:
            st.error("Slide generation failed.")
            st.markdown(result.get("message", "Unknown error occurred."))
