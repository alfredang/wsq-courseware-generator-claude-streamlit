import json
import re
import sys
import os

def validate_knowledge_and_ability():
    try:
        # Read data from the JSON file
        with open('generate_cp/json_output/ensemble_output.json', 'r', encoding='utf-8') as file:
            data = json.load(file)

        # Check if data is valid
        if data is None or not isinstance(data, dict):
            error_message = "ERROR: ensemble_output.json contains null or invalid data"
            print(error_message)
            sys.exit(error_message)

        # Extract Knowledge and Ability factors from the data
        knowledge_factors = set([k.split(":")[0].strip() for k in data['Learning Outcomes']['Knowledge']])
        ability_factors = set([a.split(":")[0].strip() for a in data['Learning Outcomes']['Ability']])

        # Extract topics and their factors
        topics = data['TSC and Topics']['Topics']
        topic_factors = []

        # Collect all K and A factors present in topics
        extra_factors = set()
        for topic in topics:
            # Extract K and A factors from the topic (assuming it's in the form of 'K[number], A[number]')
            factors = re.findall(r'(K\d+|A\d+)', topic)
            topic_factors.append(set(factors))

            # Check for extra factors (those not in Knowledge or Ability)
            for factor in factors:
                if factor not in knowledge_factors and factor not in ability_factors:
                    extra_factors.add(factor)

        # Validate that each Knowledge and Ability factor is accounted for by at least one topic
        all_factors_accounted_for = True
        missing_factors = []

        # Check each Knowledge factor
        for k in knowledge_factors:
            if not any(k in topic for topic in topic_factors):
                missing_factors.append(f"Knowledge factor {k} is missing from topics")
                all_factors_accounted_for = False

        # Check each Ability factor
        for a in ability_factors:
            if not any(a in topic for topic in topic_factors):
                missing_factors.append(f"Ability factor {a} is missing from topics")
                all_factors_accounted_for = False

        # Handle extra factors (those not in Knowledge or Ability)
        if extra_factors:
            all_factors_accounted_for = False
            for extra in extra_factors:
                missing_factors.append(f"Extra factor {extra} found in topics but not in Knowledge or Ability list")

        # Print the custom error message if any factors are missing, else print success
        if not all_factors_accounted_for:
            error_message = "FAIL: " + "; ".join(missing_factors)
            print(error_message)
            sys.exit(error_message)  # Terminate the script with error code
        else:
            print("SUCCESS")

    except Exception as e:
        # Catch any unforeseen errors and print a custom error message before exiting
        error_message = f"ERROR: {str(e)}"
        print(error_message)
        sys.exit(error_message)


def extract_final_aggregator_json(file_path: str = "group_chat_state.json"):
    """
    Reads the specified JSON file (default: 'group_chat_state.json'),
    finds the aggregator agent's final response, and extracts the
    substring from the first '{' to the last '}'.
    
    Attempts to parse the extracted substring as JSON, returning
    a Python dictionary. If parsing fails or if no final message
    is found, returns None.
    """
    with open(file_path, "r", encoding="utf-8") as f:
        data = json.load(f)

    # 1. Identify the aggregator key (can be "aggregator" or "aggregator/...")
    aggregator_key = None
    for key in data["agent_states"]:
        if key.startswith("aggregator"):
            aggregator_key = key
            break

    if not aggregator_key:
        print("No aggregator key found in agent_states.")
        return None

    # 2. Get the aggregator agent state and retrieve the final message
    aggregator_state = data["agent_states"][aggregator_key]
    messages = aggregator_state["agent_state"]["llm_context"]["messages"]
    if not messages:
        print("No messages found under aggregator agent state.")
        return None

    final_message = messages[-1].get("content", "")
    if not final_message:
        print("Final aggregator message is empty.")
        return None

    # 3. Extract the substring from the first '{' to the last '}'
    start_index = final_message.find("{")
    end_index = final_message.rfind("}")
    if start_index == -1 or end_index == -1:
        print("No JSON braces found in the final aggregator message.")
        return None

    json_str = final_message[start_index:end_index + 1].strip()

    # 4. Parse the extracted substring as JSON
    try:
        return json.loads(json_str)
    except json.JSONDecodeError:
        print("Failed to parse aggregator content as valid JSON.")
        return None

