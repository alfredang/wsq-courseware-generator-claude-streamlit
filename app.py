# app.py
import streamlit as st
from streamlit_option_menu import option_menu
from generate_ap_fg_lg_lp.utils.organizations import get_organizations, get_default_organization
import asyncio
import os

# Import skills loader
from skills import get_skill_response, get_skill_action, get_skills_system_message, list_skill_commands, match_skill_by_keywords, get_workflow_steps

# Lazy loading functions for better performance
def lazy_import_assessment():
    import generate_assessment.assessment_generation as assessment_generation
    return assessment_generation

def lazy_import_courseware():
    import generate_ap_fg_lg_lp.courseware_generation as courseware_generation
    return courseware_generation

def lazy_import_brochure_v2():
    import generate_brochure.brochure_generation as brochure_generation
    return brochure_generation

def lazy_import_annex_v2():
    import add_assessment_to_ap.annex_assessment_v2 as annex_assessment_v2
    return annex_assessment_v2

def lazy_import_course_proposal():
    import generate_cp.app as course_proposal_app
    return course_proposal_app

def lazy_import_docs():
    import check_documents.sup_doc as sup_doc
    return sup_doc

def lazy_import_settings():
    import settings.settings as settings
    return settings

def lazy_import_company_settings():
    import company.company_settings as company_settings
    return company_settings

def lazy_import_slides():
    import generate_slides.slides_generation as slides_generation
    return slides_generation


def display_homepage():
    """Display homepage with navigation boxes and chatbot"""
    st.markdown("""
        <style>
            .block-container {
                padding-top: 1rem;
            }
            .card-header {
                text-align: center;
                font-size: 1.1rem;
                font-weight: 600;
                margin-bottom: 0.25rem;
            }
            .card-desc {
                text-align: center;
                font-size: 0.8rem;
                color: #888;
                margin-bottom: 0.5rem;
            }
        </style>
        """, unsafe_allow_html=True)
    st.markdown("<h2 style='text-align: center; font-size: 1.75rem;'>WSQ Courseware Assistant with OpenAI Multi Agents</h2>", unsafe_allow_html=True)

    # Navigation boxes - 2 columns, 3 rows
    modules = [
        {"name": "Generate CP", "icon": "📄", "desc": "Create Course Proposals", "menu": "Generate CP"},
        {"name": "Generate AP/FG/LG/LP", "icon": "📚", "desc": "Generate Courseware Documents", "menu": "Generate AP/FG/LG/LP"},
        {"name": "Generate Assessment", "icon": "✅", "desc": "Create Assessment Materials", "menu": "Generate Assessment"},
        {"name": "Generate Slides", "icon": "🎯", "desc": "Create Presentation Slides", "menu": "Generate Slides"},
        {"name": "Generate Brochure", "icon": "📰", "desc": "Design Course Brochures", "menu": "Generate Brochure"},
        {"name": "Add Assessment to AP", "icon": "📎", "desc": "Attach Assessments to AP", "menu": "Add Assessment to AP"},
        {"name": "Check Documents", "icon": "🔍", "desc": "Validate Supporting Documents", "menu": "Check Documents"},
    ]

    # Display modules in 2 columns, 3 rows
    for i in range(0, len(modules), 2):
        col1, col2 = st.columns(2)

        with col1:
            m = modules[i]
            with st.container(border=True):
                st.markdown(f"<div class='card-header'>{m['icon']} {m['name']}</div>", unsafe_allow_html=True)
                st.markdown(f"<div class='card-desc'>{m['desc']}</div>", unsafe_allow_html=True)
                if st.button("Open", key=f"nav_{i}", use_container_width=True):
                    st.session_state['current_page'] = m['menu']
                    st.session_state['settings_page'] = None
                    st.rerun()

        with col2:
            if i + 1 < len(modules):
                m = modules[i + 1]
                with st.container(border=True):
                    st.markdown(f"<div class='card-header'>{m['icon']} {m['name']}</div>", unsafe_allow_html=True)
                    st.markdown(f"<div class='card-desc'>{m['desc']}</div>", unsafe_allow_html=True)
                    if st.button("Open", key=f"nav_{i+1}", use_container_width=True):
                        st.session_state['current_page'] = m['menu']
                        st.session_state['settings_page'] = None
                        st.rerun()



def get_chatbot_system_message():
    """Generate the chatbot system message with dynamically loaded skills."""
    base_message = """You are an AI assistant for WSQ (Workforce Skills Qualifications) courseware generation. You help users create training materials for Singapore's national credential system.

**IMPORTANT**: You are a skill-driven assistant. When users ask questions, ALWAYS check if their request relates to one of your skills. Use the skill's detailed instructions and knowledge to provide accurate, specific guidance.

"""
    # Add skills from .skills folder
    skills_message = get_skills_system_message()

    response_guide = """
## How to Respond

1. **Identify the relevant skill** - Match user requests to your skills, even without exact commands
2. **Use skill knowledge** - Reference the Instructions section of relevant skills for detailed guidance
3. **Provide specific answers** - Use the process steps, tips, and requirements from skills
4. **Offer to navigate** - Tell users you can take them to the relevant module
5. **Be concise but thorough** - Users are busy training professionals

## Navigation

Users can access modules from the sidebar, or type skill commands:
- `/generate_course_proposal` - Create Course Proposals
- `/generate_ap_fg_lg_lp` - Generate courseware documents (AP, FG, LG, LP)
- `/generate_assessment` - Create assessment materials (SAQ, PP, CS, Project, Assignment, Oral Interview, Demonstration, Role Play, Oral Questioning)
- `/generate_slides` - Generate presentation slides
- `/generate_brochure` - Generate course marketing brochures
- `/add_assessment_to_ap` - Add assessment annexes to Assessment Plans
- `/check_documents` - Verify and check documents

## Action Triggering

When a user asks you to perform a task that matches one of the modules above, include an ACTION tag in your response to automatically navigate them to the right page:

[ACTION:navigate=Generate CP]
[ACTION:navigate=Generate AP/FG/LG/LP]
[ACTION:navigate=Generate Assessment]
[ACTION:navigate=Generate Slides]
[ACTION:navigate=Generate Brochure]
[ACTION:navigate=Add Assessment to AP]
[ACTION:navigate=Check Documents]

Examples:
- User says "I want to create a course proposal" -> include [ACTION:navigate=Generate CP]
- User says "Generate an assessment for my course" -> include [ACTION:navigate=Generate Assessment]
- User says "I need a brochure" -> include [ACTION:navigate=Generate Brochure]
- User says "Create slides for my training" -> include [ACTION:navigate=Generate Slides]

Only include the ACTION tag when the user clearly intends to perform the task, not when just asking about it.
"""
    return base_message + skills_message + response_guide


