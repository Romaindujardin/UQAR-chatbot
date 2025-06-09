"""
Script de test pour la génération d'exercices
"""

import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))

import asyncio
import logging
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from app.services.exercise_service import ExerciseGenerationService
from app.schemas.exercise_schemas import QuestionType, DifficultyLevel
from app.models import Section

logging.basicConfig(level=logging.DEBUG)
logger = logging.getLogger(__name__)

# Database setup
SQLITE_DATABASE_URL = "sqlite:////home/dujr0001/UQAR_GIT/apptainer_data/uqar.db"
engine = create_engine(SQLITE_DATABASE_URL, connect_args={"check_same_thread": False})
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

async def test_exercise_generation():
    """Test exercise generation for a section"""
    
    db = SessionLocal()
    
    try:
        # Get sections
        sections = db.query(Section).all()
        logger.info(f"Found {len(sections)} sections")
        
        if not sections:
            logger.error("No sections found in database")
            return
            
        # Use the first section with documents
        section = None
        for s in sections:
            if s.documents:
                section = s
                break
                
        if not section:
            logger.error("No section with documents found")
            return
            
        logger.info(f"Testing with section: {section.id} - {section.name}")
        logger.info(f"Section has {len(section.documents)} documents")
        logger.info(f"ChromaDB collection: {section.chroma_collection_name}")
        
        # Initialize service
        service = ExerciseGenerationService()
        
        # Test generation
        logger.info("Starting exercise generation...")
        exercise = await service.generate_exercises(
            db=db,
            section_id=section.id,
            num_questions=3,
            difficulty=DifficultyLevel.MEDIUM,
            exercise_type=QuestionType.MCQ
        )
        
        logger.info(f"Exercise generated with ID: {exercise.id}")
        logger.info(f"Status: {exercise.status}")
        logger.info(f"Number of questions: {len(exercise.questions)}")
        
        for i, question in enumerate(exercise.questions):
            logger.info(f"\nQuestion {i+1}:")
            logger.info(f"  Text: {question.text}")
            logger.info(f"  Options: {question.options}")
            logger.info(f"  Correct answer: {question.correct_answer}")
            logger.info(f"  Explanation: {question.explanation}")
            
    except Exception as e:
        logger.error(f"Test failed: {e}", exc_info=True)
    finally:
        db.close()

if __name__ == "__main__":
    asyncio.run(test_exercise_generation()) 