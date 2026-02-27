"""Input classification to distinguish student questions from answer attempts."""
from __future__ import annotations

import json
import os
from functools import lru_cache
from typing import Literal

# Load environment variables from .env file if running outside Streamlit
try:
    from dotenv import load_dotenv
    load_dotenv()
except ImportError:
    pass

try:
    from openai import OpenAI
    _OPENAI_USES_CLIENT = True
except ImportError:
    OpenAI = None
    import openai
    _OPENAI_USES_CLIENT = False

# Use fast, cheap model for classification
CLASSIFIER_MODEL = "gpt-4o"


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
    """Create a cached OpenAI client."""
    api_key = _read_openai_key()
    if _OPENAI_USES_CLIENT:
        return OpenAI(api_key=api_key)
    import openai
    openai.api_key = api_key
    return openai


def classify_input(
    user_input: str, 
    problem: str
) -> Literal["question", "answer"]:
    """
    Classify student input as either a question or an answer attempt.
    
    Uses GPT-4o with strict token limits for fast classification.
    Ambiguous inputs are classified as "answer" to leverage formative feedback.
    
    Args:
        user_input: The student's input text
        problem: The current problem statement for context
        
    Returns:
        "question" if student is asking for help/clarification
        "answer" if student is attempting to answer (including ambiguous cases)
    """
    if not user_input.strip():
        return "answer"
    
    # # Quick heuristic checks for obvious cases (avoids API call)
    # user_lower = user_input.lower().strip()
    
    # # Obvious question patterns in Indonesian
    # question_patterns = [
    #     "bagaimana", "gimana", "cara", "apa itu", "apa maksud",
    #     "jelaskan", "tolong jelaskan", "mengapa", "kenapa",
    #     "apa artinya", "bisa jelaskan", "tidak mengerti", "ga ngerti",
    #     "bingung", "ga paham", "tidak paham", "help", "bantuin",
    #     "contoh", "kasih contoh"
    # ]
    
    # # Check if input looks like a question
    # is_likely_question = any(pattern in user_lower for pattern in question_patterns)
    
    # # Obvious answer patterns (mathematical expressions, equations)
    # answer_patterns = [
    #     "=", "x", "y", "z", "+", "-", "*", "/", 
    #     "jadi", "jawabannya", "hasilnya", "maka",
    # ]
    
    # is_likely_answer = any(pattern in user_lower for pattern in answer_patterns)
    
    # # If clearly an answer pattern, skip API call
    # if is_likely_answer and not is_likely_question:
    #     return "answer"
    
    # If clearly a question pattern and no answer pattern, could be question
    # But still use LLM for accuracy since ambiguous -> answer
    
    # Use LLM for classification
    prompt = f"""Act as Lyra, classify the student's input as either "question" or "answer". // Bertindaklah sebagai Lyra, klasifikasikan masukan siswa sebagai "question" atau "answer".

Problem: {problem}
Student Input: {user_input}

Rules:
- "question": Student is asking for help, clarification, explanation, or doesn't understand something // Kalau misalkan siswa meminta bantuan, klarifikasi, penjelasan, atau tidak mengerti sesuatu
- "answer": Student is attempting to solve the problem or provide a mathematical answer // Kalau misalkan siswa mencoba menyelesaikan masalah atau memberikan jawaban matematika

Respond with ONLY one word: "question" or "answer"
If ambiguous or uncertain, respond "question"."""

    try:
        client = _get_openai_client()
        
        if _OPENAI_USES_CLIENT:
            response = client.chat.completions.create(
                model=CLASSIFIER_MODEL,
                messages=[
                    {"role": "system", "content": "You classify student inputs. Respond with only 'question' or 'answer'."},
                    {"role": "user", "content": prompt}
                ],
                max_tokens=10,
                temperature=0,
            )
            result = response.choices[0].message.content.strip().lower()
        else:
            response = client.ChatCompletion.create(
                model=CLASSIFIER_MODEL,
                messages=[
                    {"role": "system", "content": "You classify student inputs. Respond with only 'question' or 'answer'."},
                    {"role": "user", "content": prompt}
                ],
                max_tokens=10,
                temperature=0,
            )
            result = response["choices"][0]["message"]["content"].strip().lower()
        
        # Validate response
        if "question" in result:
            return "question"
        else:
            return "answer"  # Default to answer for any ambiguous response
            
    except Exception as e:
        print(f"Error classifying input: {e}")
        # Default to answer on error (safer - will trigger evaluation)
        return "answer"


def generate_clarification_response(
    user_question: str,
    problem: str,
    problem_solution: str,
    contexts: list,
    student_profile: dict,
) -> str:
    """
    Generate a helpful response to a student's question without revealing the answer.
    
    Args:
        user_question: The student's question
        problem: The current problem statement
        problem_solution: The correct solution (for context, not to reveal)
        contexts: RAG-retrieved knowledge snippets
        student_profile: Student profile dict
        
    Returns:
        Helpful response in Bahasa Indonesia
    """
    relevant_text = "No relevant context found." if not contexts else "\n\n---\n\n".join(
        ctx["text"] for ctx in contexts
    )
    
    spk = student_profile.get("spk", "Unknown")
    sal = student_profile.get("sal", "Unknown")
    
    prompt = f"""You are Uma, a friendly fraction tutor helping a junior high school student.
The student is asking a question about the problem below.

[Problem]
{problem}

[Student Question]
{user_question}

[Student Profile]
- Prior Knowledge: {spk}
- Achievement Level: {sal}

[Relevant Knowledge]
{relevant_text}

Instructions:
1. Answer the student's question helpfully in Bahasa Indonesia
2. Do NOT reveal the final solution or answer directly
3. Guide the student toward understanding without giving away the answer
4. Be encouraging and supportive like a peer tutor
5. CRITICAL: ALL mathematical expressions MUST be wrapped in LaTeX delimiters using $...$ for inline math. For example: $\frac{1}{2}$, $\times$, $\div$, $3\frac{1}{4}$. NEVER write bare LaTeX commands like \frac or \times without $ delimiters.
6. Keep the response concise but helpful

Generate your response:"""

    try:
        client = _get_openai_client()
        
        if _OPENAI_USES_CLIENT:
            response = client.chat.completions.create(
                model="gpt-4o",
                messages=[
                    {"role": "system", "content": "You are Uma, a supportive fraction tutor. Respond in Bahasa Indonesia."},
                    {"role": "user", "content": prompt}
                ],
                max_tokens=500,
                temperature=0.3,
            )
            return response.choices[0].message.content.strip()
        else:
            response = client.ChatCompletion.create(
                model="gpt-4o",
                messages=[
                    {"role": "system", "content": "You are Uma, a supportive fraction tutor. Respond in Bahasa Indonesia."},
                    {"role": "user", "content": prompt}
                ],
                max_tokens=500,
                temperature=0.3,
            )
            return response["choices"][0]["message"]["content"].strip()
            
    except Exception as e:
        return f"Maaf, terjadi kesalahan saat memproses pertanyaanmu. Coba tanyakan lagi ya! (Error: {e})"