def extract_final_editor_json(file_path: str = "research_group_chat_state.json"):
    """
    Reads the specified JSON file (default: 'research_group_chat_state.json'),
    finds the editor agent's final response, and extracts the
    substring from the first '{' to the last '}'.
    
    Attempts to parse the extracted substring as JSON, returning
    a Python dictionary. If parsing fails or if no final message
    is found, returns None.
    """
    with open(file_path, "r", encoding="utf-8") as f:
        data = json.load(f)

    # 1. Identify the editor key (can be "editor" or "editor/...")
    editor_key = None
    for key in data["agent_states"]:
        if key.startswith("editor"):
            editor_key = key
            break

    if not editor_key:
        print("No editor key found in agent_states.")
        return None

    # 2. Get the aggregator agent state and retrieve the final message
    aggregator_state = data["agent_states"][editor_key]
    messages = aggregator_state["agent_state"]["llm_context"]["messages"]
    if not messages:
        print("No messages found under editor agent state.")
        return None

    final_message = messages[-1].get("content", "")
    if not final_message:
        print("Final editor message is empty.")
        return None

    # 3. Extract the substring from the first '{' to the last '}'
    start_index = final_message.find("{")
    end_index = final_message.rfind("}")
    if start_index == -1 or end_index == -1:
        print("No JSON braces found in the final aggregator message.")
        return None

    json_str = final_message[start_index:end_index + 1].strip()

    # 4. Parse the extracted substring as JSON
    try:
        return json.loads(json_str)
    except json.JSONDecodeError:
        print("Failed to parse editor content as valid JSON.")
        return None

def rename_keys_in_json_file(filename):
    key_mapping = {
    "course_info": "Course Information",
    "learning_outcomes": "Learning Outcomes",
    "tsc_and_topics": "TSC and Topics",
    "assessment_methods": "Assessment Methods"
    }
    # Load the JSON data from the file
    with open(filename, 'r', encoding='utf-8') as file:
        data = json.load(file)

    # Check if data is None or not a dictionary
    if data is None or not isinstance(data, dict):
        print(f"Warning: {filename} contains null or invalid data. Skipping key renaming.")
        return

    # Rename keys according to the key_mapping
    for old_key, new_key in key_mapping.items():
        if old_key in data:
            data[new_key] = data.pop(old_key)

    # Save the updated JSON data back to the same file
    with open(filename, 'w', encoding='utf-8') as file:
        json.dump(data, file, indent=4)

    print(f"Updated JSON saved to {filename}")

def update_knowledge_ability_mapping(tsc_json_path, ensemble_output_json_path):
    # Load the JSON files
    with open(tsc_json_path, 'r', encoding='utf-8') as tsc_file:
        tsc_data = json.load(tsc_file)

    with open(ensemble_output_json_path, 'r', encoding='utf-8') as ensemble_file:
        ensemble_data = json.load(ensemble_file)

    # Check if data is valid
    if tsc_data is None or not isinstance(tsc_data, dict):
        print(f"Warning: {tsc_json_path} contains null or invalid data. Cannot update mapping.")
        return

    if ensemble_data is None or not isinstance(ensemble_data, dict):
        print(f"Warning: {ensemble_output_json_path} contains null or invalid data. Cannot update mapping.")
        return

    # Extract the learning units from output_TSC
    course_proposal_form = tsc_data.get("Course_Proposal_Form", {})
    learning_units = {key: value for key, value in course_proposal_form.items() if key.startswith("LU")}

    # Check if Learning Outcomes is a dict (not a list)
    if not isinstance(ensemble_data.get("Learning Outcomes"), dict):
        print(f"Error: Learning Outcomes is not a dictionary. Cannot update mapping.")
        return

    # Prepare the Knowledge and Ability Mapping structure in ensemble_output if it does not exist
    if "Knowledge and Ability Mapping" not in ensemble_data["Learning Outcomes"]:
        ensemble_data["Learning Outcomes"]["Knowledge and Ability Mapping"] = {}

    # Loop through each Learning Unit to extract and map K and A factors
    for index, (lu_key, topics) in enumerate(learning_units.items(), start=1):
        ka_key = f"KA{index}"
        ka_mapping = []

        # Extract K and A factors from each topic within the Learning Unit
        for topic in topics:
            # Match K and A factors in the topic string using regex
            matches = re.findall(r'\b(K\d+|A\d+)\b', topic)
            if matches:
                ka_mapping.extend(matches)

        # Ensure only unique K and A factors are added
        ka_mapping = list(dict.fromkeys(ka_mapping))  # Remove duplicates while preserving order

        # Add the KA mapping to the ensemble_data
        ensemble_data["Learning Outcomes"]["Knowledge and Ability Mapping"][ka_key] = ka_mapping

    # Save the updated JSON to the same file path
    with open(ensemble_output_json_path, 'w', encoding='utf-8') as outfile:
        json.dump(ensemble_data, outfile, indent=4, ensure_ascii=False)

    print(f"Updated Knowledge and Ability Mapping saved to {ensemble_output_json_path}")

