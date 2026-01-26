import os
import re
import shutil
import tempfile
import zipfile
import json
import pandas as pd
from lxml import etree as ET
from generate_cp.utils.excel_conversion_pipeline import create_course_dataframe, create_assessment_dataframe, create_instructional_dataframe, create_instruction_description_dataframe, map_new_key_names_excel, enrich_assessment_dataframe_ka_descriptions, create_summary_dataframe

def convert_minutes_to_hours_minutes(minutes_total):
    hours = minutes_total // 60
    minutes = minutes_total % 60
    return f"{hours} hours {minutes} minutes"

def compute_total_durations(summary_df):
    # Sum up the instructional durations from the summary dataframe.
    total_instructional_minutes = summary_df["Instructional Duration (in minutes)"].sum()
    # Sum up the assessment durations from the summary dataframe.
    total_assessment_minutes = summary_df["Assessment Duration (in minutes)"].sum()
    # Total course duration is the sum of instructional and assessment durations.
    total_course_minutes = total_instructional_minutes + total_assessment_minutes

    # Convert totals to "x hours x minutes" format.
    instructional_duration = convert_minutes_to_hours_minutes(total_instructional_minutes)
    assessment_duration = convert_minutes_to_hours_minutes(total_assessment_minutes)
    course_duration = convert_minutes_to_hours_minutes(total_course_minutes)

    return instructional_duration, assessment_duration, course_duration

def save_dataframe_to_excel(df, filepath):
    """
    Saves a Pandas DataFrame to a separate Excel file.

    Args:
        df (pd.DataFrame): The DataFrame to save.
        filepath (str): The path to the Excel file to create.
    """
    try:
        df.to_excel(filepath, index=False)  # index=False prevents writing the index to the Excel file
        print(f"DataFrame saved to {filepath}")
    except Exception as e:
        print(f"Error saving DataFrame to Excel: {e}")

def cleanup_old_files(output_excel_path_modified, output_excel_path_preserved):
    """
    Deletes existing output Excel files (both intermediate and final) before script execution.
    """
    files_to_delete = [
        output_excel_path_modified,
        output_excel_path_preserved,
        output_excel_path_preserved[:-5] + ".zip"  # Potential zip file from previous run
    ]

    print("--- Cleaning up old output files ---")
    for filepath in files_to_delete:
        if os.path.exists(filepath):
            try:
                os.remove(filepath)
                print(f" попередній файл '{filepath}' успішно видалено.")
            except OSError as e:
                print(f"Error deleting existing file '{filepath}': {e}")
        else:
            print(f"Файл '{filepath}' не існує, пропускаю видалення.") # File does not exist, skipping deletion
    print("--- Cleanup complete ---")

