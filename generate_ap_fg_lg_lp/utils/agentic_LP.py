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
    
    doc = DocxTemplate(LP_TEMPLATE_DIR)

    # Add the logo to the context
    context['company_logo'] = process_logo_image(doc, name_of_organisation)
    context['Name_of_Organisation'] = name_of_organisation

    doc.render(context, autoescape=True)
    
    # Use a temporary file to save the document
    with tempfile.NamedTemporaryFile(delete=False, suffix=".docx") as tmp_file:
        doc.save(tmp_file.name)
        output_path = tmp_file.name  # Get the path to the temporary file

    return output_path  # Return the path to the temporary file
