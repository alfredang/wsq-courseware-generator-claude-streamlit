from autogen_core.models import ChatCompletionClient
from autogen_agentchat.agents import AssistantAgent
from autogen_agentchat.teams import RoundRobinGroupChat
from dotenv import load_dotenv
from settings.model_configs import get_model_config

load_dotenv()


def extraction_task(data):
    extraction_task = f"""
    1. Extract data from the following JSON file: {data}
    2. Map the extracted data according to the schemas.
    3. Return a full JSON object with all the extracted data according to the schema.
    """
    return extraction_task

def create_extraction_team(data, model_choice: str) -> RoundRobinGroupChat:
    chosen_config = get_model_config(model_choice)
    model_client = ChatCompletionClient.load_component(chosen_config)
    course_info_extractor_message = f"""
    You are to extract the following variables from {data}:
        1) Course Title
        2) Name of Organisation
        3) Classroom Hours (can be found under Instructional Duration: xxxx)
        4) Practical Hours (if none found, insert 0)
        5) Number of Assessment Hours (can be found under Assessment Duration: xxxx)
        6) Course Duration (Number of Hours)
        7) Industry

        Use the term_library below for "Industry", based on the front 3 letters of the TSC code:
        term_library = {{
            'ACC': 'Accountancy',
            'RET': 'Retail',
            'MED': 'Media',
            'ICT': 'Infocomm Technology',
            'BEV': 'Built Environment',
            'DSN': 'Design',
            'DNS': 'Design',
            'AGR': 'Agriculture',
            'ELE': 'Electronics',
            'LOG': 'Logistics',
            'STP': 'Sea Transport',
            'TOU': 'Tourism",
            'AER': 'Aerospace',
            'ATP': 'Air Transport',
            'BEV': 'Built Environment',
            'BPM': 'BioPharmaceuticals Manufacturing',
            'ECM': 'Energy and Chemicals',
            'EGS': 'Engineering Services',
            'EPW': 'Energy and Power',
            'EVS': 'Environmental Services',
            'FMF': 'Food Manufacturing',
            'FSE': 'Financial Services',
            'FSS': 'Food Services',
            'HAS': 'Hotel and Accommodation Services',
            'HCE': 'Healthcare',
            'HRS': 'Human Resource',
            'INP': 'Intellectual Property',
            'LNS': 'Landscape',
            'MAR': 'Marine and Offshore',
            'PRE': 'Precision Engineering',
            'PTP': 'Public Transport',
            'SEC': 'Security',
            'SSC': 'Social Service',
            'TAE': 'Training and Adult Education'
            'WPH': 'Workplace Safety and Health'
            'WST': 'Wholesale Trade'
            'STP': 'Sea Transport',
            'TOU': 'Tourism",
            'ECC': 'Early Childhood Care and Education',
            'ART': 'Arts'



        }}
        Format the extracted data in JSON format, with this structure, do NOT change the key names or add unnecessary spaces:
            "Course Information": {{
            "Course Title": "",
            "Name of Organisation": "",
            "Classroom Hours": ,
            "Practical Hours": ,
            "Number of Assessment Hours": ,
            "Course Duration (Number of Hours)": ,
            "Industry": ""
        }}
        Extra emphasis on following the JSON format provided, do NOT change the names of the keys, never use "course_info" as the key name.
    """

    learning_outcomes_extractor_message = f"""
    You are to extract the following variables from {data}:
        1) Learning Outcomes - include the terms LO1:, LO2:, etc. in front of each learning outcome
        2) Knowledge statements - MUST extract ALL K# statements from the TSC document
        3) Ability statements - MUST extract ALL A# statements from the TSC document

        CRITICAL INSTRUCTIONS:
        - Find ALL text blocks that start with "K1:", "K2:", "K3:", etc. - these are Knowledge statements
        - Find ALL text blocks that start with "A1:", "A2:", "A3:", etc. - these are Ability statements
        - Each statement should be a SEPARATE item in the array
        - Do NOT combine multiple statements into one string
        - Include the complete description after the colon

        Format the extracted data in JSON format with this EXACT structure:
            "Learning Outcomes": {{
                "Learning Outcomes": [
                    "LO1: First learning outcome description",
                    "LO2: Second learning outcome description"
                ],
                "Knowledge": [
                    "K1: First knowledge statement description",
                    "K2: Second knowledge statement description",
                    "K3: Third knowledge statement description"
                ],
                "Ability": [
                    "A1: First ability statement description",
                    "A2: Second ability statement description"
                ]
            }}

        CRITICAL: Extract EVERY K# and A# statement found in the document. Do not skip any.
        CRITICAL: Each K# and A# must be a separate array item, not combined with newlines.
    """

    tsc_and_topics_extractor_message = f"""
    You are to extract the following variables from {data}:
        1) TSC Title - the full title of the TSC
        2) TSC Code - the code in format XXX-XXX-XXXX-X.X
        3) Topics - MUST extract ALL topics from ALL Learning Units
        4) Learning Units - extract all LU titles WITHOUT K/A codes

        CRITICAL INSTRUCTIONS FOR TOPICS:
        - Extract EVERY topic from the document that starts with "Topic 1:", "Topic 2:", etc.
        - Include the FULL topic name INCLUDING the K# and A# codes in parentheses
        - Topics appear under each Learning Unit in the "Course Outline" section
        - You must extract topics from ALL Learning Units, not just one
        - Format: "Topic X: Topic Name (K#, A#)"

        CRITICAL INSTRUCTIONS FOR LEARNING UNITS:
        - Extract all Learning Unit titles (LU1:, LU2:, LU3:, etc.)
        - Format: "LU1: Learning Unit Title"
        - Do NOT include the (K#, A#) codes in Learning Units
        - Only the LU number and title

        Format the extracted data in JSON format, with this structure:
            "TSC and Topics": {{
            "TSC Title": ["Generative AI Model Development and Fine Tuning"],
            "TSC Code": ["ICT-BAS-0048-1.1"],
            "Topics": [
                "Topic 1: Probability Theory and Statistics (K1)",
                "Topic 2: Deep Learning Theory and Algorithms (K9)",
                "Topic 3: Machine Learning Libraries (K10)"
            ],
            "Learning Units": [
                "LU1: Foundations of Generative AI",
                "LU2: Data Preparation for Generative AI"
            ]
        }}

        CRITICAL: Extract ALL Topics from ALL Learning Units in the document.
    """

    assessment_methods_extractor_message = f"""
    You are to extract the following variables from {data}:
        1) Assessment Methods (remove the brackets and time values at the end of each string)
        2) Instructional Methods (extract the full string as-is from the TSC document)
        3) Amount of Practice Hours (insert "N.A." if not found)
        4) Course Outline - MUST extract ALL Learning Units with their Topics and Details

        CRITICAL INSTRUCTIONS FOR COURSE OUTLINE:
        - Find the "Course Outline:" section in the TSC document
        - Each Learning Unit (LU1, LU2, etc.) will list topics underneath it
        - Each topic will have a title in format "Topic X: Name (K#, A#)"
        - You MUST extract topic details/descriptions that appear under each topic
        - If no details are explicitly listed, leave Details as empty array []
        - INCLUDE THE FULL TOPIC TITLE with K and A factors in parentheses

        Format the extracted data in JSON format with this EXACT structure:
            "Assessment Methods": {{
                "Assessment Methods": ["Written Assessment", "Practical Performance"],
                "Amount of Practice Hours": "N.A.",
                "Course Outline": {{
                    "Learning Units": {{
                        "LU1": {{
                            "Description": [
                                {{
                                    "Topic": "Topic 1: Full Topic Name (K1, A1)",
                                    "Details": ["Detail point 1", "Detail point 2"]
                                }},
                                {{
                                    "Topic": "Topic 2: Another Topic (K2, A2)",
                                    "Details": []
                                }}
                            ]
                        }},
                        "LU2": {{
                            "Description": [
                                {{
                                    "Topic": "Topic 1: Topic Title (K3)",
                                    "Details": ["Detail 1"]
                                }}
                            ]
                        }}
                    }}
                }},
                "Instructional Methods": "Interactive Presentation, Demonstration, Practical"
            }}

        CRITICAL: You MUST extract Course Outline. It is mandatory. Look for the "Course Outline:" section in the document.
        CRITICAL: Extract ALL Learning Units and ALL Topics listed under each LU.
        CRITICAL: Instructional Methods should be a STRING, not an array.
    """

    aggregator_message = f"""
    You are to combine the outputs from the following agents into a single JSON object, do NOT aggregate output from the validator agent:
        1) course_info_extractor
        2) learning_outcomes_extractor
        3) tsc_and_topics_extractor
        4) assessment_methods_extractor
    Return the combined output into a single JSON file, do not alter the keys in any way, do not add or nest any keys. Ensure that the following is adhered to:
    1. **Strict JSON Formatting:**  
    - The output must be a valid JSON object with proper syntax (keys in double quotes, commas separating elements, arrays enclosed in square brackets, objects enclosed in curly braces).
    
    2. **Schema Compliance:**  
    The JSON must include the following top-level keys:  
    - `"Course Information"`  
    - `"Learning Outcomes"`  
    - `"TSC and Topics"`  
    - `"Assessment Methods"`  
    
    3. **No Trailing Commas or Missing Brackets:**  
    - Ensure that each array (`[...]`) and object (`{{...}}`) is closed properly.  
    - Do not leave trailing commas.  

    4. **Consistent Key Names:**  
    - Use consistent and properly spelled keys as specified.  

    5. **Always Validate Before Output:**  
    - Run a JSON lint check (or a `json.loads()` equivalent if you are simulating code) before returning the final JSON.  
    
    6. **Error Handling:**  
    If you detect an issue in the JSON (e.g., missing commas, brackets, or improper formatting), correct it immediately before providing the output.

    7. **Output Format:**  
    Return only the JSON object and no additional commentary.
    """

    course_info_extractor = AssistantAgent(
        name="course_info_extractor",
        model_client=model_client,
        system_message=course_info_extractor_message,
    )

    learning_outcomes_extractor = AssistantAgent(
        name="learning_outcomes_extractor",
        model_client=model_client,
        system_message=learning_outcomes_extractor_message,
    )

    tsc_and_topics_extractor = AssistantAgent(
        name="tsc_and_topics_extractor",
        model_client=model_client,
        system_message=tsc_and_topics_extractor_message,
    )

    assessment_methods_extractor = AssistantAgent(
        name="assessment_methods_extractor",
        model_client=model_client,
        system_message=assessment_methods_extractor_message,
    )

    aggregator = AssistantAgent(
        name="aggregator",
        model_client=model_client,
        system_message=aggregator_message,
    )

    extraction_group_chat = RoundRobinGroupChat([course_info_extractor, learning_outcomes_extractor, tsc_and_topics_extractor, assessment_methods_extractor, aggregator], max_turns=5)

    return extraction_group_chat