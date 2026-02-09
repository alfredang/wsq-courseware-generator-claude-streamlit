"""
Timetable Generator Module

Pure Python lesson plan schedule builder using the barrier algorithm,
and DOCX 4-column table generator.

No AI/agent calls - instant schedule generation.

Algorithm rules (from SKILL.md):
- 9:00 AM to 6:00 PM daily
- Lunch: fixed 45 mins, 12:30 PM - 1:15 PM
- Assessment: fixed 4:00 PM - 6:00 PM on last day only
- Topic duration = instructional_hours * 60 / num_topics (equal allocation)
- Topics CAN split across lunch/day-end barriers
- Minimum session: 15 minutes (avoid tiny splits; use Break instead)
- Fill remaining gaps with Breaks to fit exactly 9AM-6PM
"""

import re
import tempfile
from docx import Document
from docx.shared import Pt, RGBColor, Inches
from docx.enum.text import WD_ALIGN_PARAGRAPH
from docx.oxml.ns import qn


# =============================================================================
# Constants
# =============================================================================

DAY_START = 9 * 60            # 9:00 AM in minutes from midnight
DAY_END = 18 * 60             # 6:00 PM
LUNCH_START = 12 * 60 + 30    # 12:30 PM
LUNCH_DURATION = 45            # 45 minutes
LUNCH_END = LUNCH_START + LUNCH_DURATION  # 1:15 PM
ASSESS_START = 16 * 60         # 4:00 PM (last day only)
MIN_SESSION = 15               # Minimum session length in minutes

HEADING_COLOR = RGBColor(0x44, 0x72, 0xC4)  # Steel blue


# =============================================================================
# Utility Functions
# =============================================================================

def _parse_hours(value) -> float:
    """Parse hours from various formats: '14 hrs', '2 hours', '16', 14.5, etc."""
    if isinstance(value, (int, float)):
        return float(value)
    if not value:
        return 0.0
    s = str(value).strip()
    match = re.search(r'(\d+\.?\d*)', s)
    return float(match.group(1)) if match else 0.0


def _fmt_time(minutes_from_midnight: int) -> str:
    """Format minutes from midnight as 'H:MM AM/PM'."""
    h = minutes_from_midnight // 60
    m = minutes_from_midnight % 60
    period = "AM" if h < 12 else "PM"
    display_h = h % 12 or 12
    return f"{display_h}:{m:02d} {period}"


def _make_slot(start: int, end: int, description: str, methods: str) -> dict:
    """Create a schedule slot dictionary."""
    duration = end - start
    return {
        "timing": f"{_fmt_time(start)} - {_fmt_time(end)}",
        "duration": f"{duration} mins",
        "description": description,
        "methods": methods,
    }


def _collect_topics(context: dict) -> list:
    """Collect all topics across Learning Units with numbering and methods."""
    topics = []
    num = 1
    for lu in context.get("Learning_Units", []):
        methods = lu.get("Instructional_Methods", [])
        # Normalize method names
        normalized = []
        for m in methods:
            if m == "Classroom":
                normalized.append("Lecture")
            elif m == "Practical":
                normalized.append("Practice")
            elif m == "Discussion":
                normalized.append("Group Discussion")
            else:
                normalized.append(m)

        for topic in lu.get("Topics", []):
            topics.append({
                "num": num,
                "title": topic.get("Topic_Title", f"Topic {num}"),
                "bullet_points": topic.get("Bullet_Points", []),
                "methods": normalized or ["Lecture"],
            })
            num += 1
    return topics


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


# =============================================================================
# Schedule Builder (Barrier Algorithm)
# =============================================================================

