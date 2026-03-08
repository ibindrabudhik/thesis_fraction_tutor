import streamlit as st
import sys
import os

# Add parent directory to path to import modules
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from auth.session import require_authentication, get_student_id
from database.feedback_service import submit_student_feedback


require_authentication()

st.title("📝 Form Feedback Pengguna")
st.markdown("""
            Terima kasih sudah mau berpartisipasi di penelitian ku :)
            Bantu aku untuk mengetahui bagaimana pengalaman teman-teman 
            menggunakan AI tutor selama dua pekan ini dengan mengisi form berikut.
            """)

LIKERT_OPTIONS = {
    "1": "1 - Sangat Tidak Setuju",
    "2": "2 - Tidak Setuju",
    "3": "3 - Setuju",
    "4": "4 - Sangat Setuju",
}

SECTIONS = {
    "system_usability": {
        "title": "System Usability",
        "questions": [
            "Sistem tutor ini mudah digunakan.",
            "Instruksi yang diberikan oleh sistem jelas dan mudah dipahami.",
            "Saya dapat menggunakan sistem ini tanpa kesulitan yang sangat menghambat.",
            "Tampilan sistem tutor mudah dipahami.",
            "Saya dapat mengikuti langkah-langkah pembelajaran dengan baik menggunakan sistem ini.",
        ],
    },
    "feedback_quality": {
        "title": "Feedback Quality",
        "questions": [
            "Feedback yang diberikan tutor membantu saya memahami kesalahan saya.",
            "Feedback dari tutor tidak langsung memberikan jawaban, tetapi membantu saya berpikir.",
            "Penjelasan yang diberikan tutor mudah dimengerti.",
            "Feedback dari tutor relevan dengan jawaban yang saya berikan.",
            "Feedback dari tutor membantu saya menemukan cara yang benar untuk menyelesaikan soal.",
        ],
    },
    "pemahaman_materi_pecahan": {
        "title": "Pemahaman Materi Pecahan",
        "questions": [
            "Sistem tutor membantu saya lebih memahami konsep pecahan.",
            "Setelah menggunakan sistem ini, saya merasa lebih percaya diri dalam menyelesaikan soal pecahan.",
            "Sistem tutor membantu saya mengetahui bagian mana yang saya belum pahami.",
            "Latihan yang diberikan sistem membantu saya memperbaiki kesalahan saya.",
            "Sistem tutor membantu saya belajar langkah-langkah penyelesaian soal dengan lebih baik.",
        ],
    },
    "learning_experience": {
        "title": "Learning Experience",
        "questions": [
            "Belajar menggunakan sistem tutor ini menyenangkan.",
            "Sistem tutor membuat saya lebih tertarik untuk belajar matematika.",
            "Sistem tutor membuat proses belajar lebih interaktif.",
            "Saya merasa sistem tutor ini seperti belajar dengan seorang guru.",
        ],
    },
    "user_satisfaction": {
        "title": "User Satisfaction",
        "questions": [
            "Secara keseluruhan saya puas menggunakan sistem tutor ini.",
            "Sistem tutor ini membantu proses belajar saya.",
            "Saya akan merekomendasikan sistem ini kepada teman saya.",
        ],
    },
}

OPEN_QUESTIONS = [
    "Apa yang paling membantu dari sistem tutor ini?",
    "Apa yang menurut kamu masih perlu diperbaiki dari sistem tutor ini?",
    "Apakah ada bagian dari penjelasan tutor yang sulit dipahami? Jika ada, jelaskan.",
    "Apakah ada bagian dari penjelasan tutor yang terlihat aneh atau salah? Jika ada, jelaskan serta sebutkan berapa kali hal tersebut terjadi?",
    "Saran kamu untuk meningkatkan sistem tutor ini.",
]

student_id = get_student_id()
if not student_id:
    st.error("Student ID tidak ditemukan. Silakan login ulang.")
    st.stop()

with st.form("feedback_form"):
    likert_answers = {}

    st.info("Semua pertanyaan wajib diisi. Untuk pertanyaan terbuka, jika tidak ada jawaban khusus, isi dengan '-' (strip).")

    for section_key, section in SECTIONS.items():
        st.subheader(section["title"])
        for idx, question in enumerate(section["questions"], start=1):
            qid = f"{section_key}_{idx}"
            selected = st.radio(
                question,
                options=list(LIKERT_OPTIONS.keys()),
                format_func=lambda x: LIKERT_OPTIONS[x],
                index=None,
                key=f"q_{qid}",
            )
            likert_answers[qid] = {
                "section": section["title"],
                "question": question,
                "score": int(selected) if selected else None,
            }
        st.markdown("---")

    st.subheader("Pertanyaan Terbuka")
    open_answers = {}
    for idx, question in enumerate(OPEN_QUESTIONS, start=1):
        answer = st.text_area(question, key=f"open_{idx}", height=100)
        open_answers[f"open_{idx}"] = {
            "question": question,
            "answer": answer.strip(),
        }

    submitted = st.form_submit_button("Kirim Feedback", use_container_width=True)

    if submitted:
        unanswered_likert = [
            payload["question"]
            for payload in likert_answers.values()
            if payload["score"] is None
        ]

        unanswered_open = [
            payload["question"]
            for payload in open_answers.values()
            if not payload["answer"]
        ]

        if unanswered_likert:
            st.error("Mohon isi semua pertanyaan skala Likert (1-4).")
        elif unanswered_open:
            st.error("Mohon isi semua pertanyaan terbuka. Jika tidak ada jawaban khusus, isi dengan '-' (strip).")
        else:
            ok = submit_student_feedback(
                student_id=student_id,
                likert_answers=likert_answers,
                open_answers=open_answers,
            )
            if ok:
                st.success("✅ Terima kasih! Feedback kamu berhasil disimpan.")
            else:
                st.error("❌ Gagal menyimpan feedback. Silakan coba lagi.")
