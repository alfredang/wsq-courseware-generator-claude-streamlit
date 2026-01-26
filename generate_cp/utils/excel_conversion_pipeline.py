import json
import sys
import os
from generate_cp.utils.helpers import load_json_file, extract_lo_keys, recursive_get_keys
import pandas as pd
import re


def extract_and_concatenate_json_values(json_data, keys_to_extract, new_key_name):
    """
    Extracts values from JSON data based on keys, concatenates them into a string with newlines,
    and returns a dictionary containing the concatenated string under a new key.

    Args:
        json_data (dict): The JSON data as a dictionary.
        keys_to_extract (list of str): A list of keys to extract values from. Keys are used directly as in JSON.
        new_key_name (str): The name of the new key for the concatenated string in the output.

    Returns:
        dict: A dictionary containing the new key and the concatenated string, or None if input json_data is None.
    """
    if json_data is None:
        return None

    concatenated_string = ""
    for key_path in keys_to_extract:  # Iterate through keys as they are, NO parsing needed
        try:
            value = json_data.get(key_path)  # Use key_path directly as the JSON key

            if value is None:
                print(f"Warning: Key '{key_path}' not found in JSON data.")
                continue  # Skip to the next key if not found

            if isinstance(value, list):
                concatenated_string += "\n\n".join(map(str, value)) + "\n\n"  # Map to str to handle non-string list elements if any
            else:  # If value is not a list (e.g., string, number)
                concatenated_string += str(value) + "\n\n"  # Ensure it's a string

        except KeyError:
            print(f"Error: Key '{key_path}' not found in JSON data.")
        except TypeError as e:  # Handle cases where indexing might be attempted on non-list
            print(f"TypeError accessing key '{key_path}': {e}")

    output_data = {new_key_name: concatenated_string.rstrip('\n\n')}  # rstrip to remove trailing newline
    return output_data

def extract_and_concatenate_json_values_singlenewline(json_data, keys_to_extract, new_key_name):
    """
    Extracts values from JSON data based on keys, concatenates them into a string with newlines,
    and returns a dictionary containing the concatenated string under a new key.

    Args:
        json_data (dict): The JSON data as a dictionary.
        keys_to_extract (list of str): A list of keys to extract values from. Keys are used directly as in JSON.
        new_key_name (str): The name of the new key for the concatenated string in the output.

    Returns:
        dict: A dictionary containing the new key and the concatenated string, or None if input json_data is None.
    """
    if json_data is None:
        return None

    concatenated_string = ""
    for key_path in keys_to_extract:  # Iterate through keys as they are, NO parsing needed
        try:
            value = json_data.get(key_path)  # Use key_path directly as the JSON key

            if value is None:
                print(f"Warning: Key '{key_path}' not found in JSON data.")
                continue  # Skip to the next key if not found

            if isinstance(value, list):
                concatenated_string += "\n".join(map(str, value)) + "\n"  # Map to str to handle non-string list elements if any
            else:  # If value is not a list (e.g., string, number)
                concatenated_string += str(value) + "\n"  # Ensure it's a string

        except KeyError:
            print(f"Error: Key '{key_path}' not found in JSON data.")
        except TypeError as e:  # Handle cases where indexing might be attempted on non-list
            print(f"TypeError accessing key '{key_path}': {e}")

    output_data = {new_key_name: concatenated_string.rstrip('\n')}  # rstrip to remove trailing newline
    return output_data

def extract_and_concatenate_json_values_space_seperator(json_data, keys_to_extract, new_key_name):
    """
    Extracts values from JSON data based on keys, concatenates them into a string with spaces, THIS METHOD IS DIFFERENT FROM THE ONE WITH NO SPACES
    and returns a dictionary containing the concatenated string under a new key.

    Args:
        json_data (dict): The JSON data as a dictionary.
        keys_to_extract (list of str): A list of keys to extract values from. Keys are used directly as in JSON.
        new_key_name (str): The name of the new key for the concatenated string in the output.

    Returns:
        dict: A dictionary containing the new key and the concatenated string, or None if input json_data is None.
    """
    if json_data is None:
        return None

    concatenated_string = ""
    for key_path in keys_to_extract: # Iterate through keys as they are, NO parsing needed
        try:
            value = json_data.get(key_path) # Use key_path directly as the JSON key

            if value is None:
                print(f"Warning: Key '{key_path}' not found in JSON data.")
                continue # Skip to the next key if not found

            if isinstance(value, list):
                concatenated_string += " ".join(map(str, value)) + " " # Map to str to handle non-string list elements if any
            else: # If value is not a list (e.g., string, number)
                concatenated_string += str(value) + " " # Ensure it's a string

        except KeyError:
            print(f"Error: Key '{key_path}' not found in JSON data.")
        except TypeError as e: # Handle cases where indexing might be attempted on non-list
            print(f"TypeError accessing key '{key_path}': {e}")


    output_data = {new_key_name: concatenated_string} # rstrip to remove trailing newline
    return output_data

def write_json_file(data, output_file_path):
    """
    Writes JSON data to a file.

    Args:
        data (dict): The JSON data to write.
        output_file_path (str): The path to the output JSON file.
    """
    try:
        with open(output_file_path, 'w') as outfile:
            json.dump(data, outfile, indent=4)
        print(f"Successfully wrote data to '{output_file_path}'")
    except Exception as e:
        print(f"Error writing to '{output_file_path}': {e}")