def insert_dataframe_into_sheet(sheet_xml_path, start_row, start_col, df):
    """
    Inserts a Pandas DataFrame into the specified Excel worksheet.

    Args:
        sheet_xml_path: Path to the sheet XML file.
        start_row:     The 1-indexed row number to start inserting data.
        start_col:     The 1-indexed column number to start inserting data.
        df:            The Pandas DataFrame to insert.
    """
    ns = {'main': 'http://schemas.openxmlformats.org/spreadsheetml/2006/main'}
    parser = ET.XMLParser(remove_blank_text=False)
    tree = ET.parse(sheet_xml_path, parser)
    root = tree.getroot()

    sheetData = root.find(f"{{{ns['main']}}}sheetData")
    if sheetData is None:
        sheetData = ET.SubElement(root, f"{{{ns['main']}}}sheetData")

    rows = sheetData.findall(f"{{{ns['main']}}}row")

    for i, row_values in enumerate(df.values):
        current_row_number = start_row + i
        
        try:
            row_elem = rows[current_row_number - 1] #  Access the existing row
        except IndexError:
            row_elem = ET.SubElement(sheetData, f"{{{ns['main']}}}row", r=str(current_row_number)) #create a new row.

        row_elem.set("r", str(current_row_number)) # Ensure row number is correct

        for j, cell_value in enumerate(row_values):
            col_letter = col_idx_to_letter(start_col + j)
            cell_ref = f"{col_letter}{current_row_number}"

            # Find existing cell element in the row
            cell_elem = None
            for cell in row_elem.findall(f"{{{ns['main']}}}c"):
                if cell.get('r') == cell_ref:
                    cell_elem = cell
                    break

            # If cell doesn't exist, create it; otherwise, clear existing content
            if cell_elem is None:
                cell_elem = ET.SubElement(row_elem, f"{{{ns['main']}}}c", r=cell_ref)
            else:
                for child in list(cell_elem): # Remove existing children
                    cell_elem.remove(child)

            #Set the type attribute to inline string and add a cell Value.
            cell_elem.set('t', 'inlineStr')
            is_elem = ET.Element(f"{{{ns['main']}}}is")
            t_elem = ET.Element(f"{{{ns['main']}}}t")
            t_elem.text = str(cell_value)
            is_elem.append(t_elem)
            cell_elem.append(is_elem)

    tree.write(sheet_xml_path, encoding="UTF-8", xml_declaration=True, pretty_print=True)
    print(f"Inserted DataFrame into {sheet_xml_path}")

