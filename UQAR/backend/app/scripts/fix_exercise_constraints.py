"""
Script to fix NOT NULL constraints on legacy columns in exercises table
"""

import sqlite3
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Database path from database.py
DB_PATH = "/home/dujr0001/UQAR_GIT/apptainer_data/uqar.db"

def fix_constraints():
    """Fix NOT NULL constraints by recreating the table with proper schema"""
    
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    
    try:
        # SQLite doesn't support ALTER COLUMN, so we need to recreate the table
        logger.info("Starting to fix exercises table constraints...")
        
        # First, let's backup existing data
        cursor.execute("SELECT * FROM exercises")
        existing_data = cursor.fetchall()
        cursor.execute("PRAGMA table_info(exercises)")
        columns_info = cursor.fetchall()
        column_names = [col[1] for col in columns_info]
        logger.info(f"Backed up {len(existing_data)} existing exercises")
        
        # Create a new table with correct schema
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS exercises_new (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                section_id INTEGER NOT NULL,
                status VARCHAR DEFAULT 'pending',
                exercise_type VARCHAR,
                difficulty VARCHAR,
                title VARCHAR,
                question TEXT,
                exercise_data JSON,
                explanation TEXT,
                source_context TEXT,
                is_validated BOOLEAN,
                generated_at TIMESTAMP,
                generated_from_document_id INTEGER,
                times_attempted INTEGER,
                times_correct INTEGER,
                validated_by_id INTEGER,
                validated_at TIMESTAMP,
                validation_notes TEXT,
                generation_params JSON,
                source_documents JSON,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (section_id) REFERENCES sections(id),
                FOREIGN KEY (validated_by_id) REFERENCES users(id),
                FOREIGN KEY (generated_from_document_id) REFERENCES documents(id)
            )
        """)
        logger.info("Created new exercises table with proper schema")
        
        # Copy data from old table to new table
        if existing_data:
            # Build insert query dynamically based on existing columns
            placeholders = ','.join(['?' for _ in column_names])
            columns_str = ','.join(column_names)
            insert_query = f"INSERT INTO exercises_new ({columns_str}) VALUES ({placeholders})"
            
            for row in existing_data:
                cursor.execute(insert_query, row)
            logger.info(f"Copied {len(existing_data)} exercises to new table")
        
        # Drop the old table and rename the new one
        cursor.execute("DROP TABLE exercises")
        cursor.execute("ALTER TABLE exercises_new RENAME TO exercises")
        logger.info("Replaced old table with new table")
        
        # Recreate any indexes if needed
        cursor.execute("CREATE INDEX IF NOT EXISTS idx_exercises_section_id ON exercises(section_id)")
        cursor.execute("CREATE INDEX IF NOT EXISTS idx_exercises_status ON exercises(status)")
        
        conn.commit()
        logger.info("All changes committed successfully!")
        
    except Exception as e:
        logger.error(f"Error fixing constraints: {e}")
        conn.rollback()
        raise
    finally:
        conn.close()


if __name__ == "__main__":
    logger.info("Starting to fix exercise table constraints...")
    fix_constraints()
    logger.info("Completed!") 