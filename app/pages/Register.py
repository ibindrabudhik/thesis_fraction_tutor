"""Registration page for new students."""
import streamlit as st
import sys
import os

# Add parent directory to path to import modules
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from database.student_service import create_student, get_student_by_username
from auth.session import login_user, is_authenticated


# Redirect if already logged in
if is_authenticated():
    st.switch_page("pages/Homepage.py")

# ---------- PAGE CONFIG ----------
st.markdown("""
    <div style="display: flex; align-items: center; justify-content: center; margin-bottom: 20px;">
        <img src="https://img.icons8.com/emoji/48/robot-emoji.png" style="margin-right: 10px;">
        <h1 style="display: inline;">Uma Fraction Tutor</h1>
    </div>
""", unsafe_allow_html=True)

st.markdown("<h2 style='text-align: center;'>📝 Daftar Akun Baru</h2>", unsafe_allow_html=True)
st.markdown("<p style='text-align: center;'>Buat akun untuk mulai belajar pecahan bersama Uma</p>", unsafe_allow_html=True)

# ---------- REGISTRATION FORM ----------
with st.form("register_form"):
    st.markdown("### Informasi Akun")
    
    name = st.text_input("👤 Nama Lengkap", placeholder="Masukkan nama lengkap")
    username = st.text_input(
        "🔑 Username", 
        placeholder="YPSSTUDENT_1",
        help="Format: YPSSTUDENT_[nomor], contoh: YPSSTUDENT_1, YPSSTUDENT_2"
    )
    email = st.text_input("📧 Email (Opsional)", placeholder="nama@email.com")
    
    col1, col2 = st.columns(2)
    with col1:
        password = st.text_input("🔒 Password", type="password", placeholder="Minimal 6 karakter")
    with col2:
        password_confirm = st.text_input("🔒 Konfirmasi Password", type="password", placeholder="Ulangi password")
    
    # Terms and conditions
    agree = st.checkbox("Saya setuju dengan syarat dan ketentuan penggunaan")
    
    col1, col2, col3 = st.columns([1, 2, 1])
    with col2:
        submit = st.form_submit_button("✅ Daftar", use_container_width=True)
    
    if submit:
        # Validation
        errors = []
        
        if not name or not username or not password:
            errors.append("Nama, username, dan password harus diisi!")
        
        # Validate username format
        if username and not username.upper().startswith("YPSSTUDENT_"):
            errors.append("Format username harus: YPSSTUDENT_[nomor]")
        
        if len(password) < 6:
            errors.append("Password minimal 6 karakter!")
        
        if password != password_confirm:
            errors.append("Password dan konfirmasi password tidak cocok!")
        
        if not agree:
            errors.append("Anda harus menyetujui syarat dan ketentuan!")
        
        # Check email format (if provided)
        if email and "@" not in email:
            errors.append("Format email tidak valid!")
        
        if errors:
            for error in errors:
                st.error(f"⚠️ {error}")
        else:
            try:
                # Check if username already exists
                existing = get_student_by_username(username)
                if existing:
                    st.error("❌ Username sudah terdaftar. Silakan gunakan username lain atau login.")
                else:
                    # Create new student
                    student = create_student(
                        username=username,
                        name=name,
                        password=password,
                        email=email if email else None
                    )
                    
                    st.success("✅ Akun berhasil dibuat!")
                    st.balloons()
                    
                    # Auto-login after registration
                    login_user(student)
                    
                    st.info("🎉 Selamat datang! Anda akan diarahkan ke halaman utama...")
                    
                    # Small delay for visual feedback
                    import time
                    time.sleep(2)
                    
                    # Redirect to homepage
                    st.switch_page("pages/Homepage.py")
                    
            except Exception as e:
                st.error(f"❌ Terjadi kesalahan saat mendaftar: {e}")
                st.info("💡 Pastikan database Supabase sudah dikonfigurasi dengan benar.")

st.markdown("---")

# ---------- LOGIN LINK ----------
col1, col2, col3 = st.columns([1, 2, 1])
with col2:
    st.markdown("<p style='text-align: center;'>Sudah punya akun?</p>", unsafe_allow_html=True)
    if st.button("🔐 Login di sini", use_container_width=True):
        st.switch_page("pages/Login.py")

st.markdown("---")

# ---------- INFO ----------
with st.expander("ℹ️ Tentang Uma Fraction Tutor", expanded=False):
    st.markdown("""
    **Uma Fraction Tutor** adalah sistem pembelajaran pecahan interaktif yang menggunakan
    kecerdasan buatan untuk memberikan feedback yang disesuaikan dengan kebutuhan Anda.
    
    **Fitur:**
    - 🤖 Tutor AI yang membantu belajar pecahan
    - 📊 Pelacakan progress dan achievement
    - 💬 Feedback yang disesuaikan dengan level Anda
    - 📚 Berbagai soal dengan tingkat kesulitan bervariasi
    - 📈 Sistem adaptif yang menyesuaikan soal dengan kemampuan Anda
    
    **Privasi:**
    Data Anda aman dan hanya digunakan untuk meningkatkan pengalaman belajar Anda.
    """)
