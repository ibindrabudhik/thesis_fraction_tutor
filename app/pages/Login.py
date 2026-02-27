"""Login page for student authentication."""
import streamlit as st
import sys
import os

# Add parent directory to path to import modules
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from database.student_service import authenticate_student
from auth.session import login_user, is_authenticated


# Redirect if already logged in
if is_authenticated():
    st.switch_page("app/pages/Homepage.py")

# ---------- PAGE CONFIG ----------
st.markdown("""
    <div style="display: flex; align-items: center; justify-content: center; margin-bottom: 20px;">
        <img src="https://img.icons8.com/emoji/48/robot-emoji.png" style="margin-right: 10px;">
        <h1 style="display: inline;">Uma Fraction Tutor</h1>
    </div>
""", unsafe_allow_html=True)

st.markdown("<h2 style='text-align: center;'>🔐 Login</h2>", unsafe_allow_html=True)
st.markdown("<p style='text-align: center;'>Masuk untuk melanjutkan belajar Pecahan</p>", unsafe_allow_html=True)

# ---------- LOGIN FORM ----------
with st.form("login_form"):
    st.markdown("### Masukkan Kredensial Anda")
    
    username = st.text_input("👤 Username", placeholder="YPSSTUDENT_1")
    password = st.text_input("🔒 Password", type="password", placeholder="Masukkan password")
    
    col1, col2, col3 = st.columns([1, 2, 1])
    with col2:
        submit = st.form_submit_button("🚀 Login", use_container_width=True)
    
    if submit:
        if not username or not password:
            st.error("⚠️ Username dan password harus diisi!")
        else:
            try:
                # Authenticate user
                student = authenticate_student(username, password)
                
                if student:
                    # Login successful
                    login_user(student)
                    st.success(f"✅ Selamat datang kembali, {student.get('name', 'Siswa')}!")
                    st.balloons()
                    
                    # Small delay for visual feedback
                    import time
                    time.sleep(1)
                    
                    # Redirect to homepage
                    st.switch_page("app/pages/Homepage.py")
                else:
                    st.error("❌ Username atau password salah. Silakan coba lagi.")
                    
            except Exception as e:
                st.error(f"❌ Terjadi kesalahan: {e}")
                st.info("💡 Pastikan database Supabase sudah dikonfigurasi dengan benar.")

st.markdown("---")

# ---------- REGISTER LINK ----------
# col1, col2, col3 = st.columns([1, 2, 1])
# with col2:
#     st.markdown("<p style='text-align: center;'>Belum punya akun?</p>", unsafe_allow_html=True)
#     if st.button("📝 Daftar di sini", use_container_width=True):
#         st.switch_page("pages/Register.py")

# st.markdown("---")

# ---------- DEMO MODE ----------
with st.expander("ℹ️ Informasi Demo", expanded=False):
    st.markdown("""
    **Untuk keperluan demo/testing:**
    
    Jika database belum dikonfigurasi atau Anda ingin mencoba aplikasi tanpa login,
    Anda dapat menggunakan mode demo dengan mengakses halaman lain secara langsung.
    
    **Catatan:** Fitur database tidak akan berfungsi dalam mode demo.
    """)
