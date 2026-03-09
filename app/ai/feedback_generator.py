"""Feedback generation using LLM with formative feedback types."""
from __future__ import annotations

import json
import os
import re
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

LLM_MODEL_NAME = "gpt-5.2"
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


@st.cache_resource
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
    specific_error: str = "",
    previous_feedbacks: list = None,
) -> str:
    """Build the feedback generation prompt with all context."""
    spk = student_profile.get("spk", "Unknown")
    sal = student_profile.get("sal", "Unknown")
    student_answer = student_current_answer

    # Build previous feedback section if available
    previous_feedback_section = ""
    if previous_feedbacks:
        previous_feedback_section = "\n[Previous Attempts & Feedback - YOU MUST NOT REPEAT THESE]\n"
        for i, prev in enumerate(previous_feedbacks, 1):
            previous_feedback_section += f"""
Attempt {i}:
- Student Answer: {prev.get('student_answer', 'N/A')}
- Feedback Type: {prev.get('feedback_type', 'N/A')}
- Feedback Given: {prev.get('feedback_given', 'N/A')[:500]}
"""
        previous_feedback_section += "\nCRITICAL: The student has already received the above feedback and STILL made an error. You MUST approach the explanation from a completely different angle.\n"

    # Normalize feedback type for matching (handles variants from choose_feedback_type)
    ft_lower = feedback_type.lower()

    # Build feedback type specific instruction
    feedback_type_instruction = ""
    if feedback_type == "Correct Response":
        feedback_type_instruction = """
FEEDBACK TYPE INSTRUCTION (Correct Response — full guided solution):
This feedback is given because the student answered correctly OR has reached 3+ errors and needs the full solution walkthrough.

IF THE STUDENT ANSWERED CORRECTLY:
- Congratulate the student warmly.
- Briefly confirm WHY their answer is correct by walking through the key steps.
- Reinforce the concept so they remember the method.

IF THE STUDENT HAS 3+ ERRORS (still wrong):
- Be warm and encouraging — do NOT scold or shame.
- Clearly show the COMPLETE step-by-step solution from start to finish.
- At each step, explain WHAT you are doing and WHY.
- Point out where the student's approach went wrong and how the correct step differs.
- You MUST walk through every step until arriving at the final answer.
- It is OK to state the final answer in this feedback type.

Format the solution clearly with numbered steps, e.g.:
Langkah 1: ...
Langkah 2: ...
Langkah 3: ...
Jadi, jawabannya adalah ...
"""
    elif "response" in ft_lower and "contingent" in ft_lower:
        feedback_type_instruction = """
FEEDBACK TYPE INSTRUCTION (Response-Contingent):
- Identify the EXACT step in the student's answer where the error occurred.
- Explain specifically WHY that step is wrong by referencing the student's actual written work.
- Do NOT give generic fraction rules. Address THEIR specific calculation error.
- NEVER reveal or hint at the final answer. Only address the wrong step.
- Example: "Kamu menulis X, tetapi seharusnya Y karena Z"
"""
    elif "topic" in ft_lower and "contingent" in ft_lower:
        feedback_type_instruction = """
FEEDBACK TYPE INSTRUCTION (Topic-Contingent):
- Re-teach the specific fraction concept the student is struggling with.
- Use a SIMPLER example first (different numbers), then connect it back to THIS problem.
- Show the concept step-by-step, not just the rule.
- NEVER reveal or hint at the final answer of the current problem.
- DO NOT just say "try again" or repeat generic steps already given before.
"""
    elif "try again" in ft_lower or "try-again" in ft_lower:
        feedback_type_instruction = """
FEEDBACK TYPE INSTRUCTION (Try-Again):
- Briefly confirm what the student did correctly first.
- Point out which SPECIFIC step needs correction (e.g., "Langkah ke-2 perlu dicek lagi").
- Give ONE concrete hint about what to check, based on the actual error in their answer.
- NEVER reveal or hint at the final answer.
- Keep it short and encouraging.
"""
    elif "verification" in ft_lower:
        feedback_type_instruction = """
FEEDBACK TYPE INSTRUCTION (Verification + Response-Contingent):
- First, briefly tell the student that their answer is incorrect.
- Then identify the EXACT step where their error occurred.
- Explain specifically WHY that step is wrong.
- NEVER reveal or hint at the final answer.
"""
    else:
        # Standard / unknown feedback type
        feedback_type_instruction = f"""
FEEDBACK TYPE INSTRUCTION ({feedback_type}):
- Provide helpful feedback that addresses the student's specific error.
- Do NOT give generic advice — reference what the student actually wrote.
- NEVER reveal or hint at the final answer.
"""

    return f"""
# Fraction Tutor Feedback Task

[Current Problem]
Problem: {problem}
Correct Solution: {problem_solution}

[Student Profile]
Student Prior Knowledge (SPK): {spk}
Student Achievement Level (SAL): {sal}
Number of Errors So Far: {number_of_errors}

[Student's Current Answer]
{student_answer}

NOTE: Students type mixed fractions with a space, e.g. "1 1/3" means $1\frac{{1}}{{3}}$, "3 4/9" means $3\frac{{4}}{{9}}$. Always interpret "<integer> <fraction>" as a mixed number.

[SPECIFIC ERROR — YOUR FEEDBACK MUST ADDRESS THIS DIRECTLY]
{specific_error or evaluation_reasoning}

[Answer Evaluation Reasoning]
{evaluation_reasoning}

{feedback_type_instruction}

{previous_feedback_section}

[Relevant Knowledge Base Snippets]
{relevant_text}

[STRICT INSTRUCTIONS]
1. Your feedback MUST directly reference the student's actual answer — state what they wrote and address it specifically.
2. Do NOT give generic fraction rules. Address ONLY the specific mistake visible in the student's answer.
3. Do NOT repeat anything already said in previous feedbacks.
4. Write in friendly Bahasa Indonesia suitable for junior high school students.
5. SOLUTION REVEAL RULES (VERY IMPORTANT):
   - If Feedback Type is "Correct Response": You MUST walk through the complete step-by-step solution and you MAY state the final answer.
   - For ALL OTHER Feedback Types: NEVER reveal, hint at, or restate the final numeric/fraction answer. Use guided hints only, e.g.: "Coba hitung penyebut samanya dulu", "Periksa lagi operasi di langkah ke-2".
6. Write ALL math using inline LaTeX WITH dollar delimiters already included, e.g. $\\frac{{1}}{{2}}$, $\\times$, $\\div$, $3\\frac{{1}}{{2}}$. Always include the $ signs yourself. Use a single backslash for each command — the JSON encoder handles escaping.
7. For "Correct Response": be thorough — show every step. For other types: keep feedback concise (3-5 sentences max), focused, and actionable.
8. Return ONLY valid JSON with exactly these keys:
   {{"Feedback Type": "{feedback_type}", "Feedback": "your feedback here"}}

""".strip()