def extract_final_agent_json(file_path: str = "assessment_justification_agent_state.json"):
    """
    Reads the specified JSON file (default: 'assessment_justification_agent_state.json'),
    finds the editor agent's final response, and extracts the
    substring from the first '{' to the last '}'.
    
    Attempts to parse the extracted substring as JSON, returning
    a Python dictionary. If parsing fails or if no final message
    is found, returns None.
    """
    with open(file_path, "r", encoding="utf-8") as f:
        data = json.load(f)

    # 1. Identify the assessment_justification_agent key (can be with or without "/")
    editor_key = None
    for key in data["agent_states"]:
        if key.startswith("assessment_justification_agent"):
            editor_key = key
            break

    if not editor_key:
        print("No assessment_justification_agent key found in agent_states.")
        return None

    # 2. Get the aggregator agent state and retrieve the final message
    aggregator_state = data["agent_states"][editor_key]
    messages = aggregator_state["agent_state"]["llm_context"]["messages"]
    if not messages:
        print("No messages found under assessment_justification_agent agent state.")
        return None

    final_message = messages[-1].get("content", "")
    if not final_message:
        print("Final editor message is empty.")
        return None

    # 3. Extract the substring from the first '{' to the last '}'
    start_index = final_message.find("{")
    end_index = final_message.rfind("}")
    if start_index == -1 or end_index == -1:
        print("No JSON braces found in the final aggregator message.")
        return None

    json_str = final_message[start_index:end_index + 1].strip()

    # 4. Parse the extracted substring as JSON
    try:
        return json.loads(json_str)
    except json.JSONDecodeError:
        print("Failed to parse editor content as valid JSON.")
        return None

def extract_tsc_agent_json(file_path: str = "tsc_agent_state.json"):
    """
    Reads the specified JSON file (default: 'tsc_agent_state.json'),
    finds the editor agent's final response, and extracts the
    substring from the first '{' to the last '}'.

    Attempts to parse the extracted substring as JSON, returning
    a Python dictionary. If parsing fails or if no final message
    is found, returns None.
    """
    with open(file_path, "r", encoding="utf-8") as f:
        data = json.load(f)

    # 1. Identify the tsc_agent key (can be "tsc_agent" or "tsc_agent/...")
    editor_key = None
    for key in data["agent_states"]:
        if key.startswith("tsc_agent"):
            editor_key = key
            break

    if not editor_key:
        print("No tsc_agent key found in agent_states.")
        return None

    # 2. Get the aggregator agent state and retrieve the final message
    aggregator_state = data["agent_states"][editor_key]
    messages = aggregator_state["agent_state"]["llm_context"]["messages"]
    if not messages:
        print("No messages found under tsc_agent_state.")
        return None

    final_message = messages[-1].get("content", "")
    if not final_message:
        print("Final tsc_agent message is empty.")
        return None

    # 3. Extract the substring from the first '{' to the last '}'
    start_index = final_message.find("{")
    end_index = final_message.rfind("}")
    if start_index == -1 or end_index == -1:
        print("No JSON braces found in the final aggregator message.")
        return None

    json_str = final_message[start_index:end_index + 1].strip()

    # 4. Parse the extracted substring as JSON
    try:
        return json.loads(json_str)
    except json.JSONDecodeError:
        print("Failed to parse editor content as valid JSON.")
        return None


# Function to recursively flatten lists within the JSON structure
def flatten_json(obj):
    if isinstance(obj, dict):
        # Recursively apply to dictionary values
        return {k: flatten_json(v) for k, v in obj.items()}
    elif isinstance(obj, list):
        # Flatten the list and apply to each element in the list
        return flatten_list(obj)
    else:
        return obj

