"""
File: slides_generation.py

===============================================================================
Slides Generation Module
===============================================================================
Description:
    This module generates presentation slides from course materials using
    NotebookLM directly via the notebooklm-py library.

    NO LLM API tokens required — NotebookLM handles all AI processing.

    Flow:
    1. User uploads a document (FG, LG, CP)
    2. App extracts text from the document
    3. App calls NotebookLM directly:
       - create notebook
       - add source text
       - research internet for key topics (optional, enabled by default)
       - import research sources into notebook
       - generate slide deck with all sources
    4. User gets slides in NotebookLM Studio

    The NotebookLM MCP server (notebooklm-mcp/) is also available in the
    project for use by AI agents via MCP protocol.

Dependencies:
    - streamlit
    - notebooklm-py[browser] (pip install notebooklm-py[browser])

Author:
    WSQ Courseware Assistant
Date:
    January 2025
===============================================================================
"""

import streamlit as st
import asyncio
import logging
import re
import urllib.parse
from pathlib import Path
from typing import Optional, Dict, Any, List

logger = logging.getLogger(__name__)


def extract_text_from_file(uploaded_file) -> str:
    """
    Extract text content from uploaded file.

    Args:
        uploaded_file: Streamlit uploaded file object

    Returns:
        str: Extracted text content
    """
    try:
        file_extension = Path(uploaded_file.name).suffix.lower()

        if file_extension == '.txt':
            return uploaded_file.read().decode('utf-8')

        elif file_extension == '.pdf':
            try:
                import PyPDF2
                pdf_reader = PyPDF2.PdfReader(uploaded_file)
                text = ""
                for page in pdf_reader.pages:
                    text += page.extract_text() + "\n"
                return text
            except ImportError:
                st.warning("PyPDF2 not installed. Please install it to read PDF files.")
                return ""

        elif file_extension in ['.docx', '.doc']:
            try:
                from docx import Document
                doc = Document(uploaded_file)
                text = "\n".join([para.text for para in doc.paragraphs])
                return text
            except ImportError:
                st.warning("python-docx not installed. Please install it to read Word documents.")
                return ""

        else:
            try:
                return uploaded_file.read().decode('utf-8')
            except Exception:
                st.error(f"Unsupported file type: {file_extension}")
                return ""

    except Exception as e:
        st.error(f"Error reading file: {e}")
        return ""


def _check_notebooklm_available() -> bool:
    """Check if notebooklm-py library is installed."""
    try:
        from notebooklm import NotebookLMClient  # noqa: F401
        return True
    except ImportError:
        return False


def _find_notebooklm_mcp_path() -> Optional[str]:
    """Find the notebooklm-mcp server directory (for reference/MCP use)."""
    project_root = Path(__file__).resolve().parent.parent
    possible_paths = [
        project_root / "notebooklm-mcp",
        project_root.parent / "notebooklm-mcp",
        Path.home() / "notebooklm-mcp",
    ]
    for p in possible_paths:
        if (p / "server.py").exists():
            return str(p)
    return None


