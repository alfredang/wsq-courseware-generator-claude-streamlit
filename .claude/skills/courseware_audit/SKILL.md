# Courseware Audit

## Command
`/courseware_audit` or `courseware_audit`

## Navigate
Courseware Audit

## Keywords
check document, validate document, verify document, check files, validate files, review document, document check, file check, supporting document, sup doc, i need to check, verify my files, validate my documents, are my documents correct, check my work, courseware audit, audit courseware, cross check, compare CP

## Description
Cross-check courseware documents (AP, FG, LG, LP) against the Course Proposal (CP) as the source of truth. Validates key fields like Course Title, TGS, Topics, Training Hours, Assessment Hours, Company Name, and UEN.

## Execution
This skill runs using **Claude Code with subscription plan**. Do NOT use pay-as-you-go API keys. All AI operations should be executed through the Claude Code CLI environment with an active subscription.

## Response
I'll take you to **Courseware Audit** now.

Two audit modes are available:

1. **Quick Check** — If you've already extracted course info, this uses the CP data in your session. Just upload your courseware documents to check.
2. **Upload & Check** — Upload both your CP and courseware documents from scratch.

## Instructions

### Audit Modes

**Quick Check (after generation)**
- Requires CP data already loaded via **Extract Course Info**
- Uses session state CP context as source of truth
- User uploads AP/FG/LG/LP courseware documents to compare

**Upload & Check (existing documents)**
- User uploads a CP document (DOCX or PDF)
- AI extracts CP fields automatically
- User uploads AP/FG/LG/LP courseware documents to compare

### Audit Check Items (Checkbox Selection)
Users select which fields to check via checkboxes. All are checked by default:

| Check Item | Field Key | What It Validates |
|---|---|---|
| Course Title | `course_title` | Title matches across all documents |
| TGS Reference No. | `tgs_ref_code` | TGS reference number is consistent |
| Topics | `topics` | All topic titles match the CP |
| Training Hours | `training_hours` | Training duration follows CP |
| Assessment Hours | `assessment_hours` | Assessment duration follows CP |
| Company Name | `company_name` | Training provider name is consistent |
| UEN | `uen` | Unique Entity Number matches |

### Process
1. Select audit mode (Quick Check or Upload & Check)
2. Select items to check via checkboxes
3. CP fields are shown and editable (override if needed)
4. Upload courseware documents (AP, FG, LG, LP)
5. Click **Run Audit** to compare
6. Review results table (green = match, red = mismatch, yellow = missing)
7. Optionally **Auto-Fix** mismatched DOCX files

### Agent Details
- **Agent**: `courseware_agents/audit/audit_agent.py`
- **Function**: `extract_audit_fields(document_text, document_type)`
- **Model**: Sonnet 4 (`claude-sonnet-4-20250514`)
- **Tools**: None (text-only extraction)
- **Prompt Template**: Editable via Settings → Prompt Templates (category: `courseware_audit`)

### Auto-Fix
When mismatches are found, the system can automatically:
- Replace mismatched text in DOCX files with correct CP values
- Generate `_FIXED.docx` files for download
- Show before/after for each replacement

## Capabilities
- Cross-check courseware documents against CP source of truth
- Checkbox-based field selection for targeted auditing
- Editable CP fields for manual override
- Company Name and UEN auto-populated from Company Settings
- Color-coded results table (match/mismatch/missing)
- Auto-fix mismatched DOCX documents
- Support for both DOCX and PDF input

## Next Steps
Once your documents pass validation, you're ready for SSG submission! If you need to fix anything:
- **Regenerate courseware** — say *"generate courseware"*
- **Regenerate assessments** — say *"create assessment"*
- **Regenerate lesson plan** — say *"generate lesson plan"*
