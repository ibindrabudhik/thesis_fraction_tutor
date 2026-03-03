"""Student log service for tracking learning sessions and progress.

This module handles:
- Session creation and management
- Logging student interactions
- Tracking completion status
- Retrieving student history and statistics
"""
from __future__ import annotations

import uuid
import re
from datetime import datetime
from typing import Optional, Dict, Any, List

from database.supabase_client import get_supabase_client, SupabaseError


def create_session(student_id: str, task_id: str) -> str:
    """
    Create a new learning session.
    
    Args:
        student_id: Student UUID
        task_id: Task UUID
        
    Returns:
        Session UUID (generated)
        
    Raises:
        SupabaseError: If session creation fails
    """
    session_id = str(uuid.uuid4())
    
    # Session will be created when first interaction is logged
    # This just returns a new session ID
    return session_id


def log_student_interaction(
    session_id: str,
    student_id: str,
    task_id: str,
    task_level: str,
    question: str,
    student_answer: str,
    is_correct: bool,
    feedback_given: str,
    feedback_type: str,
    error_count: int,
    is_final: bool = False,
    achievement_level_assessed: Optional[str] = None,
    timestamp: Optional[datetime] = None,
    evaluation_result: Optional[Dict[str, Any]] = None,
    cheat_count: int = 0
) -> bool:
    """
    Log a student interaction (answer submission and feedback).
    
    Args:
        session_id: Session UUID
        student_id: Student UUID
        task_id: Task UUID
        task_level: 'Low' or 'High'
        question: Problem text
        student_answer: Student's submitted answer
        is_correct: Whether answer was correct
        feedback_given: Feedback text provided
        feedback_type: Type of feedback given
        error_count: Current error count for this session
        is_final: Whether this is the final interaction (correct or 3 errors)
        achievement_level_assessed: LLM's assessment of student level
        timestamp: Optional client timestamp (uses client time if provided, server time otherwise)
        evaluation_result: Full evaluation dict from LLM evaluator (is_correct, confidence, reasoning, error types)
        cheat_count: Number of tab/window switches detected during session
        
    Returns:
        True if logging successful, False otherwise
    """
    client = get_supabase_client()
    
    try:
        data = {
            "log_id": str(uuid.uuid4()),
            "session_id": session_id,
            "student_id": student_id,
            "task_id": task_id,
            "task_level": task_level,
            "question": question,
            "student_answer": student_answer,
            "is_correct_final": is_correct if is_final else False,
            "error_count": error_count,
            "feedback_given": feedback_given,
            "feedback_type": feedback_type,
            "achievement_level_assessed": achievement_level_assessed,
            "cheat_count": cheat_count,
        }
        
        # Add timestamp if provided (client time)
        if timestamp:
            data["timestamp"] = timestamp.isoformat()
        
        # Add evaluation result if provided (for all attempts)
        if evaluation_result:
            data["evaluation_result"] = evaluation_result
        
        response = client.table("student_logs").insert(data).execute()
        
        return response.data and len(response.data) > 0
        
    except Exception as e:
        print(f"Error logging student interaction: {e}")
        return False


def update_session_completion(
    session_id: str,
    is_correct_final: bool,
    final_feedback: str,
    achievement_assessed: str
) -> bool:
    """
    Mark a session as complete and update final assessment.
    
    Args:
        session_id: Session UUID
        is_correct_final: Whether student solved correctly
        final_feedback: Final feedback provided
        achievement_assessed: 'Low' or 'High'
        
    Returns:
        True if update successful, False otherwise
    """
    client = get_supabase_client()
    
    try:
        # Update the most recent log entry for this session
        response = client.table("student_logs").update({
            "is_correct_final": is_correct_final,
            "feedback_given": final_feedback,
            "achievement_level_assessed": achievement_assessed,
        }).eq("session_id", session_id).order("timestamp", desc=True).limit(1).execute()
        
        return response.data and len(response.data) > 0
        
    except Exception as e:
        print(f"Error updating session completion: {e}")
        return False


