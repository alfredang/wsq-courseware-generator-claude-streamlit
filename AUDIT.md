# Courseware Audit Skill

Custom courseware audit skill for cross-checking WSQ courseware documents against the Course Proposal (CP) as the source of truth.

## Overview

The audit validates that key fields are consistent across all courseware documents (AP, FG, LG, LP) by comparing them to the CP.

**Command**: `/courseware_audit`

## How It Works

1. **Upload CP** — Upload the Course Proposal document (DOCX, DOC, XLSX, XLS) or auto-loads from session if already extracted
2. **Enter TGS Reference Code** — Manually enter the TGS code (CP usually doesn't contain it)
3. **Audit Checklist** — All fields are checked by default (expandable to deselect items)
4. **Upload Courseware Documents** — Upload AP, FG, LG, LP files (DOCX, DOC, XLSX, XLS)
5. **Run Audit** — AI extracts fields from all documents and compares against CP
6. **Review Results** — Per-document checklist with green tick (pass) / red X (fail) / N/A (not applicable)
7. **Auto-Fix** — Optionally auto-fix mismatched DOCX files
8. **Clear All** — Reset everything to start a new audit for a different course

## Audit Check Items

All rules are defined in `courseware_agents/audit/templates/audit_extraction.md` (single source of truth).

| Display Name | Field Key | Type | Applicable Docs |
|---|---|---|---|
| Course Title | course_title | string | all |
| TGS Reference No. | tgs_ref_code | string | all |
| Topics | topics | list | all |
| Training Hours | training_hours | duration_field | FG, LP |
| Assessment Hours | assessment_hours | duration_field | AP, FG, LP |
| Company Name | company_name | string | all |
| UEN | uen | string | all |
| Learning Outcomes | learning_outcomes | list | AP, FG, LG |
| K Statements | k_statements | list | AP, FG, LG |
| A Statements | a_statements | list | AP, FG, LG |
| Assessment Methods | assessment_methods | list | AP, FG |
| Instructional Methods | instructional_methods | list | FG, LP |
| TSC Code | tsc_code | string | AP, FG |
| TSC Title | tsc_title | string | AP, FG |

### Applicable Docs

Based on actual DOCX template contents:
- **AP** — Course Title, TGS, Topics (via LU_Title), Assessment Hours, Company, UEN, LOs, K/A Statements, Assessment Methods, TSC Code/Title
- **FG** — All fields (most comprehensive template)
- **LG** — Course Title, TGS, Topics, Company, UEN, LOs, K/A Statements
- **LP** — Course Title, TGS, Topics (via sessions), Training Hours, Assessment Hours, Company, UEN, Instructional Methods

### Comparison Rules

| Type | How It Compares |
|---|---|
| `string` | Normalized text comparison — case-insensitive, strips punctuation, removes business suffixes (Pte, Ltd, Academy, etc.) for company name matching |
| `list` | **Existence check** — as long as the document has topics/LOs/statements, it passes (different templates structure them differently) |
| `duration_field` | Numeric comparison normalized to hours — "30 mins" = 0.5 hrs, "22.0 hrs" = 22 hrs. Also matches total hours (training + assessment) when document shows combined duration |

### Special Rules

- **Company Name & UEN**: Sourced from CP extraction. Falls back to company list only if CP doesn't have them AND the company list matches the CP's company name.
- **Topics**: Existence check only — each template structures topics differently (LU titles vs topic titles vs session titles). Green if document has topics.
- **Duration**: Handles minutes-to-hours conversion (30 mins = 0.5 hrs). Also matches when document shows total hours (training + assessment combined).
- **Missing fields**: If a document doesn't have a field, it shows as N/A (hidden) — not a failure. Different documents contain different fields.
- **CP re-extraction**: CP fields are re-extracted fresh every time "Run Audit" is clicked — no stale cached data.

## Agent Details

| Component | Detail |
|---|---|
| Agent | `courseware_agents/audit/audit_agent.py` |
| Function | `extract_audit_fields(document_text, document_type)` |
| Model | Sonnet 4 (`claude-sonnet-4-20250514`) |
| Tools | None (text-only extraction) |
| UI Page | `courseware_audit/sup_doc.py` |
| Prompt Template | `courseware_agents/audit/templates/audit_extraction.md` (single source of truth) |

## Excel CP Support

For Excel-based CPs (SSG format), the extraction skips reference/lookup sheets that contain irrelevant data:
- Skipped sheets: `TSC_Skill_Codes`, `TSC_CCS_K&A`, `TSC_Sector_Track`, `SSOC_5D`, `checks`, `other_ref`, `change_log`, `READ BEFORE FILLING`
- Only content sheets are extracted to prevent AI confusion

## Auto-Fix

When mismatches are found, the system can automatically:
- Replace mismatched text in DOCX files with correct CP values
- Generate `_FIXED.docx` files for download
- Show before/after for each replacement

## File Structure

```
AUDIT.md                                    ← This file (skill definition + rules)
courseware_audit/
├── sup_doc.py                              # Streamlit UI page
courseware_agents/audit/
├── audit_agent.py                          # Agent wrapper (extract_audit_fields)
├── templates/
│   └── audit_extraction.md                 # Source of truth for AI prompt & check items
```

**Python code has NO hardcoded rules** — all audit check items and extraction rules are defined in the markdown template (`audit_extraction.md`). To add/remove/modify check items, edit the Audit Check Items table in that file.
