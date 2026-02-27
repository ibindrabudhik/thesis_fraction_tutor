"""Student management service for database operations.

This module handles all student-related database operations including:
- Student registration and authentication
- Profile retrieval and updates
- Achievement level tracking
- Prior knowledge management
"""
from __future__ import annotations

import hashlib
import uuid
from typing import Optional, Dict, Any

from database.supabase_client import get_supabase_client, SupabaseError


def _hash_password(password: str) -> str:
    """Hash password using SHA-256."""
    return hashlib.sha256(password.encode()).hexdigest()


def create_student(username: str, name: str, password: str, email: str = None) -> Dict[str, Any]:
    """
    Register a new student in the database.
    
    Args:
        username: Student username (must be unique, format: YPSSTUDENT_X)
        name: Student full name
        password: Plain text password (will be hashed)
        email: Optional email address
        
    Returns:
        Dict containing the created student data
        
    Raises:
        SupabaseError: If registration fails (e.g., duplicate username)
    """
    client = get_supabase_client()
    
    try:
        data = {
            "username": username.upper().strip(),
            "name": name.strip(),
            "password_hash": _hash_password(password),
            "email": email.lower().strip() if email else None,
            "achievement_level": "Low",  # Default starting level
            "prior_knowledge_ordering": "Low",
            "prior_knowledge_addition": "Low",
            "prior_knowledge_subtraction": "Low",
            "prior_knowledge_multiplication": "Low",
            "prior_knowledge_division": "Low",
        }
        
        response = client.table("students").insert(data).execute()
        
        if response.data and len(response.data) > 0:
            return response.data[0]
        else:
            raise SupabaseError("Failed to create student")
            
    except Exception as e:
        raise SupabaseError(f"Error creating student: {e}")


def get_student_by_username(username: str) -> Optional[Dict[str, Any]]:
    """
    Retrieve a student by username.
    
    Args:
        username: Student username (format: YPSSTUDENT_X)
        
    Returns:
        Student data dict or None if not found
    """
    client = get_supabase_client()
    
    try:
        response = client.table("students").select("*").eq(
            "username", username.upper().strip()
        ).execute()
        
        if response.data and len(response.data) > 0:
            return response.data[0]
        return None
        
    except Exception as e:
        print(f"Error fetching student by username: {e}")
        return None


def get_student_by_id(student_id: str) -> Optional[Dict[str, Any]]:
    """
    Retrieve a student by ID.
    
    Args:
        student_id: Student UUID
        
    Returns:
        Student data dict or None if not found
    """
    client = get_supabase_client()
    
    try:
        response = client.table("students").select("*").eq(
            "student_id", student_id
        ).execute()
        
        if response.data and len(response.data) > 0:
            return response.data[0]
        return None
        
    except Exception as e:
        print(f"Error fetching student by ID: {e}")
        return None


def authenticate_student(username: str, password: str) -> Optional[Dict[str, Any]]:
    """
    Authenticate a student with username and password.
    
    Args:
        username: Student username (format: YPSSTUDENT_X)
        password: Plain text password
        
    Returns:
        Student data dict (without password_hash) if authentication successful,
        None otherwise
    """
    student = get_student_by_username(username)
    
    if not student:
        return None
    
    password_hash = _hash_password(password)
    
    if student.get("password_hash") == password_hash:
        # Remove password hash from returned data
        student_data = {k: v for k, v in student.items() if k != "password_hash"}
        return student_data
    
    return None


def update_student_achievement_level(student_id: str, level: str) -> bool:
    """
    Update student's achievement level.
    
    Args:
        student_id: Student UUID
        level: 'Low' or 'High'
        
    Returns:
        True if update successful, False otherwise
    """
    client = get_supabase_client()
    
    try:
        response = client.table("students").update({
            "achievement_level": level
        }).eq("student_id", student_id).execute()
        
        return response.data and len(response.data) > 0
        
    except Exception as e:
        print(f"Error updating achievement level: {e}")
        return False


