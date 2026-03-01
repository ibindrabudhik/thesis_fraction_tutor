"""Chat message service for persisting conversation history.

This module handles:
- Saving individual chat messages
- Retrieving complete chat history for a session
- Storing RAG contexts as JSON
"""
from __future__ import annotations

import json
import uuid
from datetime import datetime
from typing import Optional, Dict, Any, List

import numpy as np

from database.supabase_client import get_supabase_client, SupabaseError


class _SafeEncoder(json.JSONEncoder):
    """JSON encoder that handles numpy scalars and arrays."""

    def default(self, obj: Any) -> Any:
        if isinstance(obj, (np.integer,)):
            return int(obj)
        if isinstance(obj, (np.floating,)):
            return float(obj)
        if isinstance(obj, np.ndarray):
            return obj.tolist()
        return super().default(obj)


def save_message(
    session_id: str,
    student_id: str,
    role: str,
    content: str,
    contexts: Optional[List[Dict[str, Any]]] = None,
    timestamp: Optional[datetime] = None
) -> bool:
    """
    Save a chat message to the database.
    
    Args:
        session_id: Session UUID
        student_id: Student UUID
        role: 'user' or 'assistant'
        content: Message text content
        contexts: Optional list of RAG context objects
        timestamp: Optional client timestamp (uses client time if provided, server time otherwise)
        
    Returns:
        True if save successful, False otherwise
    """
    client = get_supabase_client()
    
    try:
        data = {
            "message_id": str(uuid.uuid4()),
            "session_id": session_id,
            "student_id": student_id,
            "role": role,
            "content": content,
            "contexts": json.dumps(contexts, cls=_SafeEncoder) if contexts else None,
        }
        
        # Add timestamp if provided (client time)
        if timestamp:
            data["timestamp"] = timestamp.isoformat()
        
        response = client.table("chat_messages").insert(data).execute()
        
        return response.data and len(response.data) > 0
        
    except Exception as e:
        print(f"Error saving chat message: {e}")
        return False


def get_chat_history(session_id: str) -> List[Dict[str, Any]]:
    """
    Retrieve all chat messages for a session.
    
    Args:
        session_id: Session UUID
        
    Returns:
        List of message dicts ordered by timestamp (oldest first)
    """
    client = get_supabase_client()
    
    try:
        response = client.table("chat_messages").select("*").eq(
            "session_id", session_id
        ).order("timestamp", desc=False).execute()
        
        if not response.data:
            return []
        
        # Parse contexts from JSON
        messages = []
        for msg in response.data:
            message = dict(msg)
            if message.get("contexts"):
                try:
                    message["contexts"] = json.loads(message["contexts"])
                except:
                    message["contexts"] = []
            else:
                message["contexts"] = []
            messages.append(message)
        
        return messages
        
    except Exception as e:
        print(f"Error retrieving chat history: {e}")
        return []


def get_recent_sessions_with_preview(student_id: str, limit: int = 10) -> List[Dict[str, Any]]:
    """
    Get recent sessions with first message preview.
    
    Args:
        student_id: Student UUID
        limit: Number of sessions to return
        
    Returns:
        List of dicts with keys: session_id, first_message, timestamp, message_count
    """
    client = get_supabase_client()
    
    try:
        # Get all messages for this student
        response = client.table("chat_messages").select("*").eq(
            "student_id", student_id
        ).order("timestamp", desc=True).execute()
        
        if not response.data:
            return []
        
        # Group by session and get first message
        sessions = {}
        for msg in response.data:
            session_id = msg["session_id"]
            if session_id not in sessions:
                sessions[session_id] = {
                    "session_id": session_id,
                    "first_message": msg["content"][:100] + "..." if len(msg["content"]) > 100 else msg["content"],
                    "timestamp": msg["timestamp"],
                    "message_count": 1,
                }
            else:
                sessions[session_id]["message_count"] += 1
                # Update if this message is older (first in session)
                if msg["timestamp"] < sessions[session_id]["timestamp"]:
                    sessions[session_id]["first_message"] = msg["content"][:100] + "..." if len(msg["content"]) > 100 else msg["content"]
                    sessions[session_id]["timestamp"] = msg["timestamp"]
        
        # Convert to list and sort by timestamp
        session_list = list(sessions.values())
        session_list.sort(key=lambda x: x["timestamp"], reverse=True)
        
        return session_list[:limit]
        
    except Exception as e:
        print(f"Error fetching recent sessions: {e}")
        return []


def delete_session_messages(session_id: str) -> bool:
    """
    Delete all messages for a session (cleanup utility).
    
    Args:
        session_id: Session UUID
        
    Returns:
        True if deletion successful, False otherwise
    """
    client = get_supabase_client()
    
    try:
        response = client.table("chat_messages").delete().eq(
            "session_id", session_id
        ).execute()
        
        return True
        
    except Exception as e:
        print(f"Error deleting session messages: {e}")
        return False
