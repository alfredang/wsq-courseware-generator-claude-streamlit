"""
Timetable Generator Module (Utility Functions)

Provides utility functions for timetable generation. The actual timetable
generation (AI reasoning) is handled by Claude Code skill.

This module only contains `extract_unique_instructional_methods()` which
is a pure Python function with no API calls.
"""


def extract_unique_instructional_methods(course_context):
    """
    Extracts and processes unique instructional method combinations from the provided course context.

    Args:
        course_context: Dictionary containing course details with Learning Units.

    Returns:
        Set of unique instructional method combinations as strings.
    """
    unique_methods = set()

    valid_im_pairs = {
        ("Lecture", "Didactic Questioning"),
        ("Lecture", "Peer Sharing"),
        ("Lecture", "Group Discussion"),
        ("Demonstration", "Practice"),
        ("Demonstration", "Group Discussion"),
        ("Case Study",),
        ("Role Play",),
    }

    for lu in course_context.get("Learning_Units", []):
        extracted_methods = lu.get("Instructional_Methods", [])

        corrected_methods = []
        for method in extracted_methods:
            if method == "Classroom":
                corrected_methods.append("Lecture")
            elif method == "Practical":
                corrected_methods.append("Practice")
            elif method == "Discussion":
                corrected_methods.append("Group Discussion")
            else:
                corrected_methods.append(method)

        method_pairs = set()
        for pair in valid_im_pairs:
            if all(method in corrected_methods for method in pair):
                method_pairs.add(", ".join(pair))

        if not method_pairs and corrected_methods:
            if len(corrected_methods) == 1:
                method_pairs.add(corrected_methods[0])
            elif len(corrected_methods) == 2:
                method_pairs.add(", ".join(corrected_methods))
            else:
                method_pairs.add(", ".join(corrected_methods[:2]))
                if len(corrected_methods) > 2:
                    method_pairs.add(", ".join(corrected_methods[-2:]))

        unique_methods.update(method_pairs)

    return unique_methods
