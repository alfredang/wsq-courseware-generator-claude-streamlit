"""
Skills Loader for WSQ Courseware Assistant

This module loads skill definitions from markdown files in the .agent/workflows/.skills folder.
Each skill file should have the following sections:
- # Title
- ## Command
- ## Description
- ## Response
- ## Capabilities
"""

import os
import re
from typing import Dict, Any, Optional


def _get_skills_directory() -> str:
    """Get the path to the .skills directory."""
    # Get project root (parent of the skills module directory)
    current_dir = os.path.dirname(os.path.abspath(__file__))
    project_root = os.path.dirname(current_dir)
    return os.path.join(project_root, ".skills")


def parse_skill_file(file_path: str) -> Optional[Dict[str, Any]]:
    """Parse a skill markdown file and extract its components."""
    try:
        with open(file_path, 'r', encoding='utf-8') as f:
            content = f.read()

        skill = {
            'file': os.path.basename(file_path),
            'name': os.path.splitext(os.path.basename(file_path))[0],
            'title': '',
            'commands': [],
            'navigate': '',
            'description': '',
            'response': '',
            'instructions': '',
            'capabilities': []
        }

        # Extract title (first # heading)
        title_match = re.search(r'^#\s+(.+)$', content, re.MULTILINE)
        if title_match:
            skill['title'] = title_match.group(1).strip()

        # Extract command section
        command_match = re.search(r'##\s+Command\s*\n(.*?)(?=\n##|\Z)', content, re.DOTALL | re.IGNORECASE)
        if command_match:
            commands_text = command_match.group(1).strip()
            # Extract commands from backticks
            skill['commands'] = re.findall(r'`([^`]+)`', commands_text)

        # Extract navigate section (page to navigate to)
        nav_match = re.search(r'##\s+Navigate\s*\n(.*?)(?=\n##|\Z)', content, re.DOTALL | re.IGNORECASE)
        if nav_match:
            skill['navigate'] = nav_match.group(1).strip()

        # Extract description
        desc_match = re.search(r'##\s+Description\s*\n(.*?)(?=\n##|\Z)', content, re.DOTALL | re.IGNORECASE)
        if desc_match:
            skill['description'] = desc_match.group(1).strip()

        # Extract response
        response_match = re.search(r'##\s+Response\s*\n(.*?)(?=\n##|\Z)', content, re.DOTALL | re.IGNORECASE)
        if response_match:
            skill['response'] = response_match.group(1).strip()

        # Extract instructions (detailed guidance for AI)
        inst_match = re.search(r'##\s+Instructions\s*\n(.*?)(?=\n##|\Z)', content, re.DOTALL | re.IGNORECASE)
        if inst_match:
            skill['instructions'] = inst_match.group(1).strip()

        # Extract capabilities
        cap_match = re.search(r'##\s+Capabilities\s*\n(.*?)(?=\n##|\Z)', content, re.DOTALL | re.IGNORECASE)
        if cap_match:
            cap_text = cap_match.group(1).strip()
            skill['capabilities'] = [line.lstrip('- ').strip() for line in cap_text.split('\n') if line.strip().startswith('-')]

        return skill
    except Exception as e:
        print(f"Error parsing skill file {file_path}: {e}")
        return None


def load_all_skills() -> Dict[str, Dict[str, Any]]:
    """Load all skills from the .agent/workflows/.skills folder."""
    skills = {}
    skills_dir = _get_skills_directory()

    if not os.path.exists(skills_dir):
        return skills

    for filename in os.listdir(skills_dir):
        if filename.endswith('.md'):
            file_path = os.path.join(skills_dir, filename)
            skill = parse_skill_file(file_path)
            if skill:
                # Map each command to this skill
                for cmd in skill['commands']:
                    # Normalize command (lowercase, with and without /)
                    cmd_lower = cmd.lower().strip()
                    if cmd_lower.startswith('/'):
                        skills[cmd_lower] = skill
                        skills[cmd_lower[1:]] = skill  # Also without /
                    else:
                        skills[cmd_lower] = skill
                        skills['/' + cmd_lower] = skill  # Also with /

    return skills


def get_skill_response(command: str) -> Optional[str]:
    """Get the response for a skill command."""
    skills = load_all_skills()
    cmd_lower = command.lower().strip()

    if cmd_lower in skills:
        return skills[cmd_lower].get('response', '')

    return None


def get_skill_action(command: str) -> Optional[Dict[str, Any]]:
    """Get the full action for a skill command including navigation."""
    skills = load_all_skills()
    cmd_lower = command.lower().strip()

    if cmd_lower in skills:
        skill = skills[cmd_lower]
        return {
            'response': skill.get('response', ''),
            'navigate': skill.get('navigate', ''),
            'name': skill.get('name', ''),
            'title': skill.get('title', '')
        }

    return None


def get_skills_system_message() -> str:
    """Generate a system message section describing all available skills."""
    skills = load_all_skills()

    # Get unique skills (by name)
    unique_skills = {}
    for skill in skills.values():
        if skill['name'] not in unique_skills:
            unique_skills[skill['name']] = skill

    message_parts = ["""## Your Skills

You have skills that help users with WSQ courseware tasks. When users ask about these topics, USE the relevant skill's instructions to provide accurate, detailed guidance.

**Important**: Proactively identify when a user's request relates to a skill, even if they don't use the exact command. Use the skill's instructions to answer their questions.

"""]

    for skill in unique_skills.values():
        cmd = skill['commands'][0] if skill['commands'] else skill['name']
        message_parts.append(f"### {cmd}")
        message_parts.append(f"**Description**: {skill['description']}")

        if skill['instructions']:
            message_parts.append(f"\n**Knowledge**:\n{skill['instructions']}")

        if skill['capabilities']:
            message_parts.append("\n**Capabilities**:")
            for cap in skill['capabilities']:
                message_parts.append(f"- {cap}")
        message_parts.append("")

    return "\n".join(message_parts)


def list_skill_commands() -> list:
    """List all available skill commands."""
    skills = load_all_skills()
    commands = set()
    for skill in skills.values():
        for cmd in skill['commands']:
            if cmd.startswith('/'):
                commands.add(cmd)
    return sorted(list(commands))
