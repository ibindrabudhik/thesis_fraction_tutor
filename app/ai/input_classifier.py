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
    prompt = f"""Classify the student's input as either "question" or "answer".

Problem: {problem}
Student Input: {user_input}

--- DEFINITIONS ---

"question" — the student is:
  • Asking for help, clarification, or explanation about a concept
  • Checking / verifying their STEPS or approach ("apakah langkahnya begini?", "gitu bukan?", "benar ga?")
  • Expressing confusion ("bingung", "ga ngerti", "maksudnya gimana?")
  • Requesting an example or a simpler explanation
  Even if the input contains math expressions, if the student is ASKING whether their approach or steps are correct, it is a "question".

"answer" — the student is:
  • Submitting a final result / solution ("jawabannya 5/6", "hasilnya 3/4", "= 7/10")
  • Stating a definitive answer without seeking confirmation
  • Writing only a number or fraction as their response

--- EXAMPLES ---

"question" examples:
  - "kalau gitu harusnya 9 x 3 / 30 dikurangkan dengan 2 x 10 / 30 gitu?"
  - "berarti langkah pertama cari KPK dulu ya?"
  - "maksudnya penyebutnya disamakan dulu?"
  - "apa bedanya pembilang dan penyebut?"
  - "jadi caranya gimana?"
  - "yang ini dikali silang bukan?"
  - "kalau 1/2 + 1/3 itu penyebutnya jadi 6 ya?"
  - "oh jadi harusnya dikali bukan ditambah?"

"answer" examples:
  - "5/6"
  - "jawabannya 7/10"
  - "hasilnya 3 1/2"  (this is a mixed fraction: three and a half)
  - "1 1/3"  (mixed fraction: one and one-third)
  - "2 5/6"  (mixed fraction: two and five-sixths)
  - "1/2 + 1/3 = 5/6"
  - "= 27/30 - 20/30 = 7/30"
  - "jadi hasilnya 7/30"
  - "3 4/9"  (mixed fraction answer)

NOTE: Students write mixed fractions with a SPACE, e.g. "1 1/3" means 1⅓. When a student writes "<number> <fraction>" without any question words or question marks, treat it as a mixed fraction answer.

--- KEY DISTINCTION ---
If the student ends with a question-like tone ("gitu?", "ya?", "bukan?", "benar ga?", "?") and is describing STEPS rather than stating a final result, classify as "question".
If uncertain, classify as "question" so the tutor can provide clarification.

Respond with ONLY one word: "question" or "answer" """

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
    
    prompt = f"""You are Uma, a friendly and supportive fraction tutor for Indonesian junior high school students.
The student is asking a question or verifying their approach to the problem below.

[Problem]
{problem}

[Correct Solution — for YOUR reference only]
{problem_solution}

[Student's Question / Verification Request]
{user_question}

[Student Profile]
- Prior Knowledge (SPK): {spk}
- Achievement Level (SAL): {sal}

[Relevant Knowledge Base]
{relevant_text}

--- IMPORTANT ---
Students type mixed fractions with a SPACE, e.g. "1 1/3" means $1\frac{1}{3}$, "3 4/9" means $3\frac{4}{9}$. Always interpret "<integer> <fraction>" as a mixed number.

--- INSTRUCTIONS ---

1. Determine what the student is asking:
   a) STEP VERIFICATION — the student proposes steps and asks if they are correct (e.g., "gitu?", "benar ga?", "bukan?").
      → Compare their proposed steps against the correct solution.
      → If their steps are CORRECT: confirm warmly ("Betul!") and encourage them to continue to the next step.
      → If their steps have an ERROR: gently point out which specific part is wrong and give a hint toward the correct step, WITHOUT revealing the final answer.
   b) CONCEPT CLARIFICATION — the student asks about a concept ("apa itu KPK?", "gimana caranya?").
      → Explain the concept clearly using a simple example with different numbers from the problem.
      → Then connect it back to the current problem without revealing the answer.
   c) GENERAL HELP — the student is confused or stuck.
      → Give an encouraging hint about what to try first.

2. NEVER reveal the final answer/result of the problem.
3. Write in friendly Bahasa Indonesia suitable for junior high school students.
4. Be encouraging — praise correct thinking before correcting mistakes.
5. CRITICAL: ALL math expressions MUST use LaTeX with $ delimiters, e.g. $\frac{{1}}{{2}}$, $\times$, $\div$, $3\frac{{1}}{{4}}$. NEVER write bare LaTeX without $ delimiters.
6. Keep the response concise (3-5 sentences) but helpful.

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
