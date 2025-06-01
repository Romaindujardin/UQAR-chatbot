from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from pydantic import BaseModel
from typing import List, Optional
import logging

from ..core.database import get_db
from ..models.user import User, UserRole
from ..models.section import Section
from .auth import get_current_active_user, require_role

router = APIRouter()
logger = logging.getLogger(__name__)


# Schémas Pydantic
class SectionCreate(BaseModel):
    name: str
    description: Optional[str] = None


class SectionResponse(BaseModel):
    id: int
    name: str
    description: Optional[str]
    is_active: bool
    document_count: int
    created_at: str

    class Config:
        from_attributes = True
        
    @classmethod
    def from_orm(cls, obj):
        # Convert datetime objects to strings
        data = {
            "id": obj.id,
            "name": obj.name,
            "description": obj.description,
            "is_active": obj.is_active,
            "document_count": getattr(obj, "document_count", 0),
            "created_at": obj.created_at.isoformat() if obj.created_at else None
        }
        return cls(**data)


# Routes
@router.post("/", response_model=SectionResponse)
async def create_section(
    section_data: SectionCreate,
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
):
    """Créer une nouvelle section de cours"""
    # Check if user is teacher or admin
    is_teacher = (current_user.role == UserRole.TEACHER or 
                 (hasattr(current_user.role, 'value') and current_user.role.value == 'teacher'))
    is_admin = (current_user.role == UserRole.SUPER_ADMIN or 
               (hasattr(current_user.role, 'value') and current_user.role.value == 'super_admin'))
    
    if not (is_teacher or is_admin):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Seuls les enseignants peuvent créer des sections"
        )
    
    # Générer un nom unique pour la collection ChromaDB
    import uuid
    chroma_collection_name = f"section_{uuid.uuid4().hex[:8]}"
    
    new_section = Section(
        name=section_data.name,
        description=section_data.description,
        teacher_id=current_user.id,
        chroma_collection_name=chroma_collection_name
    )
    
    db.add(new_section)
    db.commit()
    db.refresh(new_section)
    
    # Return using the from_orm method to handle datetime conversion
    return SectionResponse.from_orm(new_section)


@router.get("/", response_model=List[SectionResponse])
async def get_sections(
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
):
    """Obtenir les sections accessibles à l'utilisateur"""
    logger.info(f"Get sections called by user: {current_user.id} - {current_user.username} with role: {current_user.role}")
    
    try:
        is_teacher = (current_user.role == UserRole.TEACHER or 
                 (hasattr(current_user.role, 'value') and current_user.role.value == 'teacher'))
        is_admin = (current_user.role == UserRole.SUPER_ADMIN or 
               (hasattr(current_user.role, 'value') and current_user.role.value == 'super_admin'))
    
        logger.info(f"User roles: is_teacher={is_teacher}, is_admin={is_admin}")
        
        if is_teacher or is_admin:
            # Les enseignants voient leurs sections
            sections = db.query(Section).filter(Section.teacher_id == current_user.id).all()
            logger.info(f"Teacher/Admin: Found {len(sections)} sections created by this user")
        else:
            # Les étudiants voient toutes les sections actives
            sections = db.query(Section).filter(Section.is_active == True).all()
            logger.info(f"Student: Found {len(sections)} active sections")
        
            # Log section details for debugging
            for section in sections:
                logger.info(f"Section: id={section.id}, name={section.name}, active={section.is_active}, columns={section.__dict__}")
    
        # Convert to SectionResponse objects
        response_data = [SectionResponse.from_orm(section) for section in sections]
        logger.info(f"Converted {len(response_data)} sections to response objects")
        return response_data
    except Exception as e:
        logger.error(f"Error in get_sections: {str(e)}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error fetching sections: {str(e)}"
        )


@router.get("/{section_id}", response_model=SectionResponse)
async def get_section(
    section_id: int,
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
):
    """Obtenir une section spécifique"""
    section = db.query(Section).filter(Section.id == section_id).first()
    
    if not section:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Section non trouvée"
        )
    
    # Vérifier les permissions
    is_student = (current_user.role == UserRole.STUDENT or 
                 (hasattr(current_user.role, 'value') and current_user.role.value == 'student'))
    
    if is_student and not section.is_active:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Section non accessible"
        )
    
    # Convert to SectionResponse object
    return SectionResponse.from_orm(section) 