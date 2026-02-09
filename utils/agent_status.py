"""
Agent Status UI Components

Provides sidebar and page-level status display for background agent jobs.
Uses st.fragment for non-blocking auto-refresh (no time.sleep blocking).
"""

import streamlit as st
from datetime import datetime, timedelta
from utils.agent_runner import get_all_running_jobs, get_job


def render_sidebar_agent_status():
    """
    Render running agent status in the sidebar.
    Shows a status indicator for each running job with elapsed time.
    """
    running_jobs = get_all_running_jobs()

    if not running_jobs:
        return

    st.markdown("---")
    st.markdown(
        "<div style='font-size: 0.85rem; font-weight: 600; margin-bottom: 0.3rem;'>"
        "Running Agents</div>",
        unsafe_allow_html=True,
    )

    for job in running_jobs:
        elapsed = (datetime.now() - job["started_at"]).seconds
        st.markdown(
            f"<div style='font-size: 0.8rem; color: #ff9800; padding: 2px 0;'>"
            f"&#9881; {job['label']} ({elapsed}s)"
            f"</div>",
            unsafe_allow_html=True,
        )


def render_page_job_status(key: str, on_complete=None, running_message="Agent is processing..."):
    """
    Render job status on a page and handle completion.

    Uses st.fragment for non-blocking auto-refresh when a job is running.
    The fragment auto-refreshes every 3 seconds without blocking the rest
    of the page or causing UI ghosting.

    Args:
        key: The job key to check
        on_complete: Callback receiving job dict, called once when completed
        running_message: Message shown while running

    Returns:
        "none" | "running" | "completed" | "failed"
    """
    job = get_job(key)

    if job is None:
        return "none"

    status = job["status"]

    if status == "running":
        @st.fragment(run_every=timedelta(seconds=3))
        def _status_fragment():
            _job = get_job(key)
            if not _job or _job["status"] != "running":
                # Job finished — trigger full page rerun to show results
                st.rerun(scope="app")
                return
            elapsed = (datetime.now() - _job["started_at"]).seconds
            st.info(f"{running_message} (elapsed: {elapsed}s)")
            st.caption("You can navigate to other pages. Results will be ready when you return.")

        _status_fragment()
        return "running"

    elif status == "completed":
        elapsed = (job["completed_at"] - job["started_at"]).seconds
        st.success(f"{job['label']} completed in {elapsed} seconds!")

        if job.get("post_error"):
            st.warning(f"Post-processing warning: {job['post_error']}")

        if on_complete:
            on_complete(job)

        return "completed"

    elif status == "failed":
        st.error(f"{job['label']} failed: {job.get('error', 'Unknown error')}")

        if job.get("traceback"):
            with st.expander("Error Details"):
                st.code(job["traceback"])

        return "failed"

    return "none"
