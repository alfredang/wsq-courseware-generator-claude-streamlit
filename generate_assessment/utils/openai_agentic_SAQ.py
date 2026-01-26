"""
OpenAI SDK-based Short-Answer Question (SAQ) Generation Module.

This module replaces the Autogen-based agentic_SAQ.py with direct OpenAI SDK implementations.
Uses JSON mode for OpenRouter compatibility.

Author: Migration from Autogen to OpenAI SDK
Date: 2026-01-20
"""

import asyncio
import json
from generate_assessment.utils.pydantic_models import FacilitatorGuideExtraction
from common.common import parse_json_content
from generate_cp.utils.openai_model_client import create_openai_client


def get_topics_for_all_k_statements(fg_data):
    """
    Retrieves all topics associated with each Knowledge Statement (K statement).
    """
    k_to_topics = {}

    print(f"DEBUG SAQ: Extracting K statements from {len(fg_data.get('learning_units', []))} learning units")

    for lu in fg_data["learning_units"]:
        lu_title = lu.get("learning_unit_title", "Unknown LU")
        print(f"DEBUG SAQ: Processing LU: {lu_title}")

        for topic in lu["topics"]:
            topic_name = topic.get("name", "Unknown Topic")
            k_statements = topic.get("tsc_knowledges", [])
            print(f"  Topic: {topic_name} - {len(k_statements)} K statements")

            for k in k_statements:
                k_id = f"{k['id']}: {k['text']}"
                print(f"    Found K: {k['id']} - {k['text'][:50]}...")

                if k_id not in k_to_topics:
                    k_to_topics[k_id] = []
                k_to_topics[k_id].append(topic["name"])

    print(f"DEBUG SAQ: Total unique K statements extracted: {len(k_to_topics)}")
    print(f"DEBUG SAQ: K IDs: {[k.split(':')[0] for k in k_to_topics.keys()]}")

    return k_to_topics


async def retrieve_content_for_knowledge_statement_async(k_topics, index):
    """
    Retrieves course content relevant to each Knowledge Statement asynchronously.
    """
    if index is not None:
        query_engine = index.as_query_engine(
            similarity_top_k=15,
            verbose=True,
            response_mode="compact",
        )
    else:
        query_engine = None

    async def query_index(k_statement, topics):
        if not topics or query_engine is None:
            return k_statement, "⚠️ No slide deck content available. Assessment generated from Facilitator Guide only."

        topics_str = ", ".join(topics)
        query = f"""
        Show me all module content aligning with {topics_str} in full detail.
        Retrieve ALL available content as it appears in the source without summarizing or omitting any details.
        """
        response = await query_engine.aquery(query)

        if not response or not response.source_nodes:
            return k_statement, "⚠️ No relevant information found."

        markdown_result = "\n\n".join([
            f"### Page {node.metadata.get('page', 'Unknown')}\n{node.text}"
            for node in response.source_nodes
        ])

        return k_statement, markdown_result

    tasks = [query_index(k, topics) for k, topics in k_topics.items()]
    results = await asyncio.gather(*tasks)

    return dict(results)


async def generate_saq_for_k_openai(client, config, course_title, assessment_duration, k_statement, content):
    """
    Generates a short-answer question (SAQ) and answer pair using OpenAI SDK.
    """
    system_message = """
    You are an expert at creating simple, clear short-answer questions.

    Guidelines:
    1. Keep questions SIMPLE and DIRECT - avoid complex scenarios
    2. Create a brief 1-2 sentence scenario that relates to the knowledge statement
    3. Ask ONE clear question that can be answered in 3-5 bullet points
    4. Answers should be short, practical bullet points (5-10 words each)
    5. Base your answer on the retrieved content, but keep it simple and easy to understand
    6. Do not mention sources or references in the scenario or question

    You must return valid JSON with this structure:
    {
        "scenario": "<simple 1-2 sentence scenario>",
        "question_statement": "<simple, direct question>",
        "knowledge_id": "<knowledge_id>",
        "answer": ["<short bullet point 1>", "<short bullet point 2>", "<short bullet point 3>"]
    }
    """

    user_task = f"""
    Please generate one question-answer pair using the following:
    - Course Title: '{course_title}'
    - Assessment duration: '{assessment_duration}',
    - Knowledge Statement: '{k_statement}'
    - Retrieved Content: {content}

    Instructions:
    1. Craft a realistic scenario in 2-3 sentences that provides context related to the retrieved content, but also explicitly addresses the knowledge statement.
    2. Even if the retrieved content or course title seems unrelated to the knowledge statement, creatively bridge the gap by inferring or using general knowledge.
    3. Formulate a single, straightforward short-answer question that aligns the knowledge statement with the scenario.
    4. Provide concise, practical bullet points as the answer.
    Return the question and answer as a JSON object directly.
    """

    try:
        completion = client.chat.completions.create(
            model=config["model"],
            temperature=config["temperature"],
            messages=[
                {"role": "system", "content": system_message},
                {"role": "user", "content": user_task}
            ],
            response_format={"type": "json_object"}
        )

        content_response = completion.choices[0].message.content
        qa_result = parse_json_content(content_response)

        if qa_result is None or not isinstance(qa_result, dict):
            raise ValueError(f"Failed to parse SAQ response for {k_statement}")

        return {
            "scenario": qa_result.get("scenario", "Scenario not provided."),
            "question_statement": qa_result.get("question_statement", "Question not provided."),
            "knowledge_id": k_statement.split(":")[0],
            "answer": qa_result.get("answer", ["Answer not available."])
        }

    except Exception as e:
        print(f"Error generating SAQ for {k_statement}: {e}")
        return None


async def generate_saq(extracted_data: FacilitatorGuideExtraction, index, model_client, model_choice: str = "DeepSeek-Chat"):
    """
    Generates a full set of short-answer questions (SAQs) using OpenAI SDK.

    Args:
        extracted_data: Parsed Facilitator Guide data
        index: Slides data (optional, not used in current version)
        model_client: Legacy parameter (not used in OpenAI SDK version)
        model_choice: Model selection string

    Returns:
        dict: Structured dictionary with course_title, duration, and questions
    """
    client, config = create_openai_client(model_choice)
    extracted_data = dict(extracted_data)

    k_topics = get_topics_for_all_k_statements(extracted_data)
    k_content_dict = await retrieve_content_for_knowledge_statement_async(k_topics, index)

    assessment_duration = next(
        (assessment.get("duration", "") for assessment in extracted_data.get("assessments", []) if "SAQ" in assessment.get("code", "")),
        ""
    )

    # Generate questions sequentially (OpenAI SDK doesn't have the same async agent pattern)
    questions = []
    for k, content in k_content_dict.items():
        print(f"DEBUG SAQ: Generating question for {k.split(':')[0]}...")
        result = await generate_saq_for_k_openai(
            client, config, extracted_data["course_title"],
            assessment_duration, k, content
        )
        if result:
            questions.append(result)

    print(f"DEBUG SAQ: Successfully generated {len(questions)} questions")
    print(f"DEBUG SAQ: Total K statements: {len(k_content_dict)}")

    return {
        "course_title": extracted_data["course_title"],
        "duration": assessment_duration,
        "questions": questions
    }