def _extract_research_queries(content: str, filename: str, material_type: str,
                               num_queries: int = 2) -> List[str]:
    """
    Extract research queries from document content by finding key topics.

    Parses headings, learning outcomes, and prominent terms to build
    web research queries. No LLM needed — pure text parsing.

    Args:
        content: Extracted text from the document
        filename: Original filename
        material_type: Type of material (FG, LG, CP, etc.)
        num_queries: Number of queries to generate (1-3)

    Returns:
        List of research query strings
    """
    queries = []
    lines = content.split('\n')

    # Extract potential topic lines (headings, numbered items, short descriptive lines)
    topic_candidates = []
    for line in lines:
        stripped = line.strip()
        if not stripped or len(stripped) < 5:
            continue

        # Numbered headings like "1. Topic Name" or "1.1 Topic Name"
        if re.match(r'^\d+\.?\d*\s+\w', stripped) and len(stripped) < 120:
            topic_candidates.append(re.sub(r'^\d+\.?\d*\s+', '', stripped))

        # ALL CAPS lines (often section headers)
        elif stripped.isupper() and 5 < len(stripped) < 80:
            topic_candidates.append(stripped.title())

        # Lines starting with "Module", "Unit", "Topic", "Section", "Learning Outcome"
        elif re.match(r'^(module|unit|topic|section|learning outcome|lo\s*\d)', stripped, re.IGNORECASE):
            topic_candidates.append(stripped)

        # Lines with bold markers (markdown or common formatting)
        elif stripped.startswith('**') or stripped.startswith('##'):
            cleaned = stripped.strip('#* ')
            if 5 < len(cleaned) < 100:
                topic_candidates.append(cleaned)

    # Deduplicate and pick the most relevant topics
    seen = set()
    unique_topics = []
    for t in topic_candidates:
        normalized = t.lower().strip()
        # Skip generic headings
        if normalized in seen or normalized in ('introduction', 'conclusion', 'summary',
                                                  'references', 'appendix', 'table of contents',
                                                  'acknowledgements'):
            continue
        seen.add(normalized)
        unique_topics.append(t)

    # Build research queries from the top topics
    # Extract a course name from the filename for context
    course_name = re.sub(r'\.(pdf|docx?|txt)$', '', filename, flags=re.IGNORECASE)
    course_name = re.sub(r'[_\-]+', ' ', course_name).strip()

    for i, topic in enumerate(unique_topics[:num_queries]):
        query = f"{topic} training best practices and latest industry standards"
        queries.append(query)

    # If we don't have enough queries from topics, add a general one
    if len(queries) < num_queries:
        queries.append(f"{course_name} course content latest developments and best practices")

    # Ensure we don't exceed requested count
    return queries[:num_queries]


def _build_platform_urls(topics: List[str]) -> List[Dict[str, str]]:
    """
    Build URLs from Wikipedia and other educational platforms for the given topics.

    Each topic is used to construct search/article URLs from:
    - Wikipedia (English)
    - Wikipedia (Simple English — accessible summaries)

    Args:
        topics: List of topic strings extracted from the document

    Returns:
        List of dicts with 'url' and 'title' keys
    """
    urls = []

    for topic in topics[:3]:  # Limit to 3 topics to avoid too many sources
        # Clean topic for URL encoding
        clean_topic = re.sub(r'[^\w\s\-]', '', topic).strip()
        if not clean_topic:
            continue

        # Wikipedia — use search URL (always valid, finds best match)
        wiki_query = urllib.parse.quote_plus(clean_topic)
        urls.append({
            "url": f"https://en.wikipedia.org/w/index.php?search={wiki_query}",
            "title": f"Wikipedia: {clean_topic[:60]}"
        })

    return urls


