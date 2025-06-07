from fastapi import APIRouter, Depends, HTTPException, status, UploadFile, File, Form
from sqlalchemy.orm import Session
from typing import List, Optional
from starlette.responses import FileResponse
from pydantic import BaseModel

from ..core.database import get_db
from ..models.user import User
from ..models.document import Document, DocumentStatus
from ..services.document_service import DocumentService
from .auth import get_current_active_user

router = APIRouter()


# Schémas Pydantic
class DocumentResponse(BaseModel):
    id: int
    original_filename: str
    file_size: int
    document_type: str
    status: str
    is_vectorized: bool
    uploaded_at: str
    page_count: Optional[int] = None
    vector_count: Optional[int] = None
    
    class Config:
        from_attributes = True
        
    @classmethod
    def from_orm(cls, obj):
        # Convert document to dict with string values
        return cls(
            id=obj.id,
            original_filename=obj.original_filename,
            file_size=obj.file_size,
            document_type=obj.document_type.value if hasattr(obj.document_type, 'value') else str(obj.document_type),
            status=obj.status.value if hasattr(obj.status, 'value') else str(obj.status),
            is_vectorized=obj.is_vectorized,
            uploaded_at=obj.uploaded_at.isoformat() if obj.uploaded_at else None,
            page_count=obj.page_count,
            vector_count=obj.vector_count
        )


# Routes
@router.get("/section/{section_id}", response_model=List[DocumentResponse])
async def get_section_documents(
    section_id: int,
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
):
    """Obtenir la liste des documents d'une section"""
    document_service = DocumentService(db)
    
    try:
        documents = document_service.get_section_documents(section_id)
        return [DocumentResponse.from_orm(doc) for doc in documents]
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Erreur lors de la récupération des documents: {str(e)}"
        )


@router.post("/upload", response_model=DocumentResponse)
async def upload_document(
    file: UploadFile = File(...),
    section_id: int = Form(...),
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
):
    """Upload d'un document dans une section"""
    document_service = DocumentService(db)
    
    try:
        document = await document_service.upload_document(
            file=file,
            section_id=section_id,
            user_id=current_user.id
        )
        
        return DocumentResponse.from_orm(document)
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Erreur lors de l'upload du document: {str(e)}"
        )


@router.get("/{document_id}", response_model=DocumentResponse)
async def get_document(
    document_id: int,
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
):
    """Obtenir les détails d'un document"""
    document_service = DocumentService(db)
    
    document = document_service.get_document(document_id)
    if not document:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Document non trouvé"
        )
    
    return DocumentResponse.from_orm(document)


@router.delete("/{document_id}")
async def delete_document(
    document_id: int,
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
):
    """Supprimer un document"""
    document_service = DocumentService(db)
    
    try:
        success = document_service.delete_document(
            document_id=document_id,
            user_id=current_user.id
        )
        
        if not success:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Document non trouvé"
            )
        
        return {"message": "Document supprimé avec succès"}
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail=str(e)
        )
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Erreur lors de la suppression du document: {str(e)}"
        ) 

@router.get("/download/{document_id}")
async def download_document(
    document_id: int,
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
):
    """Télécharger un document"""
    document_service = DocumentService(db)

    try:
        file_path, original_filename = document_service.get_document_filepath(document_id)

        if not file_path or not original_filename:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Document non trouvé ou nom de fichier manquant"
            )
        
        # Assurez-vous que le fichier existe avant de tenter de le servir
        # Note: os.path.exists pourrait être utilisé ici si file_path est un chemin absolu
        # Pour cet exemple, nous supposons que get_document_filepath gère la validité du chemin

        return FileResponse(
            path=file_path,
            filename=original_filename,
            media_type='application/octet-stream'  # Ou un type MIME plus spécifique si connu
        )
    except FileNotFoundError: # Potentiellement levé par FileResponse si le chemin n'est pas valide
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Fichier non trouvé sur le serveur"
        )
    except ValueError as e: # Au cas où get_document_filepath lèverait une ValueError pour un ID non trouvé
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=str(e)
        )
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Erreur lors du téléchargement du document: {str(e)}"
        )