# Function to flatten any nested list
def flatten_list(nested_list):
    flat_list = []
    for item in nested_list:
        if isinstance(item, list):
            flat_list.extend(flatten_list(item))  # Recursively flatten any nested lists
        else:
            flat_list.append(item)
    return flat_list

import json

def append_validation_output(
    ensemble_output_path: str = "ensemble_output.json",
    validation_output_path: str = "validation_output.json",
    analyst_responses: list = None
):
    """
    Reads data from `ensemble_output.json` and appends the new course information 
    into `validation_output.json`. If `validation_output.json` already exists, 
    it will append the new course data instead of overwriting it.

    Additionally, it allows appending `analyst_responses` as a list of dictionaries 
    containing responses about industry performance gaps and course impact.

    Structure:
    {
        "course_info": { Course Title, Industry, Learning Outcomes, TSC Title, TSC Code },
        "analyst_responses": [ {...}, {...} ]  # List of analyst responses
    }
    """

    # Load the existing data if the file exists, otherwise start fresh
    if os.path.exists(validation_output_path):
        with open(validation_output_path, "r", encoding="utf-8") as f:
            try:
                existing_data = json.load(f)
            except json.JSONDecodeError:
                existing_data = {}
    else:
        existing_data = {}

    # Load ensemble_output.json
    with open(ensemble_output_path, "r", encoding="utf-8") as f:
        ensemble_data = json.load(f)

    # Check if ensemble_data is valid
    if ensemble_data is None or not isinstance(ensemble_data, dict):
        print(f"Warning: {ensemble_output_path} contains null or invalid data. Cannot append validation output.")
        return

    # Extract required fields
    course_title = ensemble_data.get("Course Information", {}).get("Course Title", "")
    industry = ensemble_data.get("Course Information", {}).get("Industry", "")
    learning_outcomes = ensemble_data.get("Learning Outcomes", {}).get("Learning Outcomes", [])
    
    # Extract TSC Title and TSC Code (first element if list exists)
    tsc_titles = ensemble_data.get("TSC and Topics", {}).get("TSC Title", [])
    tsc_codes = ensemble_data.get("TSC and Topics", {}).get("TSC Code", [])

    tsc_title = tsc_titles[0] if tsc_titles else ""
    tsc_code = tsc_codes[0] if tsc_codes else ""

    # Build the course information dictionary
    new_course_info = {
        "Course Title": course_title,
        "Industry": industry,
        "Learning Outcomes": learning_outcomes,  # This is already a list
        "TSC Title": tsc_title,
        "TSC Code": tsc_code
    }

    # Update or append course_info
    existing_data["course_info"] = new_course_info

    # Handle analyst_responses (ensure it's a list in the final output)
    if analyst_responses:
        if "analyst_responses" not in existing_data:
            existing_data["analyst_responses"] = []
        existing_data["analyst_responses"].extend(analyst_responses)

    # Write back to validation_output.json
    with open(validation_output_path, "w", encoding="utf-8") as out_f:
        json.dump(existing_data, out_f, indent=2)

    print(f"Updated validation data saved to {validation_output_path}.")

def safe_json_loads(json_str):
    """Fix common JSON issues like unescaped quotes before parsing."""
    # Escape unescaped double quotes within strings
    json_str = re.sub(r'(?<!\\)"(?![:,}\]\s])', r'\"', json_str)
    try:
        return json.loads(json_str)
    except json.JSONDecodeError as e:
        print(f"JSON Parsing Error: {e}")
        return None

def load_json_file(file_path):
    """Loads JSON data from a file."""
    try:
        with open(file_path, 'r') as f:
            return json.load(f)
    except FileNotFoundError:
        print(f"Error: JSON file not found at '{file_path}'")
        return None
    except json.JSONDecodeError:
        print(f"Error: Could not decode JSON from file '{file_path}'. Please ensure it is valid JSON.")
        return None

