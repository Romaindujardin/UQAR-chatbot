from sqlalchemy.orm import Session
from typing import Optional, List

from ..models.user import User, UserRole, UserStatus
from ..core.security import get_password_hash, verify_password


class UserService:
    """Service pour la gestion des utilisateurs"""
    
    def __init__(self, db: Session):
        self.db = db
    
    def get_user_by_id(self, user_id: int) -> Optional[User]:
        """Obtenir un utilisateur par son ID"""
        return self.db.query(User).filter(User.id == user_id).first()
    
    def get_user_by_username(self, username: str) -> Optional[User]:
        """Obtenir un utilisateur par son nom d'utilisateur"""
        return self.db.query(User).filter(User.username == username).first()
    
    def get_user_by_email(self, email: str) -> Optional[User]:
        """Obtenir un utilisateur par son email"""
        return self.db.query(User).filter(User.email == email).first()
    
    def get_pending_users(self) -> List[User]:
        """Obtenir tous les utilisateurs en attente de validation"""
        return self.db.query(User).filter(User.status == UserStatus.PENDING).all()
    
    def validate_user(self, user_id: int) -> bool:
        """Valider un utilisateur en attente"""
        user = self.get_user_by_id(user_id)
        if user and user.status == UserStatus.PENDING:
            user.status = UserStatus.ACTIVE
            self.db.commit()
            return True
        return False
    
    def create_user(self, username: str, email: str, password: str, 
                   first_name: str, last_name: str, role: UserRole = UserRole.STUDENT) -> User:
        """Créer un nouveau utilisateur"""
        hashed_password = get_password_hash(password)
        
        new_user = User(
            username=username,
            email=email,
            hashed_password=hashed_password,
            first_name=first_name,
            last_name=last_name,
            role=role,
            status=UserStatus.PENDING
        )
        
        self.db.add(new_user)
        self.db.commit()
        self.db.refresh(new_user)
        
        return new_user
    
    def authenticate_user(self, username: str, password: str) -> Optional[User]:
        """Authentifier un utilisateur"""
        user = self.get_user_by_username(username)
        if user and verify_password(password, user.hashed_password):
            return user
        return None 