def build_lesson_plan_schedule(context: dict) -> dict:
    """Build a lesson plan schedule using the barrier algorithm.

    Barriers: Lunch (12:30-1:15), Assessment (4:00-6:00 last day), Day End (6:00).
    Topics are packed sequentially and split at barriers.

    Returns:
        Dict with keys: num_days, instructional_hours, assessment_hours,
        per_topic_mins, days (dict of day_num -> list of slot dicts).
    """
    # Parse course parameters
    total_hours = _parse_hours(context.get("Total_Course_Duration_Hours", "16"))
    instr_hours = _parse_hours(context.get("Total_Training_Hours", ""))
    if not instr_hours:
        instr_hours = total_hours
    assess_hours = _parse_hours(context.get("Total_Assessment_Hours", "0"))

    num_days = max(1, round(total_hours / 8)) if total_hours >= 8 else 1

    # Collect all topics
    topics = _collect_topics(context)
    num_topics = len(topics)
    if num_topics == 0:
        return {
            "num_days": num_days,
            "instructional_hours": instr_hours,
            "assessment_hours": assess_hours,
            "per_topic_mins": 0,
            "days": {},
        }

    per_topic = (instr_hours * 60) / num_topics
    assess_mins = int(assess_hours * 60)

    days = {}
    topic_idx = 0
    topic_remaining = per_topic
    is_contd = False

    for day in range(1, num_days + 1):
        slots = []
        current = DAY_START
        is_last_day = (day == num_days)
        lunch_done = False

        # Effective end of instruction time
        instr_end = ASSESS_START if (is_last_day and assess_mins > 0) else DAY_END

        while topic_idx < num_topics and current < instr_end:
            # Insert lunch if we've reached or passed 12:30
            if not lunch_done and current >= LUNCH_START:
                lunch_end = current + LUNCH_DURATION
                slots.append(_make_slot(current, lunch_end, "Lunch Break", "-"))
                current = lunch_end
                lunch_done = True
                continue

            # Next barrier
            next_barrier = LUNCH_START if (not lunch_done) else instr_end
            available = next_barrier - current

            if available <= 0:
                break

            topic = topics[topic_idx]
            t_label = f"T{topic['num']}: {topic['title']}"
            if is_contd:
                t_label += " (Cont'd)"
            t_methods = ", ".join(topic["methods"])

            if topic_remaining <= available:
                # Topic fits completely before barrier
                end = current + int(round(topic_remaining))
                slots.append(_make_slot(current, end, t_label, t_methods))
                current = end
                topic_idx += 1
                if topic_idx < num_topics:
                    topic_remaining = per_topic
                    is_contd = False

            elif available >= MIN_SESSION:
                # Split topic at barrier
                slots.append(_make_slot(current, next_barrier, t_label, t_methods))
                topic_remaining -= available
                is_contd = True
                current = next_barrier

            else:
                # Too short for a topic session
                if not lunch_done:
                    # Start lunch early (absorb the tiny gap)
                    lunch_end = current + LUNCH_DURATION
                    slots.append(_make_slot(current, lunch_end, "Lunch Break", "-"))
                    current = lunch_end
                    lunch_done = True
                else:
                    # Insert break before next barrier
                    slots.append(_make_slot(current, next_barrier, "Break", "-"))
                    current = next_barrier

        # Ensure lunch is placed even if topics ended early
        if not lunch_done:
            if current < LUNCH_START:
                slots.append(_make_slot(current, LUNCH_START, "Break", "-"))
                current = LUNCH_START
            lunch_end = current + LUNCH_DURATION
            slots.append(_make_slot(current, lunch_end, "Lunch Break", "-"))
            current = lunch_end

        # Assessment on last day
        if is_last_day and assess_mins > 0:
            if current < ASSESS_START:
                slots.append(_make_slot(current, ASSESS_START, "Break", "-"))
                current = ASSESS_START

            am_details = context.get("Assessment_Methods_Details", [])
            if am_details:
                for am in am_details:
                    am_dur = max(int(_parse_hours(am.get("Total_Delivery_Hours", "1")) * 60), 15)
                    am_end = min(current + am_dur, DAY_END)
                    label = f"Assessment: {am.get('Assessment_Method', 'Assessment')}"
                    slots.append(_make_slot(current, am_end, label, "Assessment"))
                    current = am_end
            else:
                # Generic assessment block
                am_end = min(current + assess_mins, DAY_END)
                slots.append(_make_slot(current, am_end, "Assessment", "Assessment"))
                current = am_end

        # Fill remaining time to end of day
        if current < DAY_END:
            slots.append(_make_slot(current, DAY_END, "Break", "-"))

        days[day] = slots

    return {
        "num_days": num_days,
        "instructional_hours": instr_hours,
        "assessment_hours": assess_hours,
        "per_topic_mins": round(per_topic, 1),
        "days": days,
    }


