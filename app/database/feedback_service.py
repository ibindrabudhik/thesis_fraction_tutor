"""Feedback service for storing usability and user experience forms."""
from __future__ import annotations

import uuid
from datetime import datetime, timezone, timedelta
from typing import Dict, Any, Optional

from database.supabase_client import get_supabase_client

# GMT+8 timezone (WIB - Waktu Indonesia Barat)
GMT8 = timezone(timedelta(hours=8))


def submit_student_feedback(
    student_id: str,
    likert_answers: Dict[str, Any],
    open_answers: Optional[Dict[str, Any]] = None,
) -> bool:
    """Submit one feedback form row to database."""
    client = get_supabase_client()

    try:
        payload = {
            "feedback_id": str(uuid.uuid4()),
            "student_id": student_id,
            "likert_answers": likert_answers,
            "open_answers": open_answers or {},
            "submitted_at": datetime.now(GMT8).isoformat(),
        }
        response = client.table("student_feedback").insert(payload).execute()
        return bool(response.data and len(response.data) > 0)
    except Exception as e:
        print(f"Error submitting feedback: {e}")
        return False
