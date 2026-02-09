"""
Assessment Plan Generation Module (Template Filling)

Generates Assessment Plan (AP) and Assessment Summary Report (ASR) documents
by populating DOCX templates with course assessment details.

Assessment evidence should be pre-generated in the context dict by Claude Code skill.
No API calls are made from this module.
"""

import tempfile
import json
from pydantic import BaseModel
from typing import List, Union, Optional
from docxtpl import DocxTemplate
from generate_ap_fg_lg.utils.helper import retrieve_excel_data, process_logo_image
from utils.helpers import parse_json_content


class AssessmentMethod(BaseModel):
    evidence: Union[str, List[str]]
    submission: Union[str, List[str]]
    marking_process: Union[str, List[str]]
    retention_period: str
    no_of_scripts: Union[str, None] = None


class AssessmentMethods(BaseModel):
    PP: Optional[AssessmentMethod] = None
    CS: Optional[AssessmentMethod] = None
    RP: Optional[AssessmentMethod] = None
    OQ: Optional[AssessmentMethod] = None


class EvidenceGatheringPlan(BaseModel):
    assessment_methods: AssessmentMethods


def combine_assessment_methods(structured_data, evidence_data):
    """
    Merges assessment evidence details into the structured data under 'Assessment_Methods_Details'.
    """
    evidence_methods = evidence_data.get("assessment_methods", {})

    for method in structured_data.get("Assessment_Methods_Details", []):
        method_abbr = method.get("Method_Abbreviation")

        if method_abbr in evidence_methods:
            evidence_details = evidence_methods[method_abbr]

            if "WA-SAQ" in method_abbr:
                method.update({
                    "Evidence": evidence_details.get("evidence", ""),
                    "Submission": evidence_details.get("submission", ""),
                    "Marking_Process": evidence_details.get("marking_process", ""),
                    "Retention_Period": evidence_details.get("retention_period", "")
                })

            if "PP" in method_abbr or "CS" in method_abbr or "OQ" in method_abbr:
                method.update({
                    "Evidence": evidence_details.get("evidence", []),
                    "Submission": evidence_details.get("submission", []),
                    "Marking_Process": evidence_details.get("marking_process", []),
                    "Retention_Period": evidence_details.get("retention_period", "")
                })

            if method_abbr == "RP":
                method.update({
                    "Evidence": evidence_details.get("evidence", ""),
                    "Submission": evidence_details.get("submission", ""),
                    "Marking_Process": evidence_details.get("marking_process", []),
                    "Retention_Period": evidence_details.get("retention_period", "")
                })
                method["No_of_Scripts"] = evidence_details.get("no_of_scripts", "Not specified")

    return structured_data


AP_TEMPLATE_DIR = ".claude/skills/generate_assessment_plan/templates/AP_TGS-Ref-No_Course-Title_v1.docx"
ASR_TEMPLATE_DIR = ".claude/skills/generate_assessment_plan/templates/ASR_TGS-Ref-No_Course-Title_v1.docx"


def is_evidence_extracted(context):
    """
    Checks whether all necessary assessment evidence fields are already present in the context.
    """
    for method in context.get("Assessment_Methods_Details", []):
        method_abbr = method.get("Method_Abbreviation")
        if method_abbr == "WA-SAQ":
            continue
        for key in ["Evidence", "Submission", "Marking_Process", "Retention_Period"]:
            if method_abbr == "RP" and key in ["Evidence", "Submission"]:
                continue
            if method.get(key) is None:
                return False
    return True


def generate_assessment_plan(context: dict, name_of_organisation, sfw_dataset_dir) -> str:
    """
    Generates an Assessment Plan (AP) document by populating a DOCX template.

    Expects assessment evidence to already be in the context dict (pre-generated
    by Claude Code skill). If evidence is missing, the template will be filled
    with whatever data is available.

    Args:
        context: Structured course data including assessment methods.
        name_of_organisation: Organization name for branding.
        sfw_dataset_dir: Path to the Excel dataset for additional course data.

    Returns:
        File path of the generated Assessment Plan document.
    """
    if not is_evidence_extracted(context):
        print("WARNING: Assessment evidence is incomplete. Run Claude Code skill /generate_courseware to generate evidence.")

    doc = DocxTemplate(AP_TEMPLATE_DIR)

    import os
    if os.path.exists(sfw_dataset_dir):
        context = retrieve_excel_data(context, sfw_dataset_dir)

    # Add the logo and organization details
    context['company_logo'] = process_logo_image(doc, name_of_organisation)
    context['Name_of_Organisation'] = name_of_organisation

    # Ensure UEN is set from organization data
    from generate_ap_fg_lg.utils.organizations import get_organizations, get_default_organization
    organizations = get_organizations()
    org = next((o for o in organizations if o["name"] == name_of_organisation), None)
    if org and org.get("uen"):
        context['UEN'] = org["uen"]
    else:
        default_org = get_default_organization()
        if default_org.get("uen"):
            context['UEN'] = default_org["uen"]

    # Add Document Version Control Record data
    from datetime import datetime
    current_date = datetime.now().strftime("%d %b %Y")
    context['Rev_No'] = "1.0"
    context['Effective_Date'] = current_date
    context['Author'] = ""
    context['Reviewed_By'] = ""
    context['Approved_By'] = ""

    doc.render(context, autoescape=True)

    with tempfile.NamedTemporaryFile(delete=False, suffix=".docx") as tmp_file:
        doc.save(tmp_file.name)
        output_path = tmp_file.name

    return output_path


def generate_asr_document(context: dict, name_of_organisation) -> str:
    """Generates an Assessment Summary Report (ASR) document."""
    doc = DocxTemplate(ASR_TEMPLATE_DIR)
    context['Name_of_Organisation'] = name_of_organisation

    from generate_ap_fg_lg.utils.organizations import get_organizations, get_default_organization
    organizations = get_organizations()
    org = next((o for o in organizations if o["name"] == name_of_organisation), None)
    if org and org.get("uen"):
        context['UEN'] = org["uen"]
    else:
        default_org = get_default_organization()
        if default_org.get("uen"):
            context['UEN'] = default_org["uen"]

    from datetime import datetime
    current_date = datetime.now().strftime("%d %b %Y")
    context['Rev_No'] = "1.0"
    context['Effective_Date'] = current_date
    context['Author'] = ""
    context['Reviewed_By'] = ""
    context['Approved_By'] = ""

    doc.render(context)

    with tempfile.NamedTemporaryFile(delete=False, suffix=".docx") as tmp_file:
        doc.save(tmp_file.name)
        output_path = tmp_file.name

    return output_path


def generate_assessment_documents(context: dict, name_of_organisation, sfw_dataset_dir=None):
    """
    Generates both the Assessment Plan (AP) and Assessment Summary Report (ASR) documents.

    Args:
        context: Structured course data including assessment methods.
        name_of_organisation: Organization name for document customization.
        sfw_dataset_dir: Path to the Excel dataset. Defaults to a predefined path.

    Returns:
        Tuple of (AP file path, ASR file path).
    """
    try:
        if sfw_dataset_dir is None:
            sfw_dataset_dir = ".claude/skills/generate_courseware/data/Sfw_dataset.xlsx"

        ap_output_path = generate_assessment_plan(context, name_of_organisation, sfw_dataset_dir)
        asr_output_path = generate_asr_document(context, name_of_organisation)

        return ap_output_path, asr_output_path
    except Exception as e:
        print(f"An error occurred during document generation: {e}")
        import traceback
        print(f"Full traceback: {traceback.format_exc()}")
        raise Exception(f"Assessment document generation failed: {str(e)}")
