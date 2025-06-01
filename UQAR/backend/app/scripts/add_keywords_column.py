import sys
import os
import logging
from sqlalchemy import text

# Add the parent directory to sys.path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '../..')))

from app.core.database import engine

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def add_keywords_column():
    """Add keywords column to sections table if it doesn't exist"""
    try:
        # Check if the column exists
        with engine.connect() as conn:
            result = conn.execute(text("PRAGMA table_info(sections)"))
            columns = [row[1] for row in result.fetchall()]
            
            if 'keywords' not in columns:
                logger.info("Keywords column doesn't exist in sections table. Adding it...")
                # Add the column
                conn.execute(text("ALTER TABLE sections ADD COLUMN keywords TEXT"))
                logger.info("Successfully added keywords column to sections table")
            else:
                logger.info("Keywords column already exists in sections table")
                
            # Check after modification
            result = conn.execute(text("PRAGMA table_info(sections)"))
            columns = [row[1] for row in result.fetchall()]
            logger.info(f"Current columns in sections table: {columns}")
            
            # List sections to verify
            result = conn.execute(text("SELECT id, name, keywords FROM sections"))
            sections = result.fetchall()
            logger.info(f"Found {len(sections)} sections in the database")
            for section in sections:
                logger.info(f"Section ID: {section[0]}, Name: {section[1]}, Keywords: {section[2]}")
                
    except Exception as e:
        logger.error(f"Error adding keywords column: {e}", exc_info=True)
        raise

if __name__ == "__main__":
    logger.info("Starting migration script to add keywords column")
    add_keywords_column()
    logger.info("Migration completed") 