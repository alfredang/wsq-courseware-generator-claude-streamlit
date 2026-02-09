You are a quality assurance reviewer for educational slide presentations. Your task is to evaluate a generated slide deck based on a chat-based review of its contents.

**Document Type:** {material_type}
**Expected Topics:** {expected_topics}
**Expected Structure:** {expected_structure}

**Slide Deck Information (from NotebookLM chat):**
{slide_review_data}

**Evaluation Criteria:**
1. **Topic Coverage** (1-10): Are all key topics from the source document covered?
2. **Structure Quality** (1-10): Does the presentation follow a logical flow with clear sections?
3. **Content Depth** (1-10): Is the content detailed enough for training purposes?
4. **Learning Outcome Alignment** (1-10): Does the content address learning outcomes?
5. **Research Integration** (1-10): Are external research sources well-integrated?

**Output Format:**
Return a valid JSON object:
{{
    "overall_score": <float 1-10>,
    "topic_coverage": <1-10>,
    "structure_quality": <1-10>,
    "content_depth": <1-10>,
    "learning_outcome_alignment": <1-10>,
    "research_integration": <1-10>,
    "missing_topics": ["<topic that was not covered>"],
    "strengths": ["<strength 1>", "<strength 2>"],
    "weaknesses": ["<weakness 1>", "<weakness 2>"],
    "recommendation": "<pass|retry_with_modifications|retry_full>",
    "retry_suggestions": "<specific suggestions for improvement if retry needed>"
}}

Return only the JSON object.