def _detect_greeting_or_help(prompt):
    """Detect greetings, help, workflow requests, and common conversational inputs."""
    lower = prompt.lower().strip().rstrip('?!.')

    greetings = ["hi", "hello", "hey", "good morning", "good afternoon", "good evening",
                 "hii", "hiii", "yo", "sup", "helo", "hai", "hi there", "hello there",
                 "howdy", "greetings", "good day", "hola", "heya", "hey there"]
    help_phrases = ["help", "what can you do", "what do you do", "how to use",
                    "how does this work", "menu", "options", "show me",
                    "what are the features", "guide me", "i need help",
                    "what is this", "how to start", "getting started", "start",
                    "what features", "show features", "what tools",
                    "how do i use this", "tell me what you can do",
                    "what can i do here", "what is available",
                    "show me what you can do", "capabilities",
                    "list of features", "what's available"]
    thanks = ["thank you", "thanks", "thx", "tq", "thank u", "thankyou",
              "thanks a lot", "thank you so much", "appreciate it", "ty",
              "thanks so much", "great thanks", "ok thanks", "okay thanks"]
    workflow_phrases = ["workflow", "full workflow", "what is the process",
                        "what are the steps", "step by step", "whole process",
                        "everything", "all documents", "complete courseware",
                        "i need everything", "full course", "entire course",
                        "from start to finish", "end to end", "what order",
                        "where do i start", "what should i do first",
                        "what comes first", "what is the order",
                        "show me the process", "how does the process work",
                        "what is the workflow", "explain the workflow",
                        "full process", "complete process", "all steps",
                        "show me all the steps", "how to create a full course"]
    next_phrases = ["what's next", "whats next", "what next", "next step",
                    "what should i do next", "what do i do now", "now what",
                    "what else", "anything else", "what more", "continue",
                    "then what", "after this", "what after this",
                    "what do i do after", "and then", "what follows",
                    "next", "proceed"]

    if lower in greetings:
        return ("Hi there! I'm your WSQ Courseware Assistant.\n\n"
                "Just tell me what you'd like to do — for example:\n"
                "- **\"I want to create a brochure\"**\n"
                "- **\"Generate an assessment\"**\n"
                "- **\"Create a course proposal\"**\n"
                "- **\"I need slides for my course\"**\n"
                "- **\"Show me the full workflow\"**\n\n"
                "I'll give you step-by-step instructions and take you to the right page automatically.")

    for phrase in workflow_phrases:
        if phrase in lower:
            return get_workflow_steps()

    for phrase in next_phrases:
        if phrase in lower:
            # Check last skill used from chat history for context-aware next steps
            last_skill_name = st.session_state.get('_last_skill_name', '')
            if last_skill_name:
                # Find the specific skill by name and return its next steps
                from skills import _load_all_skill_objects
                for skill in _load_all_skill_objects():
                    if skill.get('name') == last_skill_name and skill.get('next_steps'):
                        return skill['next_steps']
            # Fallback to general workflow
            return get_workflow_steps()

    for phrase in help_phrases:
        if phrase in lower:
            return ("Here's everything I can help you with:\n\n"
                    "- **Course Proposal** — Create a new CP from TSC documents\n"
                    "- **Courseware** — Generate Assessment Plan, Facilitator Guide, Learner Guide, or Lesson Plan\n"
                    "- **Assessment** — Create SAQ, Case Study, Role Play, Project, and 5 more types\n"
                    "- **Slides** — Generate PowerPoint presentations from course content\n"
                    "- **Brochure** — Design a professional course brochure\n"
                    "- **Add Assessment to AP** — Attach assessment materials as annexes\n"
                    "- **Check Documents** — Validate your files before submission\n\n"
                    "Just type what you need — like **\"brochure\"** or **\"create assessment\"** — and I'll guide you from there.\n\n"
                    "Want to see the recommended workflow? Just say **\"show me the full workflow\"**.")

    for phrase in thanks:
        if phrase in lower:
            return "You're welcome! Let me know if you need anything else — or say **\"what's next\"** for the next step."

    # Goodbye / farewell
    goodbye_phrases = ["bye", "goodbye", "good bye", "see you", "see ya", "cya",
                       "take care", "gotta go", "i'm done", "im done", "that's all",
                       "thats all", "nothing else", "no more", "all done", "exit", "quit"]
    for phrase in goodbye_phrases:
        if phrase in lower or lower == phrase:
            return ("Goodbye! Feel free to come back anytime you need help with your WSQ courseware.\n\n"
                    "Remember, you can always start with **\"hi\"** or **\"help\"** when you return.")

    # Confused / lost users
    confused_phrases = ["i don't know", "i dont know", "i'm lost", "im lost", "confused",
                        "i'm not sure", "im not sure", "what should i do", "i need guidance",
                        "where do i start", "how to begin", "i'm stuck", "im stuck",
                        "don't understand", "dont understand", "no idea", "help me",
                        "lost", "stuck"]
    for phrase in confused_phrases:
        if phrase in lower:
            return ("No worries! Let me help you get started.\n\n"
                    "**If you're new**, the typical workflow is:\n"
                    "1. **Course Proposal** first — say *\"course proposal\"*\n"
                    "2. **Courseware** (AP, FG, LG, LP) — say *\"courseware\"*\n"
                    "3. **Assessment** — say *\"assessment\"*\n"
                    "4. **Slides & Brochure** — say *\"slides\"* or *\"brochure\"*\n\n"
                    "**If you already have a CP**, just tell me what you need — like *\"I need a facilitator guide\"*.\n\n"
                    "Or say **\"show me the full workflow\"** for the complete step-by-step process.")

    # Affirmative / conversational (yes, no, ok)
    affirmatives = ["yes", "yeah", "yep", "yup", "sure", "ok", "okay", "alright",
                    "sounds good", "let's go", "go ahead", "yes please", "do it"]
    negatives = ["no", "nope", "nah", "not now", "not yet", "later", "maybe later",
                 "no thanks", "no thank you", "not right now"]

    if lower in affirmatives:
        last_skill_name = st.session_state.get('_last_skill_name', '')
        if last_skill_name:
            return f"Taking you to the module now. You can also say **\"what's next\"** after you're done."
        return ("Great! What would you like to do? Just tell me — for example:\n"
                "- *\"Create a course proposal\"*\n"
                "- *\"Generate an assessment\"*\n"
                "- *\"Show me the full workflow\"*")

    if lower in negatives:
        return "No problem! Just let me know whenever you're ready. I'm here to help."

    # WSQ / domain knowledge questions (answer without API call)
    wsq_qa = _detect_wsq_question(lower)
    if wsq_qa:
        return wsq_qa

    return None


