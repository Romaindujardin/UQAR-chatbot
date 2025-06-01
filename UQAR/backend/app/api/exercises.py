from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from ..core.database import get_db
from ..models.user import User
from .auth import get_current_active_user

router = APIRouter()


@router.get("/")
async def get_exercises(
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
):
    """Obtenir la liste des exercices"""
    return {"message": "Exercises endpoint - à implémenter"}


@router.post("/generate")
async def generate_exercises(
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
):
    """Générer des exercices automatiquement"""
    return {"message": "Generate exercises endpoint - à implémenter"} 