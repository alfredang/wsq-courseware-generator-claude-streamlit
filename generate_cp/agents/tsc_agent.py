from autogen_agentchat.agents import AssistantAgent
from autogen_agentchat.teams import RoundRobinGroupChat
from settings.model_configs import get_model_config
from autogen_core.models import ChatCompletionClient


def tsc_agent_task(tsc_data):
    tsc_task = f"""
    1. Parse data from the following JSON file: {tsc_data}
    2. Fix spelling errors, and missing LUs if any.
    3. Ensure that the LUs do not have the same name as the Topics.
    4. Return a full JSON object with all the extracted data according to the schema.
    """
    return tsc_task

def create_tsc_agent(tsc_data, model_choice: str) -> RoundRobinGroupChat:
    chosen_config = get_model_config(model_choice)
    model_client = ChatCompletionClient.load_component(chosen_config)

    tsc_parser_agent_message = f"""
        You are to parse and correct spelling mistakes from {tsc_data}:
        The requirements are as follows:
        1. If there are no LU's present, summarize a LU from each Topics and name them sequentially. The LUs should NOT have the same name as the topics. Ignore this instruction if there are LUs present.
        1.1. If there are LU's present, ensure that they are correctly mapped to the Topics. Do NOT include additional LUs if they are already present in the data.
        2. Ensure that any mention of "Topic" is followed by a number and a colon.
        2.5. Ensure that any mention of "LU" is followed by a number and a colon.
        2.6. Ensure that the A and K factors are followed by a number and a colon.
        3. Ensure that the K and A factors are correctly mapped to the LUs in brackets.
        3.1. CRITICAL: If a Topic does NOT have K and A factors in brackets in its header, you MUST add the K and A factors from its parent LU header to the Topic header. Every Topic MUST have K and A factors in brackets.
        4. Catch and amend any spelling errors to the following words:
        Instructional Methods:
        - Didactic Questioning
        - Demonstration
        - Practical
        - Peer Sharing
        - Role Play
        - Group Discussion
        - Case Study
        Assessment Methods:
        - Written Assessment
        - Practical Performance
        - Case Study
        - Oral Questioning
        - Role Play

        For example, "case studies" is WRONG, "Case Study" is CORRECT.

        An example JSON schema looks like this, with the LUs as a key-value pair:
        {{
            "Course_Proposal_Form": {{
                "null": [
                    "Title: Hands-on AI-Assisted Programming Made Simple with GitHub Copilot",
                    "Organization: Tertiary Infotech Academy Pte Ltd",
                    "Learning Outcomes:",
                    "LO1: Identify gaps in existing programming workflows and propose AI-assisted solutions using GitHub Copilot to enhance efficiency.",
                    "LO2: Explore and apply emerging AI programming tools, including GitHub Copilot, to streamline organizational coding processes.",
                    "Couse Duration: 1 days (8 hrs)",
                    "Instructional Methods:",
                    "Classroom: 3 hours",
                    "Practical: 4 hours",
                    "Didactic Questioning",
                    "Demonstration",
                    "Assessment Methods:",
                    "Written Assessment (0.5 hr)",
                    "Practical Performance (0.5 hr)",
                    "TSC Mapping:",
                    "TSC Title: Digital Technology Adoption and Innovation",
                    "TSC Code: ACC-ICT-3004-1.1",
                    "TSC Knowledge:",
                    "K1: Relevant systems and software",
                    "K2: Organisation's processes",
                    "K3: Strengths and weaknesses of existing software and systems",
                    "K4: Emerging technological trends such as block chain, machine learning, artificial intelligence,",
                    "TSC Abilities:",
                    "A1: Identify issues in the existing software and systems",
                    "A2: Seek potential IT solutions to resolve issues or for systems upgrading",
                    "A3: Propose to management on suitable IT solutions for the organisation",
                    "A4: Keep up to date with new technologies and systems",
                    "Learning Units"
                ],
                "LU1: Introduction to Copilot (K1, K3, A1, A3)": [
                    "Topic 1: Getting Started  with Github Copilot (K1, K3, A1, A3)",
                    "What is Github Copilot?",
                    "How Github Copilot enhances software development efficiency?",
                    "Install Github Copilot on Visual Studio Code",
                    "Explore Github Copilot features"
                ],
                "LU2: Coding with Github Copilot (K2, K4, A2, A4)": [
                    "Topic 2: Software Development with Github Copilot (K2, K4, A2, A4)",
                    "Github Copilot for HTML",
                    "Github Copilot for Python",
                    "Github Copilot for Javascript",
                    "Github Copilot for REST API",
                    "Other emerging AI tools for software development"
                ]
            }}
        }}

        Take note that there can be more than 1 topic per LU, if this is the case, it is already indicated in the data as LUs will already be present and defined, so there is no need for you to further formulate more LUs.
        IMPORTANT: When a Topic does not have K and A factors in its header, you MUST inherit the K and A factors from the LU header and add them to the Topic header.
        If that is the case, you are to follow the below structure for the JSON output:
        {{
            "Course_Proposal_Form": {{
                "null": [
                    "Title: Hands-on AI-Assisted Programming Made Simple with GitHub Copilot",
                    "Organization: Tertiary Infotech Academy Pte Ltd",
                    "Learning Outcomes:",
                    "LO1: Identify gaps in existing programming workflows and propose AI-assisted solutions using GitHub Copilot to enhance efficiency.",
                    "LO2: Explore and apply emerging AI programming tools, including GitHub Copilot, to streamline organizational coding processes.",
                    "Couse Duration: 1 days (8 hrs)",
                    "Instructional Methods:",
                    "Classroom: 3 hours",
                    "Practical: 4 hours",
                    "Didactic Questioning",
                    "Demonstration",
                    "Assessment Methods:",
                    "Written Assessment (0.5 hr)",
                    "Practical Performance (0.5 hr)",
                    "TSC Mapping:",
                    "TSC Title: Digital Technology Adoption and Innovation",
                    "TSC Code: ACC-ICT-3004-1.1",
                    "TSC Knowledge:",
                    "K1: Relevant systems and software",
                    "K2: Organisation's processes",
                    "K3: Strengths and weaknesses of existing software and systems",
                    "K4: Emerging technological trends such as block chain, machine learning, artificial intelligence,",
                    "TSC Abilities:",
                    "A1: Identify issues in the existing software and systems",
                    "A2: Seek potential IT solutions to resolve issues or for systems upgrading",
                    "A3: Propose to management on suitable IT solutions for the organisation",
                    "A4: Keep up to date with new technologies and systems",
                    "Learning Units"
                ],
                "LU1: Introduction to Copilot (K1, K3, A1, A3)": [
                    "Topic 1: Getting Started  with Github Copilot (K1, A1)",
                    "What is Github Copilot?",
                    "How Github Copilot enhances software development efficiency?",
                    "Install Github Copilot on Visual Studio Code",
                    "Explore Github Copilot features",
                    "Topic 2: Software Development with Github Copilot (K3, A3)",
                    "Github Copilot for HTML",
                    "Github Copilot for Python",
                    "Github Copilot for Javascript",
                    "Github Copilot for REST API",
                    "Other emerging AI tools for software development"
                ],
            }}
        }}        
        """

    tsc_parser_agent = AssistantAgent(
        name="tsc_agent",
        model_client=model_client,
        system_message=tsc_parser_agent_message,
    )

    tsc_agent_response = RoundRobinGroupChat([tsc_parser_agent], max_turns=1)

    return tsc_agent_response