def _detect_wsq_question(lower: str):
    """Detect and answer common WSQ/courseware knowledge questions without API."""

    # What is WSQ
    if any(q in lower for q in ["what is wsq", "what's wsq", "whats wsq", "wsq meaning",
                                  "explain wsq", "tell me about wsq"]):
        return ("**WSQ (Workforce Skills Qualifications)** is Singapore's national credential system "
                "for training and skills certification.\n\n"
                "It is managed by **SkillsFuture Singapore (SSG)** and provides:\n"
                "- Nationally recognized certifications\n"
                "- Competency-based training standards\n"
                "- Industry-relevant skills frameworks\n\n"
                "This app helps you create all the courseware documents needed for WSQ-accredited courses.")

    # What is a Course Proposal
    if any(q in lower for q in ["what is a course proposal", "what's a course proposal",
                                  "what is cp", "what's cp", "explain course proposal",
                                  "what does cp contain", "purpose of course proposal"]):
        return ("A **Course Proposal (CP)** is the foundational document for a WSQ course.\n\n"
                "It contains:\n"
                "- **Course title and description**\n"
                "- **Learning outcomes** aligned to competency standards\n"
                "- **Module structure** and duration\n"
                "- **Entry requirements** for learners\n"
                "- **Assessment strategy** overview\n"
                "- **TSC (Training & Skills Competency)** references\n\n"
                "The CP must be approved before you create other courseware documents.\n\n"
                "Want to create one? Just say **\"create course proposal\"**.")

    # What is Assessment Plan
    if any(q in lower for q in ["what is an assessment plan", "what's an assessment plan",
                                  "what is ap", "what's ap", "explain assessment plan",
                                  "purpose of assessment plan"]):
        return ("An **Assessment Plan (AP)** outlines how learners will be assessed in a WSQ course.\n\n"
                "It includes:\n"
                "- **Assessment methods** (Written, Practical, Oral, etc.)\n"
                "- **Grading rubrics** and criteria\n"
                "- **Evidence requirements** for each competency\n"
                "- **Mapping to learning outcomes** from the CP\n\n"
                "The AP is generated from your approved Course Proposal.\n\n"
                "Want to create one? Just say **\"assessment plan\"**.")

    # What is Facilitator Guide
    if any(q in lower for q in ["what is a facilitator guide", "what's a facilitator guide",
                                  "what is fg", "what's fg", "explain facilitator guide",
                                  "purpose of facilitator guide"]):
        return ("A **Facilitator Guide (FG)** is the trainer's handbook for delivering a WSQ course.\n\n"
                "It includes:\n"
                "- **Session-by-session teaching instructions**\n"
                "- **Activity and discussion guidance**\n"
                "- **Key points** to emphasize\n"
                "- **Assessment integration** notes\n"
                "- **Timing and pacing** suggestions\n\n"
                "Want to create one? Just say **\"facilitator guide\"**.")

    # What is Learner Guide
    if any(q in lower for q in ["what is a learner guide", "what's a learner guide",
                                  "what is lg", "what's lg", "explain learner guide",
                                  "purpose of learner guide"]):
        return ("A **Learner Guide (LG)** is the student's course material for a WSQ course.\n\n"
                "It includes:\n"
                "- **Learning content** organized by session\n"
                "- **Exercises and activities**\n"
                "- **Self-assessment checkpoints**\n"
                "- **Key concepts and references**\n\n"
                "Want to create one? Just say **\"learner guide\"**.")

    # What is Lesson Plan
    if any(q in lower for q in ["what is a lesson plan", "what's a lesson plan",
                                  "what is lp", "what's lp", "explain lesson plan",
                                  "purpose of lesson plan"]):
        return ("A **Lesson Plan (LP)** is the detailed session schedule for a WSQ course.\n\n"
                "It includes:\n"
                "- **Session-by-session breakdown** with timing\n"
                "- **Activities and materials** per session\n"
                "- **Learning objectives** mapped to each session\n"
                "- **Assessment checkpoints**\n\n"
                "Want to create one? Just say **\"lesson plan\"**.")

    # What are the assessment types
    if any(q in lower for q in ["what assessment types", "types of assessment", "assessment methods",
                                  "what assessments can", "list of assessments", "assessment options",
                                  "how many assessment types", "what kinds of assessment"]):
        return ("This app supports **9 assessment types**:\n\n"
                "| Code | Type | Description |\n"
                "|------|------|-------------|\n"
                "| SAQ | Short Answer Questions | Written Q&A assessment |\n"
                "| CS | Case Study | Scenario-based analysis |\n"
                "| PP | Practical Performance | Hands-on skills demonstration |\n"
                "| PRJ | Project | Extended project with deliverables |\n"
                "| ASGN | Assignment | Written tasks with criteria |\n"
                "| OI | Oral Interview | Structured interview questions |\n"
                "| DEM | Demonstration | Observed hands-on tasks |\n"
                "| RP | Role Play | Simulated scenarios |\n"
                "| OQ | Oral Questioning | Verbal Q&A with probing |\n\n"
                "Want to create one? Just say **\"create assessment\"** and select the type.")

    # What documents do I need
    if any(q in lower for q in ["what documents do i need", "what files do i need",
                                  "what do i need to create", "list of documents",
                                  "what courseware do i need", "required documents",
                                  "what should i prepare", "documents needed"]):
        return ("For a complete WSQ course submission, you typically need:\n\n"
                "1. **Course Proposal (CP)** — The foundation document\n"
                "2. **Assessment Plan (AP)** — How learners are assessed\n"
                "3. **Facilitator Guide (FG)** — Trainer's handbook\n"
                "4. **Learner Guide (LG)** — Student materials\n"
                "5. **Lesson Plan (LP)** — Session schedule and timing\n"
                "6. **Assessment Materials** — SAQ, Case Studies, etc.\n"
                "7. **Presentation Slides** — For training delivery\n"
                "8. **Course Brochure** — For marketing\n\n"
                "Start with the **Course Proposal** and work through the rest.\n\n"
                "Say **\"show me the full workflow\"** for the recommended order.")

    # How does this app work / what can this app do
    if any(q in lower for q in ["how does this app work", "how does this work",
                                  "what can this app do", "what does this app do",
                                  "tell me about this app", "explain this app",
                                  "what is this app", "what is this tool"]):
        return ("This is the **WSQ Courseware Generator** — an AI-powered app that helps you create "
                "all the training documents needed for WSQ-accredited courses in Singapore.\n\n"
                "**What it does:**\n"
                "- Generates Course Proposals from TSC documents\n"
                "- Creates courseware (AP, FG, LG, LP) from approved CPs\n"
                "- Produces 9 types of assessment materials\n"
                "- Generates presentation slides via NotebookLM\n"
                "- Creates marketing brochures\n"
                "- Validates documents before submission\n\n"
                "**How to use it:**\n"
                "Just tell me what you need! For example:\n"
                "- *\"I want to create a course proposal\"*\n"
                "- *\"Generate a facilitator guide\"*\n"
                "- *\"I need an assessment\"*\n\n"
                "I'll guide you step by step and take you to the right page automatically.")

    # Difference between documents
    if any(q in lower for q in ["difference between fg and lg", "fg vs lg",
                                  "facilitator guide vs learner guide",
                                  "difference between ap and lp",
                                  "what's the difference"]):
        return ("Here's a quick comparison:\n\n"
                "| Document | For Whom | Purpose |\n"
                "|----------|----------|--------|\n"
                "| **Facilitator Guide (FG)** | Trainer | Teaching instructions, activities, timing |\n"
                "| **Learner Guide (LG)** | Student | Learning content, exercises, self-assessment |\n"
                "| **Assessment Plan (AP)** | Both | Assessment methods, rubrics, evidence requirements |\n"
                "| **Lesson Plan (LP)** | Trainer | Session schedule, timing, materials list |\n\n"
                "All are generated from your approved **Course Proposal (CP)**.")

    return None