def create_course_dataframe(json_data):
    """
    Creates a DataFrame from the provided JSON data, structured as requested.

    Args:
        json_data (dict): The JSON data containing course information.

    Returns:
        pandas.DataFrame: A DataFrame representing the course schema.
    """

    # Check if json_data is None or not a dict
    if json_data is None or not isinstance(json_data, dict):
        print("Warning: json_data is None or invalid in create_course_dataframe. Returning empty DataFrame.")
        return pd.DataFrame(columns=[
            "LU#", "Learning Unit Title", "LO#", "Learning Outcome",
            "Topic (T#: Topic title)", "Applicable K&A Statement", "Mode of Assessment"
        ])

    # Extract relevant data sections (with defaults for safety)
    tsc_and_topics = json_data.get("TSC and Topics", {}) or {}
    learning_outcomes_section = json_data.get("Learning Outcomes", {}) or {}
    assessment_methods_section = json_data.get("Assessment Methods", {}) or {}

    learning_units = tsc_and_topics.get("Learning Units", []) or []
    learning_outcomes = learning_outcomes_section.get("Learning Outcomes", []) or []
    knowledge_statements = learning_outcomes_section.get("Knowledge", []) or []
    ability_statements = learning_outcomes_section.get("Ability", []) or []
    course_outline = (assessment_methods_section.get("Course Outline", {}) or {}).get("Learning Units", {}) or {}
    tsc_codes = tsc_and_topics.get("TSC Code", ["N/A"]) or ["N/A"]
    tsc_code = tsc_codes[0] if tsc_codes else "N/A"
    assessment_methods = assessment_methods_section.get("Assessment Methods", []) or []

    # Initialize lists to hold the data for each row in the DataFrame
    data = []

    # Iterate through Learning Units (LU)
    for lu_index, lu_title in enumerate(learning_units):
        lu_num = f"LU{lu_index + 1}"  # LU1, LU2, etc.
        lu_title_only = lu_title.split(": ", 1)[1]  # Extract title after "LUx: "

        # Get Learning Outcome (LO) for the current LU
        lo_title = learning_outcomes[lu_index] if lu_index < len(learning_outcomes) else "N/A"
        lo_num = f"LO{lu_index + 1}"
        lo_title_only = lo_title.split(": ", 1)[1] if lo_title != "N/A" else "N/A" # Extract title after "LOx: "

        # Get Topics for the current LU from Course Outline
        lu_key = f"LU{lu_index + 1}"
        if lu_key in course_outline:
            topics = course_outline[lu_key].get("Description", [])
            for topic in topics:
                topic_title_full = topic.get("Topic", "N/A")
                topic_num = topic_title_full.split(":")[0].replace("Topic ", "T") # "Topic 1" -> "T1"
                topic_title = topic_title_full.split(': ', 1)[1]  # Get the title only, after the first ': '
                topic_title_short = topic_title.split(' (')[0]  # extract the topic title without KA

                # Extract K and A statements from the topic title
                ka_codes_str = topic_title_full.split('(')[-1].rstrip(')')  # Everything inside (...)
                ka_codes = [code.strip() for code in ka_codes_str.split(',')]

                if "Case Study" in assessment_methods:
                    moa = "Others: Case Study"
                elif "Role Play" in assessment_methods:
                    moa = "Role Play"
                else:
                    moa = "Practical Exam"
                
                if "Oral Questioning" in assessment_methods:
                    moa_k = "Oral Questioning"
                else:
                    moa_k = "Written Exam"                

                # Create rows for EACH K and A statement
                for code in ka_codes:
                    if code.startswith('K'):
                        k_index = int(code[1:]) - 1
                        # Correct K statement formatting:  Remove the duplicate "Kx: " prefix
                        k_statement = f"{knowledge_statements[k_index]} ({tsc_code})" if 0 <= k_index < len(knowledge_statements) else f"{code}: N/A ({tsc_code})"
                        data.append([
                            lu_num,
                            lu_title_only,
                            lo_num,
                            lo_title_only,
                            f"{topic_num}: {topic_title_short}",
                            k_statement,
                            # "Written Exam"  # Mode of Assessment for K
                            moa_k
                        ])
                    elif code.startswith('A'):
                        a_index = int(code[1:]) - 1
                        # Correct A statement formatting: Remove the duplicate "Ax: " prefix
                        a_statement = f"{ability_statements[a_index]} ({tsc_code})" if 0 <= a_index < len(ability_statements) else f"{code}: N/A ({tsc_code})"
                        data.append([
                            lu_num,
                            lu_title_only,
                            lo_num,
                            lo_title_only,
                            f"{topic_num}: {topic_title_short}",
                            a_statement,
                            # "Practical Exam"  # Mode of Assessment for A
                            moa
                        ])

    # Create the DataFrame
    df = pd.DataFrame(data, columns=[
        "LU#",
        "Learning Unit Title",
        "LO#",
        "Learning Outcome",
        "Topic (T#: Topic title)",
        "Applicable K&A Statement",
        "Mode of Assessment"
    ])

    return df

