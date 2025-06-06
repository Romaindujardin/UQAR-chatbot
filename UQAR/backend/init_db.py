import sys
sys.path.append(".")

from app.core.database import create_tables
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def initialize_database():
    logger.info("Initializing database...")
    create_tables()
    logger.info("Database initialization completed successfully.")

if __name__ == "__main__":
    initialize_database() 