def _build_skill_response(action_dict):
    """Build a rich response from a skill action, including next steps."""
    response = action_dict.get('response', '')
    next_steps = action_dict.get('next_steps', '')
    if next_steps:
        response += "\n\n---\n\n" + next_steps
    return response


def _detect_intent(prompt):
    """Detect user intent from natural language using the skills system."""
    return match_skill_by_keywords(prompt)


def handle_chat_logic(prompt):
    """Process chat message and get response from AI"""
    if not prompt or not prompt.strip():
        return

    # Check for skill commands using the skills loader (e.g. /generate_brochure)
    skill_action = get_skill_action(prompt.strip())
    if skill_action:
        st.session_state.chat_messages.append({"role": "user", "content": prompt})
        st.session_state.chat_messages.append({"role": "assistant", "content": _build_skill_response(skill_action)})
        if skill_action.get('navigate'):
            st.session_state['nav_to'] = skill_action['navigate']
            st.session_state['_last_skill_nav'] = skill_action['navigate']
        if skill_action.get('name'):
            st.session_state['_last_skill_name'] = skill_action['name']
        st.rerun()
        return

    # Check for greetings, help, workflow, and common conversational inputs (no API call needed)
    greeting_response = _detect_greeting_or_help(prompt.strip())
    if greeting_response:
        st.session_state.chat_messages.append({"role": "user", "content": prompt})
        st.session_state.chat_messages.append({"role": "assistant", "content": greeting_response})
        st.rerun()
        return

    # Check for natural language intent via skill keywords (e.g., "I want to generate a brochure")
    intent = _detect_intent(prompt.strip())
    if intent:
        st.session_state.chat_messages.append({"role": "user", "content": prompt})
        st.session_state.chat_messages.append({"role": "assistant", "content": _build_skill_response(intent)})
        if intent.get('navigate'):
            st.session_state['nav_to'] = intent['navigate']
            st.session_state['_last_skill_nav'] = intent['navigate']
        if intent.get('name'):
            st.session_state['_last_skill_name'] = intent['name']
        st.rerun()
        return

    # Add user message to history
    st.session_state.chat_messages.append({"role": "user", "content": prompt})

    try:
        from settings.api_manager import load_api_keys
        from settings.api_database import get_task_model_assignment, get_model_by_name

        api_keys = load_api_keys()

        # Check for specific Chatbot assignment first
        chatbot_assignment = get_task_model_assignment("chatbot")

        if chatbot_assignment:
            chat_model = chatbot_assignment.get("model_name")
            api_provider = chatbot_assignment.get("api_provider", "OPENROUTER")
        else:
            # Fallback to selected model (which handles page-specific or global defaults)
            chat_model = st.session_state.get('selected_model')
            api_provider = st.session_state.get('selected_api_provider', 'OPENROUTER')

        api_key = api_keys.get(f"{api_provider}_API_KEY", "")

        if not chat_model:
            st.session_state.chat_messages.append({
                "role": "assistant",
                "content": ("No AI model assigned for the chatbot yet.\n\n"
                            "**To set one up:** Go to **Settings** > **Model Assignment** and assign a model to the **Chatbot** task.\n\n"
                            "**In the meantime**, I can still help! Try:\n"
                            "- **\"help\"** — See all features\n"
                            "- **\"workflow\"** — See the full process\n"
                            "- **\"I need a course proposal\"** — I'll navigate you there\n"
                            "- **\"What is WSQ?\"** — Learn about WSQ")
            })
        elif api_key:
            # Get the model ID from database
            model_info = get_model_by_name(chat_model)
            # model_id is in config.model, not at top level
            if model_info and model_info.get("config"):
                model_id = model_info["config"].get("model", chat_model)
            else:
                model_id = chat_model

            # Build messages list for chat
            messages = []
            for msg in st.session_state.chat_messages:
                messages.append({"role": msg["role"], "content": msg["content"]})

            # Use appropriate SDK based on provider
            with st.spinner("Thinking..."):
                if api_provider == "ANTHROPIC":
                    # Use Anthropic's native SDK
                    assistant_message = _call_anthropic_chat(api_key, model_id, messages)
                elif api_provider == "GEMINI":
                    # Use Google's native Generative AI SDK
                    assistant_message = _call_gemini_chat(api_key, model_id, messages)
                else:
                    # Use OpenAI-compatible SDK for other providers (OpenRouter, OpenAI, Groq, Grok, DeepSeek)
                    assistant_message = _call_openai_compatible_chat(api_key, api_provider, model_id, messages)

            # Parse ACTION tags for auto-navigation
            import re
            action_match = re.search(r'\[ACTION:navigate=(.+?)\]', assistant_message)
            if action_match:
                nav_target = action_match.group(1)
                # Remove the ACTION tag from displayed message
                assistant_message = re.sub(r'\[ACTION:navigate=.+?\]', '', assistant_message).strip()
                st.session_state['nav_to'] = nav_target

            st.session_state.chat_messages.append({"role": "assistant", "content": assistant_message})
        else:
            st.session_state.chat_messages.append({
                "role": "assistant",
                "content": (f"**{api_provider} API key** is not configured yet.\n\n"
                            f"**To fix:** Go to **Settings** > **API Configuration** and add your {api_provider} API key.\n\n"
                            "**Free options:** Use OpenRouter with free models (Gemini 2.5 Pro, Llama 4, DeepSeek V3) — no credits needed!\n\n"
                            "**Meanwhile**, I can still help with navigation and guidance. Try asking me anything about the WSQ workflow!")
            })
    except Exception as e:
        error_msg = str(e)
        # Detect billing/quota errors and provide helpful fallback
        if any(code in error_msg for code in ["402", "429", "Insufficient Balance", "quota", "exceeded", "RESOURCE_EXHAUSTED"]):
            fallback = ("I'm unable to connect to the AI model right now (API quota/credits exceeded).\n\n"
                        "**But I can still help!** Try asking me:\n"
                        "- **\"What is WSQ?\"** or **\"What is a course proposal?\"**\n"
                        "- **\"Show me the workflow\"** for the full process\n"
                        "- **\"I need a brochure\"** and I'll navigate you there\n"
                        "- **\"What assessment types are available?\"**\n\n"
                        "Most navigation and guidance works without API credits. "
                        "To restore full chat, top up your API credits or switch to a free model in **Settings**.")
            st.session_state.chat_messages.append({"role": "assistant", "content": fallback})
        else:
            st.session_state.chat_messages.append({
                "role": "assistant",
                "content": f"Error: {error_msg}"
            })
    st.rerun()


