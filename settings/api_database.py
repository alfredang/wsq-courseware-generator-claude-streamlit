"""
Settings Database Module

SQLite-based storage for prompt templates (customizable AI prompts).

Author: Claude Code
Date: February 2026
"""

import sqlite3
import os
from typing import Dict, List, Any, Optional
from contextlib import contextmanager

# Database file location
DB_PATH = "settings/config/api_config.db"


def get_db_path() -> str:
    """Get the database file path, ensuring directory exists"""
    os.makedirs(os.path.dirname(DB_PATH), exist_ok=True)
    return DB_PATH


@contextmanager
def get_connection():
    """Context manager for database connections"""
    conn = sqlite3.connect(get_db_path())
    conn.row_factory = sqlite3.Row
    try:
        yield conn
        conn.commit()
    except Exception as e:
        conn.rollback()
        raise e
    finally:
        conn.close()


def init_database():
    """Initialize the database with required tables"""
    with get_connection() as conn:
        cursor = conn.cursor()

        # Prompt templates table
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS prompt_templates (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                category TEXT NOT NULL,
                name TEXT NOT NULL,
                display_name TEXT NOT NULL,
                description TEXT,
                content TEXT NOT NULL,
                variables TEXT,
                is_builtin INTEGER DEFAULT 0,
                is_active INTEGER DEFAULT 1,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                UNIQUE(category, name)
            )
        """)

        # Database version table
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS db_version (
                version INTEGER PRIMARY KEY
            )
        """)

        conn.commit()

    # Seed built-in prompt templates if not exists
    _seed_builtin_prompt_templates()


# ============ Prompt Templates Operations ============

BUILTIN_PROMPT_TEMPLATES = [
    # --- Courseware (AP/FG/LG) ---
    {
        "category": "courseware",
        "name": "learner_guide",
        "display_name": "[LG] Learner Guide - Content Generation",
        "description": "Generate Course Overview and Learning Outcome descriptions for the Learner Guide",
        "variables": ""
    },
    {
        "category": "courseware",
        "name": "facilitator_guide",
        "display_name": "[FG] Facilitator Guide - Content Generation",
        "description": "Generate structured content for the Facilitator Guide document",
        "variables": ""
    },
    {
        "category": "courseware",
        "name": "assessment_plan",
        "display_name": "[AP] Assessment Plan - Evidence & Justification",
        "description": "Generate structured justifications for assessment methods including Assessment Record & Summary",
        "variables": "course_title, learning_outcomes, extracted_content, assessment_methods"
    },
    # --- Lesson Plan ---
    {
        "category": "lesson_plan",
        "name": "timetable_generation",
        "display_name": "Timetable/Lesson Plan Generation",
        "description": "Generate WSQ-compliant lesson plan timetables with session scheduling",
        "variables": "num_of_days, list_of_im"
    },
    # --- Assessment ---
    {
        "category": "assessment",
        "name": "saq_generation",
        "display_name": "SAQ Generation",
        "description": "Generate Short Answer Questions for assessments",
        "variables": ""
    },
    {
        "category": "assessment",
        "name": "practical_performance",
        "display_name": "Practical Performance",
        "description": "Generate Practical Performance assessment tasks",
        "variables": ""
    },
    {
        "category": "assessment",
        "name": "case_study",
        "display_name": "Case Study",
        "description": "Generate Case Study assessment scenarios",
        "variables": ""
    },
    {
        "category": "assessment",
        "name": "project",
        "display_name": "Project",
        "description": "Generate Project-based assessment briefs with rubrics and deliverables",
        "variables": ""
    },
    {
        "category": "assessment",
        "name": "assignment",
        "display_name": "Assignment",
        "description": "Generate Assignment tasks with marking criteria",
        "variables": ""
    },
    {
        "category": "assessment",
        "name": "oral_interview",
        "display_name": "Oral Interview",
        "description": "Generate Oral Interview assessment questions and expected responses",
        "variables": ""
    },
    {
        "category": "assessment",
        "name": "demonstration",
        "display_name": "Demonstration",
        "description": "Generate Demonstration tasks with observation checklists",
        "variables": ""
    },
    {
        "category": "assessment",
        "name": "role_play",
        "display_name": "Role Play",
        "description": "Generate Role Play scenarios with evaluation criteria",
        "variables": ""
    },
    {
        "category": "assessment",
        "name": "oral_questioning",
        "display_name": "Oral Questioning",
        "description": "Generate Oral Questioning assessment with probing questions",
        "variables": ""
    },
    # --- Slides ---
    {
        "category": "slides",
        "name": "slide_generation",
        "display_name": "Slide Deck Generation",
        "description": "Instructions for generating presentation slides via NotebookLM",
        "variables": ""
    },
    # --- Brochure ---
    {
        "category": "brochure",
        "name": "brochure_generation",
        "display_name": "Brochure Content Generation",
        "description": "Generate marketing-quality content for WSQ course brochures",
        "variables": "course_title, course_topics, entry_requirements, certification_info"
    },
]


