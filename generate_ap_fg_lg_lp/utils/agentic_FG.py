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
    import os

    # Debug: Log incoming context for FG generation
    print("=" * 60)
    print("FG GENERATION - CONTEXT DEBUG")
    print("=" * 60)
    print(f"FG DEBUG: Course_Title = {context.get('Course_Title')}")
    print(f"FG DEBUG: TSC_Code = {context.get('TSC_Code')}")
    print(f"FG DEBUG: TSC_Title = {context.get('TSC_Title')}")
    print(f"FG DEBUG: TSC_Category = {context.get('TSC_Category')}")
    print(f"FG DEBUG: TSC_Sector_Abbr = {context.get('TSC_Sector_Abbr')}")
    print(f"FG DEBUG: Skills_Framework = {context.get('Skills_Framework')}")
    print(f"FG DEBUG: Proficiency_Level = {context.get('Proficiency_Level')}")
    print(f"FG DEBUG: Proficiency_Description = {context.get('Proficiency_Description')}")
    print(f"FG DEBUG: TSC_Description = {context.get('TSC_Description')}")
    print(f"FG DEBUG: Learning_Units count = {len(context.get('Learning_Units', []))}")

    # Debug: Print Learning_Units structure
    learning_units = context.get("Learning_Units", [])
    if learning_units:
        for i, lu in enumerate(learning_units):
            print(f"FG DEBUG: LU[{i}] LU_Title = {lu.get('LU_Title')}")
            print(f"FG DEBUG: LU[{i}] LO = {lu.get('LO')}")
            print(f"FG DEBUG: LU[{i}] Topics count = {len(lu.get('Topics', []))}")
            print(f"FG DEBUG: LU[{i}] K_statements count = {len(lu.get('K_numbering_description', []))}")
            print(f"FG DEBUG: LU[{i}] A_statements count = {len(lu.get('A_numbering_description', []))}")
            print(f"FG DEBUG: LU[{i}] Assessment_Methods = {lu.get('Assessment_Methods')}")
    else:
        print("FG DEBUG: WARNING - Learning_Units is EMPTY!")
    print("=" * 60)

    # Use the provided template directory or default
    if sfw_dataset_dir is None:
        sfw_dataset_dir = "generate_ap_fg_lg_lp/input/dataset/Sfw_dataset-2022-03-30 copy.xlsx"

    # Try to retrieve excel data if dataset file exists, otherwise skip
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

    # ================================================================
    # Validate and ensure all TSC fields are properly set for template
    # ================================================================
    def is_empty(val):
        return val is None or val == "" or val == "null" or val == "None"

    # Get base values for defaults
    tsc_code = context.get("TSC_Code", "")
    tsc_title = context.get("TSC_Title", "")
    course_title = context.get("Course_Title", "")

    # Extract sector abbreviation from TSC Code if available
    sector_abbr = tsc_code.split("-")[0] if "-" in tsc_code else ""

    # Sector mapping based on TSC Code prefix
    sector_mapping = {
        "LOG": ("Logistics", "Skills Framework for Logistics"),
        "ICT": ("Infocomm Technology", "Skills Framework for Infocomm Technology"),
        "FIN": ("Financial Services", "Skills Framework for Financial Services"),
        "HR": ("Human Resource", "Skills Framework for Human Resource"),
        "MFG": ("Manufacturing", "Skills Framework for Manufacturing"),
        "RET": ("Retail", "Skills Framework for Retail"),
        "SEC": ("Security", "Skills Framework for Security"),
        "TOU": ("Tourism", "Skills Framework for Tourism"),
        "HEA": ("Healthcare", "Skills Framework for Healthcare"),
        "EDU": ("Education", "Skills Framework for Training and Adult Education"),
        "HAS": ("Hotel and Accommodation Services", "Skills Framework for Hotel and Accommodation Services"),
        "FBS": ("Food Services", "Skills Framework for Food Services"),
        "ATT": ("Attractions", "Skills Framework for Attractions"),
        "TAE": ("Training and Adult Education", "Skills Framework for Training and Adult Education"),
        "SER": ("Services", "Skills Framework for Services"),
        "AIR": ("Air Transport", "Skills Framework for Air Transport"),
        "SEA": ("Sea Transport", "Skills Framework for Sea Transport"),
        "LND": ("Land Transport", "Skills Framework for Land Transport"),
        "ENE": ("Energy and Chemicals", "Skills Framework for Energy and Chemicals"),
        "AER": ("Aerospace", "Skills Framework for Aerospace"),
        "BIO": ("Biopharmaceutical Manufacturing", "Skills Framework for Biopharmaceutical Manufacturing"),
        "MED": ("Media", "Skills Framework for Media"),
        "DES": ("Design", "Skills Framework for Design"),
        "BCE": ("Built Environment", "Skills Framework for Built Environment"),
        "MAR": ("Marine and Offshore", "Skills Framework for Marine and Offshore"),
        "PRE": ("Precision Engineering", "Skills Framework for Precision Engineering"),
        "WSH": ("Workplace Safety and Health", "Skills Framework for Workplace Safety and Health"),
        "PUB": ("Public Service", "Skills Framework for Public Service"),
        "SOC": ("Social Service", "Skills Framework for Social Service"),
        "EAC": ("Early Childhood", "Skills Framework for Early Childhood"),
    }

    # Get sector info from mapping
    sector_name = ""
    skills_framework_full = ""
    if sector_abbr and sector_abbr in sector_mapping:
        sector_name, skills_framework_full = sector_mapping[sector_abbr]

    # Ensure TSC_Sector_Abbr (used in template for Skills Framework field)
    if is_empty(context.get("TSC_Sector_Abbr")):
        if skills_framework_full:
            context["TSC_Sector_Abbr"] = skills_framework_full
        elif context.get("Skills_Framework"):
            context["TSC_Sector_Abbr"] = context.get("Skills_Framework")
        else:
            context["TSC_Sector_Abbr"] = sector_name or tsc_title or ""
        print(f"FG DEBUG: Set TSC_Sector_Abbr = {context['TSC_Sector_Abbr']}")

    # Ensure Skills_Framework
    if is_empty(context.get("Skills_Framework")):
        context["Skills_Framework"] = skills_framework_full or sector_name or ""
        print(f"FG DEBUG: Set Skills_Framework = {context['Skills_Framework']}")

    # Ensure TSC_Category
    if is_empty(context.get("TSC_Category")):
        context["TSC_Category"] = sector_name or tsc_title or ""
        print(f"FG DEBUG: Set TSC_Category = {context['TSC_Category']}")

    # Ensure Proficiency_Level
    if is_empty(context.get("Proficiency_Level")):
        # Try to extract from TSC Code (format: XXX-YYY-ZZZZ-N.N)
        import re
        level_match = re.search(r'-(\d+)\.\d+$', tsc_code)
        if level_match:
            context["Proficiency_Level"] = f"Level {level_match.group(1)}"
        else:
            context["Proficiency_Level"] = ""
        print(f"FG DEBUG: Set Proficiency_Level = {context['Proficiency_Level']}")

    # Ensure Proficiency_Description (used in template for TSC Description field)
    if is_empty(context.get("Proficiency_Description")):
        # Use TSC_Description if available
        if context.get("TSC_Description"):
            context["Proficiency_Description"] = context.get("TSC_Description")
        elif tsc_title:
            context["Proficiency_Description"] = f"Apply knowledge and skills in {tsc_title.lower()} to meet organizational and industry requirements."
        elif course_title:
            context["Proficiency_Description"] = f"Apply knowledge and skills in {course_title.lower()} to meet organizational and industry requirements."
        else:
            context["Proficiency_Description"] = ""
        print(f"FG DEBUG: Set Proficiency_Description = {context['Proficiency_Description']}")

    # Ensure TSC_Description (backup)
    if is_empty(context.get("TSC_Description")):
        context["TSC_Description"] = context.get("Proficiency_Description", "")
        print(f"FG DEBUG: Set TSC_Description = {context['TSC_Description']}")

    # Log final TSC values
    print("=" * 60)
    print("FG DEBUG: FINAL TSC FIELD VALUES")
    print("=" * 60)
    print(f"FG DEBUG: TSC_Sector_Abbr = {context.get('TSC_Sector_Abbr')}")
    print(f"FG DEBUG: TSC_Category = {context.get('TSC_Category')}")
    print(f"FG DEBUG: TSC_Code = {context.get('TSC_Code')}")
    print(f"FG DEBUG: TSC_Title = {context.get('TSC_Title')}")
    print(f"FG DEBUG: Proficiency_Description = {context.get('Proficiency_Description')}")
    print(f"FG DEBUG: Proficiency_Level = {context.get('Proficiency_Level')}")
    print("=" * 60)

    # ================================================================
    # Validate and normalize Learning_Units structure for template
    # ================================================================
    learning_units = context.get("Learning_Units", [])

    # Ensure Learning_Units is a list
    if not isinstance(learning_units, list):
        print(f"FG DEBUG: WARNING - Learning_Units is not a list, type = {type(learning_units)}")
        learning_units = []

    # Validate each Learning Unit has required fields
    validated_learning_units = []
    for i, lu in enumerate(learning_units):
        if not isinstance(lu, dict):
            print(f"FG DEBUG: WARNING - LU[{i}] is not a dict, skipping")
            continue

        # Ensure required fields exist with defaults
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

        # Ensure K_numbering_description have required structure
        validated_k = []
        for k in validated_lu["K_numbering_description"]:
            if isinstance(k, dict):
                validated_k.append({
                    "K_number": k.get("K_number", ""),
                    "Description": k.get("Description", "")
                })
        validated_lu["K_numbering_description"] = validated_k

        # Ensure A_numbering_description have required structure
        validated_a = []
        for a in validated_lu["A_numbering_description"]:
            if isinstance(a, dict):
                validated_a.append({
                    "A_number": a.get("A_number", ""),
                    "Description": a.get("Description", "")
                })
        validated_lu["A_numbering_description"] = validated_a

        validated_learning_units.append(validated_lu)
        print(f"FG DEBUG: Validated LU[{i}]: LU_Title='{validated_lu['LU_Title']}', LO='{validated_lu['LO'][:50]}...', Topics={len(validated_lu['Topics'])}, K={len(validated_lu['K_numbering_description'])}, A={len(validated_lu['A_numbering_description'])}")

    # Update context with validated Learning_Units
    context["Learning_Units"] = validated_learning_units
    learning_units = validated_learning_units

    print(f"FG DEBUG: Total validated Learning_Units = {len(learning_units)}")

    # Prepare Assessment Summary with full LO descriptions and abbreviated assessment methods
    assessment_summary = []

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