def combine_los_and_topics(ensemble_output):
    """
    Combines all Learning Outcomes (LOs) and Topics from the ensemble_output into a single string.

    Args:
        ensemble_output (dict): The ensemble output JSON data.

    Returns:
        str: A string containing the combined LOs and Topics, separated by newlines.
    """

    # Check if ensemble_output is None or not a dict
    if ensemble_output is None or not isinstance(ensemble_output, dict):
        print("Warning: ensemble_output is None or invalid in combine_los_and_topics. Returning empty string.")
        return ""

    # Safely access nested data
    learning_outcomes_section = ensemble_output.get("Learning Outcomes", {}) or {}
    assessment_methods_section = ensemble_output.get("Assessment Methods", {}) or {}

    # Extract Learning Outcomes
    learning_outcomes = learning_outcomes_section.get("Learning Outcomes", []) or []
    lo_string = "\n".join(learning_outcomes) + "\n\n" if learning_outcomes else ""

    # Extract Topics and their Details
    topics_string = ""
    course_outline_section = assessment_methods_section.get("Course Outline", {}) or {}
    course_outline = course_outline_section.get("Learning Units", {}) or {}

    for lu_key, lu_content in course_outline.items():
        if lu_content is None:
            continue
        descriptions = lu_content.get('Description', []) or []
        for description in descriptions:
            if description is None:
                continue
            topic_title = description.get('Topic', 'Unknown Topic')
            details = description.get('Details', []) or []

            topics_string += f"{topic_title}:\n"
            for detail in details:
                topics_string += f"•\t{detail}\n"
            topics_string += "\n"  # Add newline after each topic

    return lo_string + topics_string

