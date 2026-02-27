import streamlit as st
import sys
import os

# Add parent directory to path to import modules
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from auth.session import require_authentication, get_student_name, get_student_id, logout_user
from database.log_service import get_student_statistics


# ---------- AUTHENTICATION ----------
require_authentication()

# ---------- PAGE CONTENT ----------
uname = get_student_name()
student_id = get_student_id()

st.markdown("""
    <div style="display: flex; align-items: center;">
        <img src="https://img.icons8.com/emoji/48/robot-emoji.png" style="margin-right: 10px;">
        <h1 style="display: inline;">Uma Fraction Tutor</h1>
    </div>
""", unsafe_allow_html=True)

st.markdown('''
            <div>
                <p style="font-size:24px; font-weight: bold;">Selamat datang kembali, {}!</p>
            </div>
            '''.format(uname), unsafe_allow_html=True)

# Logout button
col1, col2, col3 = st.columns([5, 1, 1])
with col3:
    if st.button("🚪 Logout"):
        logout_user()
        st.switch_page("app/pages/Login.py")

# ---------- Dashboard Content ----------
st.markdown("---")

# Fetch real statistics from database
try:
    if student_id and student_id != "DEMO":
        stats = get_student_statistics(student_id)
        
        total_sessions = stats.get("total_sessions", 0)
        completed_correctly = stats.get("completed_correctly", 0)
        success_rate = stats.get("success_rate", 0.0)
        recent_achievement = stats.get("recent_achievement_level", "Low")
    else:
        # Demo mode
        total_sessions = 0
        completed_correctly = 0
        success_rate = 0.0
        recent_achievement = "Low"
except Exception as e:
    st.error(f"Error loading statistics: {e}")
    total_sessions = 0
    completed_correctly = 0
    success_rate = 0.0
    recent_achievement = "Low"

col1, col2 = st.columns(2)

with col1:
    st.subheader("📊 Statistik Belajar")
    st.metric("Sesi Belajar", total_sessions)
    st.metric("Soal Diselesaikan Benar", completed_correctly)
    st.metric("Tingkat Keberhasilan", f"{success_rate}%")

with col2:
    st.subheader("🎯 Pencapaian")
    
    if total_sessions == 0:
        st.info("📝 Belum ada sesi belajar. Mulai sekarang!")
    else:
        if success_rate >= 70:
            st.success(f"✅ Achievement Level: {recent_achievement}")
            st.success(f"🎉 Tingkat keberhasilan: {success_rate}%")
        elif success_rate >= 40:
            st.info(f"📝 Achievement Level: {recent_achievement}")
            st.info(f"💪 Tingkat keberhasilan: {success_rate}%")
        else:
            st.warning(f"⏳ Achievement Level: {recent_achievement}")
            st.warning(f"📚 Tingkat keberhasilan: {success_rate}% - Terus berlatih!")
    
    st.markdown(f"**Achievement Level Terkini:** {recent_achievement}")

st.markdown("---")

st.subheader("🚀 Mulai Belajar")
st.markdown("Pilih aktivitas belajar yang ingin kamu lakukan:")

col1, col2, col3 = st.columns(3)

with col1:
    if st.button("💬 Belajar Bareng Uma", key="nav_study", use_container_width=True):
        st.switch_page("pages/Study_Chat.py")

with col2:
    if st.button("📚 Lihat Riwayat", key="nav_history", use_container_width=True):
        st.switch_page("pages/History.py")

with col3:
    if st.button("❓ Quiz Pecahan", key="nav_quiz", use_container_width=True):
        st.switch_page("pages/Quiz.py")
