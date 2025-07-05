from sqlalchemy import create_engine
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker, Session
from sqlalchemy.pool import StaticPool
from typing import Generator
import logging
import os

logger = logging.getLogger(__name__)

# Utiliser SQLite au lieu de PostgreSQL
SQLITE_DATABASE_URL = "sqlite:////home/dujr0001/UQAR_GIT/apptainer_data/uqar.db"
logger.info(f"Connexion à la base de données SQLite: {SQLITE_DATABASE_URL}")

# Moteur SQLAlchemy pour SQLite
engine = create_engine(
    SQLITE_DATABASE_URL,
    connect_args={"check_same_thread": False},
    poolclass=StaticPool,
    echo=False  # Mettre à True pour debug SQL
)

# Session factory
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

# Base pour les modèles
Base = declarative_base()


def get_db() -> Generator[Session, None, None]:
    """
    Générateur de session de base de données pour l'injection de dépendance FastAPI.
    """
    db = SessionLocal()
    try:
        yield db
    except Exception as e:
        logger.error(f"Erreur de base de données: {e}")
        db.rollback()
        raise
    finally:
        db.close()


def create_tables():
    """
    Créer toutes les tables dans la base de données.
    """
    try:
        # Import all models to ensure they are registered
        from ..models import User, Section, Document, Exercise, Question, ExerciseSubmission, ChatSession, ChatMessage, StudentFeedback
        Base.metadata.create_all(bind=engine)
        logger.info("Tables créées avec succès")
    except Exception as e:
        logger.error(f"Erreur lors de la création des tables: {e}")
        raise


def drop_tables():
    """
    Supprimer toutes les tables (utile pour les tests).
    """
    try:
        Base.metadata.drop_all(bind=engine)
        logger.info("Tables supprimées avec succès")
    except Exception as e:
        logger.error(f"Erreur lors de la suppression des tables: {e}")
        raise 