def create_assessment_dataframe(json_data):
    """
    Creates a DataFrame for assessment output based on the provided JSON data,
    including assessment duration in minutes as integers.

    Args:
        json_data (dict): The JSON data containing course information.

    Returns:
        pandas.DataFrame: A DataFrame representing the assessment schema with integer duration.
    """

    # Check if json_data is None or not a dict
    if json_data is None or not isinstance(json_data, dict):
        print("Warning: json_data is None or invalid in create_assessment_dataframe. Returning empty DataFrame.")
        return pd.DataFrame(columns=["LO#", "MOA", "Assessment Duration", "Assessors", "Candidates", "KA"])

    # Safely get nested data with null checks
    assessment_methods_section = json_data.get("Assessment Methods", {}) or {}
    learning_outcomes_section = json_data.get("Learning Outcomes", {}) or {}
    tsc_and_topics = json_data.get("TSC and Topics", {}) or {}
    course_info = json_data.get("Course Information", {}) or {}

    # --- Assessment Duration Logic (from generate_assessment_output) ---
    assessment_methods_list = assessment_methods_section.get("Assessment Methods", []) or []

    assessment_method_abbreviations = {
        "Written Assessment": "WA-SAQ",
        "Practical Performance": "PP",
        "Case Study": "CS",
        "Oral Questioning": "OQ",
        "Role Play": "RP"
    }

    normalized_assessment_methods = [assessment_method_abbreviations.get(method, method) for method in assessment_methods_list]

    assessment_method_names = {
        "WA-SAQ": "Written Exam", # Changed to match desired MOA in dataframe
        "PP": "Practical Exam",    # Changed to match desired MOA in dataframe
        "CS": "Others: Case Study",
        "OQ": "Oral Questioning",
        "Written Assessment - Short-Answer Questions (WA-SAQ) - Individual, Summative, Open book": "Written Assessment - Short-Answer Questions",
        "RP": "Role Play"
    }

    num_assessment_hours = course_info.get("Number of Assessment Hours", 0) or 0
    total_assessment_minutes = num_assessment_hours * 60

    learning_units = tsc_and_topics.get("Learning Units", []) or []
    num_lus = len(learning_units)

    ka_mapping = learning_outcomes_section.get("Knowledge and Ability Mapping", {}) or {}
    lu_ka_mapping = {} # Create LU-based KA mapping
    for idx in range(num_lus):
        ka_key = f"KA{idx + 1}"
        if ka_key in ka_mapping:
            lu_ka_mapping[f"LU{idx+1}"] = ka_mapping[ka_key]

    lu_assessment_methods = {}
    methods_used = set()

    for i, lu in enumerate(learning_units):
        lu_key = f"LU{i+1}"
        lu_data_ka = lu_ka_mapping.get(lu_key, []) # Get KA for LU

        methods_in_lu = []
        k_codes_in_lu = [item for item in lu_data_ka if item.startswith('K')]
        a_codes_in_lu = [item for item in lu_data_ka if item.startswith('A')]

        if k_codes_in_lu:
            # For K factors, prioritize Oral Questioning if available, otherwise use WA-SAQ
            if "OQ" in normalized_assessment_methods:
                methods_in_lu.append('OQ')
            elif "WA-SAQ" in normalized_assessment_methods:
                methods_in_lu.append('WA-SAQ')
            elif "Written Assessment" in assessment_methods_list:
                methods_in_lu.append('Written Assessment') # Use full name

        if a_codes_in_lu:
            # For A factors, prioritize methods in this order: RP, CS, PP, OQ
            method_priority = ['RP', 'CS', 'PP', 'OQ']
            available_methods_for_a = [method for method in method_priority if method in normalized_assessment_methods]
            if available_methods_for_a:
                methods_in_lu.append(available_methods_for_a[0])

        lu_assessment_methods[lu_key] = methods_in_lu
        methods_used.update(methods_in_lu)

    num_methods_used = len(methods_used)
    method_total_duration = total_assessment_minutes // num_methods_used if num_methods_used > 0 else 0

    method_lu_map = {method: [] for method in methods_used}
    for lu_key, methods_in_lu in lu_assessment_methods.items():
        for method in methods_in_lu:
            method_lu_map[method].append(lu_key)

    method_durations_per_lu = {}
    for method, lus in method_lu_map.items():
        num_lus_using_method = len(lus)
        duration_per_lu = method_total_duration // num_lus_using_method if num_lus_using_method > 0 else 0
        for lu_key in lus:
            if lu_key not in method_durations_per_lu:
                method_durations_per_lu[lu_key] = {}
            method_durations_per_lu[lu_key][method] = duration_per_lu

    # --- DataFrame Creation Logic (modified to include duration as integer) ---
    learning_outcomes_list = learning_outcomes_section.get("Learning Outcomes", []) or []
    knowledge_statements = learning_outcomes_section.get("Knowledge", []) or []
    ability_statements = learning_outcomes_section.get("Ability", []) or []
    tsc_codes = tsc_and_topics.get("TSC Code", ["N/A"]) or ["N/A"]
    tsc_code = tsc_codes[0] if tsc_codes else "N/A"
    assessment_methods = assessment_methods_section.get("Assessment Methods", []) or []

    data = []

    for lo_index, lo_title in enumerate(learning_outcomes_list):
        lo_num = f"LO{lo_index + 1}"
        lu_num = f"LU{lo_index + 1}" # Assuming LO index corresponds to LU index

        ka_key = f"KA{lo_index + 1}"
        if ka_key in ka_mapping:
            ka_values = ka_mapping[ka_key]
            for code in ka_values:
                if code.startswith('K'):
                    k_index = int(code[1:]) - 1
                    k_statement = f"{knowledge_statements[k_index]} ({tsc_code})" if 0 <= k_index < len(knowledge_statements) else f"{code}: N/A ({tsc_code})"
                    
                    # For K factors: Use Oral Questioning if available, otherwise use Written Exam
                    if "Oral Questioning" in assessment_methods:
                        moa = "Oral Questioning"
                        duration_minutes = method_durations_per_lu.get(lu_num, {}).get('OQ', 0)
                    else:
                        moa = "Written Exam"
                        duration_minutes = method_durations_per_lu.get(lu_num, {}).get('WA-SAQ', 0)

                    data.append([
                        lo_num,
                        moa,
                        duration_minutes,
                        1,
                        20,
                        k_statement
                    ])

                elif code.startswith('A'):
                    a_index = int(code[1:]) - 1
                    a_statement = f"{ability_statements[a_index]} ({tsc_code})" if 0 <= a_index < len(ability_statements) else f"{code}: N/A ({tsc_code})"
                    
                    # For A factors: Prioritize in this order: Role Play, Case Study, Practical Exam
                    if "Role Play" in assessment_methods:
                        moa = "Role Play"
                        duration_minutes = method_durations_per_lu.get(lu_num, {}).get('RP', 0)
                    elif "Case Study" in assessment_methods:
                        moa = "Others: Case Study"
                        duration_minutes = method_durations_per_lu.get(lu_num, {}).get('CS', 0)
                    else:
                        moa = "Practical Exam"
                        duration_minutes = method_durations_per_lu.get(lu_num, {}).get('PP', 0)

                    data.append([
                        lo_num,
                        moa,
                        duration_minutes,
                        1,
                        20,
                        a_statement
                    ])

    df = pd.DataFrame(data, columns=[
        "LO#",
        "MOA",
        "Assessment Duration",
        "Assessors",
        "Candidates",
        "KA"
    ])

    # Round all durations to the nearest multiple of 5
    for idx in range(len(df)):
        current_duration = df.loc[idx, "Assessment Duration"]
        # Round to nearest multiple of 5
        rounded_duration = round(current_duration / 5) * 5
        df.loc[idx, "Assessment Duration"] = rounded_duration

    # Verify total assessment duration matches expected value
    total_assessment_minutes = num_assessment_hours * 60
    actual_assessment_minutes = df["Assessment Duration"].sum()
    
    if actual_assessment_minutes != total_assessment_minutes:
        print(f"Warning: Assessment duration discrepancy detected after rounding to multiples of 5!")
        print(f"Expected: {total_assessment_minutes} minutes, Actual: {actual_assessment_minutes} minutes")
        
        # Calculate adjustment needed (which should also be a multiple of 5)
        diff = total_assessment_minutes - actual_assessment_minutes
        
        # Find rows to adjust based on assessment type
        if diff > 0:  # Need to add minutes
            # Try to distribute extra minutes while maintaining multiples of 5
            remaining_diff = diff
            increment = 5
            
            # Prioritize adjusting assessment types in this order
            for assessment_type in ["Written Exam", "Practical Exam", "Others: Case Study", "Oral Questioning", "Role Play"]:
                type_rows = df[df["MOA"] == assessment_type].index.tolist()
                
                if not type_rows or remaining_diff <= 0:
                    continue
                    
                # Calculate how many 5-minute increments we need to distribute
                increments_to_add = remaining_diff // 5
                if increments_to_add == 0:
                    continue
                
                # Distribute 5-minute increments across rows of this type
                for i in range(min(increments_to_add, len(type_rows))):
                    df.loc[type_rows[i], "Assessment Duration"] += 5
                    remaining_diff -= 5
                
                if remaining_diff <= 0:
                    break
                    
        elif diff < 0:  # Need to subtract minutes
            # Try to distribute reduction while maintaining multiples of 5
            remaining_diff = abs(diff)
            decrement = 5
            
            # Prioritize reducing from the rows with the largest durations
            while remaining_diff > 0:
                # Get indices of rows with duration >= 10 (to avoid zeroing out any row)
                eligible_rows = df[df["Assessment Duration"] >= 10].index.tolist()
                
                if not eligible_rows:
                    break  # No more eligible rows to reduce
                
                # Sort by duration descending
                eligible_rows = sorted(eligible_rows, 
                                      key=lambda idx: df.loc[idx, "Assessment Duration"],
                                      reverse=True)
                
                # Subtract 5 minutes from the row with the largest duration
                df.loc[eligible_rows[0], "Assessment Duration"] -= 5
                remaining_diff -= 5
    
    # Verify again
    actual_assessment_minutes = df["Assessment Duration"].sum()
    print(f"Final assessment duration: {df['Assessment Duration'].sum()} minutes")
    print(f"All durations are multiples of 5: {all(d % 5 == 0 for d in df['Assessment Duration'])}")
    
    # If there's still a discrepancy, make one final adjustment to the largest duration
    if actual_assessment_minutes != total_assessment_minutes:
        diff = total_assessment_minutes - actual_assessment_minutes
        if abs(diff) < 5:  # Only fix if difference is small
            # Find the row with the largest duration
            max_idx = df["Assessment Duration"].idxmax()
            df.loc[max_idx, "Assessment Duration"] += diff
            print(f"Made final adjustment of {diff} minutes to reach exact total")

    return df

