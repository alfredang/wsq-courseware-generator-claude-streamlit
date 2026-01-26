"""
File: helper.py

===============================================================================
Helper Functions Module for Courseware
===============================================================================
Description:
    This module provides utility functions to support various operations in the Courseware
    system. It includes functions to retrieve course-related data from an Excel dataset and to
    process an organization's logo image for insertion into DOCX documents. The retrieved data
    enriches the course context with additional information such as TSC Sector, Category, and
    Proficiency details, while the logo processing function resizes and prepares the image for
    use in document templates.

Main Functionalities:
    • retrieve_excel_data(context: dict, sfw_dataset_dir: str) -> dict:
          - Reads an Excel file from the specified directory.
          - Extracts relevant information from the "TSC_K&A" sheet using the TSC Code provided in the context.
          - Updates and returns the context dictionary with additional keys:
                "TSC_Sector", "TSC_Sector_Abbr", "TSC_Category", "Proficiency_Level", and "Proficiency_Description".
    • process_logo_image(doc, name_of_organisation, max_width_inch=7, max_height_inch=2.5) -> InlineImage:
          - Processes and resizes the organization's logo image to fit within the defined maximum dimensions.
          - Returns an InlineImage object for insertion into DOCX templates using docxtpl.

Dependencies:
    - pandas: For reading and parsing Excel files.
    - os: For file system operations.
    - PIL (Pillow): For image processing.
    - docx.shared.Inches: For specifying dimensions in Word documents.
    - docxtpl.InlineImage: For embedding images into DOCX templates.

Usage:
    - Import the helper functions when additional course data or logo processing is required.
      Example:
          from generate_ap_fg_lg_lp.utils.helper import retrieve_excel_data, process_logo_image
          context = retrieve_excel_data(context, "generate_ap_fg_lg_lp/input/dataset/Sfw_dataset-2022-03-30 copy.xlsx")
          logo_image = process_logo_image(doc, "Organisation Name")

Author:
    Derrick Lim
Date:
    3 March 2025
===============================================================================
"""

import pandas as pd
import os
from PIL import Image
from docx.shared import Inches
from docxtpl import InlineImage

def retrieve_excel_data(context: dict, sfw_dataset_dir: str) -> dict:
    """
    Retrieve course-related data from an Excel dataset based on the provided TSC Code.

    This function reads an Excel file and extracts relevant information from the "TSC_K&A" sheet 
    using the TSC Code present in the `context` dictionary. The retrieved data, including 
    sector, category, proficiency level, and description, is added to the `context` dictionary.

    Args:
        context (dict): 
            A dictionary containing course details, including the key `"TSC_Code"`, which 
            is used to filter the dataset.
        sfw_dataset_dir (str): 
            The file path to the Excel dataset containing the "TSC_K&A" sheet.

    Returns:
        dict: 
            The updated `context` dictionary containing additional retrieved information:

            - `"TSC_Sector"` (str): The sector associated with the TSC Code.
            - `"TSC_Sector_Abbr"` (str): The sector abbreviation derived from the TSC Code.
            - `"TSC_Category"` (str): The category of the TSC.
            - `"Proficiency_Level"` (str): The proficiency level required for the TSC.
            - `"Proficiency_Description"` (str): A description of the proficiency level.
    
    Raises:
        FileNotFoundError: 
            If the specified Excel file does not exist.
        KeyError: 
            If expected column names (e.g., "TSC Code", "Sector") are missing in the dataset.
        ValueError: 
            If the provided TSC Code is not found in the dataset.
    """
    # Load the Excel file
    excel_data = pd.ExcelFile(sfw_dataset_dir)
    
    # Load the specific sheet named 'TSC_K&A'
    df = excel_data.parse('TSC_K&A')
    
    tsc_code = context.get("TSC_Code")
    # Filter the DataFrame based on the TSC Code
    filtered_df = df[df['TSC Code'] == tsc_code]
    
    if not filtered_df.empty:
        row = filtered_df.iloc[0]
        
        context["TSC_Sector"] = str(row['Sector'])
        context["TSC_Sector_Abbr"] = str(tsc_code.split('-')[0])
        context["TSC_Category"] = str(row['Category'])
        context["Proficiency_Level"] = str(row['Proficiency Level'])
        context["Proficiency_Description"] = str(row['Proficiency Description'])

    # Return the retrieved data as a dictionary
    return context

def process_logo_image(doc, name_of_organisation, max_width_inch=7, max_height_inch=2.5):
    """
    Processes an organization's logo image for insertion into a Word document.

    Args:
        doc (DocxTemplate): The document where the image will be placed.
        name_of_organisation (str): The organization's name (used for logo file naming).
        max_width_inch (float): Maximum width allowed in inches.
        max_height_inch (float): Maximum height allowed in inches.

    Returns:
        InlineImage: The resized logo image for use in the document.
    """
    # Get logo path from organization data
    from generate_ap_fg_lg_lp.utils.organizations import get_organizations
    organizations = get_organizations()
    org = next((o for o in organizations if o["name"] == name_of_organisation), None)

    if org and org.get("logo"):
        logo_path = org["logo"]
    else:
        # Fallback to old logic if organization not found
        logo_filename = name_of_organisation.lower().replace(" ", "_") + ".jpg"
        logo_path = f"generate_ap_fg_lg_lp/utils/logo/{logo_filename}"

    if not os.path.exists(logo_path):
        raise FileNotFoundError(f"Logo file not found for organisation: {name_of_organisation}")

    # Open the logo image
    image = Image.open(logo_path)
    width_px, height_px = image.size

    # Get DPI and calculate dimensions in inches
    dpi = image.info.get('dpi', (96, 96))  # Default to 96 DPI if not specified
    width_inch = width_px / dpi[0]
    height_inch = height_px / dpi[1]

    # Scale dimensions if they exceed the maximum
    width_ratio = max_width_inch / width_inch if width_inch > max_width_inch else 1
    height_ratio = max_height_inch / height_inch if height_inch > max_height_inch else 1
    scaling_factor = min(width_ratio, height_ratio)

    # Apply scaling
    width_docx = Inches(width_inch * scaling_factor)
    height_docx = Inches(height_inch * scaling_factor)

    # Create and return the InlineImage
    return InlineImage(doc, logo_path, width=width_docx, height=height_docx)