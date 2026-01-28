"""
Prompt Loading Utility

This module provides centralized prompt management for the courseware generation system.
Prompts are loaded from the SQLite database first (if available), with fallback to markdown files.

Usage:
    from utils.prompt_loader import load_prompt

    # Load a basic prompt
    prompt = load_prompt("assessment/saq_generation")

    # Load with variable substitution
    prompt = load_prompt("courseware/cp_interpretation", schema=course_schema)
    prompt = load_prompt("courseware/timetable_generation", num_of_days=3, list_of_im=methods)
"""

import os
import json
import time
from typing import Dict, Any, Optional

# Global cache for prompts with timestamps
_prompt_cache = {}
_cache_enabled = True

# Flag to control whether to load from database
_use_database = True


def _load_from_database(category: str, name: str) -> Optional[str]:
    """Try to load prompt content from database"""
    if not _use_database:
        return None

    try:
        from settings.api_database import get_prompt_template
        template = get_prompt_template(category, name)
        if template and template.get("is_active", True):
            return template.get("content")
    except Exception as e:
        # Database might not be available, fall back to files
        pass

    return None


def load_prompt(prompt_path: str, **kwargs) -> str:
    """
    Load a prompt from database (preferred) or prompt_templates folder with optional variable substitution.
    Supports caching and hot-reloading for development.

    Args:
        prompt_path (str): Path to the prompt file relative to prompt_templates/ folder.
                          Example: "assessment/saq_generation" or "courseware/cp_interpretation"
        **kwargs: Variables to substitute in the prompt using string formatting.

    Returns:
        str: The loaded prompt with variables substituted.

    Raises:
        FileNotFoundError: If the prompt file doesn't exist in database or files.
        KeyError: If required variables are missing for substitution.

    Examples:
        >>> load_prompt("assessment/saq_generation")
        "You are an expert question-answer crafter..."

        >>> load_prompt("courseware/timetable_generation", num_of_days=2, list_of_im=["Lecture"])
        "You are a timetable generator for WSQ courses..."
    """
    # Parse category and name from path
    parts = prompt_path.split("/")
    if len(parts) == 2:
        category, name = parts
    else:
        category = "shared"
        name = prompt_path

    # Check cache first
    cache_key = f"{prompt_path}_{hash(str(sorted(kwargs.items())))}"

    if _cache_enabled and cache_key in _prompt_cache:
        cached = _prompt_cache[cache_key]
        # For database-loaded prompts, check if still valid (1 minute cache)
        if cached.get('source') == 'database':
            if time.time() - cached.get('loaded_at', 0) < 60:
                return cached['content']
        # For file-loaded prompts, check file modification time
        elif cached.get('mtime'):
            file_path = cached.get('file_path')
            if file_path and os.path.exists(file_path):
                if cached['mtime'] >= os.path.getmtime(file_path):
                    return cached['content']

    # Try to load from database first
    prompt_content = _load_from_database(category, name)
    source = 'database' if prompt_content else 'file'

    # Fall back to file if not in database
    if not prompt_content:
        # Get the directory containing this script
        current_dir = os.path.dirname(os.path.abspath(__file__))
        project_root = os.path.dirname(current_dir)

        # Construct full path to prompt file
        prompt_file_path = os.path.join(project_root, "prompt_templates", f"{prompt_path}.md")

        # Check if file exists
        if not os.path.exists(prompt_file_path):
            raise FileNotFoundError(f"Prompt not found in database or file: {prompt_path}")

        # Load the prompt content from file
        try:
            with open(prompt_file_path, 'r', encoding='utf-8') as f:
                prompt_content = f.read()
        except Exception as e:
            raise IOError(f"Error reading prompt file {prompt_file_path}: {e}")
    
    # Substitute variables if provided
    if kwargs:
        try:
            # Handle special JSON formatting for schema variables
            formatted_kwargs = {}
            for key, value in kwargs.items():
                if key == 'schema' and hasattr(value, 'model_json_schema'):
                    # For Pydantic models, convert to JSON schema
                    formatted_kwargs[key] = json.dumps(value.model_json_schema(), indent=2)
                elif isinstance(value, (dict, list)):
                    # Convert complex objects to JSON strings
                    formatted_kwargs[key] = json.dumps(value, indent=2)
                else:
                    formatted_kwargs[key] = str(value)

            prompt_content = prompt_content.format(**formatted_kwargs)
        except KeyError as e:
            raise KeyError(f"Missing required variable for prompt substitution: {e}")
        except Exception as e:
            raise ValueError(f"Error substituting variables in prompt: {e}")

    # Cache the result
    if _cache_enabled:
        cache_entry = {
            'content': prompt_content,
            'loaded_at': time.time(),
            'source': source
        }
        if source == 'file':
            # Get the directory containing this script
            current_dir = os.path.dirname(os.path.abspath(__file__))
            project_root = os.path.dirname(current_dir)
            prompt_file_path = os.path.join(project_root, "prompt_templates", f"{prompt_path}.md")
            if os.path.exists(prompt_file_path):
                cache_entry['mtime'] = os.path.getmtime(prompt_file_path)
                cache_entry['file_path'] = prompt_file_path
        _prompt_cache[cache_key] = cache_entry

    return prompt_content