def enrich_assessment_dataframe_ka_descriptions(df, excel_data_json_path):
    """
    Enriches the 'KA' column of an assessment DataFrame with descriptions from excel_data.json.

    Args:
        df (pd.DataFrame): The assessment DataFrame created by create_assessment_dataframe.
        excel_data_json_path (str): Path to the excel_data.json file.

    Returns:
        pd.DataFrame: The DataFrame with enriched 'KA' column values.
    """
    try:
        with open(excel_data_json_path, 'r', encoding='utf-8') as f:
            excel_data = json.load(f)
    except FileNotFoundError:
        print(f"Error: excel_data.json file not found at: {excel_data_json_path}")
        return df  # Return original DataFrame if JSON not found

    # Safety check: ensure excel_data has at least 2 elements and index 1 is not None
    if not isinstance(excel_data, list) or len(excel_data) < 2:
        print(f"⚠️ Warning: excel_data is not a list or has less than 2 elements. Skipping KA enrichment.")
        return df

    if excel_data[1] is None:
        print(f"⚠️ Warning: excel_data[1] is None. Skipping KA enrichment.")
        return df

    ka_analysis_data = excel_data[1].get("KA_Analysis", {}) # Access KA_Analysis data

    enriched_ka_values = []
    for index, row in df.iterrows():
        ka_value = row['KA']
        ka_code_match = re.match(r'([KA]\d+):', ka_value) # Regex to extract KA code (e.g., K1, A2)

        if ka_code_match:
            ka_code = ka_code_match.group(1)
            ka_description = ka_analysis_data.get(ka_code, "Description not found") # Get description from JSON
            enriched_ka_value = f"{ka_description}\n{ka_value}" # Combine description and original KA value
        else:
            enriched_ka_value = ka_value # If KA code not found, keep original value

        enriched_ka_values.append(enriched_ka_value)

    df['KA'] = enriched_ka_values # Update the KA column with enriched values
    return df

