"""
Migration script to update exercise-related database tables.
This script should be run after updating the models to ensure the database schema matches.
"""

import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))

from sqlalchemy import create_engine, text
from app.core.config import settings
from app.core.database import Base
from app.models import Exercise, Question, ExerciseSubmission
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


def run_migrations():
    """Run database migrations for exercise-related tables"""
    
    # Create engine
    engine = create_engine(settings.DATABASE_URL)
    
    try:
        # Check if we need to migrate from old schema
        with engine.connect() as conn:
            # Check if old exercise table exists with old columns
            result = conn.execute(text("""
                SELECT column_name 
                FROM information_schema.columns 
                WHERE table_name = 'exercises' 
                AND column_name IN ('title', 'question', 'exercise_data')
            """))
            
            old_columns_exist = len(result.fetchall()) > 0
            
            if old_columns_exist:
                logger.info("Old exercise schema detected. Running migration...")
                
                # 1. Create new tables
                logger.info("Creating new tables...")
                Base.metadata.create_all(bind=engine, tables=[
                    Question.__table__,
                    ExerciseSubmission.__table__
                ])
                
                # 2. Migrate data from old schema
                logger.info("Migrating exercise data...")
                conn.execute(text("""
                    -- Add new columns to exercises if they don't exist
                    ALTER TABLE exercises 
                    ADD COLUMN IF NOT EXISTS status VARCHAR DEFAULT 'pending',
                    ADD COLUMN IF NOT EXISTS generation_params JSON,
                    ADD COLUMN IF NOT EXISTS source_documents JSON,
                    ADD COLUMN IF NOT EXISTS created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
                    ADD COLUMN IF NOT EXISTS updated_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP;
                    
                    -- Update existing exercises to have status
                    UPDATE exercises 
                    SET status = CASE 
                        WHEN is_validated = true THEN 'validated'::text 
                        ELSE 'pending'::text 
                    END
                    WHERE status IS NULL;
                """))
                
                # 3. Migrate questions from old exercise_data JSON
                logger.info("Migrating questions from old format...")
                exercises = conn.execute(text("""
                    SELECT id, exercise_data, question, exercise_type, explanation 
                    FROM exercises 
                    WHERE exercise_data IS NOT NULL
                """)).fetchall()
                
                for exercise in exercises:
                    exercise_id = exercise[0]
                    exercise_data = exercise[1] or {}
                    question_text = exercise[2]
                    exercise_type = exercise[3]
                    explanation = exercise[4]
                    
                    # Create question from old data
                    if question_text:
                        conn.execute(text("""
                            INSERT INTO questions (
                                exercise_id, text, question_type, options, 
                                correct_answer, explanation, points, order_index
                            ) VALUES (
                                :exercise_id, :text, :question_type, :options,
                                :correct_answer, :explanation, 1, 0
                            )
                        """), {
                            'exercise_id': exercise_id,
                            'text': question_text,
                            'question_type': exercise_type or 'mcq',
                            'options': exercise_data.get('options'),
                            'correct_answer': exercise_data.get('correct_answer'),
                            'explanation': explanation
                        })
                
                # 4. Remove old columns
                logger.info("Removing old columns...")
                conn.execute(text("""
                    ALTER TABLE exercises 
                    DROP COLUMN IF EXISTS title,
                    DROP COLUMN IF EXISTS question,
                    DROP COLUMN IF EXISTS exercise_data,
                    DROP COLUMN IF EXISTS explanation,
                    DROP COLUMN IF EXISTS source_context,
                    DROP COLUMN IF EXISTS is_validated,
                    DROP COLUMN IF EXISTS generated_at,
                    DROP COLUMN IF EXISTS generated_from_document_id,
                    DROP COLUMN IF EXISTS times_attempted,
                    DROP COLUMN IF EXISTS times_correct,
                    DROP COLUMN IF EXISTS exercise_type,
                    DROP COLUMN IF EXISTS difficulty;
                """))
                
                conn.commit()
                logger.info("Migration completed successfully!")
                
            else:
                logger.info("No migration needed. Creating/updating tables...")
                # Just ensure all tables exist
                Base.metadata.create_all(bind=engine)
                logger.info("Tables created/updated successfully!")
                
    except Exception as e:
        logger.error(f"Migration failed: {e}")
        raise
        

if __name__ == "__main__":
    logger.info("Starting exercise migration...")
    run_migrations()
    logger.info("Migration completed!") 