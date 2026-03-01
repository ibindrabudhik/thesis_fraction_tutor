import streamlit as st
import sys
import os
import uuid
from datetime import datetime
import random

# Add parent directory to path to import modules
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from ai.rag_pipeline import explain_contexts, generate_tutor_feedback
from ai.feedback_generator import MissingAPIKeyError
from ai.achievement_evaluator import assess_achievement_level
from ai.input_classifier import classify_input, generate_clarification_response
from ai.retrieval import retrieve_context, prefetch_problem_context
from auth.session import require_authentication, get_student_id
from database.student_service import get_student_profile, update_student_achievement_level, update_prior_knowledge
from database.log_service import create_session, log_student_interaction, get_recent_session_feedback
from database.chat_service import save_message
from database.supabase_client import get_supabase_client
from components.tab_detector import render_tab_detector


def render_latex(text: str) -> str:
    """Process text to ensure all LaTeX expressions are properly wrapped in $ delimiters.
    
    Handles cases where the LLM outputs bare LaTeX commands without $ wrapping,
    e.g. \frac{1}{2} instead of $\frac{1}{2}$.
    """
    if not text:
        return text
    
    import re
    
    # Step 0: Normalize over-escaped backslashes (\\cmd → \cmd).
    # LLM sometimes outputs \\frac (double backslash) due to JSON escaping confusion.
    # A double backslash in the Python string (i.e. the chars \ ) won't match the LaTeX
    # patterns below, so we normalize first.
    for _cmd in ('frac', 'times', 'div', 'pm', 'cdot', 'sqrt', 'left', 'right', 'text', 'leq', 'geq', 'neq'):
        text = text.replace('\\\\' + _cmd, '\\' + _cmd)  # \\cmd → \cmd
    
    # Step 1: Protect already-delimited LaTeX blocks by replacing them with placeholders
    placeholders = []
    
    def _placeholder(match):
        placeholders.append(match.group(0))
        return f"\x00LATEX{len(placeholders) - 1}\x00"
    
    # Protect $$...$$ blocks first, then $...$ blocks
    text = re.sub(r'\$\$[^$]+?\$\$', _placeholder, text)
    text = re.sub(r'\$[^$]+?\$', _placeholder, text)
    
    # Step 2a: Convert plain-text mixed fractions (e.g. "1 1/3") into LaTeX.
    # Match: whole_number SPACE numerator/denominator (not already inside $ or \frac)
    # Negative lookbehind avoids matching inside existing LaTeX.
    text = re.sub(
        r'(?<!\$)(?<!\\frac\{)\b(\d+)\s+(\d+)\s*/\s*(\d+)\b(?!\})',
        r'$\1\\frac{\2}{\3}$',
        text
    )
    
    # Step 2b: Convert plain fractions (e.g. "3/4") that aren't part of a mixed number into LaTeX.
    # Only matches standalone fractions not already wrapped in $ or preceded by a digit+space (mixed).
    text = re.sub(
        r'(?<!\$)(?<!\d )(?<!\d)\b(\d+)\s*/\s*(\d+)\b(?!\})',
        r'$\\frac{\1}{\2}$',
        text
    )
    
    # Step 2c: Wrap bare \frac{...}{...} (including with optional leading number like 3\frac{1}{2})
    text = re.sub(
        r'(\d*)\\frac\{([^}]*)\}\{([^}]*)\}',
        r'$\1\\frac{\2}{\3}$',
        text
    )
    
    # Step 3: Wrap bare LaTeX operators that are not inside $ delimiters
    bare_operators = [
        (r'\\times', r'$\\times$'),
        (r'\\div', r'$\\div$'),
        (r'\\pm', r'$\\pm$'),
        (r'\\cdot', r'$\\cdot$'),
        (r'\\sqrt\{([^}]*)\}', r'$\\sqrt{\1}$'),
    ]
    for pattern, replacement in bare_operators:
        text = re.sub(pattern, replacement, text)
    
    # Step 4: Merge adjacent $ delimiters: "$a$ $b$" → "$a \; b$" and "$x$$y$" → "$x y$"
    text = re.sub(r'\$\s*\$', ' ', text)
    
    # Step 5: Restore protected blocks
    for i, original in enumerate(placeholders):
        text = text.replace(f"\x00LATEX{i}\x00", original)
    
    return text


# ---------- AUTHENTICATION ----------
require_authentication()