# main function for this script
def map_new_key_names_excel(generated_mapping_path, generated_mapping, output_json_file, excel_data_path, ensemble_output):
    # generated_mapping_path = os.path.join('..', 'json_output', 'generated_mapping.json')
    # generated_mapping = load_json_file(generated_mapping_path)

    # output_json_file = os.path.join('..', 'json_output', 'generated_mapping.json')
    # excel_data_path = os.path.join('..', 'json_output', 'excel_data.json')

    # generated_mapping_path = "generate_cp/json_output/generated_mapping.json"
    # generated_mapping = load_json_file(generated_mapping_path)

    # output_json_file = "generate_cp/json_output/generated_mapping.json"
    # excel_data_path = "generate_cp/json_output/excel_data.json"
    excel_data = load_json_file(excel_data_path)

    # Check if excel_data loaded successfully
    if excel_data is None:
        print(f"Failed to load excel data from '{excel_data_path}', cannot proceed. Exiting.")
        return

    # Check if excel_data is a list and has at least one item
    if not isinstance(excel_data, list) or len(excel_data) == 0:
        print(f"Error: excel_data is not a valid list or is empty. Cannot proceed. Exiting.")
        return

    # Check if first item exists and has course_overview
    if excel_data[0] is None or not isinstance(excel_data[0], dict):
        print(f"Error: excel_data[0] is None or not a dictionary. Cannot proceed. Exiting.")
        return

    if "course_overview" not in excel_data[0]:
        print(f"Error: 'course_overview' not found in excel_data[0]. Cannot proceed. Exiting.")
        return

    # **Load existing JSON file first**
    existing_data = load_json_file(output_json_file) # Load existing data, returns {} if file not found or invalid JSON

    if existing_data is None: # Error loading existing data
        print("Failed to load existing output JSON, cannot append. Exiting.")
        return

    # sequencing rationale
    sequencing_keys = ["#Rationale[0]", "#Sequencing", "#Conclusion[0]"]
    sequencing_rationale_data = extract_and_concatenate_json_values(generated_mapping, sequencing_keys, "#Sequencing_rationale")

    # tcs code combined with skill name
    tcs_keys = ["#TCS[1]", "#TCS[0]"]
    tcs_code_skill_data = extract_and_concatenate_json_values_space_seperator(generated_mapping, tcs_keys, "#TCS_Code_Skill")

    combined_lo = ["#LO[0]", "#LO[1]", "#LO[2]", "#LO[3]", "#LO[4]", "#LO[5]", "#LO[6]", "#LO[7]"]
    lo_data = extract_and_concatenate_json_values_singlenewline(generated_mapping, combined_lo, "#Combined_LO")

    course_background = extract_and_concatenate_json_values(
        excel_data[0]["course_overview"],
        ["course_description"],
        "#Course_Background1",
    )

    print(f"COURSE BACKGROUND:{course_background}" )

    # include declarations mapping, standard Not Applicable, and We Agree (do this in the excel template bah)
    # improve formatting of sequencing rationale
    # course type should be WSQ Course Accreditation Singular (as the standard)
    # course outline should be all the LOs on top first, then the topics (without the A and K factors)
    # course_outline_keys = recursive_get_keys(generated_mapping, "#Topics[")
    # print(course_outline_keys)
    # course_outline = extract_and_concatenate_json_values(generated_mapping, course_outline_keys, "#Course_Outline")

    course_outline = combine_los_and_topics(ensemble_output)
    # Wrap the course_outline string in a dictionary
    course_outline_data = {"#Course_Outline": course_outline}

    if sequencing_rationale_data and tcs_code_skill_data: # Check if both data extractions were successful
        # **Update the existing data dictionary**
        existing_data.update(sequencing_rationale_data)
        existing_data.update(tcs_code_skill_data)
        existing_data.update(lo_data)
        existing_data.update(course_outline_data)
        existing_data.update(course_background)

        # **Write the updated dictionary back to the output file**
        write_json_file(existing_data, output_json_file)
    else:
        print("Error during data extraction, not writing to output file.")