def process_excel_update(json_data_path, excel_template_path, output_excel_path, ensemble_output_path):
    """
    Updates specific cells in an Excel workbook (including inserting a DataFrame)
    by only modifying the worksheet XML parts. This approach unzips the .xlsx,
    updates cells, and then repackages it—preserving all other parts.
    """
    json_data = load_json_file(json_data_path)
    if not json_data or not isinstance(json_data, dict):
        print("Failed to load JSON data or data is invalid.")
        return

    ensemble_output = load_json_file(ensemble_output_path)
    if not ensemble_output or not isinstance(ensemble_output, dict):
        print("Failed to load Ensemble Output JSON data or data is invalid.")
        return

    # Validate required keys exist in ensemble_output
    required_keys = ["TSC and Topics", "Learning Outcomes", "Assessment Methods", "Course Information"]
    for key in required_keys:
        if key not in ensemble_output:
            print(f"Error: Required key '{key}' not found in ensemble_output. Cannot proceed.")
            return

    # Define cell mapping as before
    cell_replacement_map = {
        "#Company":      {"sheet": "1 - Course Particulars", "cell": "C2", "json_key": "#Company"},
        "#CourseTitle":   {"sheet": "1 - Course Particulars", "cell": "C3", "json_key": "#CourseTitle"},
        "#TCS_Code_Skill": {"sheet": "1 - Course Particulars", "cell": "C10", "json_key": "#TCS_Code_Skill"},
        "#Course_Outline": {"sheet": "1 - Course Particulars", "cell": "C7", "json_key": "#Course_Outline"},        
        "#Course_Background1": {"sheet": "1 - Course Particulars", "cell": "C6", "json_key": "#Course_Background1"},  
        "#Placeholder[0]": {"sheet": "2 - Background", "cell": "B4", "json_key": "#Placeholder[0]"},
        "#Placeholder[1]": {"sheet": "2 - Background", "cell": "B8", "json_key": "#Placeholder[1]"},
        "#Sequencing_rationale": {"sheet": "3 - Instructional Design", "cell": "B6", "json_key": "#Sequencing_rationale"},
        "#Combined_LO": {"sheet": "3 - Instructional Design", "cell": "B4", "json_key": "#Combined_LO"}
    }

    temp_dir = tempfile.mkdtemp()
    try:
        # Extract the entire workbook archive
        with zipfile.ZipFile(excel_template_path, 'r') as zin:
            zin.extractall(temp_dir)
        print(f"Extracted workbook to {temp_dir}")

        # Build mapping of sheet names to XML file paths
        rels_path = os.path.join(temp_dir, "xl", "_rels", "workbook.xml.rels")
        workbook_xml_path = os.path.join(temp_dir, "xl", "workbook.xml")
        rels_map = get_relationship_mapping(rels_path)
        sheet_mapping = get_sheet_mapping(workbook_xml_path, rels_map)

        # Update individual cells based on cell_replacement_map
        for key, mapping in cell_replacement_map.items():
            sheet_name = mapping.get("sheet")
            cell_ref = mapping.get("cell")
            json_key = mapping.get("json_key")
            new_value = json_data.get(json_key)
            if new_value is None:
                print(f"JSON key '{json_key}' not found. Skipping cell {cell_ref} in sheet {sheet_name}.")
                continue
            if sheet_name not in sheet_mapping:
                print(f"Sheet '{sheet_name}' not found in workbook. Skipping.")
                continue
            sheet_xml_path = os.path.join(temp_dir, sheet_mapping[sheet_name])
            if not re.match(r'^[A-Z]+[1-9][0-9]*$', cell_ref):
                print(f"Invalid cell reference '{cell_ref}'. Skipping.")
                continue

            updated = update_cell_in_sheet(sheet_xml_path, cell_ref, new_value)
            if updated:
                print(f"Updated {sheet_name} cell {cell_ref} with value: {new_value}")

        # Insert the DataFrame into a designated sheet (e.g., "3 - Instructional Design")
        if "3 - Instructional Design" in sheet_mapping:
            # Create the DataFrame using your helper function (provided separately)
            instructional_df = create_course_dataframe(ensemble_output)
            if not instructional_df.empty:
                sheet_xml_path = os.path.join(temp_dir, sheet_mapping["3 - Instructional Design"])
                save_dataframe_to_excel(instructional_df, "generate_cp/json_output/course_dataframe.xlsx")
                print(instructional_df)
                # For example, insert starting at row 18 and column 2 (B18)
                insert_dataframe_into_sheet(sheet_xml_path, start_row=17, start_col=2, df=instructional_df)
            else:
                print("Warning: DataFrame is empty. Nothing to insert.")
        else:
            print("Sheet '3 - Instructional Design' not found. DataFrame not inserted.")


        # Insert the DataFrame into a designated sheet (e.g., "3 - Instructional Design")
        if "3 - Methodologies" in sheet_mapping:
            # Create the DataFrame using your helper function (provided separately)
            methods_df = create_assessment_dataframe(ensemble_output)

            # append the K and A descriptions in excel_data.json to the dataframe under the KA column
            # excel_json_data = os.path.join('..', 'json_output', 'excel_data.json')
            excel_json_data = "generate_cp/json_output/excel_data.json"
            methodologies_df = enrich_assessment_dataframe_ka_descriptions(methods_df, excel_json_data)
            print(methodologies_df)
            if not methodologies_df.empty:
                sheet_xml_path = os.path.join(temp_dir, sheet_mapping["3 - Methodologies"])
                save_dataframe_to_excel(methodologies_df, "generate_cp/json_output/assessment_dataframe.xlsx")
                # For example, insert starting at row 18 and column 2 (B18)
                insert_dataframe_into_sheet(sheet_xml_path, start_row=7, start_col=10, df=methodologies_df)

                # Auto-set assessment validation in H14 based on unique assessment methods
                if "MOA" in methodologies_df.columns:
                    unique_methods = methodologies_df["MOA"].nunique()
                    has_mcq = methodologies_df["MOA"].str.contains("MCQ", case=False, na=False).any()

                    # If MCQ is used, need 3+ methods (MCQ + 2 others)
                    # Otherwise, need 2+ methods
                    required_count = 3 if has_mcq else 2

                    if unique_methods >= required_count:
                        validation_text = "Sufficient # of Mode(s) of Assessment Declared:\n Do note that MCQ can only be used as a supplementary method. If you have chosen MCQ as a mode of assessment, do ensure you have at least 2 other appropriate methods chosen."
                    else:
                        validation_text = "Insufficient # of Mode(s) of Assessment Declared:\n Do note that MCQ can only be used as a supplementary method. If you have chosen MCQ as a mode of assessment, do ensure you have at least 2 other appropriate methods chosen."

                    # Update cell H14 in "3 - Instructional Design" sheet
                    if "3 - Instructional Design" in sheet_mapping:
                        design_sheet_xml_path = os.path.join(temp_dir, sheet_mapping["3 - Instructional Design"])
                        update_cell_in_sheet(design_sheet_xml_path, "H14", validation_text)
                        print(f"Assessment validation set to: {'Sufficient' if unique_methods >= required_count else 'Insufficient'} ({unique_methods} unique methods)")
            else:
                print("Warning: DataFrame is empty. Nothing to insert.")
        else:
            print("Sheet '3 - Methodologies' not found. DataFrame not inserted.")

        # Insert the DataFrame into a designated sheet (e.g., "3 - Instructional Design")
        if "3 - Methodologies" in sheet_mapping:
            # Create the DataFrame using your helper function (provided separately)
            instructional_2_df = create_instructional_dataframe(ensemble_output)
            if not instructional_2_df.empty:
                sheet_xml_path = os.path.join(temp_dir, sheet_mapping["3 - Methodologies"])
                save_dataframe_to_excel(instructional_2_df, "generate_cp/json_output/instructional_methods_dataframe.xlsx")
                print(instructional_2_df)
                # For example, insert starting at row 18 and column 2 (B18)
                insert_dataframe_into_sheet(sheet_xml_path, start_row=7, start_col=2, df=instructional_2_df)
            else:
                print("Warning: DataFrame is empty. Nothing to insert.")
        else:
            print("Sheet '3 - Methodologies' not found. DataFrame not inserted.")

        # Insert the DataFrame into a designated sheet (e.g., "3 - Instructional Design")
        if "3 - Methodologies" in sheet_mapping:
            # ensemble_output_path = os.path.join('..', 'json_output', 'ensemble_output.json')
            # instructional_methods_path = os.path.join('..', 'json_output', 'instructional_methods.json')
            ensemble_output_path = "generate_cp/json_output/ensemble_output.json"
            instructional_methods_path = "generate_cp/json_output/im_agent_data.json"
            # Create the DataFrame using your helper function (provided separately)
            instructional_description_df = create_instruction_description_dataframe(ensemble_output_path, instructional_methods_path)
            print(instructional_description_df)
            if not instructional_description_df.empty:
                sheet_xml_path = os.path.join(temp_dir, sheet_mapping["3 - Methodologies"])
                save_dataframe_to_excel(instructional_description_df, "generate_cp/json_output/instructional_methods_description_dataframe.xlsx")
                # For example, insert starting at row 18 and column 2 (B18)
                insert_dataframe_into_sheet(sheet_xml_path, start_row=7, start_col=7, df=instructional_description_df)
            else:
                print("Warning: DataFrame is empty. Nothing to insert.")
        else:
            print("Sheet '3 - Methodologies' not found. DataFrame not inserted.")

        # Insert the DataFrame into a designated sheet (e.g., "3 - Instructional Design")
        if "3 - Summary" in sheet_mapping:

            instructional_description_df = create_instruction_description_dataframe(ensemble_output_path, instructional_methods_path)
            summary_df = create_summary_dataframe(instructional_df, instructional_2_df, methods_df)
            if not summary_df.empty:
                sheet_xml_path = os.path.join(temp_dir, sheet_mapping["3 - Summary"])
                save_dataframe_to_excel(summary_df, "generate_cp/json_output/summary_dataframe.xlsx")
                # For example, insert starting at row 18 and column 2 (B18)
                insert_dataframe_into_sheet(sheet_xml_path, start_row=7, start_col=2, df=summary_df)
                total_instructional_duration, total_assessment_duration, total_course_duration = compute_total_durations(summary_df)
                print(f"Total Instructional Duration: {total_instructional_duration}")
                print(f"Total Assessment Duration: {total_assessment_duration}")
                print(f"Total Course Duration: {total_course_duration}")
                print(summary_df)
                # Write the total durations to specific cells in the Summary sheet
                update_cell_in_sheet(sheet_xml_path, "G4", total_instructional_duration)
                update_cell_in_sheet(sheet_xml_path, "I4", total_assessment_duration) 
                update_cell_in_sheet(sheet_xml_path, "G3", total_course_duration)
                update_cell_in_sheet(sheet_xml_path, "K4", "Classroom Facilitated Training")
                update_cell_in_sheet(sheet_xml_path, "M4", total_instructional_duration)
            else:
                print("Warning: DataFrame is empty. Nothing to insert.")
        else:
            print("Sheet '3 - Methodologies' not found. DataFrame not inserted.")

        # Repackage the updated directory into a new .xlsx file
        with zipfile.ZipFile(output_excel_path, 'w', zipfile.ZIP_DEFLATED) as zout:
            for foldername, subfolders, filenames in os.walk(temp_dir):
                for filename in filenames:
                    file_path = os.path.join(foldername, filename)
                    arcname = os.path.relpath(file_path, temp_dir)
                    zout.write(file_path, arcname)
        print(f"Repackaged updated workbook to {output_excel_path}")

    finally:
        shutil.rmtree(temp_dir)