# ---------- TIME-BASED SCHEDULE ----------
# Define when each knowledge area is accessible
KNOWLEDGE_AREA_SCHEDULE = {
    "ordering": {
        "start": datetime(2026, 3, 1, 23, 0),
        "end": datetime(2026, 3, 15, 23, 59),
        "label": "Mengurutkan Pecahan"
    },
    "addition": {
        "start": datetime(2026, 3, 1, 23, 0),
        "end": datetime(2026, 3, 15, 23, 59),
        "label": "Penjumlahan Pecahan"
    },
    "subtraction": {
        "start": datetime(2026, 3, 1, 23, 0),
        "end": datetime(2026, 3, 15, 23, 59),
        "label": "Pengurangan Pecahan"
    },
    "multiplication": {
        "start": datetime(2026, 3, 4, 23, 0),
        "end": datetime(2026, 3, 15, 23, 59),
        "label": "Perkalian Pecahan"
    },
    "division": {
        "start": datetime(2026, 3, 8, 23, 0),
        "end": datetime(2026, 3, 15, 23, 59),
        "label": "Pembagian Pecahan"
    }
}


def get_active_knowledge_areas() -> list:
    """Get currently active knowledge areas based on current datetime."""
    now = datetime.now()
    active_areas = []
    
    for area, schedule in KNOWLEDGE_AREA_SCHEDULE.items():
        if schedule["start"] <= now <= schedule["end"]:
            active_areas.append(area)
    
    return active_areas


def get_active_knowledge_area_label() -> str:
    """Get display label for current knowledge area(s)."""
    active_areas = get_active_knowledge_areas()
    
    if not active_areas:
        return "Tidak ada materi aktif"
    
    labels = [KNOWLEDGE_AREA_SCHEDULE[area]["label"] for area in active_areas]
    return " & ".join(labels)


def get_random_task_by_knowledge_area(knowledge_areas: list, level: str = None) -> dict:
    """
    Get a random task that matches any of the given knowledge areas.
    
    Args:
        knowledge_areas: List of knowledge area strings (e.g., ['ordering', 'addition'])
        level: Optional level filter ('Low' or 'High')
    
    Returns:
        Random task dict or None if no matching tasks found
    """
    if not knowledge_areas:
        return None
    
    client = get_supabase_client()
    
    try:
        # Build query to filter tasks by knowledge areas
        query = client.table("tasks").select("*")
        
        # Add level filter if provided
        if level:
            query = query.eq("level", level)
        
        response = query.execute()
        
        if not response.data:
            return None
        
        # Filter tasks: ALL of a task's knowledge areas must be currently active.
        # This ensures multi-knowledge-area tasks only appear when all their areas are scheduled.
        all_area_names = ["ordering", "addition", "subtraction", "multiplication", "division"]
        matching_tasks = []
        for task in response.data:
            # Collect which knowledge areas this task requires
            task_areas = [
                area for area in all_area_names
                if task.get(f"knowledge_area_{area}", False)
            ]
            # Task must have at least one area, and ALL its areas must be active
            if task_areas and all(area in knowledge_areas for area in task_areas):
                matching_tasks.append(task)
        
        if not matching_tasks:
            return None
        
        # Return random task from matching tasks
        return random.choice(matching_tasks)
        
    except Exception as e:
        print(f"Error fetching task by knowledge area: {e}")
        return None


def _fetch_student_profile() -> dict:
    """Fetch student profile from database."""
    student_id = get_student_id()
    if not student_id:
        return {
            "student_id": "DEMO",
            "name": "Demo User",
            "spk": "Low",
            "sal": "Low",
            "tof": "Immediate",
        }
    
    try:
        profile = get_student_profile(student_id)
        return profile
    except Exception as e:
        st.error(f"Error loading profile: {e}")
        return {
            "student_id": student_id,
            "name": "User",
            "spk": "Low",
            "sal": "Low",
            "tof": "Immediate",
        }


