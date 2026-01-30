"""
File: agentic_LP.py

===============================================================================
Lesson Plan Generation Module
===============================================================================
Description:
    This module generates a Lesson Plan (LP) document by populating a DOCX template with 
    course-specific data provided via a context dictionary. It also integrates the organization's 
    branding by processing and inserting the company logo into the document. The final Lesson Plan 
    is saved as a temporary DOCX file, and the file path is returned for further use or download.

Main Functionalities:
    • generate_lesson_plan(context: dict, name_of_organisation: str) -> str:
          - Loads the Lesson Plan DOCX template.
          - Incorporates course details from the provided context.
          - Processes and inserts the organization's logo into the document.
          - Renders the populated template and saves the document as a temporary file.
          - Returns the file path of the generated Lesson Plan document.

Dependencies:
    - Standard Libraries: tempfile
    - External Libraries:
         • docxtpl (DocxTemplate) – For rendering DOCX templates.
    - Custom Utilities:
         • process_logo_image from generate_ap_fg_lg_lp/utils/helper – For processing and embedding the organization's logo.

Usage:
    - Ensure the Lesson Plan DOCX template is available at the specified path.
    - Provide a valid context dictionary containing course-related details and the organization's name.
    - Call generate_lesson_plan(context, name_of_organisation) to generate the Lesson Plan.
    - The function returns the file path of the generated document, which can then be used for further processing or download.

Author:
    Derrick Lim
Date:
    3 March 2025
===============================================================================
"""

import tempfile
from docxtpl import DocxTemplate
from generate_ap_fg_lg_lp.utils.helper import process_logo_image

LP_TEMPLATE_DIR = "generate_ap_fg_lg_lp/input/Template/LP_TGS-Ref-No_Course-Title_v1.docx" 

def generate_lesson_plan(context: dict, name_of_organisation: str) -> str:
    """
    Generates a Lesson Plan (LP) document by filling in a template with provided course data.

    This function uses a DOCX template and populates it with the given `context` dictionary.
    It also processes and inserts the organization's logo into the document before rendering it.

    Args:
        context (dict):
            A dictionary containing course-related details that will be used to populate the template.
        name_of_organisation (str):
            The name of the organization, used to fetch and insert the corresponding logo.

    Returns:
        str:
            The file path of the generated Lesson Plan document.

    Raises:
        FileNotFoundError:
            If the template file or the organization's logo file is missing.
        KeyError:
            If required keys are missing from the `context` dictionary.
        IOError:
            If there are issues with reading/writing the document.
    """
    import re

    # Debug: Log incoming context for LP generation
    print("=" * 60)
    print("LP GENERATION - CONTEXT DEBUG")
    print("=" * 60)
    print(f"LP DEBUG: Course_Title = {context.get('Course_Title')}")
    print(f"LP DEBUG: Learning_Units count = {len(context.get('Learning_Units', []))}")
    print(f"LP DEBUG: lesson_plan exists = {'lesson_plan' in context}")
    print("=" * 60)

    # Helper to check if a value is effectively null/empty
    def is_empty(val):
        return val is None or val == "" or val == "null" or val == "None"

    # ================================================================
    # Validate and normalize Learning_Units structure for template
    # ================================================================
    learning_units = context.get("Learning_Units", [])

    # Ensure Learning_Units is a list
    if not isinstance(learning_units, list):
        print(f"LP DEBUG: WARNING - Learning_Units is not a list, type = {type(learning_units)}")
        learning_units = []

    # Validate each Learning Unit has required fields
    validated_learning_units = []
    for i, lu in enumerate(learning_units):
        if not isinstance(lu, dict):
            continue

        validated_lu = {
            "LU_Title": lu.get("LU_Title", f"Learning Unit {i+1}"),
            "LO": lu.get("LO", ""),
            "Topics": lu.get("Topics", []),
            "K_numbering_description": lu.get("K_numbering_description", []),
            "A_numbering_description": lu.get("A_numbering_description", []),
            "Assessment_Methods": lu.get("Assessment_Methods", []),
            "Instructional_Methods": lu.get("Instructional_Methods", []),
        }

        # Ensure Topics have required structure
        validated_topics = []
        for topic in validated_lu["Topics"]:
            if isinstance(topic, dict):
                validated_topics.append({
                    "Topic_Title": topic.get("Topic_Title", ""),
                    "Bullet_Points": topic.get("Bullet_Points", [])
                })
        validated_lu["Topics"] = validated_topics

        # Ensure K/A statements have required structure
        validated_k = []
        for k in validated_lu["K_numbering_description"]:
            if isinstance(k, dict):
                validated_k.append({"K_number": k.get("K_number", ""), "Description": k.get("Description", "")})
        validated_lu["K_numbering_description"] = validated_k

        validated_a = []
        for a in validated_lu["A_numbering_description"]:
            if isinstance(a, dict):
                validated_a.append({"A_number": a.get("A_number", ""), "Description": a.get("Description", "")})
        validated_lu["A_numbering_description"] = validated_a

        validated_learning_units.append(validated_lu)

    context["Learning_Units"] = validated_learning_units
    print(f"LP DEBUG: Total validated Learning_Units = {len(validated_learning_units)}")

    doc = DocxTemplate(LP_TEMPLATE_DIR)

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
