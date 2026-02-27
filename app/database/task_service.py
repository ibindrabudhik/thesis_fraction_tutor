"""Task management service for database operations.

This module handles all task-related database operations including:
- Task creation and retrieval
- Random task selection by difficulty level
- Bulk import from CSV files
"""
from __future__ import annotations

import csv
import random
from typing import Optional, Dict, Any, List

from database.supabase_client import get_supabase_client, SupabaseError


def create_task(
    level: str,
    question: str,
    solution: str,
    knowledge_areas: Dict[str, bool] = None
) -> Dict[str, Any]:
    """
    Create a new task in the database.
    
    Args:
        level: 'Low' or 'High'
        question: Problem statement
        solution: Correct answer/solution
        knowledge_areas: Dict with keys:
            - ordering: bool
            - addition: bool
            - subtraction: bool
            - multiplication: bool
            - division: bool
            
    Returns:
        Dict containing the created task data
        
    Raises:
        SupabaseError: If task creation fails
    """
    client = get_supabase_client()
    
    if knowledge_areas is None:
        knowledge_areas = {
            "ordering": False,
            "addition": False,
            "subtraction": False,
            "multiplication": False,
            "division": False
        }
    
    try:
        data = {
            "level": level,
            "question": question.strip(),
            "solution": solution.strip(),
            "knowledge_area_ordering": knowledge_areas.get("ordering", False),
            "knowledge_area_addition": knowledge_areas.get("addition", False),
            "knowledge_area_subtraction": knowledge_areas.get("subtraction", False),
            "knowledge_area_multiplication": knowledge_areas.get("multiplication", False),
            "knowledge_area_division": knowledge_areas.get("division", False),
        }
        
        response = client.table("tasks").insert(data).execute()
        
        if response.data and len(response.data) > 0:
            return response.data[0]
        else:
            raise SupabaseError("Failed to create task")
            
    except Exception as e:
        raise SupabaseError(f"Error creating task: {e}")


def get_task_by_id(task_id: str) -> Optional[Dict[str, Any]]:
    """
    Retrieve a task by ID.
    
    Args:
        task_id: Task UUID
        
    Returns:
        Task data dict or None if not found
    """
    client = get_supabase_client()
    
    try:
        response = client.table("tasks").select("*").eq("task_id", task_id).execute()
        
        if response.data and len(response.data) > 0:
            return response.data[0]
        return None
        
    except Exception as e:
        print(f"Error fetching task by ID: {e}")
        return None


def get_random_task_by_level(level: str, exclude_task_ids: List[str] = None) -> Optional[Dict[str, Any]]:
    """
    Get a random task by difficulty level.
    
    Args:
        level: 'Low' or 'High'
        exclude_task_ids: List of task IDs to exclude (e.g., recently completed)
        
    Returns:
        Random task dict or None if no tasks found
    """
    client = get_supabase_client()
    
    try:
        query = client.table("tasks").select("*").eq("level", level)
        
        response = query.execute()
        
        if not response.data or len(response.data) == 0:
            return None
        
        # Filter out excluded tasks
        available_tasks = response.data
        if exclude_task_ids:
            available_tasks = [
                task for task in available_tasks
                if task["task_id"] not in exclude_task_ids
            ]
        
        if not available_tasks:
            # If all tasks excluded, return from all tasks
            available_tasks = response.data
        
        return random.choice(available_tasks)
        
    except Exception as e:
        print(f"Error fetching random task: {e}")
        return None


def get_all_tasks(level: Optional[str] = None) -> List[Dict[str, Any]]:
    """
    Retrieve all tasks, optionally filtered by level.
    
    Args:
        level: Optional filter by 'Low' or 'High'
        
    Returns:
        List of task dicts
    """
    client = get_supabase_client()
    
    try:
        query = client.table("tasks").select("*")
        
        if level:
            query = query.eq("level", level)
        
        response = query.execute()
        
        return response.data if response.data else []
        
    except Exception as e:
        print(f"Error fetching all tasks: {e}")
        return []


def bulk_import_tasks(csv_file_path: str, default_level: str = "Low") -> int:
    """
    Import tasks from a CSV file.
    
    Expected CSV columns:
    - question (required)
    - solution (required)
    - level (optional, defaults to default_level)
    - ordering (optional, boolean)
    - addition (optional, boolean)
    - subtraction (optional, boolean)
    - multiplication (optional, boolean)
    - division (optional, boolean)
    
    Args:
        csv_file_path: Path to CSV file
        default_level: Default level if not specified in CSV
        
    Returns:
        Number of tasks successfully imported
        
    Raises:
        SupabaseError: If import fails
    """
    imported_count = 0
    
    try:
        with open(csv_file_path, 'r', encoding='utf-8') as f:
            reader = csv.DictReader(f)
            
            for row in reader:
                question = row.get('question', '').strip()
                solution = row.get('solution', '').strip()
                
                if not question or not solution:
                    print(f"Skipping row with missing question or solution")
                    continue
                
                level = row.get('level', default_level).strip()
                
                knowledge_areas = {
                    "ordering": row.get('ordering', '').lower() in ['true', '1', 'yes'],
                    "addition": row.get('addition', '').lower() in ['true', '1', 'yes'],
                    "subtraction": row.get('subtraction', '').lower() in ['true', '1', 'yes'],
                    "multiplication": row.get('multiplication', '').lower() in ['true', '1', 'yes'],
                    "division": row.get('division', '').lower() in ['true', '1', 'yes'],
                }
                
                try:
                    create_task(level, question, solution, knowledge_areas)
                    imported_count += 1
                except Exception as e:
                    print(f"Error importing task: {e}")
                    continue
        
        return imported_count
        
    except Exception as e:
        raise SupabaseError(f"Error reading CSV file: {e}")


def count_tasks_by_level() -> Dict[str, int]:
    """
    Count tasks grouped by difficulty level.
    
    Returns:
        Dict with 'Low' and 'High' counts
    """
    client = get_supabase_client()
    
    try:
        low_response = client.table("tasks").select("task_id", count="exact").eq("level", "Low").execute()
        high_response = client.table("tasks").select("task_id", count="exact").eq("level", "High").execute()
        
        return {
            "Low": low_response.count if low_response.count else 0,
            "High": high_response.count if high_response.count else 0,
        }
        
    except Exception as e:
        print(f"Error counting tasks: {e}")
        return {"Low": 0, "High": 0}