def _call_anthropic_chat(api_key: str, model_id: str, messages: list) -> str:
    """Call Anthropic's native API for chat"""
    try:
        from anthropic import Anthropic

        client = Anthropic(api_key=api_key)

        # Anthropic expects system message separately
        system_message = get_chatbot_system_message()

        # Convert messages format (Anthropic doesn't use 'system' role in messages)
        anthropic_messages = []
        for msg in messages:
            if msg["role"] in ["user", "assistant"]:
                anthropic_messages.append({
                    "role": msg["role"],
                    "content": msg["content"]
                })

        response = client.messages.create(
            model=model_id,
            max_tokens=1024,
            system=system_message,
            messages=anthropic_messages
        )

        return response.content[0].text
    except Exception as e:
        raise Exception(f"Anthropic API error: {str(e)}")


def _call_gemini_chat(api_key: str, model_id: str, messages: list) -> str:
    """Call Google's Gemini API for chat"""
    try:
        import google.generativeai as genai

        genai.configure(api_key=api_key)

        # Create the model - handle model_id format (might have 'google/' prefix)
        if model_id.startswith("google/"):
            model_id = model_id.replace("google/", "")

        model = genai.GenerativeModel(
            model_name=model_id,
            system_instruction=get_chatbot_system_message()
        )

        # Convert messages to Gemini format
        gemini_history = []
        current_message = None

        for msg in messages[:-1]:  # All messages except the last one go into history
            if msg["role"] == "user":
                gemini_history.append({"role": "user", "parts": [msg["content"]]})
            elif msg["role"] == "assistant":
                gemini_history.append({"role": "model", "parts": [msg["content"]]})

        # Get the last user message
        if messages and messages[-1]["role"] == "user":
            current_message = messages[-1]["content"]
        else:
            current_message = messages[-1]["content"] if messages else ""

        # Start chat with history
        chat = model.start_chat(history=gemini_history)
        response = chat.send_message(current_message)

        return response.text
    except Exception as e:
        raise Exception(f"Gemini API error: {str(e)}")


def _call_openai_compatible_chat(api_key: str, api_provider: str, model_id: str, messages: list) -> str:
    """Call OpenAI-compatible API for chat (OpenRouter, OpenAI, Groq, Grok, DeepSeek)"""
    try:
        from openai import OpenAI

        # Provider base URLs (all OpenAI-compatible)
        base_urls = {
            "OPENROUTER": "https://openrouter.ai/api/v1",
            "OPENAI": "https://api.openai.com/v1",
            "GROQ": "https://api.groq.com/openai/v1",
            "GROK": "https://api.x.ai/v1",
            "DEEPSEEK": "https://api.deepseek.com/v1",
        }

        base_url = base_urls.get(api_provider, "https://openrouter.ai/api/v1")

        client = OpenAI(api_key=api_key, base_url=base_url)

        # Add system message if not present
        chat_messages = [{"role": "system", "content": get_chatbot_system_message()}]
        chat_messages.extend(messages)

        response = client.chat.completions.create(
            model=model_id,
            messages=chat_messages,
            max_tokens=1024
        )

        return response.choices[0].message.content
    except Exception as e:
        raise Exception(f"{api_provider} API error: {str(e)}")

def _render_markdown_to_html(content):
    """Convert markdown content to styled HTML for chat bubbles."""
    import re as _re
    lines = content.split('\n')
    html_lines = []
    in_list = False
    in_table = False

    for line in lines:
        stripped = line.strip()

        # Horizontal rule (---)
        if stripped == '---':
            if in_list:
                html_lines.append('</ul>')
                in_list = False
            if in_table:
                html_lines.append('</table>')
                in_table = False
            html_lines.append('<hr style="border:none; border-top:1px solid #ddd; margin:0.5rem 0;">')
            continue

        # Skip markdown table separator rows (|---|---|)
        if _re.match(r'^\|[\s\-:|]+\|$', stripped):
            continue

        # Handle markdown table rows (| col1 | col2 |)
        if stripped.startswith('|') and stripped.endswith('|'):
            cells = [c.strip() for c in stripped.strip('|').split('|')]
            if not in_table:
                html_lines.append('<table style="width:100%; border-collapse:collapse; font-size:0.88rem; margin:0.25rem 0;">')
                html_lines.append('<tr style="border-bottom:1px solid #ccc;">')
                for cell in cells:
                    cell = _re.sub(r'\*\*(.+?)\*\*', r'<strong>\1</strong>', cell)
                    html_lines.append(f'<td style="padding:4px 8px;"><strong>{cell}</strong></td>')
                html_lines.append('</tr>')
                in_table = True
            else:
                html_lines.append('<tr style="border-bottom:1px solid #eee;">')
                for cell in cells:
                    cell = _re.sub(r'\*\*(.+?)\*\*', r'<strong>\1</strong>', cell)
                    html_lines.append(f'<td style="padding:4px 8px;">{cell}</td>')
                html_lines.append('</tr>')
            continue

        # Close table if we were in one
        if in_table:
            html_lines.append('</table>')
            in_table = False

        # Numbered list items (e.g., "**Step 1.** ...")
        num_match = _re.match(r'^\*\*Step\s+(\d+)\.\*\*\s+(.+)', stripped)

        # Bullet points
        if stripped.startswith('- ') or stripped.startswith('* '):
            if not in_list:
                html_lines.append('<ul style="margin:0.25rem 0; padding-left:1.2rem;">')
                in_list = True
            item = stripped[2:]
            item = _re.sub(r'\*\*(.+?)\*\*', r'<strong>\1</strong>', item)
            item = _re.sub(r'\*(.+?)\*', r'<em>\1</em>', item)
            html_lines.append(f'<li style="margin-bottom:0.2rem;">{item}</li>')
        else:
            if in_list:
                html_lines.append('</ul>')
                in_list = False
            if stripped:
                # Bold and italic text
                stripped = _re.sub(r'\*\*(.+?)\*\*', r'<strong>\1</strong>', stripped)
                stripped = _re.sub(r'\*(.+?)\*', r'<em>\1</em>', stripped)
                html_lines.append(f'<p style="margin:0.25rem 0">{stripped}</p>')
            else:
                html_lines.append('<br>')

    if in_list:
        html_lines.append('</ul>')
    if in_table:
        html_lines.append('</table>')
    return ''.join(html_lines)