def _fetch_current_problem() -> dict:
    """Fetch current problem from database based on time-based schedule."""
    if "current_task" in st.session_state and st.session_state.current_task:
        return st.session_state.current_task
    
    # Get currently active knowledge areas based on date
    active_areas = get_active_knowledge_areas()
    
    if not active_areas:
        # No active knowledge area at this time
        return {
            "task_id": "LOCKED",
            "text": "Tidak ada materi yang tersedia saat ini. Silakan cek jadwal.",
            "solution": "",
            "level": "Low",
            "locked": True
        }
    
    # Get student achievement level for difficulty filtering
    student_profile = st.session_state.get("student_profile", {})
    level = student_profile.get("sal", "Low")
    
    try:
        task = get_random_task_by_knowledge_area(active_areas, level)
        
        if task:
            st.session_state.current_task = {
                "task_id": task["task_id"],
                "text": task["question"],
                "solution": task["solution"],
                "level": task["level"],
                "knowledge_area_ordering": task.get("knowledge_area_ordering", False),
                "knowledge_area_addition": task.get("knowledge_area_addition", False),
                "knowledge_area_subtraction": task.get("knowledge_area_subtraction", False),
                "knowledge_area_multiplication": task.get("knowledge_area_multiplication", False),
                "knowledge_area_division": task.get("knowledge_area_division", False),
                "active_areas": active_areas,
                "locked": False
            }
            return st.session_state.current_task
        else:
            # Fallback if no tasks match the active knowledge areas
            return {
                "task_id": "DEMO-001",
                "text": f"Tidak ada soal untuk {get_active_knowledge_area_label()}",
                "solution": "",
                "level": level,
                "locked": True
            }
    except Exception as e:
        st.error(f"Error loading task: {e}")
        return {
            "task_id": "ERROR",
            "text": "Terjadi kesalahan saat memuat soal",
            "solution": "",
            "level": "Low",
            "locked": True
        }


def _start_new_session():
    """Start a new learning session based on time-based schedule."""
    student_id = get_student_id()
    if not student_id:
        return
    
    # Get currently active knowledge areas based on date
    active_areas = get_active_knowledge_areas()
    
    if not active_areas:
        st.error("❌ Tidak ada materi yang tersedia saat ini. Silakan cek jadwal.")
        return
    
    # Get student achievement level for difficulty filtering
    student_profile = st.session_state.get("student_profile", {})
    level = student_profile.get("sal", "Low")
    
    try:
        task = get_random_task_by_knowledge_area(active_areas, level)
        
        if task:
            st.session_state.current_task = {
                "task_id": task["task_id"],
                "text": task["question"],
                "solution": task["solution"],
                "level": task["level"],
                "knowledge_area_ordering": task.get("knowledge_area_ordering", False),
                "knowledge_area_addition": task.get("knowledge_area_addition", False),
                "knowledge_area_subtraction": task.get("knowledge_area_subtraction", False),
                "knowledge_area_multiplication": task.get("knowledge_area_multiplication", False),
                "knowledge_area_division": task.get("knowledge_area_division", False),
                "active_areas": active_areas,
                "locked": False
            }
            
            # Create new session
            session_id = create_session(student_id, task["task_id"])
            st.session_state.current_session_id = session_id
            
            # Reset state
            st.session_state.chat_history = []
            st.session_state.error_count = 0
            st.session_state.session_complete = False
            st.session_state.previous_feedbacks = []  # Reset feedback history
            st.session_state.cheat_count = 0  # Reset cheat count for new session
            st.session_state.cheat_reset_count += 1  # Signal JS to reset its counter
            
            # Pre-fetch problem context for faster first response
            prefetch_problem_context(task["question"], top_k=5)
            
            st.success("✅ Soal baru dimuat!")
            st.rerun()
        else:
            st.error(f"❌ Tidak ada soal tersedia untuk {get_active_knowledge_area_label()}.")
    except Exception as e:
        st.error(f"Error starting new session: {e}")


# ---------- PAGE CONTENT ----------
st.title("🤖 Belajar Bareng Uma")
# st.markdown("Halo! Saya Uma, tutor pecahan virtual kamu. Apa yang ingin kamu pelajari hari ini?")
# Study ethics banner
st.info("""
ℹ️ **Panduan Belajar**  
Kerjakan soal secara **mandiri** tanpa bantuan ChatGPT atau alat lain. Kamu akan ketahuan ketika berpindah tab/window. Tidak apa-apa membuat kesalahan - Chatbot Uma ini akan membantumu belajar dari segala bentuk kesalahan! **Tidak ada hukuman** untuk salah saat belajar bersama Uma. 📚
""")

st.info(""" ℹ️  Tips: Beri jawaban dalam bentuk **paling sederhana** dan untuk jawaban yang melibatkan operasi, tulis langkah perhitungannya. Misalnya, untuk soal `1/2 + 1/3`, jawaban yang baik adalah `1/2 + 1/3 = 3/6 + 2/6 = 5/6`, bukan hanya `5/6`. Jawaban dengan langkah perhitungan akan mendapatkan umpan balik yang lebih baik! Jawaban untuk pecahan campuran juga harus dalam bentuk campuran, misalnya `1 1/2` bukan `3/2`.
        """)

