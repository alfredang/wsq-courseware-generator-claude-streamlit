"""
File: agentic_FG.py

===============================================================================
Facilitator's Guide Generation Module
===============================================================================
Description:
    This module is responsible for generating a Facilitator's Guide (FG) document for a course.
    It populates a DOCX template with detailed course content by merging data from an Excel dataset
    and incorporating organization-specific branding, such as the company logo. The resulting document
    serves as a comprehensive guide to assist facilitators in delivering course content effectively.

Main Functionalities:
    • generate_facilitators_guide(context: dict, name_of_organisation: str, sfw_dataset_dir=None) -> str:
          - Retrieves additional course data from an Excel dataset using custom helper functions.
          - Processes and inserts the organization's logo into the document context.
          - Renders a Facilitator's Guide DOCX template with the enriched context.
          - Saves the generated document as a temporary file and returns its file path.

Dependencies:
    - Standard Libraries: tempfile
    - External Libraries:
         • docxtpl (DocxTemplate) – For rendering DOCX templates.
    - Custom Utilities:
         • retrieve_excel_data, process_logo_image from generate_ap_fg_lg_lp/utils/helper

Usage:
    - Ensure that the FG DOCX template and the Excel dataset file are available at the specified locations.
    - Provide a course context dictionary and the organization name.
    - Optionally, specify a custom path to the Excel dataset; otherwise, the default dataset will be used.
    - Call generate_facilitators_guide(context, name_of_organisation, sfw_dataset_dir) to generate the document.
    - The function returns the file path of the generated Facilitator's Guide document.

Author:
    Derrick Lim
Date:
    3 March 2025
===============================================================================
"""

import tempfile
from docxtpl import DocxTemplate
from generate_ap_fg_lg_lp.utils.helper import retrieve_excel_data, process_logo_image

FG_TEMPLATE_DIR = "generate_ap_fg_lg_lp/input/Template/FG_TGS-Ref-No_Course-Title_v1.docx"

def generate_facilitators_guide(context: dict, name_of_organisation: str, sfw_dataset_dir=None) -> str:
    """
    Generates a Facilitator's Guide (FG) document by populating a DOCX template with course content.

    This function retrieves course-related data from an Excel dataset, processes the organization's logo,
    and inserts all relevant details into a Facilitator's Guide template before saving the document.

    Args:
        context (dict):
            A dictionary containing course details that will be included in the guide.
        name_of_organisation (str):
            The name of the organization, used to fetch and insert the corresponding logo.
        sfw_dataset_dir (str, optional):
            The file path to the Excel dataset containing course-related data. If not provided,
            a default dataset file is used.

    Returns:
        str:
            The file path of the generated Facilitator's Guide document.

    Raises:
        FileNotFoundError:
            If the template file, dataset file, or organization's logo file is missing.
        KeyError:
            If required keys are missing from the `context` dictionary.
        IOError:
            If there are issues with reading/writing the document.
    """

    # Use the provided template directory or default
    if sfw_dataset_dir is None:
        sfw_dataset_dir = "generate_ap_fg_lg_lp/input/dataset/Sfw_dataset-2022-03-30 copy.xlsx"

    # Try to retrieve excel data if dataset file exists, otherwise skip
    import os
    if os.path.exists(sfw_dataset_dir):
        context = retrieve_excel_data(context, sfw_dataset_dir)
    else:
        print(f"Dataset file not found at {sfw_dataset_dir}, continuing without it...")

    doc = DocxTemplate(FG_TEMPLATE_DIR)

    # Add the logo and organization details to the context
    context['company_logo'] = process_logo_image(doc, name_of_organisation)
    context['Name_of_Organisation'] = name_of_organisation

    # Ensure UEN is set from organization data
    from generate_ap_fg_lg_lp.utils.organizations import get_organizations, get_default_organization
    organizations = get_organizations()
    org = next((o for o in organizations if o["name"] == name_of_organisation), None)
    if org and org.get("uen"):
        context['UEN'] = org["uen"]
    else:
        # Fall back to default organization UEN
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

    # Prepare Assessment Summary with full LO descriptions and abbreviated assessment methods
    assessment_summary = []
    learning_units = context.get("Learning_Units", [])

    # Map full assessment method names to abbreviations
    method_abbreviations = {
        "Written Assessment - Short Answer Questions": "WA-SAQ",
        "Written Assessment": "WA",
        "Written Exam": "WA-SAQ",
        "Practical Performance": "PP",
        "Practical Exam": "PP",
        "Case Study": "CS",
        "Oral Questioning": "OQ",
        "Role Play": "RP",
        "Project": "PJ",
        "Portfolio": "PF",
        "Observation": "OB",
    }

    for lu in learning_units:
        # Get full LO description
        lo_full = lu.get("LO", "")

        # Get assessment methods and convert to abbreviations
        assessment_methods = lu.get("Assessment_Methods", [])
        abbreviated_methods = []
        for method in assessment_methods:
            # Check if it's already an abbreviation
            if method in ["WA-SAQ", "WA", "PP", "CS", "OQ", "RP", "PJ", "PF", "OB"]:
                abbreviated_methods.append(method)
            else:
                # Look up abbreviation
                abbr = method_abbreviations.get(method, method)
                # If not found, try to create abbreviation from first letters
                if abbr == method and len(method) > 5:
                    words = method.split()
                    abbr = "-".join([w[0].upper() for w in words if w[0].isupper() or w == words[0]])
                abbreviated_methods.append(abbr)

        assessment_summary.append({
            "LO": lo_full,
            "Assessment_Methods": ", ".join(abbreviated_methods)
        })

    context['Assessment_Summary'] = assessment_summary

    # Also update Learning_Units to have abbreviated assessment methods
    for i, lu in enumerate(learning_units):
        assessment_methods = lu.get("Assessment_Methods", [])
        abbreviated_methods = []
        for method in assessment_methods:
            if method in ["WA-SAQ", "WA", "PP", "CS", "OQ", "RP", "PJ", "PF", "OB"]:
                abbreviated_methods.append(method)
            else:
                abbr = method_abbreviations.get(method, method)
                if abbr == method and len(method) > 5:
                    words = method.split()
                    abbr = "-".join([w[0].upper() for w in words if w[0].isupper() or w == words[0]])
                abbreviated_methods.append(abbr)
        context['Learning_Units'][i]['Assessment_Methods_Abbr'] = ", ".join(abbreviated_methods)

    doc.render(context, autoescape=True)
    # Use a temporary file to save the document
    with tempfile.NamedTemporaryFile(delete=False, suffix=".docx") as tmp_file:
        doc.save(tmp_file.name)
        output_path = tmp_file.name  # Get the path to the temporary file

    return output_path  # Return the path to the temporary file
