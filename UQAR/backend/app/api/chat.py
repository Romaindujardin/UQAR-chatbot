from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.responses import StreamingResponse
from sqlalchemy.orm import Session
from typing import List, Dict, Any, Optional
import json
import asyncio

from ..core.database import get_db
from ..schemas.chat_schemas import ChatSessionResponse, ChatMessageResponse, CreateSessionRequest, SendMessageRequest
from ..models.user import User
from ..models.chat import ChatSession, ChatMessage
from ..services.chat_service import ChatService
from ..services.ollama_service import OllamaService
from .auth import get_current_active_user

router = APIRouter()





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


@router.post("/sessions/{session_id}/messages/stream")
async def send_message_stream(
    session_id: int,
    request: SendMessageRequest,
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
):
    """Envoyer un message dans le chat RAG avec streaming"""
    import logging
    import traceback
    from datetime import datetime
    from ..models.section import Section
    
    logger = logging.getLogger(__name__)

    async def generate_stream():
        try:
            logger.info(f"Streaming message request: session_id={session_id}, user_id={current_user.id}")

            chat_service = ChatService(db)

            # Vérifier la session
            session = db.query(ChatSession).filter(
                ChatSession.id == session_id,
                ChatSession.user_id == current_user.id
            ).first()

            if not session:
                yield f"data: {json.dumps({'error': 'Session non trouvée'})}\n\n"
                return

            # Sauvegarder le message utilisateur
            user_message = ChatMessage(
                session_id=session_id,
                content=request.content,
                is_assistant=False,
                created_at=datetime.utcnow()
            )
            db.add(user_message)
            db.flush()

            # Envoyer le message utilisateur
            yield f"data: {json.dumps({'type': 'user_message', 'content': request.content, 'id': user_message.id})}\n\n"

            # Récupérer le contexte RAG
            retrieved_context_texts = []
            section = None
            if chat_service.chroma_client and session.section_id:
                section = db.query(Section).filter(Section.id == session.section_id).first()
                if section and section.chroma_collection_name:
                    try:
                        collection = chat_service.chroma_client.get_collection(name=section.chroma_collection_name)
                        results = collection.query(query_texts=[request.content], n_results=3)
                        if results and results.get('documents') and results['documents'][0]:
                            retrieved_context_texts = results['documents'][0]
                    except Exception as e:
                        logger.error(f"Error querying ChromaDB: {e}")

            # Vérifier la pertinence
            if section:
                relevance_context = f"Nom de la section: {section.name}. Description: {section.description or ''}"
                is_relevant = await chat_service.ollama_service.check_relevance(request.content, relevance_context)
                
                if not is_relevant:
                    # Réponse non pertinente
                    response_content = "Désolé, cette question ne semble pas liée au sujet de cette section."
                    
                    # Sauvegarder la réponse
                    assistant_message = ChatMessage(
                        session_id=session_id,
                        content=response_content,
                        is_assistant=True,
                        created_at=datetime.utcnow()
                    )
                    db.add(assistant_message)
                    session.last_message_at = datetime.utcnow()
                    db.commit()
                    
                    yield f"data: {json.dumps({'type': 'assistant_message', 'content': response_content, 'id': assistant_message.id, 'done': True})}\n\n"
                    return

            # Générer la réponse en streaming
            yield f"data: {json.dumps({'type': 'assistant_start'})}\n\n"
            
            response_content = ""
            async for chunk in chat_service.ollama_service.generate_streaming_response(
                prompt=request.content,
                context=retrieved_context_texts if retrieved_context_texts else None
            ):
                response_content += chunk
                yield f"data: {json.dumps({'type': 'assistant_chunk', 'content': chunk})}\n\n"

            # Sauvegarder la réponse complète
            assistant_message = ChatMessage(
                session_id=session_id,
                content=response_content,
                is_assistant=True,
                created_at=datetime.utcnow()
            )
            db.add(assistant_message)
            
            # Mettre à jour la session
            session.last_message_at = datetime.utcnow()
            
            # Générer un titre si c'est le premier message
            existing_count = db.query(ChatMessage).filter(ChatMessage.session_id == session_id).count()
            if existing_count <= 2:  # user_message + assistant_message
                try:
                    new_title = await chat_service.ollama_service.generate_title(request.content)
                    session.title = new_title
                except Exception:
                    pass
            
            db.commit()
            
            yield f"data: {json.dumps({'type': 'assistant_message', 'content': response_content, 'id': assistant_message.id, 'done': True})}\n\n"

        except Exception as e:
            logger.error(f"Error in streaming: {e}")
            logger.error(f"Error traceback: {traceback.format_exc()}")
            yield f"data: {json.dumps({'error': f'Erreur lors de la génération: {str(e)}'})}\n\n"

    return StreamingResponse(
        generate_stream(),
        media_type="text/plain",
        headers={
            "Cache-Control": "no-cache",
            "Connection": "keep-alive",
            "Access-Control-Allow-Origin": "*",
            "Access-Control-Allow-Methods": "GET, POST, PUT, DELETE, OPTIONS",
            "Access-Control-Allow-Headers": "Content-Type, Authorization",
        }
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
