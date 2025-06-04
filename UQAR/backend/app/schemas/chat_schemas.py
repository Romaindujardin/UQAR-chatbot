from pydantic import BaseModel
from typing import Optional, List, Dict, Any # Added List, Dict, Any for completeness, though not strictly used by these schemas directly.

# Schémas Pydantic pour le Chat
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
    is_user: bool # Note: this was is_assistant in the model, converted in from_orm
    created_at: str

    class Config:
        from_attributes = True

    @classmethod
    def from_orm(cls, message: Any): # Type hint 'Any' for message for flexibility, or use specific model if always the same
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
