from autogen_core.models import ChatCompletionClient
from autogen_agentchat.agents import AssistantAgent
from autogen_agentchat.teams import RoundRobinGroupChat
from settings.model_configs import get_model_config

def validation_task(ensemble_output):
    validation_task = f"""
    1. Extract data from the following JSON file: {ensemble_output}
    2. Generate 3 distinct sets of answers to two specific survey questions. 
    3. Map the extracted data according to the schemas.
    4. Return a full JSON object with all the extracted data according to the schema.
    """
    return validation_task

def create_course_validation_team(ensemble_output, model_choice: str) -> RoundRobinGroupChat:
    chosen_config = get_model_config(model_choice)
    print(f"Debug: model_choice in create_course_validation: {model_choice}") # Add this line

    model_client = ChatCompletionClient.load_component(chosen_config)
    print(f"Debug: Model config for validation team: {chosen_config}")
    # insert research analysts
    analyst_message = f"""
    Using the following information from {ensemble_output}:
    1. Course title (e.g., "Data Analytics for Business")
    2. Industry (e.g., "Retail")
    3. Learning outcomes expected from the course (e.g., "Better decision-making using data, automation of business reports")

    Generate 3 distinct sets of answers to two specific survey questions.
    Survey Questions and Structure:

    {{
    Question 1: What are the performance gaps in the industry?
    Question 1 Guidelines: You are to provide a short description (1-2 paragraphs) of what the key performance issues are within the specified industry. This will be based on general industry knowledge, considering the context of the course.

    Question 2: Why you think this WSQ course will address the training needs for the industry?
    Question 2 Guidelines: You are to explain in a short paragraph (1-2 paragraphs) how the course you mentioned can help address those performance gaps in the industry. Each response will be tied to one or two of the learning outcomes you provided, without directly mentioning them.

    }}

    Rules for Each Response:
    Distinct Answers: You will provide three different answers by focusing on different learning outcomes in each response.
    Concise Structure: Each response will have no more than two paragraphs, with each paragraph containing fewer than 120 words.

    No Mention of Certain Elements:
    You won't mention the specific industry in the response.
    You won't mention or restate the learning outcomes explicitly.
    You won't indicate that I am acting in a director role.

    You are to output your response in this JSON format, do not change the keys:
    Output Format (for each of the 3 sets):
    What are the performance gaps in the industry?
    [Answer here based on the industry and course details you provide]

    Why do you think this WSQ course will address the training needs for the industry?
    [Answer here showing how the course helps address the gaps based on relevant learning outcomes]

    By following these steps, you aim to provide actionable insights that match the course content to the training needs within the specified industry.
    """

    editor_message = f"""
    You are to combine the outputs from the following agents into a single JSON object, do NOT aggregate output from the validator agent:
        1) analyst
    Return the combined output into a single JSON file.

    Follow this structure and naming convention below:
    {{
        "analyst_responses": [
            {{
                "What are the performance gaps in the industry?": "",
                "Why do you think this WSQ course will address the training needs for the industry?": ""
            }}
        ]
    }}
    """

    analyst = AssistantAgent(
        name="analyst",
        model_client=model_client,
        system_message=analyst_message
    )

    editor = AssistantAgent(
        name="editor",
        model_client=model_client,
        system_message=editor_message,
    )

    course_validation_group_chat = RoundRobinGroupChat([analyst, editor], max_turns=2)

    return course_validation_group_chat