def display_bottom_chatbot():
    """Display a permanent chatbot at the bottom of the page"""
    # Initialize session state
    if "chat_messages" not in st.session_state:
        st.session_state.chat_messages = []

    # Track expander state - keep open after sending messages
    if "chat_expander_open" not in st.session_state:
        st.session_state.chat_expander_open = False

    # Auto-open expander if there are messages (user just sent one)
    if st.session_state.chat_messages:
        st.session_state.chat_expander_open = True

    # Chat bubble styling - polished design
    st.markdown("""
        <style>
            /* User messages - right aligned */
            .chat-user {
                display: flex;
                justify-content: flex-end;
                margin-bottom: 0.6rem;
            }
            .chat-user .chat-bubble {
                background: linear-gradient(135deg, #2563eb, #1d4ed8);
                color: white;
                padding: 0.7rem 1rem;
                border-radius: 1.2rem 1.2rem 0.3rem 1.2rem;
                max-width: 75%;
                word-wrap: break-word;
                box-shadow: 0 1px 3px rgba(0,0,0,0.12);
                font-size: 0.92rem;
                line-height: 1.5;
            }
            /* Assistant messages - left aligned */
            .chat-assistant {
                display: flex;
                justify-content: flex-start;
                margin-bottom: 0.6rem;
            }
            .chat-assistant .chat-bubble {
                background: linear-gradient(135deg, #f8f9fa, #f0f0f0);
                color: #1a1a1a;
                padding: 0.7rem 1rem;
                border-radius: 1.2rem 1.2rem 1.2rem 0.3rem;
                max-width: 80%;
                word-wrap: break-word;
                box-shadow: 0 1px 3px rgba(0,0,0,0.08);
                font-size: 0.92rem;
                line-height: 1.5;
            }
            .chat-assistant .chat-bubble p,
            .chat-assistant .chat-bubble li {
                color: #1a1a1a;
            }
            .chat-assistant .chat-bubble hr {
                border: none;
                border-top: 1px solid #ddd;
                margin: 0.5rem 0;
            }
            .chat-assistant .chat-bubble table {
                margin: 0.3rem 0;
            }
            .chat-assistant .chat-bubble ul {
                margin: 0.3rem 0;
                padding-left: 1.2rem;
            }
            /* Welcome card styling */
            .welcome-card {
                background: linear-gradient(135deg, #f8f9fa, #e9ecef);
                border-radius: 1.2rem;
                padding: 1.2rem 1.2rem 0.8rem 1.2rem;
                max-width: 85%;
                box-shadow: 0 2px 8px rgba(0,0,0,0.08);
                line-height: 1.5;
            }
            .welcome-card .welcome-title {
                font-size: 1.1rem;
                font-weight: 700;
                color: #1a1a1a;
                margin-bottom: 0.4rem;
            }
            .welcome-card .welcome-subtitle {
                font-size: 0.88rem;
                color: #555;
                margin-bottom: 0.75rem;
            }
            .welcome-card .module-row {
                display: flex;
                align-items: center;
                padding: 6px 0;
                border-bottom: 1px solid #e0e0e0;
            }
            .welcome-card .module-row:last-child {
                border-bottom: none;
            }
            .welcome-card .module-icon {
                font-size: 1.1rem;
                width: 30px;
                text-align: center;
                flex-shrink: 0;
            }
            .welcome-card .module-name {
                font-weight: 600;
                color: #1a1a1a;
                min-width: 140px;
                font-size: 0.88rem;
            }
            .welcome-card .module-desc {
                color: #666;
                font-size: 0.82rem;
            }
            .welcome-card .hint-box {
                margin-top: 0.75rem;
                padding: 8px 12px;
                background: #dbeafe;
                border-radius: 8px;
                font-size: 0.83rem;
                color: #1e40af;
            }
            .welcome-card .workflow-hint {
                margin-top: 0.5rem;
                font-size: 0.8rem;
                color: #888;
            }
        </style>
    """, unsafe_allow_html=True)

    with st.expander("💬 AI Assistant — Tell me what you need", expanded=st.session_state.chat_expander_open):
        # Chat messages display (scrollable container)
        messages_container = st.container(height=380)
        with messages_container:
            if not st.session_state.chat_messages:
                st.markdown("""
                <div class="chat-assistant"><div class="welcome-card">
                    <div class="welcome-title">Hi! I'm your WSQ Courseware Assistant.</div>
                    <div class="welcome-subtitle">Tell me what you need and I'll guide you step-by-step.</div>
                    <div class="module-row"><span class="module-icon">📄</span><span class="module-name">Course Proposal</span><span class="module-desc">Create CP from TSC documents</span></div>
                    <div class="module-row"><span class="module-icon">📚</span><span class="module-name">Courseware</span><span class="module-desc">Generate AP, FG, LG, or LP</span></div>
                    <div class="module-row"><span class="module-icon">✅</span><span class="module-name">Assessment</span><span class="module-desc">SAQ, Case Study, Role Play + 6 more</span></div>
                    <div class="module-row"><span class="module-icon">🎯</span><span class="module-name">Slides</span><span class="module-desc">Create PowerPoint presentations</span></div>
                    <div class="module-row"><span class="module-icon">📰</span><span class="module-name">Brochure</span><span class="module-desc">Design a course brochure</span></div>
                    <div class="module-row"><span class="module-icon">📎</span><span class="module-name">Add Assessment to AP</span><span class="module-desc">Attach assessments as annexes</span></div>
                    <div class="module-row"><span class="module-icon">🔍</span><span class="module-name">Check Documents</span><span class="module-desc">Validate before submission</span></div>
                    <div class="hint-box">
                        <strong>Try saying:</strong> <em>"I want to generate a brochure"</em> or <em>"Create an assessment"</em><br>
                        I'll show you what's needed and take you to the right page.
                    </div>
                    <div class="workflow-hint">Tip: Say <strong>"show me the full workflow"</strong> to see the recommended step-by-step process.</div>
                </div></div>
                """, unsafe_allow_html=True)
            for msg in st.session_state.chat_messages:
                if msg["role"] == "user":
                    st.markdown(f'<div class="chat-user"><div class="chat-bubble">{msg["content"]}</div></div>', unsafe_allow_html=True)
                else:
                    html_content = _render_markdown_to_html(msg["content"])
                    st.markdown(f'<div class="chat-assistant"><div class="chat-bubble">{html_content}</div></div>', unsafe_allow_html=True)

        # Quick action buttons
        if not st.session_state.chat_messages:
            # Row 1: Main actions
            qa_row1 = [
                ("📄 Course Proposal", "I want to create a course proposal"),
                ("📚 Courseware", "I want to generate courseware"),
                ("✅ Assessment", "I want to create an assessment"),
                ("🎯 Slides", "I want to generate slides"),
            ]
            cols1 = st.columns(len(qa_row1))
            for idx, (label, msg) in enumerate(qa_row1):
                with cols1[idx]:
                    if st.button(label, key=f"quick_{idx}", use_container_width=True):
                        st.session_state.chat_expander_open = True
                        st.session_state["_pending_chat_msg"] = msg
                        st.rerun()
            # Row 2: Secondary actions
            qa_row2 = [
                ("📰 Brochure", "I want to generate a brochure"),
                ("📎 Add to AP", "I want to add assessment to ap"),
                ("🔍 Check Docs", "I want to check my documents"),
                ("🗺️ Full Workflow", "Show me the full workflow"),
            ]
            cols2 = st.columns(len(qa_row2))
            for idx, (label, msg) in enumerate(qa_row2):
                with cols2[idx]:
                    if st.button(label, key=f"quick2_{idx}", use_container_width=True):
                        st.session_state.chat_expander_open = True
                        st.session_state["_pending_chat_msg"] = msg
                        st.rerun()

        # Input row with text input, send button, and clear button
        col1, col2, col3 = st.columns([6, 0.6, 0.8])

        with col1:
            def send_message():
                user_input = st.session_state.get("chat_user_input", "")
                if user_input and user_input.strip():
                    st.session_state.chat_expander_open = True
                    st.session_state["_pending_chat_msg"] = user_input
                    st.session_state.chat_user_input = ""

            # Process pending message if exists
            if "_pending_chat_msg" in st.session_state:
                pending = st.session_state.pop("_pending_chat_msg")
                handle_chat_logic(pending)

            st.text_input(
                "Message",
                placeholder="Try: \"brochure\", \"assessment\", \"slides\", \"full workflow\", or ask anything...",
                key="chat_user_input",
                on_change=send_message,
                label_visibility="collapsed",
                autocomplete="new-password"
            )

        with col2:
            if st.button("➤", key="send_chat_btn", use_container_width=True, help="Send message"):
                user_input = st.session_state.get("chat_user_input", "")
                if user_input and user_input.strip():
                    st.session_state.chat_expander_open = True
                    st.session_state["_pending_chat_msg"] = user_input
                    st.session_state.chat_user_input = ""
                    st.rerun()

        with col3:
            if st.button("Clear", key="clear_chat_btn", use_container_width=True):
                st.session_state.chat_messages = []
                st.session_state.chat_expander_open = False
                st.session_state.pop('_last_skill_nav', None)
                st.session_state.pop('_last_skill_name', None)
                st.rerun()


