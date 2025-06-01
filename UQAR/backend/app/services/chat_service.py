import logging
from typing import List, Dict, Optional, Any
from sqlalchemy.orm import Session
from datetime import datetime

# Import chromadb conditionnellement
try:
    import chromadb
    CHROMADB_AVAILABLE = True
except (ImportError, RuntimeError) as e:
    logging.warning(f"ChromaDB not available: {e}")
    CHROMADB_AVAILABLE = False

from ..models.chat import ChatSession, ChatMessage
from ..models.section import Section
from ..models.user import User
from ..core.config import settings
from .ollama_service import OllamaService

logger = logging.getLogger(__name__)

class ChatService:
    """Service pour gérer le chat RAG avec ChromaDB et Ollama"""

    def __init__(self, db: Session):
        self.db = db
        self.ollama_service = OllamaService()
        self.chroma_client = None

        if CHROMADB_AVAILABLE:
            try:
                # Premier essai avec tenant/database
                self.chroma_client = chromadb.HttpClient(
                    host=settings.CHROMA_HOST,
                    port=settings.CHROMA_PORT,
                    tenant="default_tenant",
                    database="default_database"
                )
                logger.info("ChromaDB client initialized successfully with tenant/database")
            except Exception as e:
                logger.warning(f"Could not initialize ChromaDB with tenant/database: {e}")
                try:
                    # Deuxième essai sans tenant/database
                    self.chroma_client = chromadb.HttpClient(
                        host=settings.CHROMA_HOST,
                        port=settings.CHROMA_PORT
                    )
                    logger.info("ChromaDB client initialized without tenant/database")
                except Exception as e2:
                    logger.warning(f"Could not initialize ChromaDB without tenant/database: {e2}")
                    try:
                        # Troisième essai avec PersistentClient
                        self.chroma_client = chromadb.PersistentClient(
                            path=settings.CHROMA_PERSIST_DIRECTORY
                        )
                        logger.info("ChromaDB initialized as PersistentClient")
                    except Exception as e3:
                        logger.error(f"All ChromaDB initialization attempts failed: {e3}")
                        self.chroma_client = None
        else:
            logger.warning("ChromaDB is not available, RAG features will be disabled")
