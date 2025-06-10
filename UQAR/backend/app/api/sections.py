from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from pydantic import BaseModel
from typing import List, Optional
import logging

from ..core.database import get_db
from ..models.user import User, UserRole
from ..models.section import Section
from ..services.document_service import DocumentService
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


@router.delete("/{section_id}", status_code=status.HTTP_200_OK)
async def delete_section(
    section_id: int,
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
):
    """Supprimer une section de cours et tous les documents associés."""
    logger.info(f"Attempting to delete section {section_id} by user {current_user.id} ({current_user.role})")

    section = db.query(Section).filter(Section.id == section_id).first()

    if not section:
        logger.warning(f"Section {section_id} not found for deletion attempt by user {current_user.id}")
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Section non trouvée"
        )

    # Verify user role
    is_teacher = (current_user.role == UserRole.TEACHER or
                  (hasattr(current_user.role, 'value') and current_user.role.value == 'teacher'))
    is_super_admin = (current_user.role == UserRole.SUPER_ADMIN or
                      (hasattr(current_user.role, 'value') and current_user.role.value == 'super_admin'))

    if not (is_teacher or is_super_admin):
        logger.error(f"User {current_user.id} with role {current_user.role} forbidden to delete section {section_id}")
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Vous n'avez pas les droits pour supprimer cette section"
        )

    # Verify ownership if user is a teacher (not super_admin)
    if is_teacher and not is_super_admin and section.teacher_id != current_user.id:
        logger.error(f"Teacher {current_user.id} forbidden to delete section {section_id} owned by {section.teacher_id}")
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Vous ne pouvez supprimer que vos propres sections"
        )

    document_service = DocumentService(db=db)

    # Get and delete all documents associated with the section
    try:
        documents = document_service.get_section_documents(section_id=section_id)
        logger.info(f"Found {len(documents)} documents associated with section {section_id}")
        for doc in documents:
            logger.info(f"Deleting document {doc.id} from section {section_id}")
            # If current user is SUPER_ADMIN, they can delete any document,
            # so pass section.teacher_id to satisfy DocumentService's ownership check.
            # The actual authorization for SUPER_ADMIN is already done above.
            user_id_for_doc_deletion = section.teacher_id if is_super_admin else current_user.id
            document_service.delete_document(document_id=doc.id, user_id=user_id_for_doc_deletion)
        logger.info(f"Successfully deleted documents for section {section_id}")
    except Exception as e:
        logger.error(f"Error deleting documents for section {section_id}: {str(e)}", exc_info=True)
        # Not raising HTTPException here to allow section deletion attempt anyway,
        # but a more robust error handling might be needed depending on requirements.

    # Delete ChromaDB collection
    if section.chroma_collection_name and document_service.chroma_client:
        try:
            logger.info(f"Attempting to delete ChromaDB collection: {section.chroma_collection_name} for section {section_id}")
            document_service.chroma_client.delete_collection(name=section.chroma_collection_name)
            logger.info(f"Successfully deleted ChromaDB collection: {section.chroma_collection_name}")
        except Exception as e:
            logger.error(
                f"Error deleting ChromaDB collection {section.chroma_collection_name} for section {section_id}: {str(e)}",
                exc_info=True
            )
            # Do not block section deletion if collection deletion fails

    # Delete the section itself
    try:
        db.delete(section)
        db.commit()
        logger.info(f"Section {section_id} successfully deleted from database by user {current_user.id}")
        return {"message": "Section supprimée avec succès"}
    except Exception as e:
        db.rollback()
        logger.error(f"Error deleting section {section_id} from database: {str(e)}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Erreur lors de la suppression de la section: {str(e)}"
        )