def create_instructional_dataframe(json_data):
    """
    Creates a DataFrame for instructional methods and durations, ensuring total duration
    matches "Course Duration" - "Assessment Hours" and all durations are in multiples of 5.
    Treats all instructional methods equally with no special handling for practical hours.

    Args:
        json_data (dict): The JSON data containing course information.

    Returns:
        pandas.DataFrame: A DataFrame representing the instructional schema with durations in multiples of 5.
    """

    # Check if json_data is None or not a dict
    if json_data is None or not isinstance(json_data, dict):
        print("Warning: json_data is None or invalid in create_instructional_dataframe. Returning empty DataFrame.")
        return pd.DataFrame(columns=["LU#", "Instructional Methods", "Instructional Duration", "MOT"])

    # Safely access nested data
    course_info = json_data.get("Course Information", {}) or {}
    tsc_and_topics = json_data.get("TSC and Topics", {}) or {}
    assessment_methods_section = json_data.get("Assessment Methods", {}) or {}
    learning_outcomes_section = json_data.get("Learning Outcomes", {}) or {}

    learning_units = tsc_and_topics.get("Learning Units", []) or []
    instructional_methods_input = assessment_methods_section.get("Instructional Methods", "") or ""
    ka_mapping = learning_outcomes_section.get("Knowledge and Ability Mapping", {}) or {}
    
    # We'll use the total instructional time from course duration minus assessment hours
    assessment_hours = course_info.get("Number of Assessment Hours", 0)
    course_duration_hours = course_info.get("Course Duration (Number of Hours)", 0)

    # Calculate total instructional hours
    total_instructional_hours = course_duration_hours - assessment_hours
    total_instructional_minutes = total_instructional_hours * 60
    
    # Round to nearest multiple of 5
    total_instructional_minutes = round(total_instructional_minutes / 5) * 5

    if isinstance(instructional_methods_input, str):
        instructional_methods_list = [method.strip() for method in instructional_methods_input.split(',')]
    elif isinstance(instructional_methods_input, list):
        instructional_methods_list = [method.strip() for method in instructional_methods_input]
    else:
        print(f"Warning: Unexpected type for 'Instructional Methods': {type(instructional_methods_input)}. Defaulting to empty list.")
        instructional_methods_list = []

    lu_ka_mapping = {}
    for idx in range(len(learning_units)):
        ka_key = f"KA{idx + 1}"
        if ka_key in ka_mapping:
            lu_ka_mapping[f"LU{idx+1}"] = ka_mapping[ka_key]

    data = []
    total_rows = 0

    for lu_index, lu_title in enumerate(learning_units):
        lu_num = f"LU{lu_index + 1}"
        ka_values = lu_ka_mapping.get(lu_num, [])
        k_codes_in_lu = [item for item in ka_values if item.startswith('K')]
        a_codes_in_lu = [item for item in ka_values if item.startswith('A')]

        if k_codes_in_lu and not a_codes_in_lu: # Only K factors
            data.append([lu_num, "Classroom", 0, "Classroom Facilitated Training"]) # Initial duration 0
            total_rows += 1
        elif k_codes_in_lu and a_codes_in_lu or not k_codes_in_lu and a_codes_in_lu: # Both K and A or only A factors
            for method in instructional_methods_list:
                data.append([lu_num, method.strip(), 0, "Classroom Facilitated Training"]) # Initial duration 0
                total_rows += 1

    df = pd.DataFrame(data, columns=["LU#", "Instructional Methods", "Instructional Duration", "MOT"])

    # Calculate duration per row (evenly distributed)
    if total_rows > 0:
        base_duration_per_row = total_instructional_minutes // total_rows
        # Round to multiple of 5
        base_duration_per_row = (base_duration_per_row // 5) * 5
        
        # Calculate remainder to distribute
        remaining_minutes = total_instructional_minutes - (base_duration_per_row * total_rows)
        
        # Assign base duration to all rows
        df["Instructional Duration"] = base_duration_per_row
        
        # Distribute remaining minutes in increments of 5
        remaining_to_distribute = remaining_minutes
        row_index = 0
        
        while remaining_to_distribute >= 5 and row_index < len(df):
            df.loc[row_index, "Instructional Duration"] += 5
            remaining_to_distribute -= 5
            row_index += 1
    
    # Final verification
    total_actual_minutes = df["Instructional Duration"].sum()
    
    # If there's a discrepancy with total instructional minutes, make adjustments
    if total_actual_minutes != total_instructional_minutes:
        diff = total_instructional_minutes - total_actual_minutes
        print(f"Final adjustment of {diff} minutes needed to match total instructional time")
        
        # Only apply adjustment if it's small (less than 5 minutes per row)
        if abs(diff) <= len(df) * 5:
            # Distribute the difference as evenly as possible
            indices = df.index.tolist()
            remaining_diff = diff
            
            # Sort by duration (largest first for subtraction, smallest first for addition)
            if diff < 0:
                indices = sorted(indices, 
                               key=lambda idx: df.loc[idx, "Instructional Duration"],
                               reverse=True)
            else:
                indices = sorted(indices, 
                               key=lambda idx: df.loc[idx, "Instructional Duration"])
                
            # Apply adjustment in multiples of 5
            adjustment_per_row = 5 if diff > 0 else -5
            for idx in indices:
                if abs(remaining_diff) >= 5 and (df.loc[idx, "Instructional Duration"] + adjustment_per_row) >= 0:
                    df.loc[idx, "Instructional Duration"] += adjustment_per_row
                    remaining_diff -= adjustment_per_row
                if abs(remaining_diff) < 5:
                    break
        
    # Final verification
    print(f"Final total instructional duration: {df['Instructional Duration'].sum()} minutes")
    
    # Check if all durations are multiples of 5
    all_multiples_of_5 = all(duration % 5 == 0 for duration in df["Instructional Duration"])
    print(f"All durations are multiples of 5: {all_multiples_of_5}")

    return df

def create_instruction_description_dataframe(ensemble_json_path, im_agent_json_path):
    """
    Creates a DataFrame mapping instructional methods to their descriptions from im_agent_data.json.

    Args:
        ensemble_json_path (str): Path to the ensemble_output.json file.
        im_agent_json_path (str): Path to the im_agent_data.json file.

    Returns:
        pandas.DataFrame: A DataFrame with "Instructional Method" and "Description" columns.
                         Returns an empty DataFrame if there's an error loading the JSON files.
    """
    try:
        with open(ensemble_json_path, 'r', encoding='utf-8') as f_ensemble:
            ensemble_data = json.load(f_ensemble)
        with open(im_agent_json_path, 'r', encoding='utf-8') as f_im_agent:
            im_agent_data = json.load(f_im_agent)
    except FileNotFoundError as e:
        print(f"Error: One or both JSON files not found. {e}")
        return pd.DataFrame()  # Return empty DataFrame in case of file error
    except json.JSONDecodeError as e:
        print(f"Error: Invalid JSON in one of the files. {e}")
        return pd.DataFrame()  # Return empty DataFrame for invalid JSON

    instructional_methods_input = ensemble_data.get("Assessment Methods", {}).get("Instructional Methods", [])

    if isinstance(instructional_methods_input, str):
        instructional_methods_list = [method.strip() for method in instructional_methods_input.split(',')]
    elif isinstance(instructional_methods_input, list):
        instructional_methods_list = [method.strip() for method in instructional_methods_input]
    else:
        print(f"Warning: Unexpected type for 'Instructional Methods' in ensemble_output.json: {type(instructional_methods_input)}. Defaulting to empty list.")
        instructional_methods_list = []

    # Extract method descriptions from im_agent_data.json structure
    methods_description_map = {}
    # Handle case where im_agent_data is None
    if im_agent_data is None:
        print("Warning: im_agent_data is None. Using empty instructional methods data.")
        instructional_methods_data = {}
    else:
        instructional_methods_data = im_agent_data.get("Instructional_Methods", {})
    
    # Process each method entry in the Instructional_Methods dictionary
    for method_name, description in instructional_methods_data.items():
        if description:
            methods_description_map[method_name] = description

    data = []
    for method in instructional_methods_list:
        # Extract the base method name without duration (e.g., "Classroom: 7 hrs" -> "Classroom")
        base_method = method.split(":")[0].strip()
        
        # Look for the most closely matching key in methods_description_map
        matching_key = None
        for key in methods_description_map.keys():
            if key.lower() in base_method.lower() or base_method.lower() in key.lower():
                matching_key = key
                break
        
        # If no match found, check if the exact method exists
        if matching_key is None and base_method in methods_description_map:
            matching_key = base_method
        
        # Get description for the method
        description = methods_description_map.get(matching_key, "Description not found.")
        
        data.append([method, description])

    df = pd.DataFrame(data, columns=["Instructional Method", "Description"])
    return df


def create_summary_dataframe(course_df, instructional_df, assessment_df):
    """
    Derives a summary dataframe from supporting dataframes:
      - course_df: contains LU, LO, topics, and applicable K&A statements
      - instructional_df: contains instructional methods, their durations, and mode of training (MOT)
      - assessment_df: contains assessment modes, duration, assessor-to-candidate info, and LO#
      
    Returns a dataframe with the following columns:
      LU#, Learning Unit Title, Learning Outcome(s), Topic(s),
      Instructional Methods (modes of training, duration in minutes),
      Instructional Duration (in minutes),
      Modes of Assessment (Assessor-to-candidate Ratio, duration in minutes),
      Assessment Duration (in minutes)
    """
    
    # --- Process Course DataFrame ---
    def extract_codes(statements_series):
        """
        Given a series of "Applicable K&A Statement" strings,
        extract and return a list of KA codes (e.g., A1, K1) in order of appearance.
        """
        codes = []
        for text in statements_series:
            m = re.match(r"^(A\d+|K\d+):", text.strip())
            if m:
                codes.append(m.group(1))
        # Deduplicate while preserving order.
        seen = set()
        codes_unique = []
        for code in codes:
            if code not in seen:
                codes_unique.append(code)
                seen.add(code)
        return codes_unique

    # Group by LU# and aggregate relevant fields.
    course_agg = course_df.groupby("LU#").agg({
        "Learning Unit Title": "first",
        "LO#": "first",  # Assuming all rows for a given LU share the same LO#
        "Learning Outcome": "first",
        "Topic (T#: Topic title)": lambda x: "\n".join(["- " + str(item) for item in x]),
        "Applicable K&A Statement": lambda x: extract_codes(x)
    }).reset_index()

    # Create the formatted Learning Outcome(s) column.
    course_agg["Learning Outcome(s)"] = course_agg.apply(
        lambda row: f"{row['LO#']}: {row['Learning Outcome']} ({', '.join(row['Applicable K&A Statement'])})",
        axis=1
    )
    # Rename topics column to "Topic(s)" for clarity.
    course_agg.rename(columns={"Topic (T#: Topic title)": "Topic(s)"}, inplace=True)

    # --- Process Instructional Methods DataFrame ---
    # For each LU, concatenate each instructional method row into a string and sum durations.
    instr_agg = instructional_df.groupby("LU#").apply(lambda g: pd.Series({
        "Instructional Methods (modes of training, duration in minutes)":
            "\n".join([f"- {row['Instructional Methods']} ({row['MOT']}: {row['Instructional Duration']})"
                       for _, row in g.iterrows()]),
        "Instructional Duration (in minutes)": g["Instructional Duration"].sum()
    })).reset_index()

    # --- Process Assessment DataFrame ---
    # Normalize the LU# key using regex so that, for example, "LO04" becomes "LU4"
    assessment_df = assessment_df.copy()
    assessment_df["LU#"] = assessment_df["LO#"].apply(
        lambda x: re.sub(r'^LO0*', 'LU', x) if isinstance(x, str) else x
    )

    def agg_assessment(g):
        """
        For each group (LU), create a string of assessment modes.
        Each line is formatted as: "- MOA (Assessors:Candidates, Assessment Duration)"
        """
        lines = []
        for _, row in g.iterrows():
            ratio = f"{row['Assessors']}:{row['Candidates']}"
            lines.append(f"- {row['MOA']} ({ratio}, {row['Assessment Duration']})")
        return "\n".join(lines)

    assess_agg = assessment_df.groupby("LU#").apply(lambda g: pd.Series({
        "Modes of Assessment (Assessor-to-candidate Ratio, duration in minutes)": agg_assessment(g),
        "Assessment Duration (in minutes)": g["Assessment Duration"].sum()
    })).reset_index()

    # --- Merge Aggregated Data ---
    summary_df = course_agg[["LU#", "Learning Unit Title", "Learning Outcome(s)", "Topic(s)"]].merge(
        instr_agg, on="LU#", how="left"
    ).merge(
        assess_agg, on="LU#", how="left"
    )

    # --- Order Columns as Specified ---
    summary_df = summary_df[[
        "LU#",
        "Learning Unit Title",
        "Learning Outcome(s)",
        "Topic(s)",
        "Instructional Methods (modes of training, duration in minutes)",
        "Instructional Duration (in minutes)",
        "Modes of Assessment (Assessor-to-candidate Ratio, duration in minutes)",
        "Assessment Duration (in minutes)"
    ]]

    return summary_df

