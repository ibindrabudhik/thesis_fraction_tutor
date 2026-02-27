"""Feedback generation using LLM with formative feedback types."""
from __future__ import annotations

import json
import os
from functools import lru_cache
from typing import Dict, Sequence

# Load environment variables from .env file if running outside Streamlit
try:
    from dotenv import load_dotenv
    load_dotenv()
except ImportError:
    pass  # dotenv not installed, will rely on system env vars or Streamlit secrets

import streamlit as st

try:
    from openai import OpenAI
    _OPENAI_USES_CLIENT = True
except ImportError:
    OpenAI = None
    import openai  # type: ignore
    _OPENAI_USES_CLIENT = False

from ai.answer_evaluator import evaluate_student_answer
from ai.feedback_decision import choose_feedback_type
from ai.retrieval import retrieve_context

LLM_MODEL_NAME = "gpt-4o"
_DEFAULT_TOF = "Immediate"


class MissingAPIKeyError(RuntimeError):
    """Raised when the OpenAI API key cannot be located."""


def _read_openai_key() -> str:
    """Retrieve the OpenAI API key from environment variables or Streamlit secrets."""
    key = os.getenv("OPENAI_API_KEY")
    if not key:
        try:
            import streamlit as st
            key = st.secrets.get("OPENAI_API_KEY")
        except Exception:
            key = None
    if not key:
        raise MissingAPIKeyError(
            "OPENAI_API_KEY is missing. Set it via environment variable or Streamlit secrets."
        )
    return key


@lru_cache(maxsize=1)
def _get_openai_client():
    """Create a cached OpenAI client or module configured with the API key."""
    api_key = _read_openai_key()
    if _OPENAI_USES_CLIENT:
        return OpenAI(api_key=api_key)
    import openai  # type: ignore
    openai.api_key = api_key
    return openai


def _build_prompt(
    problem: str,
    problem_solution: str,
    student_profile: Dict[str, str],
    feedback_type: str,
    relevant_text: str,
    student_current_answer: str,
    number_of_errors: int = 0,
    evaluation_reasoning: str = "",
    previous_feedbacks: list = None,
) -> str:
    """Build the feedback generation prompt with all context."""
    spk = student_profile.get("spk", "Unknown")
    sal = student_profile.get("sal", "Unknown")
    student_answer = student_current_answer

    # Build previous feedback section if available
    previous_feedback_section = ""
    if previous_feedbacks:
        previous_feedback_section = "\n[Previous Feedback History - DO NOT REPEAT THESE]\n"
        for i, prev in enumerate(previous_feedbacks, 1):
            previous_feedback_section += f"""
Attempt {i}:
- Student Answer: {prev.get('student_answer', 'N/A')}
- Feedback Type: {prev.get('feedback_type', 'N/A')}
- Feedback Given: {prev.get('feedback_given', 'N/A')[:500]}...
"""
        previous_feedback_section += "\nIMPORTANT: Provide NEW insights, different approaches, or alternative explanations. Do NOT repeat the feedback above.\n"

    return f"""
#Explain task
Generate feedback for junior high school students who are solving fraction problems.
Follow these instructions carefully.

[Information about current problem]
Problem: {problem}
Solution: {problem_solution}

[Student Information]
Student Prior Knowledge (SPK): {spk}
Student Achievement Level (SAL): {sal}
Student Current Answer (SA): {student_answer}
Student Number of Errors: {number_of_errors}

[Feedback to provide]
Feedback Type: {feedback_type}
{previous_feedback_section}
[Relevant knowledge snippets]
{relevant_text}

[Answer Evaluation]
{evaluation_reasoning}

You must follow these steps:
1. Understand the problem and student information carefully.
2. Consider the answer evaluation above when identifying misconceptions.
3. Generate encouraging feedback in Bahasa Indonesia that matches the feedback type.
4. Do NOT reveal the final solution directly. Give the final solution only if the feedback type is "Correct Response".
5. Return the feedback in valid JSON with keys "Feedback Type" and "Feedback".
6. CRITICAL: ALL mathematical expressions MUST be wrapped in LaTeX delimiters. Use $...$ for inline math. For example: $\frac{{1}}{{2}}$, $\times$, $\div$, $3\frac{{1}}{{4}}$. NEVER write bare LaTeX commands like \frac or \times without $ delimiters.
7. Adopt the tone of a supportive peer tutor use more indonesian junior high school-friendly language.
8. If previous feedback is provided, make sure your feedback is DIFFERENT and provides NEW value.
9. Keep the feedback concise and focused not redundant. Take a look on student previous answer and feedbacks to avoid repetition.

Description about feedback:
Response-contingent is detailed comments that highlight the learner's particular response. It might explain why the right response is right and the incorrect one is incorrect. No formal error analysis is used here.
Topic-contingent is detailed feedback that gives the student details about the subject they are currently studying. This could just
mean reteaching the content.
Correct response is informs the student of the correct answer to the problem solved with no additional information.
Verification informs the students about the correctness of their response(s), such as right/wrong or overall percentage correct.
Try-again informs the student if they made an incorrect response and allows the student one or more attempts to answer the questions.

""".strip()