def update_prior_knowledge(
    student_id: str,
    ordering: Optional[str] = None,
    addition: Optional[str] = None,
    subtraction: Optional[str] = None,
    multiplication: Optional[str] = None,
    division: Optional[str] = None
) -> bool:
    """
    Update student's prior knowledge levels (Low/High).
    
    Args:
        student_id: Student UUID
        ordering: Level for ordering fractions ('Low' or 'High')
        addition: Level for fraction addition ('Low' or 'High')
        subtraction: Level for fraction subtraction ('Low' or 'High')
        multiplication: Level for fraction multiplication ('Low' or 'High')
        division: Level for fraction division ('Low' or 'High')
        
    Returns:
        True if update successful, False otherwise
    """
    client = get_supabase_client()
    
    try:
        update_data = {}
        if ordering is not None:
            update_data["prior_knowledge_ordering"] = ordering
        if addition is not None:
            update_data["prior_knowledge_addition"] = addition
        if subtraction is not None:
            update_data["prior_knowledge_subtraction"] = subtraction
        if multiplication is not None:
            update_data["prior_knowledge_multiplication"] = multiplication
        if division is not None:
            update_data["prior_knowledge_division"] = division
        
        if not update_data:
            return False
        
        response = client.table("students").update(update_data).eq(
            "student_id", student_id
        ).execute()
        
        return response.data and len(response.data) > 0
        
    except Exception as e:
        print(f"Error updating prior knowledge: {e}")
        return False


def calculate_overall_spk(
    student: Dict[str, Any],
    active_knowledge_areas: Optional[list] = None
) -> str:
    """
    Calculate overall SPK dynamically based on active knowledge areas.
    
    Args:
        student: Student data dict
        active_knowledge_areas: List of currently accessible skills
                               (e.g., ['ordering', 'addition'])
                               If None, uses all 5 fraction skills
    
    Returns:
        'High' if majority of active areas are High, else 'Low'
    """
    # Default to all fraction skills if not specified
    if active_knowledge_areas is None:
        active_knowledge_areas = ['ordering', 'addition', 'subtraction', 'multiplication', 'division']
    
    # Get levels for active areas only
    pk_levels = []
    for area in active_knowledge_areas:
        column_name = f"prior_knowledge_{area}"
        pk_levels.append(student.get(column_name, "Low"))
    
    if not pk_levels:
        return "Low"
    
    # Calculate if majority are High
    high_count = sum(1 for pk in pk_levels if pk == "High")
    return "High" if high_count > len(pk_levels) / 2 else "Low"


def get_student_profile(
    student_id: str,
    active_knowledge_areas: Optional[list] = None
) -> Dict[str, Any]:
    """
    Get student profile formatted for use in the application.
    
    Args:
        student_id: Student UUID
        active_knowledge_areas: List of currently accessible skills for dynamic SPK calculation
        
    Returns:
        Dict with keys: student_id, name, spk, sal
        
    Raises:
        SupabaseError: If student not found
    """
    student = get_student_by_id(student_id)
    
    if not student:
        raise SupabaseError(f"Student not found: {student_id}")
    
    # Calculate SPK dynamically based on active knowledge areas
    spk = calculate_overall_spk(student, active_knowledge_areas)
    
    return {
        "student_id": student["student_id"],
        "name": student["name"],
        "username": student["username"],
        "email": student.get("email"),
        "spk": spk,  # Student Prior Knowledge
        "sal": student.get("achievement_level", "Low"),  # Student Achievement Level
        "tof": "Immediate",  # Time of Feedback (default)
        # Include individual skill levels for reference
        "prior_knowledge": {
            "ordering": student.get("prior_knowledge_ordering", "Low"),
            "addition": student.get("prior_knowledge_addition", "Low"),
            "subtraction": student.get("prior_knowledge_subtraction", "Low"),
            "multiplication": student.get("prior_knowledge_multiplication", "Low"),
            "division": student.get("prior_knowledge_division", "Low"),
        }
    }
