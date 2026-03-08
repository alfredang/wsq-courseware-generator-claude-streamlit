"""
Multi-Agent Slide Generation Configuration

Constants, defaults, and configuration for the 5-phase agent pipeline:
  Phase 1: Research Agent (WebSearch + WebFetch)
  Phase 2: Content Generator (structured content blocks)
  Phase 3: Editor Agent (skeleton with infographic assignments)
  Phase 4: Infographic Agent (AntV infographics → PNG)
  Phase 5: Assembly + PPTX Build
"""

# ---------- Models ----------
DEFAULT_MODEL = "claude-sonnet-4-20250514"
FAST_MODEL = "claude-3-5-haiku-20241022"    # For simple structured tasks (DSL, JSON)
PREMIUM_MODEL = "claude-opus-4-5-20251101"

# ---------- Slide count targets ----------
SLIDE_TARGETS = {
    1: (60, 100),     # 1-day: target 100
    2: (130, 140),    # 2-day: target 140
    3: (195, 210),    # 3-day: target 210
    4: (230, 250),    # 4-day: target 250
}
SLIDES_PER_DAY_DEFAULT = 70   # Fallback for courses > 2 days
MIN_SLIDES_PER_TOPIC = 6
MAX_SLIDES_PER_TOPIC = 16    # Max infographics per topic (reduced for speed)

# ---------- Phase 1: Research Agent ----------
DEFAULT_RESEARCH_DEPTH = 5    # Sources per topic (~20-30 total across all topics)
RESEARCH_MAX_TURNS = 5        # 2 searches + 2 fetches + JSON output
RESEARCH_MODEL = FAST_MODEL   # Haiku — fast for web search tasks

# ---------- Phase 2: Content Generator ----------
CONTENT_MAX_TURNS = 5         # JSON generation + optional WebSearch for thin research
CONTENT_MODEL = FAST_MODEL    # Haiku — fast for structured JSON
DEFAULT_BLOCKS_PER_TOPIC = 6  # Content blocks per topic (6 = rich infographic coverage)

# ---------- Phase 3: Editor Agent ----------
EDITOR_MAX_TURNS = 3          # Single-shot JSON skeleton
EDITOR_MODEL = FAST_MODEL     # Haiku — fast for structured JSON

# ---------- Phase 4: Infographic Agent ----------
INFOGRAPHIC_MAX_TURNS = 2     # Per single infographic (DSL generation only)
INFOGRAPHIC_WIDTH = 1792      # AntV canvas width
INFOGRAPHIC_HEIGHT = 1024     # AntV canvas height

# ---------- Color scheme (matching PPTX template) ----------
COLORS = {
    "navy": "#1B2A4A",
    "teal": "#1ABC9C",
    "blue": "#3498DB",
    "white": "#FFFFFF",
    "gray": "#7F8C8D",
    "orange": "#F39C12",
}

# ---------- Standard WSQ slide sections ----------
STANDARD_INTRO_SLIDES = [
    {"type": "cover", "title": "Cover"},
    {"type": "attendance", "title": "Digital Attendance (Mandatory)"},
    {"type": "placeholder", "title": "About the Trainer"},
    {"type": "icebreaker", "title": "Let's Know Each Other"},
    {"type": "content", "title": "Ground Rules"},
    {"type": "content", "title": "Skills Framework"},
    {"type": "content", "title": "Knowledge & Ability Statements"},
    {"type": "content", "title": "Course Outline"},
    {"type": "content", "title": "Assessment Methods & Briefing"},
    {"type": "content", "title": "Criteria for Funding"},
]

STANDARD_CLOSING_SLIDES = [
    {"type": "section", "title": "Summary & Q&A"},
    {"type": "content", "title": "TRAQOM Survey"},
    {"type": "content", "title": "Certificate of Accomplishment"},
    {"type": "attendance", "title": "Digital Attendance"},
    {"type": "section", "title": "Final Assessment"},
    {"type": "content", "title": "Support"},
    {"type": "section", "title": "Thank You"},
]


def compute_standard_slide_count(num_topics: int) -> int:
    """Count non-content (standard) slides: intro + closing + per-topic overhead."""
    # 10 intro + 7 closing + 2 per topic (section header + activity)
    return 17 + (num_topics * 2)


def compute_total_target(total_training_hours: float) -> int:
    """Get the total slide target for a course duration."""
    course_days = max(1, round(total_training_hours / 8))
    if course_days in SLIDE_TARGETS:
        _min_total, max_total = SLIDE_TARGETS[course_days]
        return max_total
    else:
        _base_min, base_max = SLIDE_TARGETS[2]
        extra_days = course_days - 2
        return base_max + (extra_days * SLIDES_PER_DAY_DEFAULT)


def compute_slides_per_topic(total_training_hours: float, num_topics: int) -> int:
    """Compute target content slides per topic based on course duration.

    Uses tiered targets: 1-day (80), 2-day (120 exact).

    Args:
        total_training_hours: Total course duration in hours (e.g. 8, 16).
        num_topics: Total number of topics across all LUs.

    Returns:
        Target slides per topic, clamped to [MIN, MAX].
    """
    if num_topics <= 0:
        return MIN_SLIDES_PER_TOPIC

    total_target = compute_total_target(total_training_hours)
    standard_slides = compute_standard_slide_count(num_topics)
    content_budget = total_target - standard_slides
    per_topic = max(MIN_SLIDES_PER_TOPIC, content_budget // num_topics)
    return min(per_topic, MAX_SLIDES_PER_TOPIC)


def compute_per_topic_distribution(total_training_hours: float, num_topics: int) -> list:
    """Compute exact block count per topic to hit the total target exactly.

    Distributes extra slides across topics evenly when content_budget
    doesn't divide evenly by num_topics.

    Args:
        total_training_hours: Total course duration in hours.
        num_topics: Total number of topics.

    Returns:
        List of int — blocks per topic (length = num_topics).
    """
    if num_topics <= 0:
        return []

    total_target = compute_total_target(total_training_hours)
    standard_slides = compute_standard_slide_count(num_topics)
    content_budget = total_target - standard_slides

    base_per_topic = max(MIN_SLIDES_PER_TOPIC, content_budget // num_topics)
    base_per_topic = min(base_per_topic, MAX_SLIDES_PER_TOPIC)

    # Distribute remainder to first N topics (capped at num_topics)
    remainder = content_budget - (base_per_topic * num_topics)
    distribution = [base_per_topic] * num_topics
    for i in range(min(max(0, remainder), num_topics)):
        if distribution[i] < MAX_SLIDES_PER_TOPIC:
            distribution[i] += 1

    return distribution
