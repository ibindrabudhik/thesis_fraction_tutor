"""Script to import tasks from CSV files into Supabase database.

Usage:
    python import_tasks.py [path_to_csv] [--level Low|High]

Example:
    python import_tasks.py data/documents/algebra_train.csv --level Low
"""
import sys
import os
import argparse

# Load environment variables from .env file
try:
    from dotenv import load_dotenv
    env_path = os.path.join(os.path.dirname(__file__), '..', '..', '.env')
    load_dotenv(env_path)
except ImportError:
    pass  # dotenv not installed, will rely on system env vars or Streamlit secrets

# Add parent directory to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

from database.task_service import bulk_import_tasks


def main():
    parser = argparse.ArgumentParser(description="Import tasks from CSV to database")
    parser.add_argument("csv_file", help="Path to CSV file containing tasks")
    parser.add_argument("--level", choices=["Low", "High"], default="Low",
                        help="Default difficulty level for tasks")
    
    args = parser.parse_args()
    
    csv_path = args.csv_file
    default_level = args.level
    
    if not os.path.exists(csv_path):
        print(f"❌ Error: File not found: {csv_path}")
        sys.exit(1)
    
    print(f"📂 Importing tasks from: {csv_path}")
    print(f"🎯 Default level: {default_level}")
    print()
    
    try:
        count = bulk_import_tasks(csv_path, default_level=default_level)
        print(f"✅ Successfully imported {count} tasks!")
        
    except Exception as e:
        print(f"❌ Error during import: {e}")
        sys.exit(1)


if __name__ == "__main__":
    main()