def extract_lo_keys(json_data):
    """
    Extracts keys that match the pattern '#LO' followed by a number.

    Args:
        json_data (dict): The JSON data as a dictionary.

    Returns:
        list: A list of keys that match the pattern '#LO' followed by a number.
    """
    lo_keys = []
    pattern = re.compile(r'^#LO\d+$')
    for key in json_data.keys():
        print(f"Checking key: {key}")  # Debugging statement
        if pattern.match(key):
            print(f"Matched key: {key}")  # Debugging statement
            lo_keys.append(key)
    return lo_keys

def recursive_get_keys(json_data, key_prefix=""):
    """
    Extracts keys from a JSON dictionary that start with '#Topics' and returns them as a list.

    Args:
        json_data (dict): A dictionary loaded from a JSON file.

    Returns:
        list: A list of strings, where each string is a key from the json_data
              that starts with '#Topics'. For example: ['#Topics[0]', '#Topics[1]', '#Topics[2]', ...].
              Returns an empty list if no keys start with '#Topics'.
    """
    topic_keys = []
    for key in json_data.keys():
        # if key.startswith("#Topics"):
        if key.startswith(key_prefix):
            topic_keys.append(key)
    return topic_keys

def extract_agent_json(file_path: str, agent_name: str):
    """
    Reads the specified JSON file, finds the specified agent's final response,
    and extracts the substring from the first '{' to the last '}'.

    Attempts to parse the extracted substring as JSON, returning
    a Python dictionary. If parsing fails or if no final message
    is found, returns None.
    """
    with open(file_path, "r", encoding="utf-8") as f:
        data = json.load(f)

    # Identify the agent key (can be exact match or starts with agent_name)
    agent_key = None
    for key in data["agent_states"]:
        if key == agent_name or key.startswith(f"{agent_name}/"):
            agent_key = key
            break

    if not agent_key:
        print(f"No {agent_name} key found in agent_states.")
        return None

    # Get the agent state and retrieve the final message
    agent_state = data["agent_states"][agent_key]
    messages = agent_state["agent_state"]["llm_context"]["messages"]
    if not messages:
        print(f"No messages found under {agent_name} agent state.")
        return None

    final_message = messages[-1].get("content", "")
    if not final_message:
        print(f"Final {agent_name} message is empty.")
        return None

    # Extract the substring from the first '{' to the last '}'
    start_index = final_message.find("{")
    end_index = final_message.rfind("}")
    if start_index == -1 or end_index == -1:
        print(f"No JSON braces found in the final {agent_name} message.")
        return None

    json_str = final_message[start_index:end_index + 1].strip()

    # Parse the extracted substring as JSON
    try:
        parsed_json = json.loads(json_str)
        print(f"✓ Successfully parsed {agent_name} JSON")
        return parsed_json
    except json.JSONDecodeError as e:
        print(f"Failed to parse {agent_name} content as valid JSON on first attempt.")
        print(f"Error: {e}")

        # Try to fix literal control characters in string values
        try:
            # Simple character-by-character parser to escape control chars within strings
            fixed_chars = []
            in_string = False
            escape_next = False

            for i, char in enumerate(json_str):
                if escape_next:
                    fixed_chars.append(char)
                    escape_next = False
                    continue

                if char == '\\':
                    fixed_chars.append(char)
                    escape_next = True
                    continue

                if char == '"' and not escape_next:
                    # Toggle string state
                    in_string = not in_string
                    fixed_chars.append(char)
                    continue

                # If we're inside a string, escape control characters
                if in_string:
                    if char == '\n':
                        fixed_chars.append('\\n')
                    elif char == '\r':
                        fixed_chars.append('\\r')
                    elif char == '\t':
                        fixed_chars.append('\\t')
                    else:
                        fixed_chars.append(char)
                else:
                    fixed_chars.append(char)

            fixed_json = ''.join(fixed_chars)

            try:
                parsed_json = json.loads(fixed_json)
                print(f"✓ Successfully parsed {agent_name} JSON after escaping control characters")
                return parsed_json
            except:
                # Try fixing unquoted keys as well
                import re
                fixed_json = re.sub(r'(\w+):', r'"\1":', fixed_json)
                parsed_json = json.loads(fixed_json)
                print(f"✓ Successfully parsed {agent_name} JSON after fixing control chars and unquoted keys")
                return parsed_json
        except Exception as ex:
            print(f"Failed to parse {agent_name} content even after attempting fixes.")
            print(f"Error: {ex}")
            print(f"JSON string was: {json_str[:500]}...")
            return None
