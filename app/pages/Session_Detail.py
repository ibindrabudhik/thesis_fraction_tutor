"""Session detail page to view complete chat history for a session."""
import streamlit as st
import sys
import os
from datetime import datetime

# Add parent directory to path to import modules
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from auth.session import require_authentication, get_student_id
from database.log_service import get_session_details
from database.chat_service import get_chat_history
from ai.rag_pipeline import explain_contexts


def render_latex(text: str) -> str:
    """Process text to ensure all LaTeX expressions are properly wrapped in $ delimiters.
    
    Handles cases where the LLM outputs bare LaTeX commands without $ wrapping,
    e.g. \\frac{1}{2} instead of $\\frac{1}{2}$.
    """
    if not text:
        return text
    
    import re

    def _to_mixed_or_fraction(match, wrap_with_dollar: bool = True):
        """Convert plain a/b into LaTeX fraction (supports packed mixed style)."""
        num_str = match.group(1)
        den_str = match.group(2)
        numerator = int(num_str)
        denominator = int(den_str)

        def _pack(expr: str) -> str:
            return f"${expr}$" if wrap_with_dollar else expr

        if denominator == 0:
            return match.group(0)

        # Packed mixed-number heuristic: 11/5 -> 1\frac{1}{5}, 14/5 -> 1\frac{4}{5}
        if len(num_str) >= 2:
            whole_part = int(num_str[:-1])
            remainder = int(num_str[-1])
            if whole_part > 0 and 0 <= remainder < denominator:
                return _pack(f"{whole_part}\\frac{{{remainder}}}{{{denominator}}}")

        if numerator >= denominator:
            whole = numerator // denominator
            remainder = numerator % denominator
            if remainder == 0:
                return _pack(f"{whole}")
            return _pack(f"{whole}\\frac{{{remainder}}}{{{denominator}}}")

        return _pack(f"\\frac{{{numerator}}}{{{denominator}}}")
    
    # Step 1: Protect already-delimited LaTeX blocks by replacing them with placeholders
    placeholders = []
    
    def _placeholder(match):
        placeholders.append(match.group(0))
        return f"\x00LATEX{len(placeholders) - 1}\x00"
    
    # Protect $$...$$ blocks first, then $...$ blocks
    text = re.sub(r'\$\$[^$]+?\$\$', _placeholder, text)
    text = re.sub(r'\$[^$]+?\$', _placeholder, text)
    
    # Step 2: Wrap bare \frac{...}{...} (including with optional leading number like 3\frac{1}{2})
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

    # Step 4: Convert plain fractions like 11/5 to LaTeX.
    # Improper fractions are shown as mixed numbers, e.g. 11/5 -> 2\frac{1}{5}.
    text = re.sub(r'(?<!\d)(\d+)\s*/\s*(\d+)(?!\d)', _to_mixed_or_fraction, text)
    
    # Step 5: Merge adjacent $ delimiters: "$a$ $b$" → "$a \; b$" and "$x$$y$" → "$x y$"
    text = re.sub(r'\$\s*\$', ' ', text)
    
    # Step 6: Restore protected blocks
    for i, original in enumerate(placeholders):
        # Also normalize slash fractions inside existing inline math blocks: $11/5$ -> $1\frac{1}{5}$
        if original.startswith("$") and original.endswith("$") and not original.startswith("$$"):
            inner = original[1:-1]
            inner = re.sub(
                r'(?<!\d)(\d+)\s*/\s*(\d+)(?!\d)',
                lambda m: _to_mixed_or_fraction(m, wrap_with_dollar=False),
                inner,
            )
            original = f"${inner}$"
        text = text.replace(f"\x00LATEX{i}\x00", original)
    
    return text


# ---------- AUTHENTICATION ----------
require_authentication()

# ---------- PAGE CONTENT ----------
st.title("📖 Detail Sesi Belajar")

# Check if session ID is provided
if "selected_session_id" not in st.session_state or not st.session_state.selected_session_id:
    st.warning("⚠️ Tidak ada sesi yang dipilih.")
    if st.button("🔙 Kembali ke Riwayat"):
        st.switch_page("pages/History.py")
    st.stop()

session_id = st.session_state.selected_session_id
student_id = get_student_id()

