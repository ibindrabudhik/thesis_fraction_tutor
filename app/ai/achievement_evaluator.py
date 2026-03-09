"""Achievement level assessment using LLM analysis.

This module provides LLM-based evaluation of student performance
to determine achievement level (Low or High) based on:
- Answer correctness
- Problem-solving approach
- Number of errors made
- Quality of reasoning
"""
from __future__ import annotations

import json
import os
from functools import lru_cache
from typing import Dict, List

# Load environment variables from .env file if running outside Streamlit
try:
    from dotenv import load_dotenv
    load_dotenv()
except ImportError:
    pass  # dotenv not installed, will rely on system env vars or Streamlit secrets

try:
    from openai import OpenAI
    _OPENAI_USES_CLIENT = True
except ImportError:
    OpenAI = None
    import openai  # type: ignore
    _OPENAI_USES_CLIENT = False


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


def assess_achievement_level(
    problem: str,
    solution: str,
    student_answer: str,
    is_correct: bool,
    error_count: int,
    reasoning: str = ""
) -> Dict[str, object]:
    """
    Assess student's achievement level based on their performance.
    
    Uses LLM to analyze:
    1. Whether they solved correctly
    2. Number of attempts/errors made
    3. Quality of their approach and reasoning
    4. Understanding demonstrated
    
    Args:
        problem: The fraction problem statement
        solution: The correct solution
        student_answer: Student's submitted answer
        is_correct: Whether the answer was correct
        error_count: Number of errors made (0-3)
        reasoning: Optional evaluation reasoning from answer checker
        
    Returns:
        Dict with keys:
        - achievement_level: 'Low' or 'High'
        - confidence: 0.0-1.0
        - reasoning: Explanation of the assessment
    """
    
    assessment_prompt = f"""
You are an expert math education assessor. Evaluate a junior high school student's performance on an Fraction problem to determine their achievement level.

Problem: {problem}
Correct Solution: {solution}
Student's Answer: {student_answer}
Is Answer Correct: {'Yes' if is_correct else 'No'}
Number of Errors Made: {error_count}
Evaluation Notes: {reasoning if reasoning else 'None'}

Based on the information above, assess the student's achievement level as either 'Low' or 'High' considering:

1. **Correctness** (40% weight):
   - Solved correctly on first try = High indicator
   - Solved correctly after 1-2 errors = Medium indicator
   - Failed after 3 errors = Low indicator

2. **Problem-Solving Approach** (30% weight):
   - Shows systematic fractional thinking = High
   - Shows some understanding but makes mistakes = Medium
   - Shows confusion or fundamental misunderstanding = Low

3. **Error Pattern** (30% weight):
   - No errors or only minor calculation errors = High
   - Conceptual errors but can self-correct = Medium
   - Repeated conceptual errors = Low

Provide your assessment in JSON format:
{{
    "achievement_level": "High" or "Low",
    "confidence": 0.0-1.0,
    "reasoning": "Brief explanation (2-3 sentences) of why you assigned this level"
}}

Be encouraging in your reasoning, focusing on what the student demonstrated rather than what they lack.
""".strip()

    client = _get_openai_client()
    messages = [
        {"role": "system", "content": "You are an expert math education assessor for junior high school students."},
        {"role": "user", "content": assessment_prompt}
    ]

    try:
        if _OPENAI_USES_CLIENT:
            response = client.chat.completions.create(
                model="gpt-5",  # Fast and accurate for assessment
                messages=messages,
                temperature=0.3,  # Low temperature for consistent assessment
                max_completion_tokens=300,
                response_format={"type": "json_object"}
            )
            raw = response.choices[0].message.content or "{}"
        else:
            import openai
            response = client.ChatCompletion.create(
                model="gpt-5",
                messages=messages,
                temperature=0.3,
                max_tokens=300,
            )
            raw = response["choices"][0]["message"]["content"]

        result = json.loads(raw)
        
        # Validate achievement_level
        level = result.get("achievement_level", "Low")
        if level not in ["Low", "High"]:
            level = "Low"
        
        return {
            "achievement_level": level,
            "confidence": result.get("confidence", 0.5),
            "reasoning": result.get("reasoning", "Assessment completed based on performance analysis."),
        }
        
    except Exception as e:
        print(f"Error assessing achievement level: {e}")
        # Default to Low with low confidence on error
        return {
            "achievement_level": "Low",
            "confidence": 0.3,
            "reasoning": f"Unable to complete full assessment. Defaulting to Low level. Error: {str(e)[:50]}",
        }


def assess_achievement_level_from_session(
    problem: str,
    solution: str,
    chat_history: List[Dict[str, str]],
    final_is_correct: bool,
    error_count: int
) -> Dict[str, object]:
    """
    Assess achievement level based on entire session conversation.
    
    This variant analyzes the full conversation to better understand
    the student's learning progression.
    
    Args:
        problem: The fraction problem
        solution: Correct solution
        chat_history: List of message dicts with 'role' and 'content'
        final_is_correct: Final outcome (correct or 3 errors)
        error_count: Total errors made
        
    Returns:
        Dict with achievement_level, confidence, reasoning
    """
    
    # Extract student answers from chat
    student_messages = [
        msg["content"] for msg in chat_history
        if msg["role"] == "user"
    ]
    
    if not student_messages:
        return {
            "achievement_level": "Low",
            "confidence": 0.5,
            "reasoning": "No student responses to evaluate."
        }
    
    # Use the last student answer for assessment
    final_answer = student_messages[-1] if student_messages else ""
    
    # Get reasoning from conversation context
    reasoning = f"Student made {len(student_messages)} attempt(s) with {error_count} error(s)."
    
    return assess_achievement_level(
        problem=problem,
        solution=solution,
        student_answer=final_answer,
        is_correct=final_is_correct,
        error_count=error_count,
        reasoning=reasoning
    )