def load_json_file(filepath):
    try:
        with open(filepath, 'r', encoding='utf-8') as f:
            data = json.load(f)
            if data is None:
                print(f"Warning: {filepath} contains null data.")
                return {}
            return data
    except FileNotFoundError:
        print(f"Error: File not found: {filepath}")
        return {}
    except json.JSONDecodeError as e:
        print(f"Error: Invalid JSON in {filepath}: {e}")
        return {}

def get_relationship_mapping(rels_path):
    ns = {'r': 'http://schemas.openxmlformats.org/package/2006/relationships'}
    tree = ET.parse(rels_path)
    root = tree.getroot()
    rels = {}
    for rel in root.findall('r:Relationship', ns):
        rId = rel.attrib.get('Id')
        target = rel.attrib.get('Target')  # e.g., "worksheets/sheet1.xml"
        # Prepend "xl/" if needed
        rels[rId] = os.path.join('xl', target) if not target.startswith('/') else target[1:]
    return rels

def get_sheet_mapping(workbook_xml_path, rels_map):
    """
    Returns a mapping from sheet name to its full path (within the extracted directory)
    """
    ns = {'main': 'http://schemas.openxmlformats.org/spreadsheetml/2006/main',
          'r': 'http://schemas.openxmlformats.org/officeDocument/2006/relationships'}
    tree = ET.parse(workbook_xml_path)
    root = tree.getroot()
    mapping = {}
    for sheet in root.xpath('.//main:sheets/main:sheet', namespaces=ns):
        name = sheet.get('name')
        rId = sheet.get('{http://schemas.openxmlformats.org/officeDocument/2006/relationships}id')
        if rId in rels_map:
            mapping[name] = rels_map[rId]
    return mapping

