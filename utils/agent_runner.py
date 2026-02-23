"""
Background Agent Runner

Manages background execution of Claude Agent SDK agents using daemon threads.
Jobs are stored as mutable dicts in st.session_state, allowing pages to check
status on rerun without blocking the UI.

Thread safety: Python GIL ensures single-key dict mutations are atomic.
The background thread writes to the job dict, the main thread reads on rerun.
"""

import threading
import asyncio
import sys
import traceback
from datetime import datetime
from typing import Callable, Any, Optional

import streamlit as st

# Fix for Windows: Streamlit/tornado switches to SelectorEventLoop which
# doesn't support subprocess creation. Force ProactorEventLoop policy.
if sys.platform == "win32":
    asyncio.set_event_loop_policy(asyncio.WindowsProactorEventLoopPolicy())


def _run_in_thread(job: dict, async_fn: Callable, args: tuple, kwargs: dict,
                   post_process: Optional[Callable] = None):
    """
    Target function for the background thread.

    Runs the async agent function via asyncio.run() (safe in a new thread
    since there's no existing event loop). On completion, updates the mutable
    job dict in-place. Optionally runs a sync post_process callback.
    """
    try:
        result = asyncio.run(async_fn(*args, **kwargs))
        job["result"] = result
        job["status"] = "completed"
        job["completed_at"] = datetime.now()

        if post_process is not None:
            try:
                extra = post_process(result)
                if extra and isinstance(extra, dict):
                    job["post_results"] = extra
            except Exception as e:
                job["post_error"] = str(e)

    except Exception as e:
        job["status"] = "failed"
        job["error"] = f"{type(e).__name__}: {str(e)}"
        job["traceback"] = traceback.format_exc()
        job["completed_at"] = datetime.now()


def submit_agent_job(
    key: str,
    label: str,
    async_fn: Callable,
    args: tuple = (),
    kwargs: dict = None,
    post_process: Optional[Callable] = None,
) -> Optional[dict]:
    """
    Submit a background agent job. Returns the job dict immediately.

    If a job with this key is already running, returns None (prevents duplicates).

    Args:
        key: Unique job identifier (e.g., "extract_course_info")
        label: Human-readable label for sidebar display
        async_fn: The async agent function to run
        args: Positional arguments for the agent function
        kwargs: Keyword arguments for the agent function
        post_process: Optional sync callback that receives the agent result
                      and returns a dict of additional results to store
    """
    if kwargs is None:
        kwargs = {}

    session_key = f"agent_job_{key}"

    existing = st.session_state.get(session_key)
    if existing and existing.get("status") == "running":
        thread = existing.get("thread")
        if thread and thread.is_alive():
            return None

    job = {
        "key": key,
        "status": "running",
        "label": label,
        "started_at": datetime.now(),
        "completed_at": None,
        "result": None,
        "error": None,
        "traceback": None,
        "post_results": None,
        "post_error": None,
        "thread": None,
        "progress_messages": [],  # List of (message, pct) tuples from background thread
    }
    st.session_state[session_key] = job

    thread = threading.Thread(
        target=_run_in_thread,
        args=(job, async_fn, args, kwargs, post_process),
        daemon=True,
        name=f"agent-{key}",
    )
    job["thread"] = thread
    thread.start()

    return job


def get_job(key: str) -> Optional[dict]:
    """Get the current job dict for a key, or None."""
    return st.session_state.get(f"agent_job_{key}")


def get_all_running_jobs() -> list:
    """Return all currently running agent jobs, with thread health check."""
    running = []
    for k, v in st.session_state.items():
        if k.startswith("agent_job_") and isinstance(v, dict):
            if v.get("status") == "running":
                thread = v.get("thread")
                if thread and thread.is_alive():
                    running.append(v)
                else:
                    v["status"] = "failed"
                    v["error"] = "Agent thread terminated unexpectedly"
                    v["completed_at"] = datetime.now()
    return running


def clear_job(key: str):
    """Remove a completed/failed job from session state."""
    session_key = f"agent_job_{key}"
    if session_key in st.session_state:
        del st.session_state[session_key]