def _call_chat_model(messages: Sequence[Dict[str, str]], llm_model: str) -> str:
    """Call the chat model to generate feedback."""
    client = _get_openai_client()
    if _OPENAI_USES_CLIENT:
        response = client.chat.completions.create(
            model=llm_model,
            messages=list(messages),
            max_tokens=800,
            temperature=0.2,
        )
        return response.choices[0].message.content or ""

    import openai  # type: ignore
    response = client.ChatCompletion.create(
        model=llm_model,
        messages=list(messages),
        max_tokens=800,
        temperature=0.2,
    )
    return response["choices"][0]["message"]["content"]


def _extract_feedback(raw_response: str, fallback_type: str) -> Dict[str, str]:
    """Parse JSON feedback, handling Markdown fences and fallbacks."""
    cleaned = raw_response.strip()
    if cleaned.startswith("```"):
        parts = cleaned.strip("`").split("\n", 1)
        if len(parts) == 2:
            _, cleaned = parts
        cleaned = cleaned.strip()
        if cleaned.startswith("json"):
            cleaned = cleaned[4:].strip()

    try:
        payload = json.loads(cleaned)
        if isinstance(payload, dict):
            feedback_type = str(payload.get("Feedback Type", fallback_type)).strip()
            feedback_text = str(payload.get("Feedback", raw_response)).strip()
            return {
                "feedback_type": feedback_type or fallback_type,
                "feedback": feedback_text or raw_response,
                "raw": raw_response,
            }
    except json.JSONDecodeError:
        pass

    return {
        "feedback_type": fallback_type,
        "feedback": raw_response.strip(),
        "raw": raw_response,
    }


def generate_tutor_feedback(
    user_query: str,
    student_profile: Dict[str, str],
    current_problem: str,
    problem_solution: str,
    *,
    top_k: int = 3,
    llm_model: str = LLM_MODEL_NAME,
    previous_feedbacks: list = None,
) -> Dict[str, object]:
    """
    Main entry point to generate feedback for a student's answer.
    
    Args:
        user_query: The student's answer to evaluate
        student_profile: Dict with keys 'spk', 'sal', 'tof'
        current_problem: The problem statement
        problem_solution: The correct solution
        top_k: Number of context chunks to retrieve
        llm_model: LLM model to use for feedback generation
        previous_feedbacks: List of previous feedback dicts to avoid repetition
        
    Returns:
        Dict containing feedback, contexts, evaluation, and metadata
    """
    if not user_query.strip():
        raise ValueError("User query must not be empty.")

    tof = student_profile.get("tof") or _DEFAULT_TOF

    # Use LLM to evaluate the answer for correctness
    print("User Query:", user_query.strip())
    print("Problem Solution:", problem_solution.strip())
    
    evaluation = evaluate_student_answer(
        student_answer=user_query.strip(),
        correct_solution=problem_solution.strip(),
        problem=current_problem
    )
    
    is_correct = evaluation["is_correct"]
    confidence = evaluation["confidence"]
    
    print(f"Evaluation: is_correct={is_correct}, confidence={confidence:.2f}")
    print(f"Reasoning: {evaluation['reasoning']}")

    # Adjust error counting based on correctness
    if not is_correct:
        st.session_state.error_count += 1
    else:
        st.session_state.error_count = 0  # Reset on correct answer

    # Use original feedback type decision logic
    if st.session_state.error_count >= 3:
        feedback_type = "Correct Response"
    elif is_correct:
        feedback_type = "Correct Response"
    else:
        feedback_type = choose_feedback_type(
            student_profile.get("spk", "Unknown"),
            student_profile.get("sal", "Unknown"),
            tof,
        )

    # Retrieve relevant context from knowledge base
    student_current_answer = f"{user_query}"
    contexts = retrieve_context(student_current_answer, top_k=top_k)

    relevant_text = "No relevant context found." if not contexts else "\n\n---\n\n".join(
        ctx["text"] for ctx in contexts
    )
    
    # Build the prompt with all information including previous feedbacks
    prompt = _build_prompt(
        current_problem, 
        problem_solution, 
        student_profile, 
        feedback_type, 
        relevant_text, 
        student_current_answer, 
        number_of_errors=st.session_state.error_count,
        evaluation_reasoning=evaluation["reasoning"],
        previous_feedbacks=previous_feedbacks
    )
    print(prompt)

    # Generate feedback using LLM
    messages = [
        {"role": "system", "content": "You are an expert fraction tutor."},
        {"role": "user", "content": prompt},
    ]

    raw_response = _call_chat_model(messages, llm_model)
    feedback_payload = _extract_feedback(raw_response, feedback_type)

    return {
        **feedback_payload,
        "contexts": contexts,
        "feedback_type_decision": feedback_type,
        "tof": tof,
        "evaluation": evaluation,  # Include evaluation details for debugging/logging
    }
