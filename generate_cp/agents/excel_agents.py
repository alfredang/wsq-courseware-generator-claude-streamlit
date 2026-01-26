from autogen_core.models import ChatCompletionClient
from autogen_agentchat.agents import AssistantAgent
from autogen_agentchat.teams import RoundRobinGroupChat
import json
import asyncio
import os
from dotenv import load_dotenv
from settings.model_configs import get_model_config
from autogen_agentchat.ui import Console

def course_task():
    overview_task = f"""
    1. Based on the provided data, generate your justifications.
    2. Ensure your responses are structured in JSON format.
    3. Return a full JSON object with all your answers according to the schema.
    """
    return overview_task

def ka_task():
    overview_task = f"""
    1. Based on the provided data, generate your justifications, ensure that ALL the A and K factors are addressed.
    2. Ensure your responses are structured in JSON format.
    3. Return a full JSON object with all your answers according to the schema.
    """
    return overview_task

def im_task():
    im_task = f"""
    1. Based on the provided data, generate your justifications, ensure that the instructional methods are addressed.
    2. Ensure your responses are structured in JSON format.
    3. Return a full JSON object with all your answers according to the schema.
    """
    return im_task

def create_course_agent(ensemble_output, model_choice: str) -> RoundRobinGroupChat:

    chosen_config = get_model_config(model_choice)
    model_client = ChatCompletionClient.load_component(chosen_config)

    # use ensemble output for the new factors
    # insert research analysts
    about_course_message = f"""
    As a digital marketing consultant, your primary role is to assist small business owners in optimizing their websites for SEO and improving their digital marketing strategies to enhance lead generation. You should provide clear, actionable advice tailored to the challenges and opportunities typical for small businesses. Focus on offering strategies that are feasible and effective for smaller budgets and resources. Stay abreast of the latest SEO and digital marketing trends, ensuring your advice is current and practical. When necessary, ask for clarification to understand the specific needs of each business, but also be proactive in filling in general small business scenarios. Personalize your responses to reflect an understanding of the unique dynamics and constraints small businesses face in digital marketing.
    You will do so based on the course title, learning outcomes (LOs), and the Topics found in {ensemble_output}

    Your task is to create a Course Description in 2 paragraphs for the above factors.

    An example answer is as follows: "This course equips learners with essential GitHub skills, covering version control, repository management, and collaborative workflows. Participants will learn how to create repositories, manage branches, integrate Git scripts, and leverage pull requests to streamline development. Through hands-on exercises, learners will explore GitHub features like issue tracking, code reviews, and discussions to enhance team collaboration.

    The course also covers modern GitHub tools such as GitHub Actions, Copilot, and Codespaces for automation and AI-driven development. Learners will gain expertise in security best practices, including dependency management, code scanning, and authentication protocols. By the end of the course, participants will be able to diagnose configuration issues, optimize deployment processes, and implement software improvements effectively."

    You must start your answer with "This course"
    You must take into consideration the learning outcomes and topics for the Course Description.
    Do not mention the course name in your answer.
    Do not use more than 300 words, it should be a concise summary of the course and what it has to offer.
    Do not mention the LOs in your answer.
    Do not add quotation marks in your answer.

    Provide learners with a clear overview of the course:
    Highlight the benefits your course offers including skils, competencies and needs that the course will address
    Explain how the course is relevant to the industry and how it may impact the learner's career in terms of employment/ job upgrading opportunities
    Indicate that the course is for beginner learners.
    Do not have more than 1 key value pair under "course_overview", and that key value pair must be "course_description".


    Format your response in the given JSON structure under "course_overview".
    Your output MUST be as follows, with course_description being the only key-value pair under "course_overview":
    "course_overview": {{
        "course_description": "Your course description here"
        }}
    """

    validation_message = f"""
    Your only purpose is to ensure that the output from the previous agent STRICTLY matches the json schema provided below.
    It must not have any other keys other than the ones specified in the below example.
    Your output must take the content of the previous agent and ensure that it is structured in the given JSON format.

    Do not have more than 1 key value pair under "course_overview", and that key value pair must be "course_description".


    Format your response in the given JSON structure under "course_overview".
    Your output MUST be as follows, with course_description being the only key-value pair under "course_overview":
    "course_overview": {{
        "course_description": "Generated content from previous agent"
        }}
    """

    course_agent = AssistantAgent(
        name="course_agent",
        model_client=model_client,
        system_message=about_course_message,
    )

    course_agent_validator = AssistantAgent(
    name="course_agent_validator",
    model_client=model_client,
    system_message=validation_message,
    )

    course_agent_chat = RoundRobinGroupChat([course_agent, course_agent_validator], max_turns=2)

    return course_agent_chat

