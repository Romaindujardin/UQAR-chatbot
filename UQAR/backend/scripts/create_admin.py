#!/usr/bin/env python3
"""
Script pour créer un utilisateur super_admin dans la base de données SQLite.
Ce script est utile pour la première initialisation de la base de données.
"""

import sys
import os
import logging
from datetime import datetime
from pathlib import Path

# Ajouter le répertoire parent au chemin d'importation
sys.path.insert(0, str(Path(__file__).parent.parent))

# Configurer le logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

# Importer les modules nécessaires
from app.core.database import SessionLocal, Base, engine
from app.models.user import User
from app.core.security import get_password_hash
from sqlalchemy.exc import IntegrityError

def create_admin_user():
    """Créer un utilisateur super_admin dans la base de données"""
    
    # Informations de l'utilisateur admin
    admin_data = {
        "username": "admin",
        "email": "admin@gmail.com",
        "first_name": "Romain",
        "last_name": "Dujardin",
        "password": "@Azerty123",
        "role": "SUPER_ADMIN",
        "status": "ACTIVE"
    }
    
    # Créer les tables si elles n'existent pas
    logger.info("Création des tables si elles n'existent pas...")
    Base.metadata.create_all(bind=engine)
    
    # Créer une session
    db = SessionLocal()
    
    try:
        # Vérifier si l'utilisateur existe déjà
        existing_user = db.query(User).filter(User.username == admin_data["username"]).first()
        
        if existing_user:
            logger.info(f"L'utilisateur {admin_data['username']} existe déjà!")
            # Mettre à jour le statut si nécessaire
            if existing_user.status != "ACTIVE":
                existing_user.status = "ACTIVE"
                db.commit()
                logger.info(f"Le statut de l'utilisateur {admin_data['username']} a été mis à jour à 'ACTIVE'.")
            return
        
        # Créer un nouvel utilisateur
        hashed_password = get_password_hash(admin_data["password"])
        
        admin_user = User(
            username=admin_data["username"],
            email=admin_data["email"],
            first_name=admin_data["first_name"],
            last_name=admin_data["last_name"],
            hashed_password=hashed_password,
            role=admin_data["role"],
            status=admin_data["status"],
            created_at=datetime.utcnow()
        )
        
        db.add(admin_user)
        db.commit()
        
        logger.info(f"Utilisateur super_admin '{admin_data['username']}' créé avec succès!")
        logger.info(f"Email: {admin_data['email']}")
        logger.info(f"Mot de passe: {admin_data['password']}")
        
    except IntegrityError as e:
        db.rollback()
        logger.error(f"Erreur d'intégrité: {e}")
    except Exception as e:
        db.rollback()
        logger.error(f"Erreur lors de la création de l'utilisateur: {e}")
    finally:
        db.close()

if __name__ == "__main__":
    logger.info("Début de la création de l'utilisateur super_admin...")
    create_admin_user()
    logger.info("Fin du script.") 