# Initialize session state
if "student_profile" not in st.session_state:
    st.session_state.student_profile = _fetch_student_profile()
if "chat_history" not in st.session_state:
    st.session_state.chat_history = []
if "error_count" not in st.session_state:
    st.session_state.error_count = 0
if "session_complete" not in st.session_state:
    st.session_state.session_complete = False
if "previous_feedbacks" not in st.session_state:
    st.session_state.previous_feedbacks = []
if "cheat_count" not in st.session_state:
    st.session_state.cheat_count = 0
if "cheat_reset_count" not in st.session_state:
    st.session_state.cheat_reset_count = 0
if "last_processed_reset" not in st.session_state:
    st.session_state.last_processed_reset = 0
if "current_session_id" not in st.session_state:
    student_id = get_student_id()
    current_task = _fetch_current_problem()
    st.session_state.current_session_id = create_session(student_id, current_task.get("task_id", "DEMO"))
    # Pre-fetch problem context on initial load
    prefetch_problem_context(current_task.get("text", ""), top_k=5)

# Render tab detector (installs JS listeners on parent window)
# The component returns the cheat count directly via bidirectional communication
# Pass cheat_reset_count so JS resets parentWin.__cheatSwitchCount on new session
detected_switches = render_tab_detector(reset_count=st.session_state.cheat_reset_count)

# Guard against stale component value after a reset.
# On the first rerun after _start_new_session(), the JS component may not have
# processed the new reset_count yet and returns the old (non-zero) count.
# We skip updating cheat_count for that one rerun to prevent it from being
# immediately overwritten back to the old value.
if st.session_state.cheat_reset_count > st.session_state.last_processed_reset:
    # Reset was just signaled — mark it as processed and ignore the stale JS value.
    st.session_state.last_processed_reset = st.session_state.cheat_reset_count
elif detected_switches > st.session_state.cheat_count:
    st.session_state.cheat_count = detected_switches
    st.rerun()  # Immediately re-render to update the warning banner

# Show persistent warning banner if student has switched tabs
if st.session_state.cheat_count > 0:
    st.warning(f"⚠️ **Peringatan:** Terdeteksi {st.session_state.cheat_count}x berpindah tab/window. Mohon kerjakan soal secara mandiri tanpa mencari bantuan di tab lain!")

student_profile = st.session_state.student_profile
student_spk = student_profile.get("spk", "-")
student_sal = student_profile.get("sal", "-")

col1, col2 = st.columns([1, 4])
with col1:
    # Display current active knowledge area
    active_label = get_active_knowledge_area_label()
    st.info(f"📚 Materi Aktif: **{active_label}**")
    
    soal_data = _fetch_current_problem()
    soal = soal_data.get("text", "Soal tidak ditemukan.")
    solution = soal_data.get("solution", "")
    task_level = soal_data.get("level", "Low")
    is_locked = soal_data.get("locked", False)
    
    st.subheader("Soal Saat Ini")
    
    if is_locked:
        st.warning(soal)
    else:
        # Debug: print raw soal to console
        # print(f"DEBUG - Raw soal: {repr(soal)}")
        # Render LaTeX math expressions (Streamlit auto-renders $$ and $ delimiters)
        st.markdown(render_latex(soal))
    
    st.subheader("Profil Siswa")
    info_cols = st.columns(2)
    info_cols[0].metric("SPK", student_spk)
    info_cols[1].metric("SAL", student_sal)
    
    error_cols = st.columns(1)
    if st.session_state.error_count >= 3:
        error_cols[0].error(f"❌ Kesalahan: {st.session_state.error_count}/3")
    else:
        error_cols[0].info(f"Kesalahan: {st.session_state.error_count}/3")
    
    # Always show Next Problem button (but disable when session not complete or locked)
    st.markdown("---")
    if is_locked:
        st.button(
            "➡️ Soal Berikutnya", 
            use_container_width=True, 
            disabled=True,
            help="Tidak ada materi yang tersedia saat ini"
        )
    elif st.session_state.session_complete:
        st.success("🎉 Sesi selesai!")
        if st.button("➡️ Soal Berikutnya", use_container_width=True, type="primary"):
            _start_new_session()
    else:
        st.button(
            "➡️ Soal Berikutnya", 
            use_container_width=True, 
            disabled=True,
            help="Selesaikan soal saat ini terlebih dahulu"
        )
    
    # Show schedule information
    with st.expander("📅 Lihat Jadwal Materi"):
        for area, schedule in KNOWLEDGE_AREA_SCHEDULE.items():
            start_str = schedule["start"].strftime("%d %b %Y")
            end_str = schedule["end"].strftime("%d %b %Y")
            st.markdown(f"**{schedule['label']}**: {start_str} - {end_str}")