def create_ka_analysis_agent(ensemble_output, instructional_methods_data, model_choice: str) -> RoundRobinGroupChat:

    chosen_config = get_model_config(model_choice)
    model_client = ChatCompletionClient.load_component(chosen_config)

    # instructional_methods_data = create_instructional_dataframe()
    ka_analysis_message = f"""
    You are responsible for elaborating on the appropriateness of the assessment methods in relation to the K and A statements. For each LO-MoA (Learning Outcome - Method of Assessment) pair, input rationale for each on why this MoA was chosen, and specify which K&As it
    pair, input rationale for each on why this MoA was chosen, and specify which K&As it will assess.

    The data provided which contains the ensemble of K and A statements, and the Learning Outcomes and Methods of Assessment, is in this dataframe: {instructional_methods_data}
    For each explanation, you are to provide no more than 50 words. Do so for each A and K factor present.
    Your response should be structured in the given JSON format under "KA_Analysis".
    Full list of K factors: {ensemble_output.get('Learning Outcomes', {}).get('Knowledge', [])}
    Full list of A factors: {ensemble_output.get('Learning Outcomes', {}).get('Ability', [])}
    Ensure that ALL of the A and K factors are addressed.
    Only use the first 2 characters as the key names for your JSON output, like K1 for example. Do not use the full A and K factor description as the key name.

    Do not mention any of the Instructional Methods directly.
    K factors must address theory and knowledge, while A factors must address practical application and skills, you must reflect this in your analysis.

    Follow the suggested answer structure shown below, respective to A and K factors.
    For example:
    KA_Analysis: {{
    K1: "The candidate will respond to a series of [possibly scenario based] short answer questions related to: ",
    A1: "The candidate will perform [some form of practical exercise] on this [topic] and submit [materials done] for: ",
    K2: "explanation",
    A2: "explanation",
    ...
    (and so on for however many A and K factors)
    }}

    """

    ka_analysis_agent = AssistantAgent(
        name="ka_analysis_agent",
        model_client=model_client,
        system_message=ka_analysis_message,
    )

    ka_analysis_chat = RoundRobinGroupChat([ka_analysis_agent], max_turns=1)

    return ka_analysis_chat

def create_instructional_methods_agent(ensemble_output, instructional_methods_json, model_choice: str) -> RoundRobinGroupChat:

    chosen_config = get_model_config(model_choice)
    model_client = ChatCompletionClient.load_component(chosen_config)

    # instructional_methods_data = create_instructional_dataframe()
    im_analysis_message = f"""
    You are responsible for contextualising the explanations of the chosen instructional methods to fit the context of the course. 
    You will take the template explanations and provide a customised explanation for each instructional method.
    Your response must be structured in the given JSON format under "Instructional_Methods".
    Focus on explaining why each of the IM is appropriate and not just on what will be done using the particular IM.
    Do not mention any A and K factors directly.
    Do not mention any topics directly.
    Do not mention the course name directly.

    Your response should be structured in the given JSON format under "Instructional_Methods".
    The following JSON output details the course, and the full list of chosen instructional methods can be found under the Instructional Methods key: {ensemble_output}
    Full list of template answers for the chosen instructional methods: {instructional_methods_json}

    Do not miss out on any of the chosen instructional methods.
    The key names must be the exact name of the instructional method, and the value must be the explanation.

    For example:
    Instructional_Methods: {{
    Lecture: "",
    Didactic Questioning: "",
    ...
    }}

    """

    instructional_methods_agent = AssistantAgent(
        name="instructional_methods_agent",
        model_client=model_client,
        system_message=im_analysis_message,
    )

    im_analysis_chat = RoundRobinGroupChat([instructional_methods_agent], max_turns=1)

    return im_analysis_chat

# async def run_excel_agents():
#     # Load the existing research_output.json
#     with open('json_output/research_output.json', 'r', encoding='utf-8') as f:
#         research_output = json.load(f)

#     course_agent = create_course_agent(research_output, model_choice=model_choice)
#     stream = course_agent.run_stream(task=overview_task)
#     await Console(stream)

#     course_agent_state = await course_agent.save_state()
#     with open("json_output/course_agent_state.json", "w") as f:
#         json.dump(course_agent_state, f)
#     course_agent_data = extract_final_agent_json("json_output/course_agent_state.json")  
#     with open("json_output/excel_data.json", "w", encoding="utf-8") as f:
#         json.dump(course_agent_data, f)  

#     # K and A analysis pipeline
#     instructional_methods_data = create_instructional_dataframe()
#     ka_agent = create_ka_analysis_agent(instructional_methods_data, model_choice=model_choice)
#     stream = ka_agent.run_stream(task=overview_task)
#     await Console(stream)
#     #TSC JSON management
#     state = await ka_agent.save_state()
#     with open("json_output/ka_agent_state.json", "w") as f:
#         json.dump(state, f)
#     ka_agent_data = extract_final_agent_json("json_output/ka_agent_state.json")
#     with open("json_output/excel_data.json", "w", encoding="utf-8") as out:
#         json.dump(ka_agent_data, out, indent=2)

# if __name__ == "__main__":
    # # Load the existing research_output.json
    # with open('json_output/research_output.json', 'r', encoding='utf-8') as f:
    #     research_output = json.load(f)

    # course_agent = create_course_agent(research_output, model_choice=model_choice)
    # stream = course_agent.run_stream(task=overview_task)
    # await Console(stream)

    # course_agent_state = await course_agent.save_state()
    # with open("json_output/course_agent_state.json", "w") as f:
    #     json.dump(course_agent_state, f)
    # course_agent_data = extract_final_agent_json("json_output/course_agent_state.json")  
    # with open("json_output/excel_data.json", "w", encoding="utf-8") as f:
    #     json.dump(course_agent_data, f)  

    # # K and A analysis pipeline
    # instructional_methods_data = create_instructional_dataframe()
    # ka_agent = create_ka_analysis_agent(instructional_methods_data, model_choice=model_choice)
    # stream = ka_agent.run_stream(task=overview_task)
    # await Console(stream)
    # #TSC JSON management
    # state = await ka_agent.save_state()
    # with open("json_output/ka_agent_state.json", "w") as f:
    #     json.dump(state, f)
    # ka_agent_data = extract_final_agent_json("json_output/ka_agent_state.json")
    # with open("json_output/excel_data.json", "w", encoding="utf-8") as out:
    #     json.dump(ka_agent_data, out, indent=2)

