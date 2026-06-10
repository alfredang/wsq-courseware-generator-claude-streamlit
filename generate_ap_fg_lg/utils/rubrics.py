"""
Marking Rubric criteria for the Assessment Plan (AP).

Provides a standard, fixed set of Competent / Not Yet Competent (C/NYC)
performance criteria for each assessment method. These are injected into the
AP context dict so the AP template can render a "Marking Rubric" section
(one C/NYC checklist table per assessment method).

The criteria are intentionally generic and reusable across all courses so the
rubric is consistent regardless of subject matter.
"""

from typing import List


# Standard fixed C/NYC marking criteria, keyed by assessment method.
# Matched by substring against Method_Abbreviation (e.g. "WA-SAQ", "PP", "CS",
# "RP", "OQ") so minor naming variations still resolve correctly.
RUBRIC_CRITERIA = {
    "SAQ": [
        "Addresses all parts of the question.",
        "Demonstrates the required underpinning knowledge.",
        "Provides accurate, relevant and complete content.",
        "Uses correct terminology and presents answers clearly.",
    ],
    "PP": [
        "Follows the correct procedure and sequence of steps.",
        "Observes safety and workplace requirements.",
        "Applies the required skills and techniques competently.",
        "Achieves the expected quality of outcome within the time given.",
    ],
    "CS": [
        "Accurately analyses the given scenario.",
        "Applies relevant concepts and principles.",
        "Provides justified recommendations or solutions.",
        "Presents the response in a clear and structured manner.",
    ],
    "RP": [
        "Demonstrates the required behaviours and responses.",
        "Responds appropriately to the situation presented.",
        "Communicates clearly and professionally.",
        "Applies relevant underpinning knowledge in the interaction.",
    ],
    "OQ": [
        "Provides accurate and complete responses.",
        "Demonstrates understanding of the underpinning knowledge.",
        "Justifies answers with relevant reasoning.",
        "Articulates responses clearly.",
    ],
}

# Fallback criteria for any unrecognised assessment method.
DEFAULT_RUBRIC_CRITERIA = [
    "Meets the stated assessment requirements.",
    "Demonstrates the required knowledge and abilities.",
    "Provides accurate and relevant evidence.",
    "Presents the work clearly and completely.",
]


def get_rubric_criteria(method_abbreviation: str) -> List[str]:
    """Return the fixed C/NYC criteria for a given assessment method abbreviation."""
    abbr = (method_abbreviation or "").upper()
    for key, criteria in RUBRIC_CRITERIA.items():
        if key in abbr:
            return list(criteria)
    return list(DEFAULT_RUBRIC_CRITERIA)


def attach_rubric_criteria(context: dict) -> dict:
    """
    Inject standard C/NYC marking-rubric criteria into each assessment method.

    Adds a `Rubric_Criteria` list to every item in
    `context["Assessment_Methods_Details"]`. Safe to call multiple times.

    Returns the same context dict (mutated in place) for convenience.
    """
    for method in context.get("Assessment_Methods_Details", []):
        method["Rubric_Criteria"] = get_rubric_criteria(
            method.get("Method_Abbreviation", "")
        )
    return context