def _call_chat_model(messages: Sequence[Dict[str, str]], llm_model: str, use_json_format: bool = False) -> str:
    """Call the chat model to generate feedback."""
    client = _get_openai_client()
    if _OPENAI_USES_CLIENT:
        kwargs: dict = dict(
            model=llm_model,
            messages=list(messages),
            max_completion_tokens=1000,
            temperature=0.2,
        )
        if use_json_format:
            kwargs["response_format"] = {"type": "json_object"}
        response = client.chat.completions.create(**kwargs)
        return response.choices[0].message.content or ""

    import openai  # type: ignore
    response = client.ChatCompletion.create(
        model=llm_model,
        messages=list(messages),
        max_tokens=1000,
        temperature=0.2,
    )
    return response["choices"][0]["message"]["content"]


def _extract_feedback(raw_response: str, fallback_type: str) -> Dict[str, str]:
    """Parse JSON feedback with LaTeX sanitization and a regex fallback."""
    cleaned = raw_response.strip()

    # Strip markdown code fences (```json ... ``` or ``` ... ```)
    if cleaned.startswith("```"):
        cleaned = re.sub(r'^```[a-z]*\n?', '', cleaned)
        cleaned = re.sub(r'\n?```\s*$', '', cleaned).strip()

    # Pre-process: escape bare LaTeX backslash commands that are INVALID JSON escapes.
    # Valid single-char JSON escapes: " \ / b f n r t u
    # Commands like \div, \cdot, \sqrt, \pm, \leq cause JSONDecodeError — fix them.
    # Note: \frac (\f) and \times (\t) ARE valid JSON escapes but corrupt silently — fixed post-parse.
    cleaned = re.sub(r'\\(?!["\\\/ bfnrtu]|u[0-9a-fA-F]{4})', r'\\\\', cleaned)

    try:
        payload = json.loads(cleaned)
        if isinstance(payload, dict):
            feedback_type = str(payload.get("Feedback Type", fallback_type)).strip()
            feedback_text = str(payload.get("Feedback", "")).strip()

            # Post-process: fix LaTeX silently corrupted by JSON escape parsing.
            # JSON \f (form feed, chr 12) appears where \frac was written without doubling.
            # JSON \t (tab, chr 9) appears where \times/\text was written without doubling.
            feedback_text = feedback_text.replace('\x0c', '\\f')   # form-feed → \f  (gives \frac, etc.)
            feedback_text = feedback_text.replace('\x09imes', '\\times')  # tab+imes → \times
            feedback_text = feedback_text.replace('\x09ext', '\\text')    # tab+ext  → \text

            # Normalize over-escaped backslashes: \\frac → \frac etc.
            # Happens when LLM outputs 4 backslashes in JSON (2 after parsing) instead of 2 (1 after parsing).
            for _cmd in ('frac', 'times', 'div', 'pm', 'cdot', 'sqrt', 'left', 'right', 'text', 'leq', 'geq', 'neq'):
                feedback_text = feedback_text.replace('\\\\' + _cmd, '\\' + _cmd)

            return {
                "feedback_type": feedback_type or fallback_type,
                "feedback": feedback_text if feedback_text else raw_response.strip(),
                "raw": raw_response,
            }
    except json.JSONDecodeError:
        pass

    # Regex fallback: extract Feedback value even from malformed JSON
    match = re.search(r'"Feedback"\s*:\s*"((?:[^"\\]|\\.)*)"', raw_response)
    if match:
        return {
            "feedback_type": fallback_type,
            "feedback": match.group(1).replace('\\"', '"'),
            "raw": raw_response,
        }

    # Last resort: strip obvious JSON wrapper so plain text shows instead of raw JSON
    stripped = re.sub(r'^\{.*?"Feedback"\s*:\s*"', '', raw_response, flags=re.DOTALL)
    stripped = re.sub(r'".*\}\s*$', '', stripped, flags=re.DOTALL).strip()
    return {
        "feedback_type": fallback_type,
        "feedback": stripped if stripped else raw_response.strip(),
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
    error_count: int = 0,
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
        error_count: Current cumulative error count for this session (before this attempt)
        
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

    # Calculate what the error count will be AFTER this attempt
    # (caller is responsible for actually updating session state)
    effective_error_count = error_count + 1 if not is_correct else error_count

    # Decide feedback type based on effective error count
    if effective_error_count >= 3:
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
        number_of_errors=effective_error_count,
        evaluation_reasoning=evaluation["reasoning"],
        specific_error=evaluation.get("specific_error", ""),
        previous_feedbacks=previous_feedbacks
    )
    print(prompt)

    # Generate feedback using LLM
    messages = [
        {
            "role": "system",
            "content": (
                "You are an expert fraction tutor for Indonesian junior high school students. "
                "You ALWAYS give SPECIFIC feedback that directly references the student's actual answer. "
                "NEVER give generic advice — always reference what the student actually wrote. "
                "For the 'Correct Response' feedback type: you MUST provide a complete step-by-step "
                "solution walkthrough including the final answer. "
                "For ALL OTHER feedback types: NEVER reveal the final answer — give hints and "
                "scaffolding only so the student can discover the answer themselves. "
                "For ALL math expressions, you MUST include the dollar-sign delimiters yourself, "
                "e.g. write $\\frac{1}{2}$ not just \\frac{1}{2}. Use a single backslash for LaTeX commands."
            ),
        },
        {"role": "user", "content": prompt},
    ]

    raw_response = _call_chat_model(messages, llm_model, use_json_format=True)
    feedback_payload = _extract_feedback(raw_response, feedback_type)

    return {
        **feedback_payload,
        "contexts": contexts,
        "feedback_type_decision": feedback_type,
        "tof": tof,
        "evaluation": evaluation,  # Include evaluation details for debugging/logging
    }
