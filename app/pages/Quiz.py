import streamlit as st
from datetime import datetime
import sys
import os

# Add parent directory to path for imports
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from auth.session import is_authenticated, get_student_id
from database.student_service import get_student_profile, calculate_overall_spk
from database.quiz_service import log_quiz_submission, calculate_quiz_score
from pages.quiz_data import get_questions_by_section

# Check authentication
if not is_authenticated():
    st.switch_page("pages/Login.py")

# Quiz schedule - hardcoded dates for each section
QUIZ_SCHEDULE = {
    # "pre_test": datetime(2026, 2, 20, 0, 0),  # Available from Feb 20, 2026
    "ordering_fractions": datetime(2026, 3, 5, 0, 0),  # Feb 21
    "fraction_addition": datetime(2026, 3, 5, 0, 0),  # Feb 22
    "fraction_subtraction": datetime(2026, 3, 5, 0, 0),  # Feb 23
    "fraction_multiplication": datetime(2026, 3, 5, 0, 0),  # Feb 24
    # "fraction_division": datetime(2026, 2, 25, 0, 0),  # Feb 25
    # # "post_test": datetime(2026, 2, 26, 0, 0)  # Feb 26
}

# Section metadata
SECTION_INFO = {
    # "pre_test": {
    #     "title": "📝 Pre-Test",
    #     "description": "Tes awal untuk mengukur pengetahuan awal Anda tentang pecahan",
    #     "knowledge_areas": ["ordering", "addition", "subtraction", "multiplication", "division"]
    # },
    "ordering_fractions": {
        "title": "📊 Mengurutkan Pecahan",
        "description": "Latihan mengurutkan dan membandingkan pecahan",
        "knowledge_areas": ["ordering"]
    },
    "fraction_addition": {
        "title": "➕ Penjumlahan Pecahan",
        "description": "Latihan penjumlahan pecahan",
        "knowledge_areas": ["addition"]
    },
    "fraction_subtraction": {
        "title": "➖ Pengurangan Pecahan",
        "description": "Latihan pengurangan pecahan",
        "knowledge_areas": ["subtraction"]
    },
    "fraction_multiplication": {
        "title": "✖️ Perkalian Pecahan",
        "description": "Latihan perkalian pecahan",
        "knowledge_areas": ["multiplication"]
    },
    # "fraction_division": {
    #     "title": "➗ Pembagian Pecahan",
    #     "description": "Latihan pembagian pecahan",
    #     "knowledge_areas": ["division"]
    # },
    # "post_test": {
    #     "title": "✅ Post-Test",
    #     "description": "Tes akhir untuk mengukur peningkatan pengetahuan Anda",
    #     "knowledge_areas": ["ordering", "addition", "subtraction", "multiplication", "division"]
    # }
}

# Initialize session state
if "current_section" not in st.session_state:
    st.session_state.current_section = "ordering_fractions"

if "quiz_answers" not in st.session_state:
    st.session_state.quiz_answers = {}  # {section: {question_id: answer}}

if "quiz_scores" not in st.session_state:
    st.session_state.quiz_scores = {}  # {section: score}

if "completed_sections" not in st.session_state:
    st.session_state.completed_sections = set()


def is_section_unlocked(section_key: str) -> bool:
    """Check if a section is unlocked based on current datetime."""
    now = datetime.now()
    return now >= QUIZ_SCHEDULE[section_key]


def get_unlocked_sections() -> list:
    """Get list of currently unlocked section keys."""
    return [key for key in QUIZ_SCHEDULE.keys() if is_section_unlocked(key)]


def get_time_until_unlock(section_key: str) -> str:
    """Get formatted time remaining until section unlocks."""
    now = datetime.now()
    unlock_time = QUIZ_SCHEDULE[section_key]
    
    if now >= unlock_time:
        return "Unlocked"
    
    time_diff = unlock_time - now
    days = time_diff.days
    hours, remainder = divmod(time_diff.seconds, 3600)
    minutes, _ = divmod(remainder, 60)
    
    if days > 0:
        return f"{days} hari lagi"
    elif hours > 0:
        return f"{hours} jam lagi"
    else:
        return f"{minutes} menit lagi"


def render_section_navigation():
    """Render the section navigation sidebar."""
    st.sidebar.title("📚 Bagian Quiz")
    
    for section_key, info in SECTION_INFO.items():
        unlocked = is_section_unlocked(section_key)
        completed = section_key in st.session_state.completed_sections
        
        # Create button label
        if completed:
            icon = "✅"
        elif unlocked:
            icon = "🔓"
        else:
            icon = "🔒"
        
        label = f"{icon} {info['title'].split(' ', 1)[1]}"  # Remove emoji from title
        
        # Show unlock time if locked
        if not unlocked:
            time_left = get_time_until_unlock(section_key)
            st.sidebar.caption(f"{label} - {time_left}")
        else:
            if st.sidebar.button(
                label,
                key=f"nav_{section_key}",
                disabled=not unlocked,
                use_container_width=True
            ):
                st.session_state.current_section = section_key
                st.rerun()
    
    # Show progress
    st.sidebar.divider()
    completed_count = len(st.session_state.completed_sections)
    total_count = len(SECTION_INFO)
    st.sidebar.progress(completed_count / total_count)
    st.sidebar.caption(f"Progress: {completed_count}/{total_count} bagian selesai")


