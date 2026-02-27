"""Session management and authentication helpers.

This module provides functions for:
- Managing user sessions in Streamlit
- Checking authentication status
- User logout
- Getting current user information
"""
from __future__ import annotations

from typing import Optional, Dict, Any
import streamlit as st


def is_authenticated() -> bool:
    """
    Check if a user is currently authenticated.
    
    Returns:
        True if user is logged in, False otherwise
    """
    return "student_id" in st.session_state and st.session_state.student_id is not None


def get_current_user() -> Optional[Dict[str, Any]]:
    """
    Get the currently logged-in user's information.
    
    Returns:
        Dict with user info or None if not authenticated
    """
    if not is_authenticated():
        return None
    
    return {
        "student_id": st.session_state.get("student_id"),
        "name": st.session_state.get("student_name"),
        "username": st.session_state.get("student_username"),
    }


def login_user(student_data: Dict[str, Any]) -> None:
    """
    Log in a user by storing their information in session state.
    
    Args:
        student_data: Dict containing student_id, name, username
    """
    st.session_state.student_id = student_data["student_id"]
    st.session_state.student_name = student_data.get("name", "")
    st.session_state.student_username = student_data.get("username", "")
    st.session_state.authenticated = True


def logout_user() -> None:
    """
    Log out the current user by clearing session state.
    """
    # Clear authentication-related session state
    keys_to_clear = [
        "student_id",
        "student_name",
        "student_username",
        "authenticated",
        "chat_history",
        "error_count",
        "current_session_id",
        "current_task",
        "student_profile",
    ]
    
    for key in keys_to_clear:
        if key in st.session_state:
            del st.session_state[key]


def require_authentication() -> bool:
    """
    Require authentication for a page. Redirect to login if not authenticated.
    
    Returns:
        True if authenticated, False otherwise (will show warning)
    """
    if not is_authenticated():
        st.warning("⚠️ Silakan login terlebih dahulu untuk mengakses halaman ini.")
        if st.button("🔐 Login di sini", type="primary"):
            st.switch_page("pages/Login.py")
        st.stop()
        return False
    return True


def get_student_id() -> Optional[str]:
    """
    Get the current student's ID.
    
    Returns:
        Student ID string or None if not authenticated
    """
    return st.session_state.get("student_id")


def get_student_name() -> str:
    """
    Get the current student's name.
    
    Returns:
        Student name or "Guest" if not authenticated
    """
    return st.session_state.get("student_name", "Guest")
