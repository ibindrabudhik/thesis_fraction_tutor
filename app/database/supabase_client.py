"""Supabase client initialization and connection management.

This module provides a centralized Supabase client for database operations.
The client is cached to avoid creating multiple connections.
"""
from __future__ import annotations

import os
from functools import lru_cache
from typing import Optional

# Load environment variables from .env file if running outside Streamlit
try:
    from dotenv import load_dotenv
    load_dotenv()
except ImportError:
    pass  # dotenv not installed, will rely on system env vars or Streamlit secrets

try:
    import streamlit as st
    _HAS_STREAMLIT = True
except ImportError:
    _HAS_STREAMLIT = False

try:
    from supabase import create_client, Client
    _HAS_SUPABASE = True
except ImportError:
    _HAS_SUPABASE = False
    Client = None


class SupabaseError(Exception):
    """Raised when Supabase operations fail."""
    pass


class MissingCredentialsError(SupabaseError):
    """Raised when Supabase credentials are missing."""
    pass


def _get_supabase_url() -> str:
    """Retrieve Supabase URL from environment or Streamlit secrets."""
    url = os.getenv("SUPABASE_URL")
    if not url and _HAS_STREAMLIT:
        try:
            url = st.secrets.get("SUPABASE_URL")
        except Exception:
            pass
    
    if not url:
        raise MissingCredentialsError(
            "SUPABASE_URL is missing. Set it via environment variable or Streamlit secrets."
        )
    return url


def _get_supabase_key() -> str:
    """Retrieve Supabase anon key from environment or Streamlit secrets."""
    key = os.getenv("SUPABASE_KEY")
    if not key and _HAS_STREAMLIT:
        try:
            key = st.secrets.get("SUPABASE_KEY")
        except Exception:
            pass
    
    if not key:
        raise MissingCredentialsError(
            "SUPABASE_KEY is missing. Set it via environment variable or Streamlit secrets."
        )
    return key


@lru_cache(maxsize=1)
def get_supabase_client() -> Client:
    """
    Get a cached Supabase client instance.
    
    Returns:
        Supabase Client instance
        
    Raises:
        MissingCredentialsError: If credentials are not configured
        SupabaseError: If client creation fails
    """
    if not _HAS_SUPABASE:
        raise SupabaseError(
            "supabase-py is not installed. Install it with: pip install supabase"
        )
    
    try:
        url = _get_supabase_url()
        key = _get_supabase_key()
        client = create_client(url, key)
        return client
    except MissingCredentialsError:
        raise
    except Exception as e:
        raise SupabaseError(f"Failed to create Supabase client: {e}")


def test_connection() -> bool:
    """
    Test the Supabase connection.
    
    Returns:
        True if connection is successful, False otherwise
    """
    try:
        client = get_supabase_client()
        # Try a simple query to test connection
        client.table("students").select("student_id").limit(1).execute()
        return True
    except Exception as e:
        print(f"Connection test failed: {e}")
        return False
