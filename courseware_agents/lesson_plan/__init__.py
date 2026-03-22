"""Lesson Plan generation (standalone feature).

Uses barrier algorithm for schedule building + docxtpl template filling.
"""

from courseware_agents.lesson_plan.lesson_plan import generate_lesson_plan

__all__ = ["generate_lesson_plan"]
