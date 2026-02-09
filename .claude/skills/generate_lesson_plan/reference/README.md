# Lesson Plan Generation Reference

## Overview

The Lesson Plan (LP) generation module creates a structured teaching plan document for instructors. It extracts data from the Course Proposal, builds a day-by-day schedule using the barrier algorithm, and populates a DOCX template.

## Pipeline Flow

```
Course Proposal → Data Extraction → Learning Units Validation → Schedule Building (Barrier Algorithm) → Template Population → LP Document (DOCX)
```

## Components

| File | Purpose |
|------|---------|
| [01_template_context.md](01_template_context.md) | Context fields extracted from Course Proposal |

## Data Source

The Lesson Plan extracts data from the Course Proposal, including:
- Course Title
- Learning Units (LU_Title, LO, Topics)
- K and A Factors
- Assessment Methods
- Instructional Methods
- Training Duration (days, hours)

## Template

Uses DOCX template: `generate_ap_fg_lg/input/Template/LP_TGS-Ref-No_Course-Title_v1.docx`

## Key Features

1. **Barrier Algorithm**: Schedule building with fixed lunch (12:30-1:15 PM) and assessment (4:00-6:00 PM last day) slots
2. **Topic Splitting**: Topics can split across sessions at natural barriers (lunch, day end)
3. **Equal Time Allocation**: Each topic gets exactly `instructional_hours * 60 / num_topics` minutes
4. **Break Filling**: Remaining gaps filled with breaks to fit 9:00 AM - 6:00 PM per day
5. **Learning Units Validation**: Ensures proper structure for all LUs
6. **Organization Branding**: Company logo integration
7. **Assessment Summary**: LO to Assessment Method mapping with abbreviations
8. **Version Control**: Automatic date stamping and revision tracking