def render_quiz_section(section_key: str):
    """Render the quiz for a specific section."""
    section_info = SECTION_INFO[section_key]
    
    # Header
    st.title(section_info["title"])
    st.markdown(f"*{section_info['description']}*")
    st.divider()
    
    # Check if unlocked
    if not is_section_unlocked(section_key):
        st.warning(f"⏰ Bagian ini akan tersedia pada {QUIZ_SCHEDULE[section_key].strftime('%d %B %Y, %H:%M')}")
        time_left = get_time_until_unlock(section_key)
        st.info(f"Waktu tersisa: {time_left}")
        return
    
    # Get questions
    questions = get_questions_by_section(section_key)
    
    if not questions:
        st.error("Tidak ada soal untuk bagian ini.")
        return
    
    # Initialize answers for this section if not exists
    if section_key not in st.session_state.quiz_answers:
        st.session_state.quiz_answers[section_key] = {}
    
    # Check if already completed
    if section_key in st.session_state.completed_sections:
        score = st.session_state.quiz_scores.get(section_key, 0)
        total = len(questions)
        percentage = (score / total * 100) if total > 0 else 0
        
        st.success(f"✅ Anda telah menyelesaikan bagian ini!")
        st.metric("Skor Anda", f"{score}/{total}", f"{percentage:.1f}%")
        
        # if st.button("Ulangi Quiz"):
        #     # Reset answers and completion status
        #     st.session_state.quiz_answers[section_key] = {}
        #     st.session_state.completed_sections.discard(section_key)
        #     if section_key in st.session_state.quiz_scores:
        #         del st.session_state.quiz_scores[section_key]
        #     st.rerun()
        return
    
    # Render questions
    with st.form(key=f"quiz_form_{section_key}"):
        answers = {}
        
        for i, question in enumerate(questions, 1):
            st.subheader(f"Soal {i}")
            
            # Render question with LaTeX support
            st.markdown(question["question"])
            
            # Get previous answer if exists
            prev_answer = st.session_state.quiz_answers[section_key].get(question["id"])
            
            # Render options
            answer = st.radio(
                "Pilih jawaban:",
                options=question["options"],
                key=f"{section_key}_{question['id']}",
                index=None if prev_answer is None else question["options"].index(prev_answer) if prev_answer in question["options"] else None
            )
            
            answers[question["id"]] = answer
            st.divider()
        
        # Submit button
        submitted = st.form_submit_button("Submit Jawaban", use_container_width=True)
        
        if submitted:
            # Check if all questions answered
            unanswered = [i+1 for i, q in enumerate(questions) if not answers.get(q["id"])]
            
            if unanswered:
                st.error(f"⚠️ Mohon jawab semua soal! Soal yang belum dijawab: {', '.join(map(str, unanswered))}")
            else:
                # Calculate score
                score = 0
                for question in questions:
                    selected = answers[question["id"]]
                    # Extract letter from answer (e.g., "A. ..." -> "A")
                    selected_letter = selected.split(".")[0] if selected else None
                    if selected_letter == question["correct_answer"]:
                        score += 1
                
                # Log to database
                try:
                    student_id = get_student_id()
                    if student_id:
                        # Log each question submission to quiz_results table
                        for question in questions:
                            selected = answers[question["id"]]
                            selected_letter = selected.split(".")[0] if selected else None
                            is_correct = selected_letter == question["correct_answer"]
                            success = log_quiz_submission(
                                student_id=student_id,
                                quiz_section=section_key,
                                question_id=question["id"],
                                question_text=question["question"],
                                student_answer=selected or "No answer",
                                correct_answer=question["correct_answer"],
                                is_correct=is_correct,
                                knowledge_areas=question.get("knowledge_areas", [])
                            )
                            
                            if not success:
                                st.warning(f"Gagal menyimpan jawaban soal {question['id']}")
                                
                except Exception as e:
                    st.error(f"Gagal menyimpan hasil ke database: {e}")
                
                 # Save results
                st.session_state.quiz_answers[section_key] = answers
                st.session_state.quiz_scores[section_key] = score
                st.session_state.completed_sections.add(section_key)
                st.rerun()


# Main app
st.set_page_config(page_title="Quiz Pecahan", page_icon="📝", layout="wide")

# Render navigation
render_section_navigation()

# Render current section
render_quiz_section(st.session_state.current_section)