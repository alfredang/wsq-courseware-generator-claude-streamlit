# Assessment Plan Template Context

## Purpose

Documents the context fields extracted from the Course Proposal and AI evidence extraction, used to populate the Assessment Plan and ASR DOCX templates.

## Context Structure

### Course Information

| Field | Source | Description |
|-------|--------|-------------|
| `Course_Title` | Course Proposal | Full course name |
| `Name_of_Organisation` | User selection | Training provider name |
| `UEN` | Organization database | Unique Entity Number |
| `company_logo` | Logo directory | Organization logo image |

### Learning Units Array

```json
{
    "Learning_Units": [
        {
            "LU_Title": "Learning Unit 1: Introduction to Topic",
            "LO": "Full learning outcome description",
            "Topics": [
                {
                    "Topic_Title": "Topic 1: Fundamentals",
                    "Bullet_Points": ["Point 1", "Point 2", "Point 3"]
                }
            ],
            "Assessment_Methods": ["Written Assessment", "Practical Performance"]
        }
    ]
}
```

### Assessment Methods Details

```json
{
    "Assessment_Methods_Details": [
        {
            "Method_Name": "Written Assessment - Short Answer Questions",
            "Method_Abbreviation": "WA-SAQ",
            "Duration": "0.5 hr"
        },
        {
            "Method_Name": "Practical Performance",
            "Method_Abbreviation": "PP",
            "Duration": "0.5 hr",
            "Evidence": ["LO1: Candidates will...", "LO2: Candidates will..."],
            "Submission": ["Candidates will submit..."],
            "Marking_Process": ["Criterion 1.", "Criterion 2.", "Criterion 3."],
            "Retention_Period": "All submitted evidence will be retained for 3 years..."
        },
        {
            "Method_Name": "Role Play",
            "Method_Abbreviation": "RP",
            "Duration": "0.5 hr",
            "Evidence": "Role Play",
            "Submission": ["Assessor will evaluate..."],
            "Marking_Process": ["Criterion 1.", "Criterion 2.", "Criterion 3."],
            "Retention_Period": "...",
            "No_of_Scripts": "Minimum of two distinct role-play scripts..."
        }
    ]
}
```

### Version Control

| Field | Default | Description |
|-------|---------|-------------|
| `Rev_No` | "1.0" | Document revision number |
| `Effective_Date` | Current date | Date in "DD Mon YYYY" format |
| `Author` | "" | Author name (user input) |
| `Reviewed_By` | "" | Reviewer name (user input) |
| `Approved_By` | "" | Approver name (user input) |

## Evidence Extraction Check

Before extracting evidence, the system checks if required fields exist:

```python
def is_evidence_extracted(context):
    for method in context.get("Assessment_Methods_Details", []):
        method_abbr = method.get("Method_Abbreviation")

        # Skip WA-SAQ - hardcoded in template
        if method_abbr == "WA-SAQ":
            continue

        # Check required keys
        for key in ["Evidence", "Submission", "Marking_Process", "Retention_Period"]:
            # For RP, skip Evidence and Submission check
            if method_abbr == "RP" and key in ["Evidence", "Submission"]:
                continue
            if method.get(key) is None:
                return False
    return True
```

## Template Placeholders

### Assessment Plan (AP)

```
{{ Course_Title }}
{{ Name_of_Organisation }}
{{ UEN }}
{{ company_logo }}

{% for method in Assessment_Methods_Details %}
    {{ method.Method_Name }}
    {{ method.Method_Abbreviation }}
    {{ method.Duration }}

    {% if method.Evidence %}
        {% for ev in method.Evidence %}
            {{ ev }}
        {% endfor %}
    {% endif %}

    {% for sub in method.Submission %}
        {{ sub }}
    {% endfor %}

    {% for mp in method.Marking_Process %}
        {{ mp }}
    {% endfor %}

    {{ method.Retention_Period }}

    {% if method.No_of_Scripts %}
        {{ method.No_of_Scripts }}
    {% endif %}
{% endfor %}
```

### Marking Rubric (AP)

The AP also renders a **Marking Rubric** section: one Competent / Not Yet
Competent (C/NYC) checklist table per assessment method. Each method gets a
fixed `Rubric_Criteria` list (4 items) injected automatically by
`generate_ap_fg_lg/utils/rubrics.py` (`attach_rubric_criteria`) at render time —
it is **not** produced by the evidence agent, so no extraction step is needed.

```
{% for mtd in Assessment_Methods_Details %}
    {{ mtd.Assessment_Method }} ({{ mtd.Method_Abbreviation }})
    {{ mtd.Rubric_Criteria[0] }}   # rows 0..3, each judged C / NYC
{% endfor %}
```

### Assessment Summary Report (ASR)

```
{{ Course_Title }}
{{ Name_of_Organisation }}
{{ UEN }}

{% for lu in Learning_Units %}
    {{ lu.LU_Title }}
    {{ lu.LO }}
{% endfor %}
```