# ---------- FETCH SESSION DATA ----------
try:
    # Get session logs
    logs = get_session_details(session_id)
    
    if not logs:
        st.error("❌ Sesi tidak ditemukan atau sudah dihapus.")
        if st.button("🔙 Kembali ke Riwayat"):
            st.switch_page("pages/History.py")
        st.stop()
    
    # Get the first log for problem details
    first_log = logs[0]
    question = first_log.get("question", "N/A")
    task_level = first_log.get("task_level", "N/A")
    
    # Get the last log for final results
    last_log = logs[-1]
    is_correct_final = last_log.get("is_correct_final", False)
    error_count = last_log.get("error_count", 0)
    achievement_assessed = last_log.get("achievement_level_assessed", "N/A")
    feedback_type = last_log.get("feedback_type", "N/A")
    
    # Get chat history
    chat_messages = get_chat_history(session_id)
    
    # ---------- DISPLAY HEADER ----------
    st.markdown("### 📝 Informasi Sesi")
    
    col1, col2, col3 = st.columns(3)
    with col1:
        st.metric("Status", "✅ Benar" if is_correct_final else "❌ Salah")
    with col2:
        st.metric("Jumlah Kesalahan", error_count)
    with col3:
        st.metric("Achievement Level", achievement_assessed)
    
    col1, col2 = st.columns(2)
    with col1:
        st.metric("Task Level", task_level)
    with col2:
        st.metric("Feedback Type", feedback_type)
    
    st.markdown("---")
    
    # ---------- DISPLAY PROBLEM ----------
    st.markdown("### 📋 Soal")
    # Render LaTeX by using st.markdown directly (Streamlit auto-renders $ and $$ delimiters)
    st.markdown(render_latex(question))
    
    st.markdown("---")
    
    # ---------- DISPLAY CHAT HISTORY ----------
    st.markdown("### 💬 Riwayat Percakapan")
    
    if not chat_messages:
        st.info("📭 Tidak ada percakapan yang tersimpan untuk sesi ini.")
    else:
        for idx, message in enumerate(chat_messages):
            role = message.get("role", "")
            content = message.get("content", "")
            contexts = message.get("contexts", [])
            
            with st.chat_message(role):
                # Render LaTeX in messages
                st.markdown(render_latex(content))
                
                # Show contexts for assistant messages
                if role == "assistant" and contexts:
                    with st.expander("📚 Sumber Pengetahuan", expanded=False):
                        for formatted in explain_contexts(contexts):
                            st.markdown(render_latex(formatted))
    
    st.markdown("---")
    
    # ---------- DISPLAY FINAL FEEDBACK ----------
    st.markdown("### 📊 Feedback Akhir")
    final_feedback = last_log.get("feedback_given", "Tidak ada feedback")
    # Render LaTeX in final feedback
    st.markdown(render_latex(final_feedback))
    
    st.markdown("---")
    
    # ---------- STATISTICS ----------
    with st.expander("📈 Statistik Sesi", expanded=False):
        total_messages = len(chat_messages)
        user_messages = len([m for m in chat_messages if m.get("role") == "user"])
        assistant_messages = len([m for m in chat_messages if m.get("role") == "assistant"])
        
        col1, col2, col3 = st.columns(3)
        with col1:
            st.metric("Total Pesan", total_messages)
        with col2:
            st.metric("Pesan Siswa", user_messages)
        with col3:
            st.metric("Pesan Uma", assistant_messages)
        
        # Timestamp info
        if chat_messages:
            first_msg_time = chat_messages[0].get("timestamp", "")
            last_msg_time = chat_messages[-1].get("timestamp", "")
            
            if first_msg_time and last_msg_time:
                try:
                    first_dt = datetime.fromisoformat(first_msg_time.replace("Z", "+00:00"))
                    last_dt = datetime.fromisoformat(last_msg_time.replace("Z", "+00:00"))
                    duration = last_dt - first_dt
                    
                    st.markdown(f"**Waktu Mulai:** {first_dt.strftime('%d %b %Y, %H:%M')}")
                    st.markdown(f"**Waktu Selesai:** {last_dt.strftime('%d %b %Y, %H:%M')}")
                    st.markdown(f"**Durasi:** {duration.total_seconds() / 60:.1f} menit")
                except:
                    pass

except Exception as e:
    st.error(f"❌ Terjadi kesalahan saat mengambil detail sesi: {e}")
    st.info("💡 Pastikan database Supabase sudah dikonfigurasi dengan benar.")

# ---------- ACTIONS ----------
st.markdown("---")
col1, col2, col3 = st.columns(3)

with col1:
    if st.button("🔙 Kembali ke Riwayat", use_container_width=True):
        if "selected_session_id" in st.session_state:
            del st.session_state.selected_session_id
        st.switch_page("pages/History.py")

with col2:
    if st.button("🏠 Ke Beranda", use_container_width=True):
        if "selected_session_id" in st.session_state:
            del st.session_state.selected_session_id
        st.switch_page("pages/Homepage.py")

with col3:
    if st.button("🤖 Belajar Lagi", use_container_width=True):
        if "selected_session_id" in st.session_state:
            del st.session_state.selected_session_id
        st.switch_page("pages/Study_Chat.py")