def get_student_history(student_id: str, limit: int = 50) -> List[Dict[str, Any]]:
    """
    Get all learning sessions for a student.
    
    Returns one record per session (the latest log entry for each session).
    
    Args:
        student_id: Student UUID
        limit: Maximum number of sessions to return
        
    Returns:
        List of session dicts, ordered by most recent first
    """
    client = get_supabase_client()
    
    try:
        # Get all logs for this student
        response = client.table("student_logs").select("*").eq(
            "student_id", student_id
        ).order("timestamp", desc=True).execute()
        
        if not response.data:
            return []
        
        # Group by session_id and take the latest entry for each
        sessions = {}
        for log in response.data:
            session_id = log["session_id"]
            if session_id not in sessions:
                sessions[session_id] = log
        
        # Convert to list and sort by timestamp
        session_list = list(sessions.values())
        session_list.sort(key=lambda x: x["timestamp"], reverse=True)
        
        return session_list[:limit]
        
    except Exception as e:
        print(f"Error fetching student history: {e}")
        return []


def get_session_details(session_id: str) -> List[Dict[str, Any]]:
    """
    Get all log entries for a specific session (detailed interaction history).
    
    Args:
        session_id: Session UUID
        
    Returns:
        List of log entries ordered by timestamp
    """
    client = get_supabase_client()
    
    try:
        response = client.table("student_logs").select("*").eq(
            "session_id", session_id
        ).order("timestamp", desc=False).execute()
        
        return response.data if response.data else []
        
    except Exception as e:
        print(f"Error fetching session details: {e}")
        return []


def get_student_statistics(student_id: str) -> Dict[str, Any]:
    """
    Calculate statistics for a student.
    
    Args:
        student_id: Student UUID
        
    Returns:
        Dict with keys:
        - total_sessions: Total number of unique sessions
        - completed_correctly: Number of sessions completed correctly
        - success_rate: Percentage of correct completions
        - total_attempts: Total number of answer attempts
        - recent_achievement_level: Most recent achievement level assessed
    """
    client = get_supabase_client()
    
    try:
        # Get all logs for this student
        response = client.table("student_logs").select("*").eq(
            "student_id", student_id
        ).execute()
        
        if not response.data:
            return {
                "total_sessions": 0,
                "completed_correctly": 0,
                "success_rate": 0.0,
                "total_attempts": 0,
                "recent_achievement_level": "Low",
            }
        
        logs = response.data
        
        # Group by session
        sessions = {}
        for log in logs:
            session_id = log["session_id"]
            if session_id not in sessions:
                sessions[session_id] = []
            sessions[session_id].append(log)
        
        total_sessions = len(sessions)
        completed_correctly = 0
        total_attempts = len(logs)
        recent_achievement = "Low"
        
        # Analyze each session
        for session_id, session_logs in sessions.items():
            # Sort by timestamp to get the latest
            session_logs.sort(key=lambda x: x["timestamp"], reverse=True)
            latest = session_logs[0]
            
            if latest.get("is_correct_final"):
                completed_correctly += 1
            
            if latest.get("achievement_level_assessed"):
                recent_achievement = latest["achievement_level_assessed"]
        
        success_rate = (completed_correctly / total_sessions * 100) if total_sessions > 0 else 0.0
        
        return {
            "total_sessions": total_sessions,
            "completed_correctly": completed_correctly,
            "success_rate": round(success_rate, 1),
            "total_attempts": total_attempts,
            "recent_achievement_level": recent_achievement,
        }
        
    except Exception as e:
        print(f"Error calculating statistics: {e}")
        return {
            "total_sessions": 0,
            "completed_correctly": 0,
            "success_rate": 0.0,
            "total_attempts": 0,
            "recent_achievement_level": "Low",
        }


def get_recent_sessions(student_id: str, limit: int = 10) -> List[Dict[str, Any]]:
    """
    Get recent problem sessions (summary view).
    
    Args:
        student_id: Student UUID
        limit: Number of recent sessions
        
    Returns:
        List of session summaries
    """
    return get_student_history(student_id, limit=limit)


