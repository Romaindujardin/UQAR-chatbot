from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from typing import List, Dict, Any, Optional
from pydantic import BaseModel

from ..core.database import get_db
from ..models.user import User
from ..models.chat import ChatSession, ChatMessage
from ..services.chat_service import ChatService
from ..services.ollama_service import OllamaService
from .auth import get_current_active_user

router = APIRouter()


# Schémas Pydantic
class ChatSessionResponse(BaseModel):
    id: int
    title: str
    section_id: int
    section_name: str
    created_at: str
    last_message_at: Optional[str] = None
    message_count: int

    class Config:
        from_attributes = True


class ChatMessageResponse(BaseModel):
    id: int
    content: str
    is_user: bool
    created_at: str

    class Config:
        from_attributes = True

    @classmethod
    def from_orm(cls, message):
        """Convertir un objet ChatMessage en ChatMessageResponse"""
        return cls(
            id=message.id,
            content=message.content,
            is_user=not message.is_assistant,  # Convertir is_assistant en is_user
            created_at=message.created_at.isoformat()
        )


class CreateSessionRequest(BaseModel):
    section_id: int


class SendMessageRequest(BaseModel):
    content: str


# Routes
@router.get("/sessions", response_model=List[ChatSessionResponse])
async def get_chat_sessions(
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
):
    """Obtenir les sessions de chat de l'utilisateur"""
    chat_service = ChatService(db)

    try:
        sessions = chat_service.get_user_sessions(current_user.id)

        # Convertir les sessions en réponse API
        result = []
        for session in sessions:
            result.append({
                "id": session.id,
                "title": session.title,
                "section_id": session.section_id,
                "section_name": session.section.name,
                "created_at": session.created_at.isoformat(),
                "last_message_at": session.last_message_at.isoformat() if session.last_message_at else None,
                "message_count": session.message_count
            })

        return result
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Erreur lors de la récupération des sessions: {str(e)}"
        )


@router.post("/sessions", response_model=ChatSessionResponse)
async def create_chat_session(
    request: CreateSessionRequest,
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
):
    """Créer une nouvelle session de chat"""
    chat_service = ChatService(db)

    try:
        session = await chat_service.create_session(
            user_id=current_user.id,
            section_id=request.section_id
        )

        return {
            "id": session.id,
            "title": session.title,
            "section_id": session.section_id,
            "section_name": session.section.name,
            "created_at": session.created_at.isoformat(),
            "last_message_at": session.last_message_at.isoformat() if session.last_message_at else None,
            "message_count": 0
        }
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Erreur lors de la création de la session: {str(e)}"
        )


@router.get("/sessions/{session_id}/messages", response_model=List[ChatMessageResponse])
async def get_session_messages(
    session_id: int,
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
):
    """Obtenir les messages d'une session de chat"""
    chat_service = ChatService(db)

    try:
        messages = chat_service.get_session_messages(
            session_id=session_id,
            user_id=current_user.id
        )

        return [ChatMessageResponse.from_orm(message) for message in messages]
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail=str(e)
        )
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Erreur lors de la récupération des messages: {str(e)}"
        )


@router.post("/sessions/{session_id}/messages", response_model=Dict[str, Any])
async def send_message(
    session_id: int,
    request: SendMessageRequest,
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
):
    """Envoyer un message dans le chat RAG"""
    import logging
    import traceback
    logger = logging.getLogger(__name__)

    try:
        logger.info(f"Send message request: session_id={session_id}, user_id={current_user.id}, content={request.content[:50]}...")

        chat_service = ChatService(db)

        logger.info(f"ChatService initialized, Ollama model: {chat_service.ollama_service.model}")

        session = db.query(ChatSession).filter(
            ChatSession.id == session_id,
            ChatSession.user_id == current_user.id
        ).first()

        if not session:
            logger.error(f"Session {session_id} not found or not authorized for user {current_user.id}")
            raise ValueError(f"Session {session_id} non trouvée ou non autorisée")

        logger.info(f"Session found: {session.id}, section_id: {session.section_id}")

        result = await chat_service.send_message(
            session_id=session_id,
            user_id=current_user.id,
            content=request.content
        )

        logger.info(f"Message sent successfully: user_message_id={result['user_message']['id']}, system_message_id={result['system_message']['id']}")

        return result

    except ValueError as e:
        logger.error(f"ValueError in send_message: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail=str(e)
        )
    except Exception as e:
        logger.error(f"Error in send_message API handler: {str(e)}")
        logger.error(f"Error traceback: {traceback.format_exc()}")

        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Erreur lors de l'envoi du message: {str(e)}"
        )


@router.delete("/sessions/{session_id}")
async def delete_chat_session(
    session_id: int,
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
):
    """Supprimer une session de chat"""
    chat_service = ChatService(db)

    try:
        success = chat_service.delete_session(
            session_id=session_id,
            user_id=current_user.id
        )

        if not success:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Session non trouvée"
            )

        return {"message": "Session supprimée avec succès"}
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Erreur lors de la suppression de la session: {str(e)}"
        )


@router.get("/ollama-health")
async def check_ollama_health():
    """Vérifier si Ollama est disponible"""
    try:
        ollama_service = OllamaService()
        is_healthy = await ollama_service.health_check()
        return {
            "status": "healthy" if is_healthy else "unhealthy",
            "model": ollama_service.model
        }
    except Exception as e:
        return {
            "status": "error",
            "message": str(e)
        }
