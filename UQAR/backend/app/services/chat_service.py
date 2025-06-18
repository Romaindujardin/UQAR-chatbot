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
from ..schemas.chat_schemas import ChatMessageResponse # Updated import
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

    def get_user_sessions(self, user_id: int) -> List[ChatSession]:
        """
        Récupère toutes les sessions de chat pour un utilisateur donné.
        """
        # Ensure ChatSession is imported if not already visible in this scope
        # from ..models.chat import ChatSession # This should already be at the top of the file

        logger.info(f"Attempting to fetch chat sessions for user_id: {user_id}")
        try:
            sessions = self.db.query(ChatSession).filter(ChatSession.user_id == user_id).all()
            if not sessions:
                logger.info(f"No chat sessions found for user_id: {user_id}")
                return []
            logger.info(f"Found {len(sessions)} chat sessions for user_id: {user_id}")
            return sessions
        except Exception as e:
            logger.error(f"Error fetching chat sessions for user_id {user_id}: {e}", exc_info=True)
            # Re-raise the exception to be caught by the API layer, or handle appropriately
            raise

    async def create_session(self, user_id: int, section_id: int) -> ChatSession:
        """
        Crée une nouvelle session de chat pour un utilisateur et une section donnés.
        """
        # Imports are assumed to be at the top of the file:
        # from ..models.chat import ChatSession
        # from ..models.section import Section
        # from datetime import datetime
        
        logger.info(f"Creating new chat session for user_id: {user_id}, section_id: {section_id}")
        
        try:
            # Vérifier si la section existe
            section = self.db.query(Section).filter(Section.id == section_id).first()
            if not section:
                logger.warning(f"Section with id {section_id} not found.")
                raise ValueError(f"Section {section_id} non trouvée.")

            # Créer un titre par défaut pour la session
            # Assurez-vous que le modèle ChatSession a un champ 'title'
            session_title = f"Chat sur '{section.name}' - {datetime.now().strftime('%Y-%m-%d %H:%M')}"
            
            new_session = ChatSession(
                user_id=user_id,
                section_id=section_id,
                title=session_title,
                created_at=datetime.utcnow(), # Assuming created_at is managed this way
                last_message_at=datetime.utcnow() # Initially same as created_at
            )
            
            self.db.add(new_session)
            self.db.commit()
            self.db.refresh(new_session)
            
            logger.info(f"Chat session created with id: {new_session.id}, title: {new_session.title}")
            return new_session
        except ValueError as ve: # Catch specific ValueError to re-raise
            raise ve
        except Exception as e:
            logger.error(f"Error creating chat session for user_id {user_id}, section_id {section_id}: {e}", exc_info=True)
            # Re-raise a generic exception or a custom one to be caught by API layer
            raise Exception(f"Erreur interne lors de la création de la session: {str(e)}")

    def get_session_messages(self, session_id: int, user_id: int) -> List[ChatMessage]:
        """
        Récupère les messages d'une session de chat spécifique,
        après avoir vérifié que l'utilisateur y a accès.
        """
        # Imports are assumed to be at the top of the file:
        # from ..models.chat import ChatSession, ChatMessage
        # from typing import List
        
        logger.info(f"Fetching messages for session_id: {session_id}, user_id: {user_id}")
        
        try:
            # Vérifier si la session existe et si l'utilisateur y a accès
            # Assumant que ChatSession a un champ 'user_id'
            session = self.db.query(ChatSession).filter(
                ChatSession.id == session_id,
                ChatSession.user_id == user_id  # Vérification de propriété/accès
            ).first()

            if not session:
                logger.warning(f"Session_id {session_id} not found or user_id {user_id} is not authorized.")
                # Il est important de ne pas révéler si la session existe ou si l'utilisateur n'est pas autorisé
                # pour des raisons de sécurité, donc une erreur générique "non trouvé" ou "accès interdit" est préférable.
                raise ValueError("Session non trouvée ou accès non autorisé.")

            # Récupérer les messages de la session, ordonnés par date de création
            # Assumant que ChatMessage a des champs 'session_id' et 'created_at'
            messages = self.db.query(ChatMessage).filter(
                ChatMessage.session_id == session_id
            ).order_by(ChatMessage.created_at.asc()).all()
            
            if not messages:
                logger.info(f"No messages found for session_id: {session_id}")
                return []
                
            logger.info(f"Found {len(messages)} messages for session_id: {session_id}")
            return messages
        except ValueError as ve: # Catch specific ValueError to re-raise
            logger.warning(f"ValueError in get_session_messages: {ve}")
            raise ve
        except Exception as e:
            logger.error(f"Error fetching messages for session_id {session_id}: {e}", exc_info=True)
            raise Exception(f"Erreur interne lors de la récupération des messages: {str(e)}")

    async def send_message(self, session_id: int, user_id: int, content: str) -> Dict[str, Any]:
        """
        Gère l'envoi d'un message par l'utilisateur, récupère le contexte RAG,
        obtient une réponse de Ollama, et sauvegarde les messages.
        """
        # Imports are assumed to be at the top of the file:
        # from ..models.chat import ChatSession, ChatMessage
        # from ..models.section import Section # Added for fetching section details
        # from datetime import datetime
        # from typing import Dict, Any, List # List might be needed for context

        logger.info(f"Sending message for session_id: {session_id}, user_id: {user_id}")

        try:
            # 1. Vérifier la session et l'accès utilisateur
            session = self.db.query(ChatSession).filter(
                ChatSession.id == session_id,
                ChatSession.user_id == user_id
            ).first()

            if not session:
                logger.warning(f"Session_id {session_id} not found or user_id {user_id} is not authorized for send_message.")
                raise ValueError("Session non trouvée ou accès non autorisé.")

            # 2. Compter les messages existants pour savoir si c'est le premier
            existing_count = (
                self.db.query(ChatMessage)
                .filter(ChatMessage.session_id == session_id)
                .count()
            )

            # 3. Sauvegarder le message de l'utilisateur

            # 3. Sauvegarder le message de l'utilisateur
            # Assumant que ChatMessage a les champs: session_id, content, is_assistant, created_at
            user_message = ChatMessage(
                session_id=session_id,
                content=content,
                is_assistant=False,  # Message de l'utilisateur
                created_at=datetime.utcnow()
            )
            self.db.add(user_message)
            self.db.flush()  # Pour obtenir l'ID du message utilisateur si besoin avant commit

            # 4. Récupérer le contexte RAG via ChromaDB
            retrieved_context_texts = []
            section = None
            if self.chroma_client and session.section_id:
                section = self.db.query(Section).filter(Section.id == session.section_id).first()
                if section and section.chroma_collection_name:
                    try:
                        logger.info(f"Querying ChromaDB collection: {section.chroma_collection_name} for section {section.id}")
                        collection = self.chroma_client.get_collection(name=section.chroma_collection_name)
                        # Nombre de résultats à récupérer (ajuster si nécessaire)
                        results = collection.query(query_texts=[content], n_results=3) 
                        if results and results.get('documents') and results['documents'][0]:
                            retrieved_context_texts = results['documents'][0]
                            logger.info(f"Retrieved {len(retrieved_context_texts)} context snippets from ChromaDB.")
                        else:
                            logger.info("No context found in ChromaDB for the query.")
                    except Exception as chroma_exc:
                        logger.error(f"Error querying ChromaDB collection {section.chroma_collection_name}: {chroma_exc}", exc_info=True)
                        # Continuer sans contexte si ChromaDB échoue
                else:
                    logger.warning(f"Section {session.section_id} not found or has no chroma_collection_name for RAG.")
            else:
                logger.info("ChromaDB client not available or section_id missing; proceeding without RAG context.")

            if retrieved_context_texts:
                logger.info(f"Retrieved RAG context. Number of snippets: {len(retrieved_context_texts)}")
                for i, text in enumerate(retrieved_context_texts):
                    logger.info(f"RAG context snippet {i+1} (first 100 chars): {text[:100]}")
                    logger.info(f"RAG context snippet {i+1} (length): {len(text)}")
            else:
                logger.info("No RAG context was retrieved or used.")
            
            # Construire un contexte simple pour la vérification de pertinence
            if section:
                relevance_context = f"Nom de la section: {section.name}. Description: {section.description or ''}"
            else:
                relevance_context = ""


            is_relevant = await self.ollama_service.check_relevance(content, relevance_context)

            if not is_relevant:
                ai_response_content = "Désolé, cette question ne semble pas liée au sujet de cette section."
            else:
                # 4. Obtenir la réponse de OllamaService
                # Le system_prompt par défaut est dans OllamaService._build_prompt
                ai_response_content = await self.ollama_service.generate_response(
                    prompt=content,
                    context=retrieved_context_texts if retrieved_context_texts else None
                )

                if existing_count == 0:
                    try:
                        new_title = await self.ollama_service.generate_title(content)
                        session.title = new_title
                    except Exception:
                        pass

            # 5. Sauvegarder le message de l'assistant
            assistant_message = ChatMessage(
                session_id=session_id,
                content=ai_response_content,
                is_assistant=True, # Message de l'assistant
                created_at=datetime.utcnow()
            )
            self.db.add(assistant_message)
            
            # 6. Mettre à jour last_message_at pour la session
            session.last_message_at = datetime.utcnow()
            self.db.add(session) # Ajouter la session mise à jour à la session de la DB

            self.db.commit() # Commit tous les changements (user_message, assistant_message, session update)
            self.db.refresh(user_message)
            self.db.refresh(assistant_message)
            
            logger.info(f"User message (id: {user_message.id}) and assistant message (id: {assistant_message.id}) saved.")

            # 7. Retourner les messages (ou leurs représentations Pydantic si nécessaire par l'API)
            # L'API s'attend à Dict[str, Any], qui est ensuite probablement converti en ChatMessageResponse.
            # Pour simplifier ici, nous allons retourner les objets ORM, l'API se chargera de la sérialisation.
            # Cependant, l'API chat.py s'attend à `result['user_message']['id']`, etc.
            # Il faut donc retourner un dict structuré.
            
            # Convertir les objets ORM en dictionnaires simples pour correspondre à la structure attendue par l'API
            # ou s'assurer que l'API peut gérer les objets ORM directement via Pydantic .from_orm()
            # Pour l'instant, on retourne un dict avec les objets, l'API devra les sérialiser.
            # L'API `chat.py` utilise `ChatMessageResponse.from_orm(message)`
            # Le retour attendu par l'API POST /sessions/{session_id}/messages est Dict[str, Any]
            # Dans l'API: result = await chat_service.send_message(...)
            # logger.info(f"Message sent successfully: user_message_id={result['user_message']['id']}, system_message_id={result['system_message']['id']}")
            # Donc, la structure doit être:
            return {
                "user_message": ChatMessageResponse.from_orm(user_message).model_dump(),
                "system_message": ChatMessageResponse.from_orm(assistant_message).model_dump()
            }

        except ValueError as ve:
            logger.warning(f"ValueError in send_message: {ve}")
            self.db.rollback() # Rollback en cas d'erreur avant commit
            raise ve
        except Exception as e:
            logger.error(f"Error in send_message for session_id {session_id}: {e}", exc_info=True)
            self.db.rollback()
            raise Exception(f"Erreur interne lors de l'envoi du message: {str(e)}")

    def delete_session(self, session_id: int, user_id: int) -> bool:
        """
        Supprime une session de chat et tous ses messages,
        après avoir vérifié que l'utilisateur est propriétaire de la session.
        """
        # Imports are assumed to be at the top of the file:
        # from ..models.chat import ChatSession, ChatMessage
        
        logger.info(f"Attempting to delete chat session_id: {session_id} for user_id: {user_id}")
        
        try:
            # 1. Trouver la session et vérifier la propriété
            session = self.db.query(ChatSession).filter(
                ChatSession.id == session_id,
                ChatSession.user_id == user_id
            ).first()

            if not session:
                logger.warning(f"Session_id {session_id} not found or user_id {user_id} is not authorized for deletion.")
                return False # Ou lever une exception si l'API doit distinguer "non trouvé" de "non autorisé"

            # 2. Supprimer les messages associés à la session
            # Assumant que ChatMessage a un champ 'session_id'
            num_messages_deleted = self.db.query(ChatMessage).filter(
                ChatMessage.session_id == session_id
            ).delete(synchronize_session=False) # 'fetch' pourrait être plus sûr pour cascades si configurées
            
            logger.info(f"Deleted {num_messages_deleted} messages for session_id: {session_id}")

            # 3. Supprimer la session elle-même
            self.db.delete(session)
            
            # 4. Commit la transaction
            self.db.commit()
            
            logger.info(f"Successfully deleted session_id: {session_id} for user_id: {user_id}")
            return True
            
        except Exception as e:
            logger.error(f"Error deleting session_id {session_id} for user_id {user_id}: {e}", exc_info=True)
            self.db.rollback() # Rollback en cas d'erreur
            # Selon la gestion d'erreur souhaitée, on pourrait retourner False ou lever l'exception
            # L'API actuelle s'attend à un booléen pour retourner 404 si False.
            # Mais une exception interne devrait plutôt être un 500.
            # Pour correspondre à l'API, on peut retourner False ici, mais c'est discutable.
            # Levons l'exception pour que l'API la gère comme un 500, ce qui est plus précis pour une erreur interne.
            raise Exception(f"Erreur interne lors de la suppression de la session: {str(e)}")