st.set_page_config(layout="wide")

# Global CSS
st.markdown("""
<style>
    /* Sidebar styling - wider width */
    [data-testid="stSidebar"] { min-width: 350px; max-width: 350px; }
    [data-testid="stSidebar"] > div:first-child { width: 350px; }
    [data-testid="stSidebar"] hr { margin: 0.5rem 0 !important; }

    /* Disabled selectbox styling - keep text white */
    [data-testid="stSidebar"] [data-baseweb="select"] [aria-disabled="true"] {
        color: #ffffff !important;
        -webkit-text-fill-color: #ffffff !important;
        opacity: 1 !important;
    }

    [data-testid="stSidebar"] [data-baseweb="select"] [aria-disabled="true"] div {
        color: #ffffff !important;
        -webkit-text-fill-color: #ffffff !important;
    }
</style>
""", unsafe_allow_html=True)

# Initialize API system - cached
@st.cache_resource
def initialize_apis():
    try:
        from settings.api_manager import initialize_api_system
        initialize_api_system()
    except ImportError:
        pass

initialize_apis()

# Ensure built-in models are always up to date (runs on each session start)
if 'models_refreshed' not in st.session_state:
    try:
        from settings.api_database import refresh_builtin_models
        refresh_builtin_models()
        st.session_state['models_refreshed'] = True
    except Exception:
        pass

# Get organizations and setup company selection - cached
@st.cache_data
def get_cached_organizations():
    return get_organizations()

@st.cache_data
def get_cached_default_organization():
    return get_default_organization()

organizations = get_cached_organizations()
default_org = get_cached_default_organization()

