from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from pydantic import BaseModel
from typing import List, Optional

from ..core.database import get_db
from ..models.user import User, UserRole, UserStatus
from .auth import get_current_active_user, require_role

router = APIRouter()


# Schémas Pydantic
class UserResponse(BaseModel):
    id: int
    username: str
    email: str
    full_name: str
    role: str
    status: str
    created_at: Optional[str] = None
    last_login: Optional[str] = None

    class Config:
        from_attributes = True
        
    @classmethod
    def from_orm(cls, obj):
        # Convert datetime objects to strings
        data = {
            "id": obj.id,
            "username": obj.username,
            "email": obj.email,
            "full_name": obj.full_name,
            "role": obj.role.value if hasattr(obj.role, 'value') else str(obj.role),
            "status": obj.status.value if hasattr(obj.status, 'value') else str(obj.status),
            "created_at": obj.created_at.isoformat() if obj.created_at else None,
            "last_login": obj.last_login.isoformat() if obj.last_login else None
        }
        return cls(**data)


class UserUpdate(BaseModel):
    status: Optional[UserStatus] = None
    role: Optional[UserRole] = None


# Routes
@router.get("/pending", response_model=List[UserResponse])
async def get_pending_users(
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
):
    """Obtenir la liste des utilisateurs en attente de validation"""
    # Check if user is super_admin
    print(f"Pending users request from: {current_user.username}, role={current_user.role}")
    
    # Accept both enum and string value
    is_admin = (current_user.role == UserRole.SUPER_ADMIN or 
                (hasattr(current_user.role, 'value') and current_user.role.value == 'super_admin') or
                current_user.role == 'super_admin')
    
    if not is_admin:
        print(f"User {current_user.username} is not admin: {current_user.role}")
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Permissions insuffisantes"
        )
        
    pending_users = db.query(User).filter(User.status == UserStatus.PENDING).all()
    print(f"Found {len(pending_users)} pending users")
    # Convert each user to UserResponse object
    return [UserResponse.from_orm(user) for user in pending_users]


@router.patch("/{user_id}/validate")
async def validate_user(
    user_id: int,
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
):
    """Valider un utilisateur en attente"""
    # Check if user is super_admin
    is_admin = (current_user.role == UserRole.SUPER_ADMIN or 
                (hasattr(current_user.role, 'value') and current_user.role.value == 'super_admin') or
                current_user.role == 'super_admin')
    
    if not is_admin:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Permissions insuffisantes"
        )
        
    user = db.query(User).filter(User.id == user_id).first()
    
    if not user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Utilisateur non trouvé"
        )
    
    if user.status != UserStatus.PENDING:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="L'utilisateur n'est pas en attente de validation"
        )
    
    user.status = UserStatus.ACTIVE
    db.commit()
    
    return {"message": f"Utilisateur {user.username} validé avec succès"}


@router.get("/", response_model=List[UserResponse])
async def get_all_users(
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
):
    """Obtenir la liste de tous les utilisateurs"""
    # Check if user is super_admin
    is_admin = (current_user.role == UserRole.SUPER_ADMIN or 
                (hasattr(current_user.role, 'value') and current_user.role.value == 'super_admin') or
                current_user.role == 'super_admin')
    
    if not is_admin:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Permissions insuffisantes"
        )
        
    users = db.query(User).all()
    # Convert each user to a UserResponse object using from_orm
    return [UserResponse.from_orm(user) for user in users]


@router.patch("/{user_id}")
async def update_user(
    user_id: int,
    user_update: UserUpdate,
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
):
    """Mettre à jour un utilisateur"""
    # Check if user is super_admin
    is_admin = (current_user.role == UserRole.SUPER_ADMIN or 
                (hasattr(current_user.role, 'value') and current_user.role.value == 'super_admin') or
                current_user.role == 'super_admin')
    
    if not is_admin:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Permissions insuffisantes"
        )
        
    user = db.query(User).filter(User.id == user_id).first()
    
    if not user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Utilisateur non trouvé"
        )
    
    if user_update.status is not None:
        user.status = user_update.status
    
    if user_update.role is not None:
        user.role = user_update.role
    
    db.commit()
    
    return {"message": f"Utilisateur {user.username} mis à jour avec succès"} 