# =============================================================================
# DOCX 4-Column Table Generator
# =============================================================================

def _set_header_cell(cell, text: str):
    """Style a table header cell with steel blue background and white text."""
    cell.text = ""
    p = cell.paragraphs[0]
    run = p.add_run(text)
    run.bold = True
    run.font.size = Pt(10)
    run.font.name = "Calibri"
    run.font.color.rgb = RGBColor(255, 255, 255)
    p.alignment = WD_ALIGN_PARAGRAPH.CENTER
    tc_pr = cell._element.get_or_add_tcPr()
    shading = tc_pr.makeelement(
        qn("w:shd"), {qn("w:fill"): "4472C4", qn("w:val"): "clear"},
    )
    tc_pr.append(shading)


def _add_colored_heading(doc, text: str, level: int = 2):
    """Add a heading with steel blue color."""
    heading = doc.add_heading(text, level=level)
    for run in heading.runs:
        run.font.color.rgb = HEADING_COLOR


def generate_lesson_plan_docx(context: dict, schedule_data: dict, org_name: str = "") -> str:
    """Generate a Lesson Plan DOCX with 4-column tables.

    Args:
        context: Course context dict with Course_Title, etc.
        schedule_data: Output from build_lesson_plan_schedule().
        org_name: Organization name (for metadata).

    Returns:
        Path to the generated DOCX file.
    """
    doc = Document()

    # Default style
    style = doc.styles["Normal"]
    style.font.name = "Calibri"
    style.font.size = Pt(11)
    style.paragraph_format.space_after = Pt(6)

    # Title
    title_para = doc.add_paragraph()
    title_run = title_para.add_run(f"Lesson Plan: {context.get('Course_Title', 'Course')}")
    title_run.bold = True
    title_run.font.size = Pt(14)
    title_run.font.name = "Calibri"

    # Metadata
    num_days = schedule_data.get("num_days", 1)
    instr_hrs = schedule_data.get("instructional_hours", 0)
    assess_hrs = schedule_data.get("assessment_hours", 0)

    methods = extract_unique_instructional_methods(context)
    methods_text = ", ".join(sorted(methods)) if methods else "N/A"

    metadata_lines = [
        f"Course Duration: {num_days} Day(s) (9:00 AM - 6:00 PM daily)",
        f"Total Training Hours: {instr_hrs} hrs",
        f"Total Assessment Hours: {assess_hrs} hrs",
        f"Instructional Methods: {methods_text}",
    ]
    if org_name:
        metadata_lines.insert(0, f"Organisation: {org_name}")

    for line in metadata_lines:
        p = doc.add_paragraph(line)
        for run in p.runs:
            run.font.name = "Calibri"
            run.font.size = Pt(11)
        p.paragraph_format.space_after = Pt(2)

    # Day-by-day 4-column tables
    days = schedule_data.get("days", {})
    col_widths = [Inches(1.5), Inches(0.8), Inches(2.5), Inches(1.7)]

    for day_num in sorted(days.keys()):
        _add_colored_heading(doc, f"Day {day_num}")

        slots = days[day_num]
        table = doc.add_table(rows=1, cols=4)
        table.style = "Table Grid"
        table.autofit = False

        for i, width in enumerate(col_widths):
            table.columns[i].width = width

        # Header row
        _set_header_cell(table.rows[0].cells[0], "Timing")
        _set_header_cell(table.rows[0].cells[1], "Duration")
        _set_header_cell(table.rows[0].cells[2], "Description")
        _set_header_cell(table.rows[0].cells[3], "Instructional Methods")

        # Data rows
        for slot in slots:
            row = table.add_row()
            values = [
                slot.get("timing", ""),
                slot.get("duration", ""),
                slot.get("description", ""),
                slot.get("methods", ""),
            ]
            for j, val in enumerate(values):
                cell = row.cells[j]
                cell.width = col_widths[j]
                cell.text = ""
                p = cell.paragraphs[0]
                run = p.add_run(val)
                run.font.name = "Calibri"
                run.font.size = Pt(10)

        doc.add_paragraph()  # Spacing between days

    # Save to temp file
    with tempfile.NamedTemporaryFile(delete=False, suffix=".docx") as tmp:
        doc.save(tmp.name)
        return tmp.name
