"""Script to seed test data into the database.

This script creates:
- Test student accounts
- Sample tasks at different levels
- Sample learning sessions

Usage:
    python seed_test_data.py
"""
import sys
import os
from dotenv import load_dotenv

# Load environment variables from .env file (if it exists)
# This looks for .env in the project root
env_path = os.path.join(os.path.dirname(__file__), '..', '..', '.env')
load_dotenv(env_path)

# Add parent directory to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

from database.student_service import create_student, get_student_by_username
from database.task_service import create_task, count_tasks_by_level
from database.log_service import create_session, log_student_interaction


def create_test_students():
    """Create test student accounts."""
    print("👥 Creating test students...")
    
    test_students = [
        {"username": "YPSSTUDENT_1", "name": "Andi Pratama", "password": "test123", "email": "andi@test.com"},
        {"username": "YPSSTUDENT_2", "name": "Budi Santoso", "password": "test123", "email": "budi@test.com"},
        {"username": "YPSSTUDENT_3", "name": "Citra Dewi", "password": "test123", "email": "citra@test.com"},
    ]
    
    created_students = []
    
    for student_data in test_students:
        try:
            # Check if already exists
            existing = get_student_by_username(student_data["username"])
            if existing:
                print(f"  ℹ️  {student_data['name']} already exists")
                created_students.append(existing)
            else:
                student = create_student(**student_data)
                print(f"  ✅ Created: {student_data['name']}")
                created_students.append(student)
        except Exception as e:
            print(f"  ❌ Error creating {student_data['name']}: {e}")
    
    return created_students


def create_sample_tasks():
    """Create sample algebra tasks."""
    print("\n📝 Creating sample tasks...")
    
    sample_tasks = [
        {
            "level": "Low",
            "question": "Sederhanakan: 2x + 3x",
            "solution": "5x",
            "knowledge_areas": {"menyederhanakan": True}
        },
        {
            "level": "Low",
            "question": "Jika x + 5 = 12, maka x = ?",
            "solution": "x = 7",
            "knowledge_areas": {"sifat_operasi": True}
        },
        {
            "level": "Low",
            "question": "Hitung: 3(x + 2) jika x = 4",
            "solution": "18",
            "knowledge_areas": {"menyederhanakan": True, "sifat_operasi": True}
        },
        {
            "level": "High",
            "question": "Sederhanakan: 2(3x - 4) + 5(x + 1)",
            "solution": "11x - 3",
            "knowledge_areas": {"menyederhanakan": True, "sifat_operasi": True}
        },
        {
            "level": "High",
            "question": "Jika 2x - 3 = 5x + 6, maka x = ?",
            "solution": "x = -3",
            "knowledge_areas": {"sifat_operasi": True}
        },
        {
            "level": "High",
            "question": "Sebuah persegi panjang memiliki panjang (2x + 3) dan lebar (x - 1). Jika kelilingnya 24 cm, maka x = ?",
            "solution": "x = 4",
            "knowledge_areas": {"pemodelan": True, "sifat_operasi": True}
        },
    ]
    
    created_tasks = []
    
    for task_data in sample_tasks:
        try:
            task = create_task(**task_data)
            print(f"  ✅ Created {task_data['level']} task: {task_data['question'][:50]}...")
            created_tasks.append(task)
        except Exception as e:
            print(f"  ❌ Error creating task: {e}")
    
    return created_tasks


def create_sample_sessions(students, tasks):
    """Create sample learning sessions."""
    print("\n📊 Creating sample sessions...")
    
    if not students or not tasks:
        print("  ⚠️  No students or tasks available")
        return
    
    # Create a few sample sessions
    session_count = 0
    
    for i, student in enumerate(students[:2]):  # First 2 students
        student_id = student["student_id"]
        
        for j, task in enumerate(tasks[:3]):  # First 3 tasks
            task_id = task["task_id"]
            
            try:
                session_id = create_session(student_id, task_id)
                
                # Log a sample interaction
                log_student_interaction(
                    session_id=session_id,
                    student_id=student_id,
                    task_id=task_id,
                    task_level=task["level"],
                    question=task["question"],
                    student_answer="Sample answer for testing",
                    is_correct=(j % 2 == 0),  # Alternate correct/incorrect
                    feedback_given="Sample feedback",
                    feedback_type="Focused Formative Feedback",
                    error_count=(j % 3),
                    is_final=True,
                    achievement_level_assessed="High" if (j % 2 == 0) else "Low"
                )
                
                session_count += 1
                print(f"  ✅ Created session for {student['name']} - Task: {task['question'][:40]}...")
                
            except Exception as e:
                print(f"  ❌ Error creating session: {e}")
    
    print(f"\n  📈 Total sessions created: {session_count}")


def main():
    print("🌱 Seeding test data...\n")
    print("=" * 60)
    
    try:
        # Create test students
        students = create_test_students()
        
        # Create sample tasks
        tasks = create_sample_tasks()
        
        # Show task counts
        counts = count_tasks_by_level()
        print(f"\n  📊 Task counts - Low: {counts['Low']}, High: {counts['High']}")
        
        # Create sample sessions
        create_sample_sessions(students, tasks)
        
        print("\n" + "=" * 60)
        print("✅ Test data seeding completed!\n")
        
        print("📋 Test Accounts Created:")
        print("  Username: YPSSTUDENT_1 | Password: test123")
        print("  Username: YPSSTUDENT_2 | Password: test123")
        print("  Username: YPSSTUDENT_3 | Password: test123")
        
    except Exception as e:
        print(f"\n❌ Error during seeding: {e}")
        sys.exit(1)


if __name__ == "__main__":
    main()
