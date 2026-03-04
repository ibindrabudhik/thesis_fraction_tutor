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
You are a math teacher evaluating a student's answer to a fraction problem.

Problem: {problem}
Correct Solution: {correct_solution}
Student Answer: {student_answer}

IMPORTANT RULES:
- Students type mixed fractions with a SPACE between the whole number and the fraction, e.g. "1 1/3" means 1⅓ (one and one-third), "3 4/9" means 3⁴⁄₉, "2 5/6" means 2⁵⁄₆. ALWAYS interpret "<integer> <numerator>/<denominator>" as a mixed fraction, NOT as separate numbers.
- Students are NOT required to show their work or steps. A correct final answer alone (e.g. "7 1/2", "15/2", "3.5") is fully acceptable.
- Accept any mathematically equivalent form: mixed numbers (e.g. "1 1/3"), improper fractions (e.g. "4/3"), simplified or unsimplified, decimals.
- When comparing, convert both the student's answer and the correct solution to the same form (e.g. both to improper fractions or both to decimals) before checking equality.
- Only mark as incorrect if the numerical value is WRONG, not because steps are missing or the form differs.

Carefully check if the student's answer equals the correct solution.
Respond ONLY in JSON format:
{{
    "is_correct": true or false,
    "confidence": 0.0-1.0,
    "reasoning": "(1) what value the student gave, (2) what the correct value is, (3) whether they match",
    "specific_error": "If wrong: quote exactly what the student wrote and explain what is mathematically incorrect. If correct: leave empty.",
    "has_method_error": true if student used a wrong procedure (ignore missing steps),
    "has_calculation_error": true if the arithmetic result is wrong
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
                model="gpt-5.2",
                messages=messages,
                temperature=0,
                response_format={"type": "json_object"}
            )
            raw = response.choices[0].message.content or "{}"
        else:
            import openai
            response = client.ChatCompletion.create(
                model="gpt-5.2",
                messages=messages,
                temperature=0,
            )
            raw = response["choices"][0]["message"]["content"]

        result = json.loads(raw)
        return {
            "is_correct": result.get("is_correct", False),
            "confidence": result.get("confidence", 0.0),
            "reasoning": result.get("reasoning", ""),
            "specific_error": result.get("specific_error", ""),
            "has_method_error": result.get("has_method_error", False),
            "has_calculation_error": result.get("has_calculation_error", False),
        }
    except Exception as e:
        print(f"Error evaluating answer: {e}")
        return {
            "is_correct": False,
            "confidence": 0.0,
            "reasoning": f"Failed to evaluate: {str(e)}",
            "specific_error": "",
            "has_method_error": False,
            "has_calculation_error": False,
        }
