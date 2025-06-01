from pydantic_settings import BaseSettings
from typing import Optional, List
import os


class Settings(BaseSettings):
    # Application
    APP_NAME: str = "Assistant Éducatif UQAR"
    APP_VERSION: str = "1.0.0"
    DEBUG: bool = True
    
    # Base de données PostgreSQL
    DATABASE_URL: str = os.environ.get("DATABASE_URL", "postgresql://uqar_user:uqar_password@10.0.30.51:38705/uqar_db")
    
    # ChromaDB
    CHROMA_HOST: str = os.environ.get("CHROMA_HOST", "10.0.30.51")
    CHROMA_PORT: int = int(os.environ.get("CHROMA_PORT", 8001))
    CHROMA_PERSIST_DIRECTORY: str = "./chroma_data"
    
    # Ollama (remplace vLLM pour Apple Silicon)
    OLLAMA_HOST: str = os.environ.get("OLLAMA_HOST", "127.0.0.1")
    OLLAMA_PORT: int = int(os.environ.get("OLLAMA_PORT", 11434))
    OLLAMA_MODEL: str = os.environ.get("OLLAMA_MODEL", "llama3")
    
    # Serveur de fichiers
    UPLOAD_FOLDER: str = "./uploads"
    MAX_CONTENT_LENGTH: int = 50 * 1024 * 1024  # 50 MB
    ALLOWED_EXTENSIONS: List[str] = ["pdf", "txt", "docx", "pptx", "xlsx"]
    
    # Sécurité
    SECRET_KEY: str = os.environ.get("SECRET_KEY", "secret-key-for-dev-only")
    ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 60 * 24 * 7  # 7 jours
    
    # Journalisation
    LOG_LEVEL: str = os.environ.get("LOG_LEVEL", "INFO")
    LOG_FILE: str = os.environ.get("LOG_FILE", "./logs/app.log")
    
    # Utilisateurs par défaut
    DEFAULT_ADMIN_EMAIL: str = os.environ.get("DEFAULT_ADMIN_EMAIL", "admin@uqar.ca")
    DEFAULT_ADMIN_PASSWORD: str = os.environ.get("DEFAULT_ADMIN_PASSWORD", "adminpassword")
    DEFAULT_USER_EMAIL: str = os.environ.get("DEFAULT_USER_EMAIL", "etudiant@uqar.ca")
    DEFAULT_USER_PASSWORD: str = os.environ.get("DEFAULT_USER_PASSWORD", "etudiantpassword")
    
    class Config:
        env_file = ".env"
        env_file_encoding = "utf-8"

settings = Settings() 