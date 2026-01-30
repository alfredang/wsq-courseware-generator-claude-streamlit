"""
Skills Loader for WSQ Courseware Assistant

This module loads skill definitions from markdown files in the .skills folder.
Each skill file should have the following sections:
- # Title
- ## Command
- ## Keywords (natural language triggers)
- ## Navigate
- ## Description
- ## Response
- ## Instructions
- ## Capabilities
"""

import os
import re
from typing import Dict, Any, Optional, List


def _get_skills_directory() -> str:
    """Get the path to the .skills directory."""
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
            'keywords': [],
            'navigate': '',
            'description': '',
            'response': '',
            'instructions': '',
            'capabilities': [],
            'next_steps': ''
        }

        # Extract title (first # heading)
        title_match = re.search(r'^#\s+(.+)$', content, re.MULTILINE)
        if title_match:
            skill['title'] = title_match.group(1).strip()

        # Extract command section
        command_match = re.search(r'##\s+Command\s*\n(.*?)(?=\n##|\Z)', content, re.DOTALL | re.IGNORECASE)
        if command_match:
            commands_text = command_match.group(1).strip()
            skill['commands'] = re.findall(r'`([^`]+)`', commands_text)

        # Extract keywords section (natural language triggers)
        kw_match = re.search(r'##\s+Keywords\s*\n(.*?)(?=\n##|\Z)', content, re.DOTALL | re.IGNORECASE)
        if kw_match:
            kw_text = kw_match.group(1).strip()
            skill['keywords'] = [kw.strip().lower() for kw in kw_text.split(',') if kw.strip()]

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

        # Extract next steps (workflow chaining)
        next_match = re.search(r'##\s+Next\s*Steps?\s*\n(.*?)(?=\n##|\Z)', content, re.DOTALL | re.IGNORECASE)
        if next_match:
            skill['next_steps'] = next_match.group(1).strip()

        return skill
    except Exception as e:
        print(f"Error parsing skill file {file_path}: {e}")
        return None


def _load_all_skill_objects() -> List[Dict[str, Any]]:
    """Load all unique skill objects from .skills folder."""
    skills_dir = _get_skills_directory()
    skill_list = []

    if not os.path.exists(skills_dir):
        return skill_list

    for filename in os.listdir(skills_dir):
        if filename.endswith('.md'):
            file_path = os.path.join(skills_dir, filename)
            skill = parse_skill_file(file_path)
            if skill:
                skill_list.append(skill)

    return skill_list


def load_all_skills() -> Dict[str, Dict[str, Any]]:
    """Load all skills mapped by command strings."""
    skills = {}

    for skill in _load_all_skill_objects():
        for cmd in skill['commands']:
            cmd_lower = cmd.lower().strip()
            if cmd_lower.startswith('/'):
                skills[cmd_lower] = skill
                skills[cmd_lower[1:]] = skill
            else:
                skills[cmd_lower] = skill
                skills['/' + cmd_lower] = skill

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
            'title': skill.get('title', ''),
            'next_steps': skill.get('next_steps', '')
        }

    return None


def _fuzzy_match(keyword: str, user_input: str) -> bool:
    """Check if keyword partially matches user input (handles typos/missing chars).

    Matches if keyword is a substring OR if the user typed at least 80% of a
    keyword that is 5+ chars long (e.g. 'brochur' matches 'brochure').
    """
    if keyword in user_input:
        return True

    # Only fuzzy match on keywords 5+ chars to avoid false positives
    if len(keyword) < 5:
        return False

    # Check if any word in input is a close partial match to keyword
    input_words = user_input.split()
    for word in input_words:
        if len(word) < 4:
            continue
        # Check if word is a prefix of keyword (user typed partial word)
        if keyword.startswith(word) and len(word) >= len(keyword) * 0.75:
            return True
        # Check if keyword is a prefix of word (user typed extra chars)
        if word.startswith(keyword):
            return True

    return False


def match_skill_by_keywords(user_input: str) -> Optional[Dict[str, Any]]:
    """Match user natural language input to a skill using keywords.

    Returns the skill action dict if a match is found, None otherwise.

    Scoring:
    - Each matching keyword adds its length to the skill's total score
    - Multiple keyword hits on the same skill stack (more relevant = higher score)
    - Fuzzy matching catches typos and partial words
    - Minimum score threshold of 3 to avoid false positives on tiny matches
    """
    lower_input = user_input.lower().strip()
    all_skills = _load_all_skill_objects()

    best_match = None
    best_score = 0

    for skill in all_skills:
        if not skill.get('keywords'):
            continue

        skill_score = 0
        for keyword in skill['keywords']:
            if _fuzzy_match(keyword, lower_input):
                # Add keyword length to total score (multiple hits stack)
                skill_score += len(keyword)

        if skill_score > best_score and skill_score >= 3:
            best_score = skill_score
            best_match = skill

    if best_match:
        return {
            'response': best_match.get('response', ''),
            'navigate': best_match.get('navigate', ''),
            'name': best_match.get('name', ''),
            'title': best_match.get('title', ''),
            'next_steps': best_match.get('next_steps', '')
        }

    return None


def get_workflow_steps() -> str:
    """Return the recommended WSQ courseware development workflow."""
    return (
        "Here's the recommended workflow for developing WSQ courseware:\n\n"
        "**Step 1.** **Course Proposal (CP)** — Start here. Upload your TSC document to generate the foundation.\n\n"
        "**Step 2.** **Courseware Documents** — Use your approved CP to generate:\n"
        "- Assessment Plan (AP)\n"
        "- Facilitator Guide (FG)\n"
        "- Learner Guide (LG)\n"
        "- Lesson Plan (LP)\n\n"
        "**Step 3.** **Assessment Materials** — Upload your FG to create assessments (SAQ, Case Study, etc.)\n\n"
        "**Step 4.** **Add Assessment to AP** — Attach your generated assessments to the Assessment Plan\n\n"
        "**Step 5.** **Slides** — Generate presentation slides from your course materials\n\n"
        "**Step 6.** **Brochure** — Create a marketing brochure for your course\n\n"
        "**Step 7.** **Check Documents** — Validate everything before submission\n\n"
        "Which step would you like to start with? Just tell me!"
    )


def get_skills_system_message() -> str:
    """Generate a system message section describing all available skills."""
    all_skills = _load_all_skill_objects()

    message_parts = ["""## Your Skills

You have skills that help users with WSQ courseware tasks. When users ask about these topics, USE the relevant skill's instructions to provide accurate, detailed guidance.

**Important**: Proactively identify when a user's request relates to a skill, even if they don't use the exact command. Use the skill's instructions to answer their questions.

"""]

    for skill in all_skills:
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
