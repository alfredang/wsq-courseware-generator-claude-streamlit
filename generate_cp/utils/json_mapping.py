import re
import streamlit as st

def flatten_list(nested_list):
    flat_list = []
    for item in nested_list:
        if isinstance(item, list):
            flat_list.extend(flatten_list(item))  # Recursively flatten any nested lists
        else:
            flat_list.append(item)
    return flat_list

def combine_lu_luex(mapping):
    sequencing = []

    # Determine the number of LUs available
    lu_keys = [key for key in mapping.keys() if key.startswith("#LU[")]
    num_lus = len(lu_keys)

    # Iterate through all LU and LUex pairs
    for i in range(num_lus):
        lu_key = f"#LU[{i}]"
        luex_key = f"#LUex[{i}]"

        # Get the LU and LUex values from the mapping
        lu_values = mapping.get(lu_key, [""])
        luex_values = mapping.get(luex_key, [""])

        lu_value = lu_values[0] if lu_values else ""
        luex_value = luex_values[0] if luex_values else ""

        # Remove leading 'LU#:' from lu_value
        lu_value_clean = re.sub(r'^LU\d+:\s*', '', lu_value)

        # Combine LU and LUex into the desired format
        if lu_value_clean and luex_value:
            combined = f"LU{i+1}: {lu_value_clean}\n{luex_value}\n"
        elif lu_value_clean:
            combined = f"LU{i+1}: {lu_value_clean}\n"
        elif luex_value:
            combined = f"{luex_value}\n"
        else:
            combined = ""

        if combined.strip():
            sequencing.append(combined.strip())

    # Add the combined result to the new #Sequencing key in the mapping
    mapping["#Sequencing"] = sequencing

def find_instructional_methods(obj):
    if isinstance(obj, dict):
        for key, value in obj.items():
            if key == 'Instructional Methods':
                return value
            else:
                result = find_instructional_methods(value)
                if result:
                    return result
    elif isinstance(obj, list):
        for item in obj:
            result = find_instructional_methods(item)
            if result:
                return result
    return None

# Define a function to sort codes in ascending order
def sort_codes(codes):
    def code_key(code):
        prefix = code[0]
        number = int(code[1:]) if code[1:].isdigit() else 0
        return (prefix, number)
    return sorted(codes, key=code_key)

def normalize_course_outline(course_outline):
    normalized_topics = {}
    for lu_key, lu_content in course_outline['Learning Units'].items():
        topics_list = []
        for description in lu_content['Description']:
            # Check for nested topics
            if isinstance(description['Details'], list) and len(description['Details']) > 0 and isinstance(description['Details'][0], dict):
                # Nested topics present
                for nested_topic in description['Details']:
                    topics_list.append({
                        'Topic': nested_topic['Topic'],
                        'Details': nested_topic['Description']
                    })
            else:
                # No nested topics
                topics_list.append({
                    'Topic': description['Topic'],
                    'Details': description['Details']
                })
        normalized_topics[lu_key] = topics_list
    return normalized_topics