def get_recent_session_feedback(session_id: str, limit: int = 2) -> List[Dict[str, Any]]:
    """
    Get the most recent feedback entries for a session.
    
    Used for providing context to LLM to avoid repetitive feedback.
    
    Args:
        session_id: Session UUID
        limit: Number of recent feedbacks to retrieve (default 2)
        
    Returns:
        List of feedback dicts with keys: feedback_given, feedback_type, student_answer, error_count
        Ordered from most recent to oldest.
    """
    client = get_supabase_client()
    
    try:
        response = client.table("student_logs").select(
            "feedback_given, feedback_type, student_answer, error_count, evaluation_result"
        ).eq(
            "session_id", session_id
        ).order("timestamp", desc=True).limit(limit).execute()
        
        if not response.data:
            return []
        
        return [
            {
                "feedback_given": log.get("feedback_given", ""),
                "feedback_type": log.get("feedback_type", ""),
                "student_answer": log.get("student_answer", ""),
                "error_count": log.get("error_count", 0),
                "evaluation_result": log.get("evaluation_result", {}),
            }
            for log in response.data
        ]
        
    except Exception as e:
        print(f"Error fetching recent session feedback: {e}")
        return []


def get_session_leaderboard(min_sessions: int = 1) -> List[Dict[str, Any]]:
    """
    Build leaderboard ranking students by number of unique sessions.

    Only students with username format YPSSTUDENT_XXX are included,
    where XXX is exactly 3 digits.

    Args:
        min_sessions: Minimum number of unique sessions to include

    Returns:
        List of leaderboard rows sorted by total_sessions desc, total_logs desc.
        Each row contains: rank, student_id, username, name, total_sessions,
        total_logs, first_activity, last_activity.
    """
    client = get_supabase_client()

    try:
        # Pull logs needed for aggregation
        logs_response = client.table("student_logs").select(
            "student_id, session_id, timestamp"
        ).execute()

        if not logs_response.data:
            return []

        # Pull student identity map
        students_response = client.table("students").select(
            "student_id, username, name"
        ).execute()

        student_map: Dict[str, Dict[str, Any]] = {}
        for student in students_response.data or []:
            student_map[student.get("student_id")] = student

        # Keep only usernames exactly matching YPSSTUDENT_XXX
        username_pattern = re.compile(r"^YPSSTUDENT_\d{3}$", re.IGNORECASE)

        aggregates: Dict[str, Dict[str, Any]] = {}
        for row in logs_response.data:
            student_id = row.get("student_id")
            if not student_id:
                continue

            student = student_map.get(student_id)
            username = (student or {}).get("username", "")

            if not username_pattern.match(username or ""):
                continue

            if student_id not in aggregates:
                aggregates[student_id] = {
                    "student_id": student_id,
                    "username": username,
                    "name": (student or {}).get("name", "-"),
                    "sessions": set(),
                    "total_logs": 0,
                    "first_activity": row.get("timestamp"),
                    "last_activity": row.get("timestamp"),
                }

            agg = aggregates[student_id]
            session_id = row.get("session_id")
            if session_id:
                agg["sessions"].add(session_id)
            agg["total_logs"] += 1

            ts = row.get("timestamp")
            if ts:
                if not agg["first_activity"] or ts < agg["first_activity"]:
                    agg["first_activity"] = ts
                if not agg["last_activity"] or ts > agg["last_activity"]:
                    agg["last_activity"] = ts

        # Build final sorted rows
        rows: List[Dict[str, Any]] = []
        for agg in aggregates.values():
            total_sessions = len(agg["sessions"])
            if total_sessions < min_sessions:
                continue

            rows.append({
                "student_id": agg["student_id"],
                "username": agg["username"],
                "name": agg["name"],
                "total_sessions": total_sessions,
                "total_logs": agg["total_logs"],
                "first_activity": agg["first_activity"],
                "last_activity": agg["last_activity"],
            })

        rows.sort(
            key=lambda r: (r["total_sessions"], r["total_logs"], r["last_activity"] or ""),
            reverse=True,
        )

        for idx, row in enumerate(rows, start=1):
            row["rank"] = idx

        return rows

    except Exception as e:
        print(f"Error building session leaderboard: {e}")
        return []
