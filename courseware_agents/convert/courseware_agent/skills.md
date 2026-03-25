# Convert Courseware Agent — Skills

## Purpose
Extracts structured courseware data from existing AP/FG/LG/ASR documents and rebuilds them using the standardised WSQ DOCX templates.

## Skills
1. **Document Type Detection** — Auto-detects AP, FG, LG, or ASR from content and filename
2. **Learning Unit Extraction** — Extracts all LUs with topics, K/A statements, LOs, assessment methods
3. **Course Metadata Extraction** — Extracts course title, TGS code, company name, UEN, TSC info, hours
4. **Template Filling** — Fills standardised DOCX template using docxtpl (Jinja2)

## Input
- Existing courseware DOCX files (AP, FG, LG, ASR — any format)

## Output
- Standardised WSQ courseware DOCX files

## Templates
- `courseware_agents/courseware/templates/AP_TGS-Ref-No_Course-Title_v1.docx`
- `courseware_agents/courseware/templates/FG_TGS-Ref-No_Course-Title_v1.docx`
- `courseware_agents/courseware/templates/LG_TGS-Ref-No_Course-Title_v1.docx`
- `courseware_agents/courseware/templates/ASR_TGS-Ref-No_Course-Title_v1.docx`
