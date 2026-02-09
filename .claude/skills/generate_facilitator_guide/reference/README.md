# Facilitator Guide Generation Reference

## Overview

The Facilitator Guide (FG) generation module creates a comprehensive training document for instructors/facilitators. It extracts data from the Course Proposal and populates a DOCX template. This module does NOT use AI generation - it performs data extraction and template population only.

## Pipeline Flow

```
Course Proposal (Excel) → Data Extraction → TSC Field Validation → Template Population → FG Document (DOCX)
```

## Components

| File | Purpose |
|------|---------|
| [01_template_context.md](01_template_context.md) | Context fields extracted from Course Proposal |
| [02_tsc_field_mapping.md](02_tsc_field_mapping.md) | TSC sector mapping and field validation |

## Data Source

The Facilitator Guide extracts data from the Course Proposal Excel file, including:
- Course Title
- TSC Code, TSC Title, TSC Category
- Skills Framework information
- Proficiency Level and Description
- Learning Units (LU_Title, LO, Topics)
- K and A Factors
- Assessment Methods
- Instructional Methods

## Template

Uses DOCX template: `generate_ap_fg_lg/input/Template/FG_TGS-Ref-No_Course-Title_v1.docx`

## Key Features

1. **No AI Generation**: Pure data extraction and template population
2. **TSC Field Validation**: Automatic sector detection from TSC Code
3. **Proficiency Description**: Auto-generation if not provided
4. **Organization Branding**: Company logo integration
5. **Assessment Summary**: LO to Assessment Method mapping
