"""
Common Utility Functions

This module provides shared utility functions used across multiple modules
in the Courseware AutoGen system.

Author: Derrick Lim
Date: 3 March 2025
"""

import os
import re
import json
from typing import Any, Optional, Dict


def parse_json_content(content: str) -> Optional[Dict[str, Any]]:
    """
    Parse JSON content from various formats including markdown code blocks.
    Handles literal newlines and other control characters in JSON strings.

    Args:
        content: Raw content that may contain JSON

    Returns:
        Parsed JSON dictionary or None if parsing fails
    """
    # Try to match well-formed markdown blocks with both opening and closing ```
    json_pattern = re.compile(r'```json\s*(\{.*?\})\s*```', re.DOTALL)
    match = json_pattern.search(content)

    if match:
        # If both ```json and ``` are present, extract the JSON content
        json_str = match.group(1)
    else:
        # Fallback: Extract from first { to last } (handles missing closing ``` or no markers)
        first_brace = content.find('{')
        last_brace = content.rfind('}')

        if first_brace != -1 and last_brace != -1 and last_brace > first_brace:
            json_str = content[first_brace:last_brace + 1]
        else:
            # No braces found, use entire content as-is
            json_str = content

    # Remove any leading/trailing whitespace
    json_str = json_str.strip()

    try:
        # Try to parse the JSON string directly
        parsed_json = json.loads(json_str)
        return parsed_json
    except json.JSONDecodeError as e:
        print(f"Error parsing JSON on first attempt: {e}")

        # Try to fix literal control characters in string values
        try:
            # Character-by-character parser to escape control chars within strings
            fixed_chars = []
            in_string = False
            escape_next = False

            for i, char in enumerate(json_str):
                if escape_next:
                    fixed_chars.append(char)
                    escape_next = False
                    continue

                if char == '\\':
                    fixed_chars.append(char)
                    escape_next = True
                    continue

                if char == '"' and not escape_next:
                    # Toggle string state
                    in_string = not in_string
                    fixed_chars.append(char)
                    continue

                # If we're inside a string, escape control characters
                if in_string:
                    if char == '\n':
                        fixed_chars.append('\\n')
                    elif char == '\r':
                        fixed_chars.append('\\r')
                    elif char == '\t':
                        fixed_chars.append('\\t')
                    else:
                        fixed_chars.append(char)
                else:
                    fixed_chars.append(char)

            fixed_json = ''.join(fixed_chars)

            try:
                parsed_json = json.loads(fixed_json)
                print("✓ Successfully parsed JSON after escaping control characters")
                return parsed_json
            except:
                # Try fixing unquoted keys as well
                fixed_json = re.sub(r'(\w+):', r'"\1":', fixed_json)
                parsed_json = json.loads(fixed_json)
                print("✓ Successfully parsed JSON after fixing control chars and unquoted keys")
                return parsed_json
        except Exception as ex:
            print(f"Failed to parse JSON content even after attempting fixes.")
            print(f"Error: {ex}")
            print(f"JSON string preview: {json_str[:500]}...")
            return None


def save_uploaded_file(uploaded_file, save_dir: str) -> str:
    """
    Save uploaded Streamlit file to specified directory.
    
    Args:
        uploaded_file: Streamlit uploaded file object
        save_dir: Directory to save the file
        
    Returns:
        Full path to the saved file
    """
    if not os.path.exists(save_dir):
        os.makedirs(save_dir)
    file_path = os.path.join(save_dir, uploaded_file.name)
    with open(file_path, 'wb') as f:
        f.write(uploaded_file.getbuffer())
    return file_path


def ensure_directory(directory: str) -> None:
    """
    Ensure a directory exists, create if it doesn't.
    
    Args:
        directory: Directory path to ensure exists
    """
    if not os.path.exists(directory):
        os.makedirs(directory, exist_ok=True)


def load_json_file(file_path: str) -> Optional[Dict[str, Any]]:
    """
    Load JSON data from a file with error handling.
    
    Args:
        file_path: Path to the JSON file
        
    Returns:
        JSON data as dictionary or None if loading fails
    """
    try:
        with open(file_path, 'r', encoding='utf-8') as file:
            return json.load(file)
    except (FileNotFoundError, json.JSONDecodeError, IOError) as e:
        print(f"Error loading JSON file {file_path}: {e}")
        return None


def save_json_file(data: Dict[str, Any], file_path: str) -> bool:
    """
    Save data to JSON file with error handling.
    
    Args:
        data: Dictionary to save as JSON
        file_path: Path where to save the file
        
    Returns:
        True if successful, False otherwise
    """
    try:
        ensure_directory(os.path.dirname(file_path))
        with open(file_path, 'w', encoding='utf-8') as file:
            json.dump(data, file, indent=2, ensure_ascii=False)
        return True
    except (IOError, TypeError) as e:
        print(f"Error saving JSON file {file_path}: {e}")
        return False