def _load_prompt_file_content(category: str, name: str) -> str:
    """Load prompt content from markdown file in skills folders."""
    current_file = os.path.abspath(__file__)
    settings_dir = os.path.dirname(current_file)
    project_root = os.path.dirname(settings_dir)

    # Search in .claude/skills/*/prompts/ directories
    skills_dir = os.path.join(project_root, ".claude", "skills")
    if os.path.isdir(skills_dir):
        for skill_name in os.listdir(skills_dir):
            prompt_path = os.path.join(skills_dir, skill_name, "prompts", f"{name}.md")
            if os.path.exists(prompt_path):
                try:
                    with open(prompt_path, 'r', encoding='utf-8') as f:
                        return f.read()
                except Exception as e:
                    print(f"Error reading prompt file {prompt_path}: {e}")

    # Legacy fallback paths
    for legacy_dir in ["utils/prompt_templates", "prompt_templates"]:
        prompt_path = os.path.join(project_root, legacy_dir, category, f"{name}.md")
        if os.path.exists(prompt_path):
            try:
                with open(prompt_path, 'r', encoding='utf-8') as f:
                    return f.read()
            except Exception as e:
                print(f"Error reading prompt file {prompt_path}: {e}")

    return ""


def _seed_builtin_prompt_templates():
    """Seed built-in prompt templates from markdown files"""
    with get_connection() as conn:
        cursor = conn.cursor()

        for template in BUILTIN_PROMPT_TEMPLATES:
            try:
                cursor.execute(
                    "SELECT id FROM prompt_templates WHERE category = ? AND name = ?",
                    (template["category"], template["name"])
                )
                if cursor.fetchone():
                    continue

                content = _load_prompt_file_content(template["category"], template["name"])
                if not content:
                    continue

                cursor.execute("""
                    INSERT INTO prompt_templates
                    (category, name, display_name, description, content, variables, is_builtin)
                    VALUES (?, ?, ?, ?, ?, ?, 1)
                """, (
                    template["category"],
                    template["name"],
                    template["display_name"],
                    template["description"],
                    content,
                    template["variables"]
                ))
            except Exception as e:
                print(f"Error seeding prompt template {template['name']}: {e}")

        conn.commit()


def get_all_prompt_templates() -> List[Dict[str, Any]]:
    """Get all prompt templates from database"""
    init_database()
    with get_connection() as conn:
        cursor = conn.cursor()
        cursor.execute("SELECT * FROM prompt_templates ORDER BY category, display_name")
        rows = cursor.fetchall()

        return [
            {
                "id": row["id"],
                "category": row["category"],
                "name": row["name"],
                "display_name": row["display_name"],
                "description": row["description"],
                "content": row["content"],
                "variables": row["variables"],
                "is_builtin": bool(row["is_builtin"]),
                "is_active": bool(row["is_active"]),
            }
            for row in rows
        ]


def get_prompt_templates_by_category(category: str) -> List[Dict[str, Any]]:
    """Get prompt templates for a specific category"""
    init_database()
    with get_connection() as conn:
        cursor = conn.cursor()
        cursor.execute("""
            SELECT * FROM prompt_templates
            WHERE category = ? AND is_active = 1
            ORDER BY display_name
        """, (category,))
        rows = cursor.fetchall()

        return [
            {
                "id": row["id"],
                "category": row["category"],
                "name": row["name"],
                "display_name": row["display_name"],
                "description": row["description"],
                "content": row["content"],
                "variables": row["variables"],
                "is_builtin": bool(row["is_builtin"]),
                "is_active": bool(row["is_active"]),
            }
            for row in rows
        ]