def col_idx_to_letter(n):
    """Converts a 1-indexed column number to an Excel column letter."""
    result = ""
    while n:
        n, remainder = divmod(n - 1, 26)
        result = chr(65 + remainder) + result
    return result

def update_cell_in_sheet(sheet_xml_path, cell_ref, new_value):
    """Updates cell value in sheet XML (implementation from previous response remains the same)"""
    ns = {'main': 'http://schemas.openxmlformats.org/spreadsheetml/2006/main'}
    parser = ET.XMLParser(remove_blank_text=False)
    tree = ET.parse(sheet_xml_path, parser)
    root = tree.getroot()
    found = False

    # Flatten new_value if it's a list
    if isinstance(new_value, list):
        if len(new_value) == 1:
            new_value = new_value[0]
        else:
            new_value = "\n".join(map(str, new_value))

    # Find the <c> element with attribute r equal to cell_ref
    for cell in root.xpath('.//main:c[@r="%s"]' % cell_ref, namespaces=ns):
        # Skip cells that have a formula (we don’t want to overwrite them)
        if cell.xpath('main:f', namespaces=ns):
            print(f"Notice: Overwriting formula in cell {cell_ref}")


        # Remove any existing value elements (<v> or <is>)
        # for child in list(cell):
        #     if child.tag in {f"{{{ns['main']}}}v", f"{{{ns['main']}}}is"}:
        #         cell.remove(child)
        for child in list(cell):
            cell.remove(child)
        # Set type attribute to inline string
        cell.set('t', 'inlineStr')
        is_elem = ET.Element(f"{{{ns['main']}}}is")
        t_elem = ET.Element(f"{{{ns['main']}}}t")
        t_elem.text = str(new_value)
        is_elem.append(t_elem)
        cell.append(is_elem)
        found = True
        break

    if not found:
        print(f"Cell {cell_ref} not found in {sheet_xml_path}. Skipping.")
        return False

    tree.write(sheet_xml_path, encoding="UTF-8", xml_declaration=True, pretty_print=True)
    return True


