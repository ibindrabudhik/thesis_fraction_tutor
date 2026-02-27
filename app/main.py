import streamlit as st
import sys
import os

# Add current directory to path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from sidebar import get_pages_main, render_sidebar_main
from auth.session import is_authenticated

# ---------- CONFIG ----------
st.set_page_config(page_title="Uma Fraction Tutor", page_icon="🤖", layout="wide")

# ---------- SESSION STATE ----------
if "chat_history" not in st.session_state:
    st.session_state.chat_history = []

# ---------- CHECK AUTHENTICATION ----------
# Redirect to login if not authenticated
if not is_authenticated():
    # Show login page as default
    pg = st.navigation([
        st.Page("pages/Login.py", title="Login", icon="🔐"),
        # st.Page("pages/Register.py", title="Register", icon="📝"),
    ])
    pg.run()
else:
    # ---------- NAVIGATION ----------
    # Create and run the navigation for authenticated users
    pages = get_pages_main()
    pg = st.navigation(pages, position="sidebar")
    
    # ---------- RENDER SIDEBAR ----------
    render_sidebar_main("main")
    
    # ---------- RUN THE SELECTED PAGE ----------
    pg.run()
