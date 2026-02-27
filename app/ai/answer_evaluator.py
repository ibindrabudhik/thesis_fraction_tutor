"""Answer evaluation using LLM to check mathematical correctness."""
from __future__ import annotations

import json
import os
from functools import lru_cache
from typing import Dict

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


def evaluate_student_answer(
    student_answer: str,
    correct_solution: str,
    problem: str,
) -> Dict[str, object]:
    """
    Use LLM to evaluate if student answer is mathematically equivalent to the solution.
    Returns correctness assessment and reasoning.
    """
    evaluation_prompt = f"""
You are a math teacher evaluating a student's answer to an fraction problem.

Problem: {problem}
Correct Solution: {correct_solution}
Student Answer: {student_answer}

Evaluate if the student's answer is mathematically correct and equivalent to the solution.
Consider:
1. Mathematical equivalence (e.g., "x=5" equals "5=x")
2. Simplified vs unsimplified forms (e.g., "2x+4" equals "2(x+2)")
3. Format differences (spaces, notation)
4. Partial correctness or work shown

Respond in JSON format:
{{
    "is_correct": true/false,
    "confidence": 0.0-1.0,
    "reasoning": "Brief explanation of why it's correct/incorrect",
    "has_method_error": true/false,
    "has_calculation_error": true/false
}}
""".strip()

    client = _get_openai_client()
    messages = [
        {"role": "system", "content": "You are an expert math teacher."},
        {"role": "user", "content": evaluation_prompt}
    ]

    try:
        if _OPENAI_USES_CLIENT:
            response = client.chat.completions.create(
                model="gpt-4o-mini",  # Cheaper and faster for evaluation
                messages=messages,
                temperature=0,
                max_tokens=300,
                response_format={"type": "json_object"}
            )
            raw = response.choices[0].message.content or "{}"
        else:
            import openai
            response = client.ChatCompletion.create(
                model="gpt-4o-mini",
                messages=messages,
                temperature=0,
                max_tokens=300,
            )
            raw = response["choices"][0]["message"]["content"]

        result = json.loads(raw)
        return {
            "is_correct": result.get("is_correct", False),
            "confidence": result.get("confidence", 0.0),
            "reasoning": result.get("reasoning", ""),
            "has_method_error": result.get("has_method_error", False),
            "has_calculation_error": result.get("has_calculation_error", False),
        }
    except Exception as e:
        print(f"Error evaluating answer: {e}")
        return {
            "is_correct": False,
            "confidence": 0.0,
            "reasoning": f"Failed to evaluate: {str(e)}",
            "has_method_error": False,
            "has_calculation_error": False,
        }