def get_prompt_template(category: str, name: str) -> Optional[Dict[str, Any]]:
    """Get a specific prompt template by category and name"""
    init_database()
    with get_connection() as conn:
        cursor = conn.cursor()
        cursor.execute("""
            SELECT * FROM prompt_templates
            WHERE category = ? AND name = ?
        """, (category, name))
        row = cursor.fetchone()

        if row:
            return {
                "id": row["id"],
                "category": row["category"],
                "name": row["name"],
                "display_name": row["display_name"],
                "description": row["description"],
                "content": row["content"],
                "variables": row["variables"],
                "is_builtin": bool(row["is_builtin"]),
                "is_active": bool(row["is_active"]),
            }
        return None


def get_prompt_template_by_id(template_id: int) -> Optional[Dict[str, Any]]:
    """Get a specific prompt template by ID"""
    init_database()
    with get_connection() as conn:
        cursor = conn.cursor()
        cursor.execute("SELECT * FROM prompt_templates WHERE id = ?", (template_id,))
        row = cursor.fetchone()

        if row:
            return {
                "id": row["id"],
                "category": row["category"],
                "name": row["name"],
                "display_name": row["display_name"],
                "description": row["description"],
                "content": row["content"],
                "variables": row["variables"],
                "is_builtin": bool(row["is_builtin"]),
                "is_active": bool(row["is_active"]),
            }
        return None


def update_prompt_template(
    template_id: int,
    content: Optional[str] = None,
    display_name: Optional[str] = None,
    description: Optional[str] = None,
    variables: Optional[str] = None,
    is_active: Optional[bool] = None
) -> bool:
    """Update a prompt template"""
    init_database()
    try:
        with get_connection() as conn:
            cursor = conn.cursor()

            updates = []
            params = []

            if content is not None:
                updates.append("content = ?")
                params.append(content)
            if display_name is not None:
                updates.append("display_name = ?")
                params.append(display_name)
            if description is not None:
                updates.append("description = ?")
                params.append(description)
            if variables is not None:
                updates.append("variables = ?")
                params.append(variables)
            if is_active is not None:
                updates.append("is_active = ?")
                params.append(1 if is_active else 0)

            if not updates:
                return True

            updates.append("updated_at = CURRENT_TIMESTAMP")
            params.append(template_id)

            query = f"UPDATE prompt_templates SET {', '.join(updates)} WHERE id = ?"
            cursor.execute(query, params)
            return cursor.rowcount > 0
    except Exception as e:
        print(f"Error updating prompt template: {e}")
        return False


def add_prompt_template(
    category: str,
    name: str,
    display_name: str,
    content: str,
    description: str = "",
    variables: str = ""
) -> bool:
    """Add a new custom prompt template"""
    init_database()
    try:
        with get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("""
                INSERT INTO prompt_templates
                (category, name, display_name, description, content, variables, is_builtin)
                VALUES (?, ?, ?, ?, ?, ?, 0)
            """, (category, name, display_name, description, content, variables))
            return True
    except sqlite3.IntegrityError:
        return False
    except Exception as e:
        print(f"Error adding prompt template: {e}")
        return False


def delete_prompt_template(template_id: int) -> bool:
    """Delete a custom prompt template (cannot delete built-in)"""
    init_database()
    try:
        with get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute(
                "DELETE FROM prompt_templates WHERE id = ? AND is_builtin = 0",
                (template_id,)
            )
            return cursor.rowcount > 0
    except Exception as e:
        print(f"Error deleting prompt template: {e}")
        return False


def reset_prompt_template_to_default(template_id: int) -> bool:
    """Reset a built-in prompt template to its default content from file"""
    init_database()
    template = get_prompt_template_by_id(template_id)
    if not template or not template["is_builtin"]:
        return False

    content = _load_prompt_file_content(template["category"], template["name"])
    if not content:
        return False

    return update_prompt_template(template_id, content=content)


def get_prompt_template_categories() -> List[str]:
    """Get list of unique prompt template categories"""
    init_database()
    with get_connection() as conn:
        cursor = conn.cursor()
        cursor.execute("SELECT DISTINCT category FROM prompt_templates ORDER BY category")
        rows = cursor.fetchall()
        return [row["category"] for row in rows]