# Define the mapping rules
def map_values(mapping_source, ensemble_output, research_output):
    # background_analysis = ""
    # for key, value in research_output["Background Analysis"].items():
    #     background_analysis += f"{value.strip()}\n\n"
    # mapping_source["#Placeholder[0]"] = [background_analysis.strip()]
        # Define the string to insert at the beginning
    introductory_string = "SkillsFuture's report Skills Demand For The Future Economy (https://www.skillsfuture.gov.sg/skillsreport) published in 2025, spotlights the priority skills and jobs in demand in three specially selected, emerging, high-growth areas. This report is designed for Singaporeans as a resource for an individual’s skills development journey over the next one to three years.  Singapore's key growth areas (Digital, Green & Care Economy) bring exciting job and skills opportunities. It also introduced the idea of 'priority skills, ' highly transferable skills across job roles within the three economies. In other words, these skills are applicable in many job roles and will contribute significantly to the individual's long-term career versatility. A new dimension on skills demands growth has been added and analysed alongside skills transferability. Demand growth captures the relative scale of the increase in demand for that skill, while transferability captures the scope of the skill's applicability across different job roles. The two-dimensional analysis seeks to provide deeper insights to the reader into the nature of the priority skills identified. \n\n"

    background_analysis = ""
    if "Background Analysis" in research_output and isinstance(research_output["Background Analysis"], dict):
        for key, value in research_output["Background Analysis"].items():
            background_analysis += f"{value.strip()}\n\n"

    # Insert the introductory string at the beginning
    background_analysis = introductory_string + background_analysis.strip()
    mapping_source["#Placeholder[0]"] = [background_analysis]

    performance_analysis = "Performance gaps were identified through survey forms distributed to external stakeholders:\n\n"

    # Iterate through the performance analysis
    if "Performance Analysis" in research_output and isinstance(research_output["Performance Analysis"], dict):
        for key, value in research_output["Performance Analysis"].items():
            if key == "Performance Gaps":
                performance_analysis += f"{key}:\n"
                if isinstance(value, list):
                    for item in value:
                        performance_analysis += f"•\t{item.strip()}\n"
                else:
                    performance_analysis += f"•\t{value.strip()}\n"
                performance_analysis += "\n"

        performance_analysis += "Through targeted training programs, learners will gain the following attributes to address the identified performance gaps after the training:\n\n"

        for key, value in research_output["Performance Analysis"].items():
            if key == "Attributes Gained":
                performance_analysis += f"{key}:\n"
                if isinstance(value, list):
                    for item in value:
                        performance_analysis += f"•\t{item.strip()}\n"
                else:
                    performance_analysis += f"•\t{value.strip()}\n"
                performance_analysis += "\n"

        for key, value in research_output["Performance Analysis"].items():
            if key == "Post-Training Benefits to Learners":
                performance_analysis += f"{key}:\n"
                if isinstance(value, list):
                    for item in value:
                        performance_analysis += f"•\t{item.strip()}\n"
                else:
                    performance_analysis += f"•\t{value.strip()}\n"
                performance_analysis += "\n"

    mapping_source["#Placeholder[1]"] = [performance_analysis.strip()]

    if "Sequencing Analysis" in research_output and isinstance(research_output["Sequencing Analysis"], dict):
        if "Sequencing Explanation" in research_output["Sequencing Analysis"]:
            mapping_source["#Rationale[0]"] = [research_output["Sequencing Analysis"]["Sequencing Explanation"]]

    # Mapping for Hours
    mapping_source["#Hours[0]"] = [ensemble_output["Course Information"]["Classroom Hours"]]
    mapping_source["#Hours[1]"] = [ensemble_output["Course Information"]["Number of Assessment Hours"]]
    mapping_source["#Hours[2]"] = [ensemble_output["Course Information"]["Course Duration (Number of Hours)"]]
    mapping_source["#Hours[3]"] = [ensemble_output.get("Assessment Methods", {}).get("Amount of Practice Hours", "N.A.")]

    # Safely access Conclusion
    if "Sequencing Analysis" in research_output and isinstance(research_output["Sequencing Analysis"], dict):
        if "Conclusion" in research_output["Sequencing Analysis"]:
            mapping_source["#Conclusion[0]"] = [research_output["Sequencing Analysis"]["Conclusion"]]
        else:
            mapping_source["#Conclusion[0]"] = ["The course structure is designed to progressively build knowledge and skills."]
    else:
        mapping_source["#Conclusion[0]"] = ["The course structure is designed to progressively build knowledge and skills."]

    cp_type = st.session_state.get('cp_type', "New CP")
    if cp_type == "Old CP":
        if "Assessment Phrasing" in research_output:
            mapping_source["#AssessmentJustification"] = [research_output["Assessment Phrasing"]]
        else:
            mapping_source["#AssessmentJustification"] = ["Assessment methods are aligned with learning outcomes."]

    # Mapping for Course Title
    mapping_source["#CourseTitle"] = [ensemble_output["Course Information"]["Course Title"]]

    # Mapping for TSC
    # Handle both string and array formats from LLM
    tsc_title = ensemble_output["TSC and Topics"]["TSC Title"]
    tsc_code = ensemble_output["TSC and Topics"]["TSC Code"]
    mapping_source["#TCS[0]"] = [tsc_title[0] if isinstance(tsc_title, list) else tsc_title]
    mapping_source["#TCS[1]"] = [tsc_code[0] if isinstance(tsc_code, list) else tsc_code]

    mapping_source["#Company"] = [ensemble_output["Course Information"]["Name of Organisation"]]

    # Mapping for Learning Outcomes
    learning_outcomes = ensemble_output["Learning Outcomes"]["Learning Outcomes"]
    lo_dict = {}
    for index, lo in enumerate(learning_outcomes):
        lo_code = f"LO{index+1}"
        if lo.startswith(f"{lo_code}: "):
            lo_description = lo[len(f"{lo_code}: "):]
        else:
            lo_description = lo
        lo_dict[lo_code] = lo_description

    for i, lo in enumerate(learning_outcomes):
        if f"#LO[{i}]" in mapping_source:
            mapping_source[f"#LO[{i}]"] = [lo]

    # Mapping for Learning Units
    learning_units = ensemble_output["TSC and Topics"]["Learning Units"]
    for i, lu in enumerate(learning_units):
        if f"#LU[{i}]" in mapping_source:
            mapping_source[f"#LU[{i}]"] = [lu]

    # Mapping for Learning Unit Descriptions (from research_output)
    if "Sequencing Analysis" in research_output and isinstance(research_output["Sequencing Analysis"], dict):
        for i in range(1, 6):  # LU1 to LU5
            lu_key = f"LU{i}"
            if lu_key in research_output["Sequencing Analysis"]:
                lu_data = research_output["Sequencing Analysis"][lu_key]
                if isinstance(lu_data, dict) and "Description" in lu_data:
                    mapping_source[f"#LUex[{i-1}]"] = [lu_data["Description"]]

    # Mapping for Knowledge and Abilities
    knowledge = ensemble_output["Learning Outcomes"]["Knowledge"]
    abilities = ensemble_output["Learning Outcomes"]["Ability"]
    knowledge_dict = {k.split(': ')[0]: k.split(': ')[1] for k in knowledge}
    ability_dict = {a.split(': ')[0]: a.split(': ')[1] for a in abilities}

    for i, k in enumerate(knowledge):
        if f"#K[{i}]" in mapping_source:
            mapping_source[f"#K[{i}]"] = [k]
    for i, a in enumerate(abilities):
        if f"#A[{i}]" in mapping_source:
            mapping_source[f"#A[{i}]"] = [a]

    # Normalize the course outline from Assessment Methods
    normalized_course_outline = normalize_course_outline(ensemble_output['Assessment Methods']['Course Outline'])

    # Build a mapping from topic titles to their details
    topic_details_map = {}

    for lu_key, topics_list in normalized_course_outline.items():
        for topic_desc in topics_list:
            topic_title = topic_desc['Topic']
            details = topic_desc['Details']
            topic_details_map[topic_title] = details

    # Extract topics and their K's and A's directly from normalized_course_outline
    topic_data_map = {}

    for lu_key, topics_list in normalized_course_outline.items():
        for topic_desc in topics_list:
            topic_title = topic_desc['Topic']

            # Use regex to extract the topic number, title, and codes
            match = re.match(r"Topic\s*(\d+):\s*(.*?)\s*(?:\((.*?)\))?$", topic_title)
            if match:
                topic_number = int(match.group(1))
                topic_title_clean = match.group(2).strip()
                codes_str = match.group(3) if match.group(3) else ''
                codes = [code.strip() for code in codes_str.split(',')] if codes_str else []
            else:
                continue  # Skip if the format doesn't match

            K_codes = [code for code in codes if code.startswith('K')]
            A_codes = [code for code in codes if code.startswith('A')]

            topic_data = {
                'topic_number': topic_number,
                'topic_title': topic_title_clean,
                'K_codes': K_codes,
                'A_codes': A_codes,
                'details': topic_desc['Details']
            }
            topic_data_map[topic_title] = topic_data

    # Build lu_mapping
    lu_mapping = {}
    for lu_key, topics_list in normalized_course_outline.items():
        lu_entry = {
            'title': lu_key,
            'topics': []
        }
        for topic_desc in topics_list:
            topic_title = topic_desc['Topic']
            topic_data = topic_data_map.get(topic_title)
            if not topic_data:
                continue  # Topic not found, skip

            topic_entry_dict = {
                'topic_number': topic_data['topic_number'],
                'topic_title': topic_data['topic_title'],
                'details': topic_data['details'],
                'K_codes': topic_data['K_codes'],
                'A_codes': topic_data['A_codes']
            }
            lu_entry['topics'].append(topic_entry_dict)

        # Map LU to LO
        # Assuming LU1 corresponds to LO1, LU2 to LO2, etc.
        lu_number_match = re.search(r'LU(\d+)', lu_key)
        if lu_number_match:
            lu_number = int(lu_number_match.group(1))
            lo_code = f'LO{lu_number}'
            lo_description = lo_dict.get(lo_code, '')
        else:
            lo_code = ''
            lo_description = ''

        lu_entry['LO_code'] = lo_code
        lu_entry['LO_description'] = lo_description

        # Collect K and A codes at LU level
        lu_K_codes = set()
        lu_A_codes = set()
        for topic in lu_entry['topics']:
            lu_K_codes.update(topic['K_codes'])
            lu_A_codes.update(topic['A_codes'])

        # Include K and A codes and descriptions at LU level, sorted in ascending order
        lu_entry['K_codes'] = sort_codes(list(lu_K_codes))
        lu_entry['A_codes'] = sort_codes(list(lu_A_codes))
        lu_entry['K_descriptions'] = {k_code: knowledge_dict.get(k_code, '') for k_code in lu_entry['K_codes']}
        lu_entry['A_descriptions'] = {a_code: ability_dict.get(a_code, '') for a_code in lu_entry['A_codes']}

        lu_mapping[lu_key] = lu_entry

    # Map LUs to "#Topics[n]"
    for i, (lu_key, lu_entry) in enumerate(lu_mapping.items()):
        topic_lines = []
        for topic in lu_entry['topics']:
            # Sort K_codes and A_codes for the topic
            sorted_K_codes = sort_codes(topic['K_codes'])
            sorted_A_codes = sort_codes(topic['A_codes'])
            K_codes_str = ', '.join(sorted_K_codes)
            A_codes_str = ', '.join(sorted_A_codes)

            # Build codes_str appropriately
            if K_codes_str and A_codes_str:
                codes_str = f" ({K_codes_str}, {A_codes_str})"
            elif K_codes_str:
                codes_str = f" ({K_codes_str})"
            elif A_codes_str:
                codes_str = f" ({A_codes_str})"
            else:
                codes_str = ''

            topic_line = f"Topic {topic['topic_number']}: {topic['topic_title']}{codes_str}"
            topic_lines.append(topic_line)
            # Append details if available
            for detail in topic['details']:
                topic_lines.append(f"•\t{detail}")
            topic_lines.append('')  # Empty line after each topic

        # Add LO after all topics
        topic_lines.append(f"{lu_entry['LO_code']} – {lu_entry['LO_description']}\n\n")
        # Add K and A codes and descriptions, sorted
        for k_code in lu_entry['K_codes']:
            k_desc = lu_entry['K_descriptions'][k_code]
            topic_lines.append(f"{k_code}: {k_desc}\n")
        for a_code in lu_entry['A_codes']:
            a_desc = lu_entry['A_descriptions'][a_code]
            topic_lines.append(f"{a_code}: {a_desc}\n")
        topic_lines.append('')  # Empty line after K and A descriptions

        # Join the lines into a single string
        consolidated_string = '\n'.join(topic_lines)

        # Map to "#Topics[{i}]"
        mapping_source[f"#Topics[{i}]"] = [consolidated_string]

    # Mapping for KA
    ka_mapping = ensemble_output["Learning Outcomes"].get("Knowledge and Ability Mapping", {})
    for i, (ka_key, ka_values) in enumerate(ka_mapping.items()):
        if f"#KA[{i}]" in mapping_source:
            # Separate K's and A's
            ks = sorted([v for v in ka_values if v.startswith('K')], key=lambda x: int(x[1:]))
            as_ = sorted([v for v in ka_values if v.startswith('A')], key=lambda x: int(x[1:]))
            # Combine K's and A's in the desired order
            ordered_values = ks + as_
            mapping_source[f"#KA[{i}]"] = [', '.join(ordered_values)]

    # Ensure any key with no mapping retains an empty list
    for key in mapping_source:
        if key not in mapping_source or not mapping_source[key]:
            mapping_source[key] = []

    # Function to generate assessment output and map it into mapping_source
    def generate_assessment_output(data, mapping_source):
        # Extract assessment methods
        assessment_methods = flatten_list(data.get("Assessment Methods", {}).get("Assessment Methods", []))

        # Map assessment method names to their abbreviations
        assessment_method_abbreviations = {
            "Written Assessment": "WA-SAQ",
            "Practical Performance": "PP",
            "Case Study": "CS",
            "Oral Questioning": "OQ",
            "Role Play": "RP"
        }

        # Normalize assessment methods to their abbreviated forms
        normalized_assessment_methods = [assessment_method_abbreviations.get(method, method) for method in assessment_methods]

        # Map assessment method abbreviations to full names
        assessment_method_names = {
            "WA-SAQ": "Written Assessment - Short-Answer Questions",
            "PP": "Practical Performance",
            "CS": "Case Study",
            "OQ": "Oral Questioning",
            "Written Assessment - Short-Answer Questions (WA-SAQ) - Individual, Summative, Open book": "Written Assessment - Short-Answer Questions",
            "RP": "Role Play"
        }

        # Create a list that combines the full names with their short forms
        full_method_names = [
            f"{assessment_method_names.get(method, method)} ({method})"
            for method in normalized_assessment_methods
        ]

        # Store the combined full names with short forms in the mapping_source for #AssessMethods
        mapping_source["#AssessMethods"] = full_method_names

        # Extract number of assessment hours and convert to minutes
        num_assessment_hours = data.get("Course Information", {}).get("Number of Assessment Hours", 0)
        total_assessment_minutes = num_assessment_hours * 60  # Convert hours to minutes

        # Get the list of Learning Units (LUs)
        learning_units = data["TSC and Topics"]["Learning Units"]
        num_lus = len(learning_units)

        # Build lu_mapping for assessment
        lu_assessment_methods = {}
        methods_used = set()

        for i, lu in enumerate(learning_units):
            lu_key = f"LU{i+1}"
            lu_data = lu_mapping.get(lu_key, {})

            methods_in_lu = []

            # Determine assessment methods based on K's and A's in the LU
            if lu_data.get('K_codes'):
                methods_in_lu.append('WA-SAQ')
            if lu_data.get('A_codes'):
                # Dynamically determine which method is used for A's
                # Check which methods are available for abilities
                available_methods = [method for method in ['PP', 'CS', 'OQ', 'RP'] if method in normalized_assessment_methods]
                if available_methods:
                    methods_in_lu.append(available_methods[0])  # Use the first available method

            lu_assessment_methods[lu_key] = methods_in_lu
            methods_used.update(methods_in_lu)

        # Divide total assessment duration equally among methods
        num_methods_used = len(methods_used)
        if num_methods_used > 0:
            method_total_duration = total_assessment_minutes // num_methods_used
        else:
            method_total_duration = 0

        # For each method, collect the LUs that use it
        method_lu_map = {method: [] for method in methods_used}
        for lu_key, methods_in_lu in lu_assessment_methods.items():
            for method in methods_in_lu:
                method_lu_map[method].append(lu_key)

        # For each method, divide its total duration equally among LUs that use it
        method_durations_per_lu = {}
        for method, lus in method_lu_map.items():
            num_lus_using_method = len(lus)
            if num_lus_using_method > 0:
                duration_per_lu = method_total_duration // num_lus_using_method
            else:
                duration_per_lu = 0
            for lu_key in lus:
                if lu_key not in method_durations_per_lu:
                    method_durations_per_lu[lu_key] = {}
                method_durations_per_lu[lu_key][method] = duration_per_lu

        # Define the method order to ensure "Written Assessment" comes first
        method_order = ['WA-SAQ', 'PP', 'CS', 'OQ', 'RP']

        # Map durations per method per LU into #ADuration[n]
        for i, lu_key in enumerate([f"LU{idx+1}" for idx in range(num_lus)]):
            durations_in_lu = method_durations_per_lu.get(lu_key, {})
            duration_lines = []
            # Ensure methods are ordered correctly
            for method in method_order:
                if method in durations_in_lu:
                    duration = durations_in_lu[method]
                    duration_line = f"{assessment_method_names[method]} ({method}) – {duration} mins"
                    duration_lines.append(duration_line)
            # Map to #ADuration[i]
            mapping_source[f"#ADuration[{i}]"] = ["\n\n".join(duration_lines)]

        # For backward compatibility, you can consolidate the total durations per method
        # Calculate total duration per method
        total_method_durations = {}
        for method in methods_used:
            total_duration = method_total_duration  # Each method has method_total_duration allocated
            total_method_durations[method] = total_duration

        # Map total durations to #ADurationTotal
        total_duration_lines = []
        total_duration_minutes = 0
        for method in method_order:
            if method in total_method_durations:
                duration_minutes = total_method_durations[method]
                duration_hours = duration_minutes / 60
                duration_hours_str = f"{int(duration_hours)} hr" if duration_hours.is_integer() else f"{duration_hours} hr"
                duration_line = f"{method} – {duration_hours_str}"
                total_duration_lines.append(duration_line)
                total_duration_minutes += duration_minutes
        # Add total duration at the end
        total_duration_hours = total_duration_minutes / 60
        total_duration_hours_str = f"{int(total_duration_hours)} hr" if total_duration_hours.is_integer() else f"{total_duration_hours} hr"
        total_duration_lines.append(f"Total – {total_duration_hours_str}")
        mapping_source["#ADurationTotal"] = ["\n".join(total_duration_lines)]

        # For each KA, create an assessment
        ka_mapping = data.get("Learning Outcomes", {}).get("Knowledge and Ability Mapping", {})
        ka_list = list(ka_mapping.items())

        for idx, (ka_key, ka_values) in enumerate(ka_list):
            # Determine which LU this KA belongs to
            lu_index = idx % num_lus  # Assuming KAs are evenly distributed
            lu_key = f"LU{lu_index+1}"
            methods_in_lu = lu_assessment_methods.get(lu_key, [])

            # Separate K's and A's
            ks = [item for item in ka_values if item.startswith('K')]
            as_ = [item for item in ka_values if item.startswith('A')]

            assessment_lines = []
            # Allocate K's to WA-SAQ if it's in the methods for this LU
            if "WA-SAQ" in methods_in_lu and ks:
                assessment_lines.append(f"{assessment_method_names['WA-SAQ']} (WA-SAQ) – {', '.join(ks)}")

            # Allocate A's to the appropriate method if it's in the methods for this LU
            for method in method_order:
                if method != 'WA-SAQ' and method in methods_in_lu and as_:
                    assessment_lines.append(f"{assessment_method_names[method]} ({method}) – {', '.join(as_)}")
                    break  # Use the first matching method

            # Combine assessment lines
            assessment_text = "\n\n".join(assessment_lines)
            # Map to "#Assessment[{idx}]"
            mapping_source[f"#Assessment[{idx}]"] = [assessment_text]

        # Map Instructional Methods
        instructional_methods = find_instructional_methods(data)

        # If instructional methods is a comma-separated string, split it into a list
        if isinstance(instructional_methods, str):
            instructional_methods = instructional_methods.split(', ')

        # Ensure instructional methods is a proper list in mapping_source
        mapping_source["#IM"] = instructional_methods

        return mapping_source

    # Call the function to generate assessments and map them
    generate_assessment_output(ensemble_output, mapping_source)

    combine_lu_luex(mapping_source)
    return mapping_source