async def _add_platform_sources(client, notebook_id: str, topics: List[str],
                                 progress_callback=None) -> List[str]:
    """
    Add sources from Wikipedia and educational platforms to the notebook.

    Uses client.sources.add_url() to add web pages directly as sources.
    Failed URLs are silently skipped (page may not exist).

    Args:
        client: NotebookLMClient instance (already connected)
        notebook_id: The notebook to add sources to
        topics: List of topic strings
        progress_callback: Optional callback for progress updates

    Returns:
        List of successfully added source IDs
    """
    platform_urls = _build_platform_urls(topics)
    added_source_ids = []

    if not platform_urls:
        return added_source_ids

    if progress_callback:
        progress_callback(
            f"Adding {len(platform_urls)} Wikipedia/educational sources...",
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
            # URL may not exist or may be blocked — skip silently
            logger.info(f"Skipped platform source {url_info['url']}: {e}")

    return added_source_ids


async def _do_internet_research(client, notebook_id: str, queries: List[str],
                                 progress_callback=None) -> List[str]:
    """
    Perform web research using NotebookLM's Research API and import sources.

    For each query:
    1. Start a deep web research session
    2. Poll until research completes
    3. Import the found sources into the notebook

    Args:
        client: NotebookLMClient instance (already connected)
        notebook_id: The notebook to research for
        queries: List of research query strings
        progress_callback: Optional callback for progress updates

    Returns:
        List of imported source IDs
    """
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
            # Start web research (fast mode returns sources with URLs for import)
            task = await client.research.start(notebook_id, query, source="web", mode="fast")
            task_id = task.get("task_id") or task.get("report_id", "")
            logger.info(f"Research started: task_id={task_id}")

            # Poll until research is complete (timeout after 120s per query)
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
                continue

            # Get found sources
            found_sources = research_result.get("sources", [])
            summary = research_result.get("summary", "")
            logger.info(f"Research found {len(found_sources)} sources. Summary: {summary[:100]}...")

            if not found_sources:
                logger.info(f"No sources found for query: {query}")
                continue

            # Import top sources (max 5 per query to avoid overloading)
            sources_to_import = [s for s in found_sources if s.get("url")][:5]

            if progress_callback:
                progress_callback(
                    f"Step 6/8: Importing {len(sources_to_import)} research sources (topic {query_num}/{total_queries})...",
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
                    logger.info(f"Imported {len(imported)} sources for query: {query}")
                except Exception as e:
                    logger.warning(f"Failed to import sources for query '{query}': {e}")

        except Exception as e:
            logger.warning(f"Research failed for query '{query}': {e}")
            continue

    # Wait for all imported sources to be processed
    if all_imported_source_ids:
        if progress_callback:
            progress_callback(
                f"Step 6/8: Waiting for {len(all_imported_source_ids)} research sources to be processed...",
                55
            )
        try:
            await client.sources.wait_for_sources(
                notebook_id, all_imported_source_ids, timeout=120.0
            )
            logger.info(f"All {len(all_imported_source_ids)} research sources ready")
        except Exception as e:
            logger.warning(f"Some research sources may not be ready: {e}")

    return all_imported_source_ids


async def _generate_slides_direct(content: str, filename: str, config: Dict[str, Any],
                                   progress_callback=None) -> Dict[str, Any]:
    """
    Generate slides by calling NotebookLM directly — NO LLM tokens needed.

    This uses the notebooklm-py library to:
    1. Create a notebook
    2. Add the course content as a source
    3. (Optional) Research topics from the internet and import sources
    4. Trigger slide deck generation with all sources

    Args:
        content: Extracted text from uploaded document
        filename: Name of the uploaded file
        config: Slide configuration options (includes enable_research, num_queries)
        progress_callback: Optional callback to update progress

    Returns:
        dict with keys: success (bool), message (str), notebook_id (str), task_id (str)
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
        # Step 1: Initialize NotebookLM client
        if progress_callback:
            progress_callback(f"Step 1/{total_steps}: Connecting to NotebookLM...", 5)

        client = await NotebookLMClient.from_storage()

        async with client:
            # Step 2: Create a new notebook
            if progress_callback:
                progress_callback(f"Step 2/{total_steps}: Creating notebook in NotebookLM...", 10)

            material_type = config.get('material_type', 'Course Material')
            notebook_title = f"{filename} - {material_type} Slides"
            notebook = await client.notebooks.create(notebook_title)
            notebook_id = notebook.id
            logger.info(f"Created notebook: {notebook_id} - {notebook_title}")

            # Step 3: Add course content as source
            if progress_callback:
                progress_callback(f"Step 3/{total_steps}: Uploading course content to notebook...", 15)

            source_title = f"{filename} ({material_type})"
            source_text = content[:100000]
            source = await client.sources.add_text(notebook_id, source_title, source_text)
            source_id = source.id
            logger.info(f"Added source: {source_id} - {source.title}")

            # Wait for source to be processed
            if progress_callback:
                progress_callback(f"Step 3/{total_steps}: Waiting for source to be processed...", 20)

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

            # Collect all source IDs for slide generation
            all_source_ids = [source_id]
            research_queries_used = []
            research_sources_count = 0
            platform_sources_count = 0

            # Step 4-6: Internet research (if enabled)
            if enable_research:
                # Step 4: Extract research queries / topics
                if progress_callback:
                    progress_callback(f"Step 4/{total_steps}: Extracting research topics from document...", 25)

                queries = _extract_research_queries(content, filename, material_type, num_queries)
                research_queries_used = queries
                logger.info(f"Generated {len(queries)} research queries: {queries}")

                if queries:
                    # Add Wikipedia sources (using search URLs for reliability)
                    if progress_callback:
                        progress_callback(f"Step 4/{total_steps}: Adding Wikipedia sources...", 28)

                    topic_names = []
                    for q in queries:
                        core = re.sub(r'\s+(training|best practices|latest|industry|standards|developments|course content).*$',
                                      '', q, flags=re.IGNORECASE).strip()
                        if core:
                            topic_names.append(core)

                    platform_source_ids = await _add_platform_sources(
                        client, notebook_id, topic_names, progress_callback
                    )
                    all_source_ids.extend(platform_source_ids)
                    platform_sources_count = len(platform_source_ids)
                    logger.info(f"Added {platform_sources_count} Wikipedia sources")

                    # Step 5-6: Run web research and import sources
                    research_source_ids = await _do_internet_research(
                        client, notebook_id, queries, progress_callback
                    )
                    all_source_ids.extend(research_source_ids)
                    research_sources_count = len(research_source_ids)
                    logger.info(
                        f"Research added {research_sources_count} web sources + "
                        f"{platform_sources_count} Wikipedia sources. "
                        f"Total sources: {len(all_source_ids)}"
                    )

                    # Wait for Wikipedia sources to finish processing
                    if platform_source_ids:
                        try:
                            await client.sources.wait_for_sources(
                                notebook_id, platform_source_ids, timeout=60.0
                            )
                        except Exception as e:
                            logger.warning(f"Some Wikipedia sources may not be ready: {e}")
                else:
                    logger.info("No research queries extracted from document")

            # Step 7: Generate slide deck
            slide_step = 7 if enable_research else 4
            if progress_callback:
                progress_callback(f"Step {slide_step}/{total_steps}: Triggering slide deck generation...", 65)

            # Build instructions
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
            if enable_research and research_sources_count > 0:
                instructions += (
                    "Incorporate the latest research findings and industry best practices "
                    "from the web research sources provided. "
                )
            instructions += "Ensure all key learning outcomes and competencies are covered."

            # Retry up to 3 times with explicit source_ids
            gen_result = None
            task_id = None
            for attempt in range(3):
                try:
                    if progress_callback and attempt > 0:
                        progress_callback(
                            f"Step {slide_step}/{total_steps}: Retrying slide generation (attempt {attempt + 1}/3)...",
                            70
                        )
                    gen_result = await client.artifacts.generate_slide_deck(
                        notebook_id,
                        source_ids=all_source_ids,
                        instructions=instructions,
                    )
                    task_id = gen_result.task_id if hasattr(gen_result, 'task_id') else str(gen_result)
                    logger.info(f"Slide generation triggered: task_id={task_id}, sources={len(all_source_ids)}")
                    break
                except Exception as e:
                    logger.warning(f"Slide generation attempt {attempt + 1} failed: {e}")
                    if attempt < 2:
                        await asyncio.sleep(8)
                    else:
                        raise

            # Step 8: Wait for slides to be generated
            wait_step = 8 if enable_research else 5
            if progress_callback:
                progress_callback(
                    f"Step {wait_step}/{total_steps}: Waiting for slides to be generated (this may take 1-3 min)...",
                    80
                )

            generation_status = "triggered"
            if task_id:
                try:
                    final_status = await client.artifacts.wait_for_completion(
                        notebook_id, task_id, timeout=300.0
                    )
                    generation_status = "completed"
                    logger.info(f"Slide generation completed: {final_status}")
                except TimeoutError:
                    generation_status = "timeout"
                    logger.warning("Slide generation timed out after 300s — may still be generating")
                except Exception as e:
                    generation_status = f"wait_error: {e}"
                    logger.warning(f"Wait for completion error: {e}")

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
                "research_queries": research_queries_used,
                "research_sources_count": research_sources_count,
                "platform_sources_count": platform_sources_count,
                "total_sources": len(all_source_ids),
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
                        "This will open a browser to authenticate with your Google account.")
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
                            "```")
            }
        return {
            "success": False,
            "message": f"**Error generating slides:** {error_msg}"
        }


def app():
    """
    Streamlit web interface for Slides Generation.
    """
    st.title("Generate Slides")
    st.markdown("Generate professional presentation slides from course materials using **NotebookLM**")

    st.divider()

    # Check dependencies
    nlm_available = _check_notebooklm_available()
    mcp_path = _find_notebooklm_mcp_path()

    if not nlm_available:
        st.error("""
        **notebooklm-py library not installed.**

        Run in your terminal:
        ```
        pip install notebooklm-py[browser]
        ```

        Then authenticate with NotebookLM:
        ```
        python -m notebooklm login
        ```
        """)
        return

    # Show NotebookLM status in sidebar
    if mcp_path:
        st.sidebar.success("✅ NotebookLM Connected")
    else:
        st.sidebar.info("NotebookLM MCP server not found (optional — direct mode active)")

    # File Upload Section
    st.subheader("1. Upload Course Materials")

    col1, col2 = st.columns(2)

    with col1:
        material_type = st.selectbox(
            "Select Material Type:",
            ["Facilitator Guide (FG)", "Learner Guide (LG)", "Course Proposal (CP)", "Other Document"],
            help="Choose the type of course material you're uploading"
        )

    with col2:
        output_format = st.selectbox(
            "Output Format:",
            ["PowerPoint (PPTX)", "PDF Slides", "Google Slides"],
            help="Choose the output format for your slides"
        )

    uploaded_file = st.file_uploader(
        "Upload your course material:",
        type=['pdf', 'docx', 'doc', 'txt'],
        help="Supported formats: PDF, Word documents (.docx, .doc), Text files (.txt)"
    )

    st.divider()

    # Configuration Section
    st.subheader("2. Slide Configuration")

    # Agentic Mode toggle
    st.markdown("#### AI-Enhanced Generation")
    enable_agentic = st.checkbox(
        "Enable AI-Enhanced Generation (Agentic Mode)",
        value=True,
        help="Uses AI agents for intelligent topic analysis, source quality evaluation, "
             "optimized slide instructions, and post-generation quality validation"
    )

    if enable_agentic:
        st.caption("AI agents analyze your document, evaluate research sources, craft optimal instructions, and validate quality.")
    else:
        st.caption("No LLM API tokens required — NotebookLM handles all AI processing directly.")

    # Internet Research toggle (prominent)
    st.markdown("#### Internet Research")
    rcol1, rcol2 = st.columns([2, 1])
    with rcol1:
        enable_research = st.checkbox(
            "Research from Internet before generating slides",
            value=True,
            help="Performs deep web research on key topics from your document to enrich slides with the latest information, best practices, and industry standards"
        )
    with rcol2:
        num_queries = st.slider(
            "Number of research topics:",
            min_value=1,
            max_value=3,
            value=2,
            disabled=not enable_research,
            help="More topics = more thorough research but longer generation time"
        )

    if enable_research:
        st.info("Internet research is enabled. NotebookLM will search the web for the latest information on key topics from your document before generating slides.")

    st.markdown("#### Slide Options")
    col1, col2, col3 = st.columns(3)

    with col1:
        slides_per_topic = st.number_input(
            "Slides per Topic:",
            min_value=1,
            max_value=10,
            value=3,
            help="Number of slides to generate per topic/learning unit"
        )

    with col2:
        include_notes = st.checkbox(
            "Include Speaker Notes",
            value=True,
            help="Add facilitator notes to each slide"
        )

    with col3:
        include_summaries = st.checkbox(
            "Include Section Summaries",
            value=True,
            help="Add summary slides at the end of each section"
        )

    # Additional options
    with st.expander("Advanced Options"):
        col1, col2 = st.columns(2)

        with col1:
            slide_style = st.selectbox(
                "Slide Style:",
                ["Professional", "Modern", "Minimal", "Educational"],
                help="Choose the visual style for your slides"
            )

            color_scheme = st.selectbox(
                "Color Scheme:",
                ["Blue Professional", "Green Fresh", "Orange Warm", "Purple Creative", "Custom"],
                help="Choose the color scheme for your slides"
            )

        with col2:
            include_objectives = st.checkbox(
                "Include Learning Objectives Slide",
                value=True,
                help="Add a slide listing learning objectives"
            )

            include_assessment = st.checkbox(
                "Include Assessment Reminders",
                value=True,
                help="Add reminders about assessment points"
            )

            enable_validation = st.checkbox(
                "Enable Quality Validation",
                value=True,
                disabled=not enable_agentic,
                help="AI validates generated slides and can trigger automatic retry if quality is low"
            )

    st.divider()

    # Preview Section (when file is uploaded)
    if uploaded_file:
        st.subheader("3. Content Preview")

        content = extract_text_from_file(uploaded_file)

        if content:
            with st.expander("Preview Extracted Content", expanded=False):
                st.text_area(
                    "Extracted Text (first 2000 characters):",
                    value=content[:2000] + ("..." if len(content) > 2000 else ""),
                    height=200,
                    disabled=True
                )

            st.success(f"File loaded successfully. Extracted {len(content):,} characters of text.")

            # Store content in session state
            st.session_state['slides_content'] = content
            st.session_state['slides_filename'] = uploaded_file.name
        else:
            st.error("Could not extract content from the uploaded file.")

    st.divider()

    # Generation Section
    st.subheader("4. Generate Slides")

    generate_enabled = uploaded_file is not None and 'slides_content' in st.session_state

    if st.button("Generate Presentation Slides", type="primary", disabled=not generate_enabled):
        if not generate_enabled:
            st.error("Please upload a course material file first.")
            return

        content = st.session_state.get('slides_content', '')
        filename = st.session_state.get('slides_filename', 'course_material')

        # Build config from UI options
        config = {
            'slides_per_topic': slides_per_topic,
            'include_notes': include_notes,
            'include_summaries': include_summaries,
            'slide_style': slide_style,
            'color_scheme': color_scheme,
            'include_objectives': include_objectives,
            'include_assessment': include_assessment,
            'output_format': output_format,
            'material_type': material_type,
            'enable_research': enable_research,
            'num_queries': num_queries,
            'enable_agentic': enable_agentic,
            'enable_validation': enable_validation if enable_agentic else False,
        }

        # Progress indicators
        progress_bar = st.progress(0)
        status_text = st.empty()

        def update_progress(message, pct):
            status_text.text(message)
            progress_bar.progress(pct)

        # Run generation pipeline
        try:
            loop = asyncio.new_event_loop()
            if enable_agentic:
                from generate_slides.agents.orchestrator import run_agentic_pipeline
                model_choice = st.session_state.get('selected_model', 'DeepSeek-Chat')
                result = loop.run_until_complete(
                    run_agentic_pipeline(
                        content, filename, config, model_choice,
                        progress_callback=update_progress,
                        max_retries=1 if config.get('enable_validation', True) else 0,
                    )
                )
            else:
                # Original pipeline — no LLM tokens needed
                result = loop.run_until_complete(
                    _generate_slides_direct(content, filename, config, progress_callback=update_progress)
                )
            loop.close()
        except Exception as e:
            result = {"success": False, "message": f"Error: {str(e)}"}

        # Final progress
        progress_bar.progress(100)
        status_text.empty()
        progress_bar.empty()

        # Display the result
        if result.get("success"):
            notebook_id = result.get('notebook_id', '')
            direct_link = f"https://notebooklm.google.com/notebook/{notebook_id}" if notebook_id else "https://notebooklm.google.com"

            gen_status = result.get('generation_status', 'unknown')
            research_note = ""
            if result.get('research_enabled'):
                total_src = result.get('total_sources', 1)
                web_src = result.get('research_sources_count', 0)
                platform_src = result.get('platform_sources_count', 0)
                research_note = f" {total_src} sources used ({web_src} web + {platform_src} Wikipedia + 1 uploaded document)."
            else:
                research_note = " Internet research was disabled — only the uploaded document was used."

            if gen_status == "completed":
                st.success(f"Slides generated successfully! Your slide deck is ready in NotebookLM.{research_note}")
            elif gen_status == "timeout":
                st.warning("Slide generation is still in progress. Open NotebookLM — your slides should appear shortly in the Studio panel.")
            else:
                st.success(f"Slide generation triggered! Opening NotebookLM — check the Studio panel on the right.{research_note}")

            st.info("Note: Slides may take 1–2 minutes to fully generate inside NotebookLM. "
                    "Internet research sources will be included in the slides for richer content.")

            # Auto-open the notebook in a new tab
            st.components.v1.html(
                f'<script>window.open("{direct_link}", "_blank");</script>',
                height=0,
            )

            # Manual button
            st.markdown("### Your Slides Are Ready")
            st.link_button("Open Your Slides in NotebookLM", direct_link, type="primary")
            st.caption("A new tab should have opened automatically. If not, click the button above. Your slide deck is in the **Studio** panel on the right side.")

            with st.expander("Generation Details"):
                research_info = ""
                if result.get('research_enabled'):
                    queries = result.get('research_queries', [])
                    queries_str = ", ".join(f'"{q[:50]}"' for q in queries) if queries else "None"
                    platform_count = result.get('platform_sources_count', 0)
                    web_count = result.get('research_sources_count', 0)
                    research_info = f"""| **Internet Research** | Enabled |
| **Research Queries** | {queries_str} |
| **Web Research Sources** | {web_count} |
| **Wikipedia Sources** | {platform_count} |
| **Total Sources Used** | {result.get('total_sources', 1)} |
"""
                else:
                    research_info = "| **Internet Research** | Disabled |\n"

                st.markdown(f"""
| Detail | Value |
|--------|-------|
| **Notebook** | {result.get('notebook_title', 'N/A')} |
| **Source Added** | {result.get('source_title', 'N/A')} |
| **Source ID** | `{result.get('source_id', 'N/A')}` |
{research_info}| **Notebook ID** | `{notebook_id}` |
| **Task ID** | `{result.get('task_id', 'N/A')}` |
| **Generation Status** | `{result.get('generation_status', 'N/A')}` |
| **Direct Link** | [{direct_link}]({direct_link}) |
                """)

            # Quality Validation Report (agentic mode only)
            if result.get("quality_report"):
                with st.expander("Quality Validation Report", expanded=True):
                    report = result["quality_report"]
                    overall = report.get("overall_score", 0)

                    # Overall score
                    st.metric("Overall Quality Score", f"{overall}/10")

                    # Per-criterion scores
                    score_cols = st.columns(5)
                    criteria = [
                        ("topic_coverage", "Topic Coverage"),
                        ("structure_quality", "Structure"),
                        ("content_depth", "Content Depth"),
                        ("learning_outcome_alignment", "LO Alignment"),
                        ("research_integration", "Research Integration"),
                    ]
                    for i, (key, label) in enumerate(criteria):
                        score_cols[i].metric(label, f"{report.get(key, 'N/A')}/10")

                    # Strengths and weaknesses
                    strengths = report.get("strengths", [])
                    weaknesses = report.get("weaknesses", [])
                    if strengths:
                        st.markdown("**Strengths:**")
                        for s in strengths:
                            st.markdown(f"- {s}")
                    if weaknesses:
                        st.markdown("**Areas for Improvement:**")
                        for w in weaknesses:
                            st.markdown(f"- {w}")

                    # Recommendation
                    rec = report.get("recommendation", "pass")
                    if rec == "pass":
                        st.success("Quality validation passed.")
                    elif rec == "retry_with_modifications":
                        st.info("Quality validation triggered an automatic retry with improved instructions.")
                    elif rec == "retry_full":
                        st.warning("Quality validation recommends re-generating. Consider re-running with different settings.")

            # Topic Analysis Details (agentic mode only)
            if result.get("topic_analysis"):
                with st.expander("AI Topic Analysis"):
                    ta = result["topic_analysis"]
                    st.markdown(f"**Document Domain:** {ta.get('document_domain', 'N/A')}")
                    topics = ta.get("topics", [])
                    for t in topics:
                        st.markdown(
                            f"- **{t.get('name', 'Unknown')}** (score: {t.get('relevance_score', 'N/A')}/10) — "
                            f"*{t.get('rationale', '')}*"
                        )

            st.balloons()
        else:
            st.error("Slides generation failed.")
            st.markdown(result.get("message", "Unknown error occurred."))

    # Help section
    with st.expander("How to Use This Module"):
        st.markdown("""
        ### Steps to Generate Slides:

        1. **Upload Course Material**: Upload your Facilitator Guide, Learner Guide, or Course Proposal
        2. **Configure Options**: Choose slides per topic, include speaker notes, etc.
        3. **Generate**: Click "Generate Presentation Slides"
        4. **Download**: Open NotebookLM Studio to view and download your slides

        ### Tips for Best Results:

        - **Facilitator Guide**: Best for comprehensive slides with teaching notes
        - **Course Proposal**: Good for overview/summary presentations
        - **Learner Guide**: Best for student-focused presentations

        ### How It Works:

        This module calls **NotebookLM directly** (no LLM API tokens required):
        1. **Creates a notebook** in your Google NotebookLM account
        2. **Adds your course content** as a source to the notebook
        3. **Researches the internet** for latest information on key topics (if enabled)
        4. **Imports research sources** into the notebook for richer content
        5. **Generates a slide deck** using NotebookLM's AI with all sources

        The NotebookLM MCP server (`notebooklm-mcp/`) is also included in this project
        for use by AI agents via MCP protocol.

        ### First-Time Setup:

        ```
        pip install notebooklm-py[browser]
        cd notebooklm-mcp
        uv run notebooklm login
        ```

        The login command opens a browser to authenticate with your Google account.
        This only needs to be done once.
        """)


if __name__ == "__main__":
    app()