with st.sidebar:
    # Company Selection
    if organizations:
        company_names = [org["name"] for org in organizations]

        # Find Tertiary Infotech as default company
        default_company_idx = 0
        for i, name in enumerate(company_names):
            if "tertiary infotech" in name.lower():
                default_company_idx = i
                break

        # Use default on first load, then respect user selection
        if 'selected_company_idx' not in st.session_state:
            st.session_state['selected_company_idx'] = default_company_idx

        # Validate stored index to prevent out-of-range errors
        if st.session_state['selected_company_idx'] >= len(organizations):
            st.session_state['selected_company_idx'] = default_company_idx

        selected_company_idx = st.selectbox(
            "Select Company:",
            range(len(company_names)),
            format_func=lambda x: company_names[x],
            index=st.session_state['selected_company_idx']
        )

        # Store selection in session state
        st.session_state['selected_company_idx'] = selected_company_idx
        selected_company = organizations[selected_company_idx]
    else:
        selected_company = default_org
        st.session_state['selected_company_idx'] = 0

    # Store selected company in session state for other modules
    st.session_state['selected_company'] = selected_company

    # Model Selection (no divider for compact layout)
    from settings.api_manager import get_all_available_models, get_all_api_key_configs, load_api_keys
    from settings.api_database import get_all_models as db_get_all_models, get_task_model_assignment

    # Mapping from menu names to task IDs
    MENU_TO_TASK_ID = {
        "Home": "chatbot",
        "Generate CP": "generate_cp",
        "Generate AP/FG/LG/LP": "generate_courseware",
        "Generate Assessment": "generate_assessment",
        "Generate Slides": "generate_slides",
        "Generate Brochure": "generate_brochure",
        "Add Assessment to AP": "add_assessment_ap",
        "Check Documents": "check_documents",
    }

    # Get all API key configurations and current keys
    api_key_configs = get_all_api_key_configs()
    current_keys = load_api_keys()

    # Build API provider options (only show configured ones first, then unconfigured)
    configured_providers = []
    unconfigured_providers = []
    for config in api_key_configs:
        provider_name = config["key_name"].replace("_API_KEY", "")
        display = config['display_name']
        is_configured = bool(current_keys.get(config["key_name"], ""))
        if is_configured:
            configured_providers.append((provider_name, display))
        else:
            unconfigured_providers.append((provider_name, f"{display} (No API Key)"))

    # Combine: configured first, then unconfigured
    all_providers = configured_providers + unconfigured_providers
    provider_names = [p[0] for p in all_providers]
    provider_display = [p[1] for p in all_providers]

    # Check if current menu has a model assignment
    current_menu = st.session_state.get('previous_menu_selection', 'Home')
    task_id = MENU_TO_TASK_ID.get(current_menu, None)
    task_assignment = get_task_model_assignment(task_id) if task_id else None

    # Fallback to Global Default if no specific task assignment
    if not task_assignment:
        task_assignment = get_task_model_assignment("global")

    # If task has an assignment, use it; otherwise use session state or default
    if task_assignment:
        assigned_provider = task_assignment.get("api_provider", "OPENROUTER")
        assigned_model = task_assignment.get("model_name", "")
        # Update session state to reflect the assignment
        st.session_state['selected_api_provider'] = assigned_provider
        st.session_state['assigned_model_for_task'] = assigned_model
    else:
        # Default to OPENROUTER if no assignment and no previous selection
        if 'selected_api_provider' not in st.session_state:
            st.session_state['selected_api_provider'] = "OPENROUTER"
        # Clear any task-specific model assignment
        if 'assigned_model_for_task' in st.session_state:
            del st.session_state['assigned_model_for_task']

    # Find index of current provider
    try:
        default_provider_idx = provider_names.index(st.session_state['selected_api_provider'])
    except ValueError:
        default_provider_idx = 0

    # API Provider selector (disabled if task has assignment)
    selected_provider_idx = st.selectbox(
        "API Provider:",
        range(len(provider_names)),
        format_func=lambda x: provider_display[x],
        index=default_provider_idx,
        help="Select which API key to use for models" + (" (Set by Model Assignment)" if task_assignment else ""),
        disabled=bool(task_assignment)
    )
    selected_provider = provider_names[selected_provider_idx]
    if not task_assignment:
        st.session_state['selected_api_provider'] = selected_provider

    # Get all models and filter by selected provider (only show enabled models)
    all_db_models = db_get_all_models(include_builtin=True)
    filtered_models = [m for m in all_db_models
                       if m.get("api_provider", "OPENROUTER") == st.session_state['selected_api_provider']
                       and m.get("is_enabled", True)]

    # If no models for this provider, show message
    if not filtered_models:
        st.warning(f"No models configured for {st.session_state['selected_api_provider']}. Add models in Settings → Add Custom Model.")
        model_names = []
        st.session_state['selected_model'] = None
        st.session_state['selected_model_config'] = None
    else:
        model_names = [m["name"] for m in filtered_models]

        # Determine which model to select
        # If task has an assignment, use assigned model
        if task_assignment and st.session_state.get('assigned_model_for_task') in model_names:
            current_idx = model_names.index(st.session_state['assigned_model_for_task'])
        elif 'user_selected_model' in st.session_state and st.session_state['user_selected_model'] in model_names:
            current_idx = model_names.index(st.session_state['user_selected_model'])
        else:
            current_idx = 0

        # Model selector (disabled if task has assignment)
        selected_model_idx = st.selectbox(
            "Select Model:",
            range(len(model_names)),
            format_func=lambda x: model_names[x],
            index=current_idx,
            disabled=bool(task_assignment)
        )

        # Track user's explicit model selection (only if no task assignment)
        if not task_assignment and model_names[selected_model_idx] != model_names[current_idx]:
            st.session_state['user_selected_model'] = model_names[selected_model_idx]

        # Store selection in session state
        st.session_state['selected_model'] = model_names[selected_model_idx]

        # Get full model config with API key
        all_models = get_all_available_models()
        if model_names[selected_model_idx] in all_models:
            st.session_state['selected_model_config'] = all_models[model_names[selected_model_idx]]
        else:
            st.session_state['selected_model_config'] = None

    # Show indicator if using model assignment
    if task_assignment:
        st.caption(f"📌 Using assigned model for {current_menu}")

    # Main features menu (no divider for compact layout)
    menu_options = [
        "Home",
        "Generate CP",
        "Generate AP/FG/LG/LP",
        "Generate Assessment",
        "Generate Slides",
        "Generate Brochure",
        "Add Assessment to AP",
        "Check Documents",
    ]

    menu_icons = [
        "house",
        "filetype-doc",
        "file-earmark-richtext",
        "clipboard-check",
        "easel",
        "file-earmark-pdf",
        "folder-symlink",
        "search",
    ]

    # Handle navigation from chatbot skills
    nav_to = st.session_state.get('nav_to', None)
    if nav_to and nav_to in menu_options:
        st.session_state['current_page'] = nav_to
        st.session_state['settings_page'] = None  # Clear settings page
        st.session_state['nav_to'] = None  # Clear after use

    # Initialize current page if not set
    if 'current_page' not in st.session_state:
        st.session_state['current_page'] = "Home"

    # Get the default index based on current page
    current_page = st.session_state['current_page']
    if current_page in menu_options:
        default_idx = menu_options.index(current_page)
    else:
        default_idx = 0

    selected = option_menu(
        "",  # Title of the sidebar
        menu_options,
        icons=menu_icons,
        menu_icon="boxes",  # Icon for the sidebar title
        default_index=default_idx,  # Default selected item
        key="main_nav_menu"
    )

    # Update current page when menu selection changes
    if selected != current_page:
        st.session_state['current_page'] = selected
        st.session_state['settings_page'] = None  # Clear settings page when navigating via menu
        current_page = selected  # Update local variable too
        st.rerun()  # Force rerun to update the page

    # Separate Settings section using buttons (compact)
    st.markdown("<hr style='margin: 0.5rem 0;'>", unsafe_allow_html=True)
    st.markdown("<div style='font-size: 0.85rem; font-weight: 600; margin-bottom: 0.3rem;'>Settings</div>", unsafe_allow_html=True)

    col1, col2 = st.columns(2)
    with col1:
        if st.button("API & Models", use_container_width=True):
            st.session_state['settings_page'] = "API & LLM Models"
            st.rerun()
    with col2:
        if st.button("Companies", use_container_width=True):
            st.session_state['settings_page'] = "Company Management"
            st.rerun()

    # Powered by footer
    st.markdown("---")
    st.markdown("""
        <div style='text-align: center; color: #888; font-size: 0.8rem;'>
            Powered by <b>Tertiary Infotech Academy Pte Ltd</b>
        </div>
    """, unsafe_allow_html=True)

# Track if user clicked on main menu (not just a rerun)
previous_menu = st.session_state.get('previous_menu_selection', None)
menu_changed = previous_menu is not None and previous_menu != selected
st.session_state['previous_menu_selection'] = selected

# If menu changed, clear settings page and rerun to navigate to the new page
if menu_changed:
    st.session_state['settings_page'] = None
    st.rerun()

# Check if a settings page is selected (takes priority over main menu)
settings_page = st.session_state.get('settings_page', None)

# Use current_page for navigation (more reliable than selected from option_menu)
page_to_display = st.session_state.get('current_page', 'Home')

# Main content area (full width)
# Display the selected app - using lazy loading for performance
if settings_page == "API & LLM Models":
    settings = lazy_import_settings()
    settings.llm_settings_app()

elif settings_page == "Company Management":
    company_settings = lazy_import_company_settings()
    company_settings.company_management_app()

elif page_to_display == "Home":
    st.session_state['settings_page'] = None
    display_homepage()

elif page_to_display == "Generate CP":
    st.session_state['settings_page'] = None
    course_proposal_app = lazy_import_course_proposal()
    course_proposal_app.app()

elif page_to_display == "Generate AP/FG/LG/LP":
    st.session_state['settings_page'] = None
    courseware_generation = lazy_import_courseware()
    courseware_generation.app()

elif page_to_display == "Generate Assessment":
    st.session_state['settings_page'] = None
    assessment_generation = lazy_import_assessment()
    assessment_generation.app()

elif page_to_display == "Generate Slides":
    st.session_state['settings_page'] = None
    slides_generation = lazy_import_slides()
    slides_generation.app()

elif page_to_display == "Check Documents":
    st.session_state['settings_page'] = None
    sup_doc = lazy_import_docs()
    sup_doc.app()

elif page_to_display == "Generate Brochure":
    st.session_state['settings_page'] = None
    brochure_generation = lazy_import_brochure_v2()
    brochure_generation.app()

elif page_to_display == "Add Assessment to AP":
    st.session_state['settings_page'] = None
    annex_assessment_v2 = lazy_import_annex_v2()
    annex_assessment_v2.app()

# Permanent chatbot at the bottom
st.divider()
display_bottom_chatbot()

