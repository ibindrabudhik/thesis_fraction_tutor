"""History page to view past learning sessions."""
import streamlit as st
import sys
import os
import re
from datetime import datetime

# Add parent directory to path to import modules
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from auth.session import require_authentication, get_student_id
from database.log_service import get_student_history


def _format_question_preview(question: str, max_len: int = 80) -> str:
    """Convert common LaTeX tokens to readable symbols for preview text."""
    if not question:
        return ""

    # Truncate first to avoid breaking rendered math markup in preview
    formatted = question[:max_len] + "..." if len(question) > max_len else question

    def _to_mixed_fraction(match):
        num_str = match.group(1)
        den_str = match.group(2)
        denominator = int(den_str)

        if denominator == 0:
            return match.group(0)

        # Packed mixed-number heuristic: 11/5 -> 1\frac{1}{5}, 14/5 -> 1\frac{4}{5}
        if len(num_str) >= 2:
            whole_part = int(num_str[:-1])
            remainder = int(num_str[-1])
            if whole_part > 0 and 0 <= remainder < denominator:
                return f"${whole_part}\\frac{{{remainder}}}{{{denominator}}}$"

        numerator = int(num_str)
        if numerator >= denominator:
            whole = numerator // denominator
            remainder = numerator % denominator
            if remainder == 0:
                return f"${whole}$"
            return f"${whole}\\frac{{{remainder}}}{{{denominator}}}$"

        return f"$\\frac{{{numerator}}}{{{denominator}}}$"

    # Convert common operators
    formatted = formatted.replace(r"\times", "×")
    formatted = formatted.replace(r"\div", "÷")
    formatted = formatted.replace(r"\cdot", "·")

    # Convert simple fractions: \frac{a}{b} -> a/b
    formatted = re.sub(r"\\frac\{([^{}]+)\}\{([^{}]+)\}", r"\1/\2", formatted)

    # Convert plain fractions to math-rendered form
    formatted = re.sub(r'(?<!\d)(\d+)\s*/\s*(\d+)(?!\d)', _to_mixed_fraction, formatted)

    # Remove inline math delimiters
    return formatted


# ---------- AUTHENTICATION ----------
require_authentication()

# ---------- PAGE CONTENT ----------
st.title("📚 Riwayat Belajar")
st.markdown("Lihat semua sesi belajar yang pernah kamu lakukan")

student_id = get_student_id()

if not student_id:
    st.error("⚠️ Student ID tidak ditemukan. Silakan login kembali.")
    st.stop()

# ---------- FETCH HISTORY ----------
try:
    sessions = get_student_history(student_id, limit=50)
    
    if not sessions:
        st.info("📭 Belum ada riwayat belajar. Mulai belajar dengan Uma untuk melihat progress kamu!")
        
        if st.button("🚀 Mulai Belajar"):
            st.switch_page("pages/Study_Chat.py")
    else:
        st.markdown(f"**Total Sesi:** {len(sessions)}")
        st.markdown("---")
        
        # Filter options
        col1, col2, col3 = st.columns(3)
        with col1:
            filter_level = st.selectbox("Filter Level", ["Semua", "Low", "High"])
        with col2:
            filter_status = st.selectbox("Filter Status", ["Semua", "Benar", "Salah"])
        with col3:
            sort_order = st.selectbox("Urutkan", ["Terbaru", "Terlama"])
        
        # Apply filters
        filtered_sessions = sessions.copy()
        
        if filter_level != "Semua":
            filtered_sessions = [s for s in filtered_sessions if s.get("task_level") == filter_level]
        
        if filter_status == "Benar":
            filtered_sessions = [s for s in filtered_sessions if s.get("is_correct_final") == True]
        elif filter_status == "Salah":
            filtered_sessions = [s for s in filtered_sessions if s.get("is_correct_final") == False]
        
        # Sort
        if sort_order == "Terlama":
            filtered_sessions.reverse()
        
        st.markdown(f"**Ditampilkan:** {len(filtered_sessions)} sesi")
        st.markdown("---")
        
        # Display sessions
        for idx, session in enumerate(filtered_sessions):
            question = session.get("question", "")
            question_preview = _format_question_preview(question, max_len=80)
            
            timestamp = session.get("timestamp", "")
            if timestamp:
                try:
                    dt = datetime.fromisoformat(timestamp.replace("Z", "+00:00"))
                    formatted_time = dt.strftime("%d %b %Y, %H:%M")
                except:
                    formatted_time = timestamp
            else:
                formatted_time = "N/A"
            
            is_correct = session.get("is_correct_final", False)
            error_count = session.get("error_count", 0)
            task_level = session.get("task_level", "N/A")
            achievement = session.get("achievement_level_assessed", "N/A")
            
            # Status icon
            status_icon = "✅" if is_correct else "❌"
            status_text = "Benar" if is_correct else "Salah (3 kesalahan)"
            status_color = "green" if is_correct else "red"
            
            # Create card
            with st.container():
                col1, col2 = st.columns([3, 1])
                
                with col1:
                    st.markdown(f"### {status_icon} Sesi #{idx + 1}")
                    st.markdown(f"**Soal:** {question_preview}")
                    st.markdown(f"**Level:** {task_level} | **Achievement:** {achievement} | **Errors:** {error_count}")
                    st.caption(f"⏰ {formatted_time}")
                
                with col2:
                    st.markdown(f"<p style='color: {status_color}; font-weight: bold; font-size: 18px;'>{status_text}</p>", unsafe_allow_html=True)
                    
                    # View detail button
                    if st.button("📖 Lihat Detail", key=f"detail_{session['session_id']}"):
                        st.session_state.selected_session_id = session['session_id']
                        st.switch_page("pages/Session_Detail.py")
                
                st.markdown("---")
        
        # Pagination (if needed)
        if len(sessions) >= 50:
            st.info("💡 Menampilkan 50 sesi terbaru. Filter untuk melihat sesi tertentu.")

except Exception as e:
    st.error(f"❌ Terjadi kesalahan saat mengambil riwayat: {e}")
    st.info("💡 Pastikan database Supabase sudah dikonfigurasi dengan benar.")

# ---------- ACTIONS ----------
st.markdown("---")
col1, col2 = st.columns(2)

with col1:
    if st.button("🏠 Kembali ke Beranda", use_container_width=True):
        st.switch_page("Homepage.py")

with col2:
    if st.button("🤖 Belajar Bareng Uma", use_container_width=True):
        st.switch_page("Study_Chat.py")