# Disable chat input if session is complete or locked
if is_locked:
    user_input = None
    st.warning("💬 Chat dinonaktifkan. Tidak ada materi yang tersedia saat ini.")
elif st.session_state.session_complete:
    user_input = None
    st.info("💬 Chat dinonaktifkan. Klik 'Soal Berikutnya' untuk melanjutkan.")
else:
    user_input = st.chat_input("Ketik pertanyaan atau jawaban kamu di sini...")

with col2:
    # Create scrollable container for chat history
    with st.container(height=600):
        st.markdown('<div class="scrollable-container">', unsafe_allow_html=True)
        for message in st.session_state.chat_history:
            with st.chat_message(message["role"]):
                # Render LaTeX in all messages
                st.markdown(render_latex(message["content"]))
                if message["role"] == "assistant" and message.get("contexts"):
                    with st.expander("Sumber pengetahuan", expanded=False):
                        for formatted in explain_contexts(message["contexts"]):
                            st.markdown(render_latex(formatted))
        
        if user_input:
            # Add user message
            st.session_state.chat_history.append({"role": "user", "content": user_input})
            with st.chat_message("user"):
                # Render LaTeX in user message too (in case they type math)
                st.markdown(render_latex(user_input))

            try:
                # Classify input as question or answer
                input_type = classify_input(user_input, soal)
                print(f"Input classified as: {input_type}")
                
                student_id = get_student_id()
                session_id = st.session_state.current_session_id
                client_time = datetime.now()
                
                if input_type == "question":
                    # Handle as clarification question (no evaluation, no error counting)
                    contexts = retrieve_context(user_input, top_k=5)
                    
                    clarification_response = generate_clarification_response(
                        user_question=user_input,
                        problem=soal,
                        problem_solution=solution,
                        contexts=contexts,
                        student_profile=student_profile
                    )
                    
                    tutor_markdown = f"**💡 Penjelasan**\n\n{clarification_response}"
                    assistant_turn = {
                        "role": "assistant",
                        "content": tutor_markdown,
                        "contexts": contexts,
                    }
                    
                    # Save to chat messages only (no student_logs for questions)
                    if student_id and student_id != "DEMO":
                        save_message(session_id, student_id, "user", user_input, timestamp=client_time)
                        save_message(
                            session_id, 
                            student_id, 
                            "assistant", 
                            tutor_markdown,
                            contexts,
                            timestamp=client_time
                        )
                else:
                    # Handle as answer attempt (with evaluation and feedback)
                    query = "Current problem: " + soal + " " + user_input
                    
                    # Get previous feedbacks from session state (cached) or database
                    previous_feedbacks = st.session_state.get("previous_feedbacks", [])
                    if not previous_feedbacks and session_id:
                        previous_feedbacks = get_recent_session_feedback(session_id, limit=2)
                    
                    # Generate feedback using RAG pipeline with previous feedback context
                    feedback = generate_tutor_feedback(
                        query, 
                        student_profile, 
                        soal, 
                        solution,
                        previous_feedbacks=previous_feedbacks,
                        error_count=st.session_state.error_count,
                    )
                    
                    tutor_markdown = (
                        f"**{feedback['feedback_type']}**\n\n" f"{feedback['feedback']}"
                    )
                    assistant_turn = {
                        "role": "assistant",
                        "content": tutor_markdown,
                        "contexts": feedback.get("contexts", []),
                    }
                    
                    # Check if session should be completed
                    evaluation = feedback.get("evaluation", {})
                    is_correct = evaluation.get("is_correct", False)
                    
                    # Update error count HERE (single source of truth)
                    # Only increment on wrong answers; do NOT reset on correct
                    # so the cumulative session error count is preserved for logging.
                    if not is_correct:
                        st.session_state.error_count += 1
                    
                    # Determine if this is the final interaction
                    is_final = is_correct or st.session_state.error_count >= 3
                    
                    # Assess achievement level if final
                    achievement_assessed = None
                    if is_final:
                        assessment = assess_achievement_level(
                            problem=soal,
                            solution=solution,
                            student_answer=user_input,
                            is_correct=is_correct,
                            error_count=st.session_state.error_count,
                            reasoning=evaluation.get("reasoning", "")
                        )
                        achievement_assessed = assessment["achievement_level"]
                        
                        # Update student achievement level and prior knowledge in database
                        if student_id and student_id != "DEMO":
                            update_student_achievement_level(student_id, achievement_assessed)
                            # Update session state
                            st.session_state.student_profile["sal"] = achievement_assessed
                            
                            # Update prior knowledge based on task's knowledge areas
                            # Only update if the student answered correctly
                            if is_correct:
                                task_data = st.session_state.get("current_task", {})
                                if task_data.get("knowledge_area_ordering"):
                                    update_prior_knowledge(student_id, ordering=achievement_assessed)
                                if task_data.get("knowledge_area_addition"):
                                    update_prior_knowledge(student_id, addition=achievement_assessed)
                                if task_data.get("knowledge_area_subtraction"):
                                    update_prior_knowledge(student_id, subtraction=achievement_assessed)
                                if task_data.get("knowledge_area_multiplication"):
                                    update_prior_knowledge(student_id, multiplication=achievement_assessed)
                                if task_data.get("knowledge_area_division"):
                                    update_prior_knowledge(student_id, division=achievement_assessed)
                        
                        # Mark session as complete
                        st.session_state.session_complete = True
                    
                    # Log interaction with full evaluation result
                    if student_id and student_id != "DEMO":
                        log_student_interaction(
                            session_id=session_id,
                            student_id=student_id,
                            task_id=soal_data.get("task_id", "DEMO"),
                            task_level=task_level,
                            question=soal,
                            student_answer=user_input,
                            is_correct=is_correct,
                            feedback_given=tutor_markdown,
                            feedback_type=feedback.get("feedback_type", ""),
                            error_count=st.session_state.error_count,
                            is_final=is_final,
                            achievement_level_assessed=achievement_assessed,
                            timestamp=client_time,
                            evaluation_result=evaluation,  # Store full evaluation
                            cheat_count=st.session_state.get("cheat_count", 0)  # Add cheat detection
                        )
                        
                        # Save chat messages with client time
                        save_message(session_id, student_id, "user", user_input, timestamp=client_time)
                        save_message(
                            session_id, 
                            student_id, 
                            "assistant", 
                            tutor_markdown,
                            feedback.get("contexts", []),
                            timestamp=client_time
                        )
                    
                    # Update cached previous feedbacks for next iteration
                    st.session_state.previous_feedbacks.insert(0, {
                        "feedback_given": tutor_markdown,
                        "feedback_type": feedback.get("feedback_type", ""),
                        "student_answer": user_input,
                        "error_count": st.session_state.error_count,
                    })
                    # Keep only last 2
                    st.session_state.previous_feedbacks = st.session_state.previous_feedbacks[:2]
                    
                    # Persist the final feedback in chat history BEFORE rerun
                    # so it is displayed after the page reloads
                    if is_final:
                        st.session_state.chat_history.append(assistant_turn)
                        st.rerun()
                
            except MissingAPIKeyError as err:
                assistant_turn = {"role": "assistant", "content": f"⚠️ {err}"}
                print(f"MissingAPIKeyError: {err}")
            except FileNotFoundError as err:
                assistant_turn = {
                    "role": "assistant",
                    "content": (
                        "⚠️ Konten pendukung belum siap. Pastikan embeddings dan chunk tersedia.\n"
                        f"Detail: {err}"
                    ),
                }
                print(f"FileNotFoundError: {err}")
            except Exception as err:
                import traceback
                error_details = traceback.format_exc()
                print(f"Error in feedback generation: {error_details}")
                assistant_turn = {
                    "role": "assistant",
                    "content": f"⚠️ Terjadi kesalahan saat menghasilkan feedback: {str(err)}\n\nDetail: {error_details}",
                }

            st.session_state.chat_history.append(assistant_turn)

            with st.chat_message("assistant"):
                # Render LaTeX in assistant message
                st.markdown(render_latex(assistant_turn["content"]))
                if assistant_turn.get("contexts"):
                    with st.expander("Sumber pengetahuan", expanded=False):
                        for formatted in explain_contexts(assistant_turn["contexts"]):
                            st.markdown(render_latex(formatted))
        st.markdown('</div>', unsafe_allow_html=True)
