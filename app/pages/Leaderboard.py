"""Leaderboard page ranking students by completed sessions."""
import streamlit as st
import sys
import os

# Add parent directory to path to import modules
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from auth.session import require_authentication, get_student_id
from database.log_service import get_session_leaderboard


# ---------- AUTHENTICATION ----------
require_authentication()

# ---------- PAGE CONTENT ----------
st.title("🏆 Leaderboard Sesi Belajar")
st.markdown("Ranking berdasarkan jumlah sesi unik yang diselesaikan")
st.markdown("Top Students yang menyelesaikan sesi terbanyak akan dapat hadiah menarik loh! 🎁")
# st.caption("Hanya menghitung username format YPSSTUDENT_XXX (3 digit).")

min_sessions = st.number_input("Minimum sesi", min_value=1, value=1, step=1)

leaderboard = get_session_leaderboard(min_sessions=min_sessions)

if not leaderboard:
    st.info("Belum ada data leaderboard yang cocok.")
    st.stop()

current_student_id = get_student_id()

rows = []
for row in leaderboard:
    name = row.get("name") or "-"
    username = row.get("username") or "-"

    display_name = f"⭐ {name}" if row.get("student_id") == current_student_id else name

    rows.append({
        "Rank": row.get("rank"),
        "Nama": display_name,
        "Total Sesi": row.get("total_sessions", 0),
        "Total Log": row.get("total_logs", 0),
        "Aktivitas Terakhir": row.get("last_activity"),
    })

st.dataframe(
    rows,
    use_container_width=True,
    hide_index=True,
)

# Top 3 quick cards
st.markdown("### 🥇 Top 3")
cols = st.columns(3)
for i in range(3):
    with cols[i]:
        if i < len(leaderboard):
            r = leaderboard[i]
            st.metric(
                label=f"#{r['rank']} {r.get('username', '-')}",
                value=f"{r.get('total_sessions', 0)} sesi"
            )
        else:
            st.metric(label="-", value="0 sesi")