def list_available_prompt_templates() -> Dict[str, list]:
    """
    List all available prompt templates organized by category.
    
    Returns:
        Dict[str, list]: Dictionary with categories as keys and list of prompt names as values.
        
    Example:
        >>> list_available_prompt_templates()
        {
            'assessment': ['saq_generation', 'practical_performance', 'case_study'],
            'courseware': ['cp_interpretation', 'timetable_generation'],
            'course_proposal': ['tsc_agent', 'research_team'],
            'shared': ['common_instructions']
        }
    """
    # Get the directory containing this script
    current_dir = os.path.dirname(os.path.abspath(__file__))
    project_root = os.path.dirname(current_dir)
    prompt_templates_dir = os.path.join(project_root, "prompt_templates")
    
    if not os.path.exists(prompt_templates_dir):
        return {}
    
    available_prompt_templates = {}
    
    # Walk through all subdirectories in prompt_templates/
    for root, dirs, files in os.walk(prompt_templates_dir):
        # Get relative path from prompt_templates directory
        rel_path = os.path.relpath(root, prompt_templates_dir)
        
        # Skip root directory
        if rel_path == '.':
            continue
            
        # Filter only .md files and remove extension
        txt_files = [os.path.splitext(f)[0] for f in files if f.endswith('.md')]
        
        if txt_files:
            available_prompt_templates[rel_path] = txt_files
    
    return available_prompt_templates


def validate_prompt_variables(prompt_path: str, **kwargs) -> bool:
    """
    Validate that a prompt can be loaded with the provided variables.
    
    Args:
        prompt_path (str): Path to the prompt file.
        **kwargs: Variables to test for substitution.
    
    Returns:
        bool: True if the prompt can be loaded successfully, False otherwise.
    """
    try:
        load_prompt(prompt_path, **kwargs)
        return True
    except (FileNotFoundError, KeyError, ValueError):
        return False


# Convenience functions for common prompt categories
def load_assessment_prompt(prompt_name: str, **kwargs) -> str:
    """Load an assessment-related prompt."""
    return load_prompt(f"assessment/{prompt_name}", **kwargs)


def load_courseware_prompt(prompt_name: str, **kwargs) -> str:
    """Load a courseware-related prompt."""
    return load_prompt(f"courseware/{prompt_name}", **kwargs)


def load_course_proposal_prompt(prompt_name: str, **kwargs) -> str:
    """Load a course proposal-related prompt."""
    return load_prompt(f"course_proposal/{prompt_name}", **kwargs)


def load_shared_prompt(prompt_name: str, **kwargs) -> str:
    """Load a shared prompt."""
    return load_prompt(f"shared/{prompt_name}", **kwargs)


# Prompt Management Functions for Streamlit Interface
def clear_prompt_cache():
    """Clear all cached prompts to force reload from disk."""
    global _prompt_cache
    _prompt_cache.clear()
    return len(_prompt_cache) == 0


def get_cache_info() -> Dict[str, Any]:
    """Get information about the current prompt cache."""
    return {
        'cache_enabled': _cache_enabled,
        'cached_prompts': len(_prompt_cache),
        'cache_keys': list(_prompt_cache.keys()),
        'total_memory_kb': sum(len(item['content']) for item in _prompt_cache.values()) / 1024
    }


def set_cache_enabled(enabled: bool):
    """Enable or disable prompt caching."""
    global _cache_enabled
    _cache_enabled = enabled
    if not enabled:
        clear_prompt_cache()


def get_prompt_preview(prompt_path: str, max_chars: int = 200) -> str:
    """Get a preview of a prompt file without full loading."""
    current_dir = os.path.dirname(os.path.abspath(__file__))
    project_root = os.path.dirname(current_dir)
    prompt_file_path = os.path.join(project_root, "prompt_templates", f"{prompt_path}.md")
    
    if not os.path.exists(prompt_file_path):
        return f"❌ File not found: {prompt_path}.md"
    
    try:
        with open(prompt_file_path, 'r', encoding='utf-8') as f:
            content = f.read(max_chars + 50)
            if len(content) > max_chars:
                content = content[:max_chars] + "..."
            return content
    except Exception as e:
        return f"❌ Error reading file: {e}"


def get_prompt_stats() -> Dict[str, Any]:
    """Get statistics about all prompt files."""
    current_dir = os.path.dirname(os.path.abspath(__file__))
    project_root = os.path.dirname(current_dir)
    prompt_templates_dir = os.path.join(project_root, "prompt_templates")
    
    if not os.path.exists(prompt_templates_dir):
        return {'error': 'Prompts directory not found'}
    
    stats = {
        'total_files': 0,
        'total_size_kb': 0,
        'categories': {},
        'last_modified': None
    }
    
    latest_mtime = 0
    
    for root, dirs, files in os.walk(prompt_templates_dir):
        category = os.path.relpath(root, prompt_templates_dir)
        if category == '.':
            continue
            
        txt_files = [f for f in files if f.endswith('.md')]
        if not txt_files:
            continue
            
        category_stats = {
            'files': len(txt_files),
            'size_kb': 0,
            'filenames': [os.path.splitext(f)[0] for f in txt_files]
        }
        
        for filename in txt_files:
            filepath = os.path.join(root, filename)
            file_size = os.path.getsize(filepath)
            file_mtime = os.path.getmtime(filepath)
            
            category_stats['size_kb'] += file_size / 1024
            stats['total_size_kb'] += file_size / 1024
            stats['total_files'] += 1
            
            if file_mtime > latest_mtime:
                latest_mtime = file_mtime
        
        stats['categories'][category] = category_stats
    
    if latest_mtime > 0:
        stats['last_modified'] = time.ctime(latest_mtime)
    
    return stats