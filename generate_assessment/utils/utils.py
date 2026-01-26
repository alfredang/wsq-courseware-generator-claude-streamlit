"""
File: utils.py

===============================================================================
Utilities Module for File Handling
===============================================================================
Description:
    This module provides utility functions to support file operations.

Main Functionalities:
    - save_uploaded_file(uploaded_file, save_dir):
      Saves an uploaded file to the specified directory
    - get_page_number(file_name):
      Extracts a page number from an image filename
    - _get_sorted_image_files(image_dir):
      Retrieves and returns image files sorted by page number

Dependencies:
    - Standard Libraries: re, os, pathlib (Path)

Author: Derrick Lim
Date: 3 March 2025
===============================================================================
"""

import re
import os
from pathlib import Path


def save_uploaded_file(uploaded_file, save_dir):
    """Save an uploaded file to the specified directory."""
    if not os.path.exists(save_dir):
        os.makedirs(save_dir)
    file_path = os.path.join(save_dir, uploaded_file.name)
    with open(file_path, 'wb') as f:
        f.write(uploaded_file.getbuffer())
    return file_path


def get_page_number(file_name):
    """Extract page number from filename."""
    match = re.search(r"-page-(\d+)\.jpg$", str(file_name))
    if match:
        return int(match.group(1))
    return 0


def _get_sorted_image_files(image_dir):
    """Get image files sorted by page."""
    raw_files = [f for f in list(Path(image_dir).iterdir()) if f.is_file()]
    sorted_files = sorted(raw_files, key=get_page_number)
    return sorted_files


def get_text_nodes(json_dicts, image_dir=None):
    """Convert JSON dicts to simple node dictionaries."""
    nodes = []
    image_files = _get_sorted_image_files(image_dir) if image_dir is not None else []
    md_texts = [d["text"] for d in json_dicts]

    for idx, md_text in enumerate(md_texts):
        node = {
            "page_num": idx + 1,
            "image_path": str(image_files[idx]) if idx < len(image_files) else None,
            "parsed_text_markdown": md_text,
            "text": md_text
        }
        nodes.append(node)

    return nodes
