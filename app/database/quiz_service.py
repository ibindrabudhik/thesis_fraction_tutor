"""Quiz service for managing quiz submissions and results.

This module handles:
- Logging quiz submissions
- Retrieving quiz results
- Calculating quiz statistics
"""
from __future__ import annotations

import uuid
from typing import Optional, Dict, Any, List
from datetime import datetime

from database.supabase_client import get_supabase_client, SupabaseError


def log_quiz_submission(
    student_id: str,
    quiz_section: str,
    question_id: str,
    question_text: str,
    student_answer: str,
    correct_answer: str,
    is_correct: bool,
    knowledge_areas: Optional[List[str]] = None
) -> bool:
    """
    Log a single quiz question submission.
    
    Args:
        student_id: Student UUID
        quiz_section: Quiz section name (e.g., 'pre_test', 'ordering_fractions')
        question_id: Question identifier (e.g., 'pre_1', 'ordering_1')
        question_text: The question text
        student_answer: Student's selected answer (full text)
        correct_answer: Correct answer letter (e.g., 'A', 'B', 'C', 'D')
        is_correct: Whether the answer was correct
        knowledge_areas: List of knowledge areas tested (e.g., ['ordering', 'addition'])
        
    Returns:
        True if logging successful, False otherwise
    """
    client = get_supabase_client()
    
    try:
        data = {
            "result_id": str(uuid.uuid4()),
            "student_id": student_id,
            "quiz_section": quiz_section,
            "question_id": question_id,
            "question_text": question_text,
            "student_answer": student_answer,
            "correct_answer": correct_answer,
            "is_correct": is_correct,
            "knowledge_areas": knowledge_areas or [],
            "timestamp": datetime.now().isoformat()
        }
        print(f"[DEBUG] Attempting to insert quiz result: {data}")  # Debug log
        response = client.table("quiz_results").insert(data).execute()
        print(f"[DEBUG] Insert response: {response}")  # Debug log
        if not response.data:
            print(f"[ERROR] No data returned from insert")
            return False
        return response.data and len(response.data) > 0
        
    except Exception as e:
        print(f"Error logging quiz submission: {e}")
        return False


def get_quiz_results(
    student_id: str,
    quiz_section: Optional[str] = None
) -> List[Dict[str, Any]]:
    """
    Get quiz results for a student.
    
    Args:
        student_id: Student UUID
        quiz_section: Optional specific quiz section to filter by
        
    Returns:
        List of quiz result records
    """
    client = get_supabase_client()
    
    try:
        query = client.table("quiz_results").select("*").eq("student_id", student_id)
        
        if quiz_section:
            query = query.eq("quiz_section", quiz_section)
        
        response = query.order("timestamp", desc=True).execute()
        
        return response.data or []
        
    except Exception as e:
        print(f"Error getting quiz results: {e}")
        return []


def calculate_quiz_score(student_id: str, quiz_section: str) -> Dict[str, Any]:
    """
    Calculate score for a specific quiz section.
    
    Args:
        student_id: Student UUID
        quiz_section: Quiz section name
        
    Returns:
        Dict with score, total, and percentage
    """
    results = get_quiz_results(student_id, quiz_section)
    
    if not results:
        return {"score": 0, "total": 0, "percentage": 0.0}
    
    # Group by question_id to get only the latest attempt for each question
    latest_attempts = {}
    for result in results:
        q_id = result["question_id"]
        if q_id not in latest_attempts:
            latest_attempts[q_id] = result
    
    total = len(latest_attempts)
    correct = sum(1 for r in latest_attempts.values() if r["is_correct"])
    percentage = (correct / total * 100) if total > 0 else 0.0
    
    return {
        "score": correct,
        "total": total,
        "percentage": percentage
    }


def get_all_quiz_scores(student_id: str) -> Dict[str, Dict[str, Any]]:
    """
    Get scores for all quiz sections for a student.
    
    Args:
        student_id: Student UUID
        
    Returns:
        Dict mapping section names to score dictionaries
    """
    results = get_quiz_results(student_id)
    
    # Group by section
    sections = {}
    for result in results:
        section = result["quiz_section"]
        if section not in sections:
            sections[section] = []
        sections[section].append(result)
    
    # Calculate score for each section
    scores = {}
    for section, section_results in sections.items():
        # Get unique questions (latest attempt only)
        latest_attempts = {}
        for result in section_results:
            q_id = result["question_id"]
            if q_id not in latest_attempts or result["timestamp"] > latest_attempts[q_id]["timestamp"]:
                latest_attempts[q_id] = result
        
        total = len(latest_attempts)
        correct = sum(1 for r in latest_attempts.values() if r["is_correct"])
        percentage = (correct / total * 100) if total > 0 else 0.0
        
        scores[section] = {
            "score": correct,
            "total": total,
            "percentage": percentage
        }
    
    return scores


def has_completed_quiz_section(student_id: str, quiz_section: str) -> bool:
    """
    Check if a student has completed a specific quiz section.
    
    Args:
        student_id: Student UUID
        quiz_section: Quiz section name
        
    Returns:
        True if the student has submitted answers for this section
    """
    results = get_quiz_results(student_id, quiz_section)
    return len(results) > 0
