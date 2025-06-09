"""
Simple script to add missing columns to exercises table for SQLite
"""

import sqlite3
import json
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Database path from database.py
DB_PATH = "/home/dujr0001/UQAR_GIT/apptainer_data/uqar.db"

def add_missing_columns():
    """Add missing columns to exercises table"""
    
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    
    try:
        # Get current columns
        cursor.execute("PRAGMA table_info(exercises)")
        existing_columns = {row[1] for row in cursor.fetchall()}
        logger.info(f"Existing columns in exercises table: {existing_columns}")
        
        # Add missing columns one by one (SQLite doesn't support multiple ADD COLUMN in one statement)
        columns_to_add = [
            ("status", "VARCHAR DEFAULT 'pending'"),
            ("generation_params", "JSON"),
            ("source_documents", "JSON"),
            ("created_at", "TIMESTAMP DEFAULT CURRENT_TIMESTAMP"),
            ("updated_at", "TIMESTAMP DEFAULT CURRENT_TIMESTAMP")
        ]
        
        for column_name, column_def in columns_to_add:
            if column_name not in existing_columns:
                try:
                    sql = f"ALTER TABLE exercises ADD COLUMN {column_name} {column_def}"
                    cursor.execute(sql)
                    logger.info(f"Added column: {column_name}")
                except sqlite3.OperationalError as e:
                    if "duplicate column name" in str(e):
                        logger.info(f"Column {column_name} already exists")
                    else:
                        raise
        
        # Create questions table if it doesn't exist
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS questions (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                exercise_id INTEGER NOT NULL,
                text TEXT NOT NULL,
                question_type VARCHAR NOT NULL,
                options JSON,
                correct_answer TEXT,
                expected_keywords JSON,
                explanation TEXT,
                points INTEGER DEFAULT 1,
                order_index INTEGER DEFAULT 0,
                FOREIGN KEY (exercise_id) REFERENCES exercises(id) ON DELETE CASCADE
            )
        """)
        logger.info("Created/verified questions table")
        
        # Create exercise_submissions table if it doesn't exist
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS exercise_submissions (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                exercise_id INTEGER NOT NULL,
                student_id INTEGER NOT NULL,
                answers JSON NOT NULL,
                score REAL,
                percentage REAL,
                feedback JSON,
                submitted_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (exercise_id) REFERENCES exercises(id),
                FOREIGN KEY (student_id) REFERENCES users(id)
            )
        """)
        logger.info("Created/verified exercise_submissions table")
        
        # Update any existing exercises to have a status
        cursor.execute("""
            UPDATE exercises 
            SET status = 'pending' 
            WHERE status IS NULL
        """)
        
        conn.commit()
        logger.info("All changes committed successfully!")
        
    except Exception as e:
        logger.error(f"Error updating database: {e}")
        conn.rollback()
        raise
    finally:
        conn.close()


if __name__ == "__main__":
    logger.info("Starting to add missing columns to exercises table...")
    add_missing_columns()
    logger.info("Completed!") 