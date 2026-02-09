# Assessment Plan Generation Reference

## Overview

The Assessment Plan (AP) generation module creates comprehensive assessment documentation including an Assessment Plan and Assessment Summary Report (ASR). It uses AI to extract structured assessment evidence for non-WA-SAQ assessment methods (CS, PP, OQ, RP).

## Pipeline Flow

```
Course Proposal (Excel) → Data Extraction → AI Evidence Extraction → Template Population → AP + ASR Documents (DOCX)
```

## Components

| File | Purpose |
|------|---------|
| [01_evidence_extraction.md](01_evidence_extraction.md) | AI prompt for assessment evidence extraction |
| [02_template_context.md](02_template_context.md) | Context fields and template population |
| [03_assessment_methods.md](03_assessment_methods.md) | Assessment method structures and data models |

## Data Source

The Assessment Plan extracts data from the Course Proposal Excel file, including:
- Course Title
- Learning Outcomes
- Topics Covered
- Assessment Methods (WA-SAQ, PP, CS, OQ, RP)

## Templates

- Assessment Plan: `generate_ap_fg_lg/input/Template/AP_TGS-Ref-No_Course-Title_v1.docx`
- Assessment Summary Report: `generate_ap_fg_lg/input/Template/ASR_TGS-Ref-No_Course-Title_v1.docx`

## Key Features

1. **AI Evidence Extraction**: Generates structured justifications for CS, PP, OQ, RP
2. **Evidence Fields**: Type of Evidence, Submission Method, Marking Process, Retention Period
3. **Role Play Special Handling**: Additional field for number of scripts
4. **Organization Branding**: Company logo integration
5. **Dual Document Generation**: Both AP and ASR documents