def preserve_excel_metadata(template_path, modified_path, output_path):
    """Preserve metadata function remains the same as the previous response"""
    temp_template_dir = "temp_template"
    temp_modified_dir = "temp_modified"

    try:
        # 1. Unzip both files
        with zipfile.ZipFile(template_path, 'r') as template_zip:
            template_zip.extractall(temp_template_dir)
        with zipfile.ZipFile(modified_path, 'r') as modified_zip:
            modified_zip.extractall(temp_modified_dir)

        # 2. Copy missing files and folders (based on diff report - adapt as needed)
        files_to_copy = [
            "xl/calcChain.xml",
            "xl/comments",
            "xl/drawings/commentsDrawing1.vml", # Example - add all vmlDrawing files if needed
            "xl/drawings/commentsDrawing2.vml",
            "xl/drawings/commentsDrawing3.vml",
            "xl/drawings/commentsDrawing4.vml",
            "xl/drawings/commentsDrawing5.vml",
            "xl/drawings/commentsDrawing6.vml",
            "xl/drawings/commentsDrawing7.vml",
            "xl/drawings/commentsDrawing8.vml",
            "xl/drawings/commentsDrawing9.vml",
            "xl/drawings/commentsDrawing10.vml",
            "xl/metadata.xml",
            "xl/persons",
            "xl/printerSettings",
            "xl/richData",
            "xl/sharedStrings.xml",
            "customXml",
            "customXml/_rels"
        ]

        for item in files_to_copy:
            template_item_path = os.path.join(temp_template_dir, item)
            modified_item_path = os.path.join(temp_modified_dir, item)
            if os.path.exists(template_item_path):
                if os.path.isdir(template_item_path):
                    if os.path.exists(modified_item_path):
                        shutil.rmtree(modified_item_path) # remove existing dir to avoid issues
                    shutil.copytree(template_item_path, modified_item_path)
                else:
                    shutil.copy2(template_item_path, modified_item_path) # copy2 to preserve metadata

        # 3. Update relationship XMLs
        content_types_path_template = os.path.join(temp_template_dir, "[Content_Types].xml")
        content_types_path_modified = os.path.join(temp_modified_dir, "[Content_Types].xml")
        workbook_rels_path_template = os.path.join(temp_template_dir, "xl", "_rels", "workbook.xml.rels")
        workbook_rels_path_modified = os.path.join(temp_modified_dir, "xl", "_rels", "workbook.xml.rels")

        # Update [Content_Types].xml - Example, needs to be comprehensive based on diff report
        tree_content_types_template = ET.parse(content_types_path_template)
        root_content_types_template = tree_content_types_template.getroot()
        tree_content_types_modified = ET.parse(content_types_path_modified)
        root_content_types_modified = tree_content_types_modified.getroot()

        for element in root_content_types_template.findall("Override"): # Copy Override elements from template
            if not any(override.get('PartName') == element.get('PartName') for override in root_content_types_modified.findall("Override")): # Avoid duplicates
                root_content_types_modified.append(element)
        tree_content_types_modified.write(content_types_path_modified, xml_declaration=True, encoding='UTF-8', standalone=True)


        # Update xl/_rels/workbook.xml.rels - Example, needs to be comprehensive based on diff report
        tree_workbook_rels_template = ET.parse(workbook_rels_path_template)
        root_workbook_rels_template = tree_workbook_rels_template.getroot()
        tree_workbook_rels_modified = ET.parse(workbook_rels_path_modified)
        root_workbook_rels_modified = tree_workbook_rels_modified.getroot()

        for element in root_workbook_rels_template.findall("Relationship"): # Copy Relationship elements from template
             if not any(rel.get('Id') == element.get('Id') for rel in root_workbook_rels_modified.findall("Relationship")): # Avoid duplicates
                root_workbook_rels_modified.append(element)
        tree_workbook_rels_modified.write(workbook_rels_path_modified, xml_declaration=True, encoding='UTF-8', standalone=True)

        output_zip_path = output_path[:-5] + ".zip" # Path for the zip archive before renaming
        # Check if zip file already exists and remove it
        if os.path.exists(output_zip_path):
            try:
                os.remove(output_zip_path)
                print(f" попередній файл '{output_zip_path}' успішно видалено.")
            except OSError as e:
                print(f"Error deleting existing zip file '{output_zip_path}': {e}")
                raise # Re-raise the exception if deletion fails

        # 4. Re-zip to XLSX
        shutil.make_archive(output_path[:-5], 'zip', temp_modified_dir) # Create zip archive
        os.rename(output_path[:-5] + ".zip", output_path) # Rename to .xlsx

        print(f"Metadata preserved Excel file saved to: {output_path}")

    except Exception as e:
        print(f"Error preserving metadata: {e}")
    finally:
        # Cleanup temporary directories
        shutil.rmtree(temp_template_dir, ignore_errors=True)
        shutil.rmtree(temp_modified_dir, ignore_errors=True)


