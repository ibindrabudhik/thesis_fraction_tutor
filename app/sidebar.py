import streamlit as st
import datetime

# GMT+8 timezone (WIB - Waktu Indonesia Barat)
GMT8 = datetime.timezone(datetime.timedelta(hours=8))

# ---------- CONFIG ----------
# Translate tanggal ke bahasa Indonesia
days_id = {
    "Monday": "Senin", "Tuesday": "Selasa", "Wednesday": "Rabu",
    "Thursday": "Kamis", "Friday": "Jumat", "Saturday": "Sabtu", "Sunday": "Minggu"
}

months_id = {
    "January": "Januari", "February": "Februari", "March": "Maret", "April": "April",
    "May": "Mei", "June": "Juni", "July": "Juli", "August": "Agustus",
    "September": "September", "October": "Oktober", "November": "November", "December": "Desember"
}

# Get current time in GMT+8
now = datetime.datetime.now(GMT8)

# Translate
english_day = now.strftime("%A")
english_month = now.strftime("%B")
tanggal = now.strftime("%d")
tahun = now.strftime("%Y")

indonesian_day = days_id.get(english_day, english_day)
indonesian_month = months_id.get(english_month, english_month)

# Final string
datetime_today = f"{indonesian_day}, {tanggal} {indonesian_month} {tahun}"

# ---------- SIDEBAR ----------
def render_sidebar_main(page_key="main"):
    st.sidebar.markdown("<h1 style='text-align: center;'>{}</h1>".format(datetime_today), unsafe_allow_html=True)



def get_pages_main():
    pages = {
        "Beranda": [
            st.Page("pages/Homepage.py", title="Halaman Utama", icon="🏠")
        ],
        "Belajar": [
            st.Page("pages/Study_Chat.py", title="Belajar Bareng Uma", icon="💬"),
            st.Page("pages/Quiz.py", title="Quiz Pecahan", icon="❓")
        ],
        "Progress": [
            st.Page("pages/History.py", title="Riwayat Belajar", icon="📚"),
            st.Page("pages/Session_Detail.py", title="Detail Sesi", icon="📖"),
            st.Page("pages/Leaderboard.py", title="Leaderboard", icon="🏆"),
            st.Page("pages/Feedback_Form.py", title="Form Feedback", icon="📝")
        ],
        # "Sumber Pembelajaran": [
        #     st.Page("pages/Resources.py", title="Sumber Belajar", icon="📖")
        # ]
    }
    return pages

def get_pages_other():
    pages = {
        "Beranda": [
            st.Page("pages/Homepage.py", title="Halaman Utama", icon="🏠")
        ],
        "Belajar": [
            st.Page("pages/Study_Chat.py", title="Belajar Bareng Uma", icon="💬"),
            st.Page("pages/Quiz.py", title="Quiz Pecahan", icon="❓")
        ]
    }
    return pages