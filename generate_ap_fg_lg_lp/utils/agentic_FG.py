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

    sfw_dataset_dir = "generate_ap_fg_lg_lp/input/dataset/Sfw_dataset-2022-03-30 copy.xlsx"
    context = retrieve_excel_data(context, sfw_dataset_dir)

    doc = DocxTemplate(FG_TEMPLATE_DIR)
    
    # Add the logo to the context
    context['company_logo'] = process_logo_image(doc, name_of_organisation)
    context['Name_of_Organisation'] = name_of_organisation

    doc.render(context, autoescape=True)
    # Use a temporary file to save the document
    with tempfile.NamedTemporaryFile(delete=False, suffix=".docx") as tmp_file:
        doc.save(tmp_file.name)
        output_path = tmp_file.name  # Get the path to the temporary file

    return output_path  # Return the path to the temporary file