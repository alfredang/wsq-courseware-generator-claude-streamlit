# Learner Guide Generation Reference

## Overview

The Learner Guide (LG) generation module creates a comprehensive training document for learners. It uses AI to generate course descriptions and populates a DOCX template with course data extracted from the Course Proposal.

## Pipeline Flow

```
Course Proposal (Excel) → Data Extraction → AI Content Generation → Template Population → LG Document (DOCX)
```

## Components

| File | Purpose |
|------|---------|
| [01_content_generation.md](01_content_generation.md) | AI prompt for Course Overview and LO Description |
| [02_template_context.md](02_template_context.md) | Context fields extracted from Course Proposal |

## Data Source

The Learner Guide extracts data from the Course Proposal Excel file, including:
- Course Title
- Learning Units (LU_Title, LO, Topics)
- K and A Factors
- Assessment Methods
- Instructional Methods

## Template

Uses DOCX template: `generate_ap_fg_lg/input/Template/LG_TGS-Ref-No_Course-Title_v1.docx`

## Key Features

1. **AI-Generated Content**: Course Overview (90-100 words) and LO Description (45-50 words)
2. **Organization Branding**: Company logo integration
3. **Assessment Summary**: LO to Assessment Method mapping with abbreviations
4. **Version Control**: Automatic date stamping and revision tracking