# if __name__ == "__main__":

#     map_new_key_names_excel()
#     json_data_path = os.path.join('..', 'json_output', 'generated_mapping.json')
#     excel_template_path = os.path.join('..', 'templates', 'CP_excel_template.xlsx')
#     output_excel_path_modified = os.path.join('..', 'output_docs', 'CP_template_updated_cells_output.xlsx') # Intermediate output after cell update
#     output_excel_path_preserved = os.path.join('..', 'output_docs', 'CP_template_metadata_preserved.xlsx') # Final output with metadata preserved
#     ensemble_output_path = os.path.join('..', 'json_output', 'ensemble_output.json')

#     # --- CALL CLEANUP FUNCTION HERE ---
#     output_excel_path_modified = os.path.join('..', 'output_docs', 'CP_template_updated_cells_output.xlsx') # Intermediate output after cell update
#     output_excel_path_preserved = os.path.join('..', 'output_docs', 'CP_template_metadata_preserved.xlsx') # Final output with metadata preserved
#     cleanup_old_files(output_excel_path_modified, output_excel_path_preserved)

#     # First, run the XML-based code to update cell values (output to _modified file)
#     process_excel_update(json_data_path, excel_template_path, output_excel_path_modified, ensemble_output_path)

#     # Then, preserve metadata, taking the modified file and template, and outputting the final, preserved file
#     preserve_excel_metadata(excel_template_path, output_excel_path_modified, output_excel_path_preserved)