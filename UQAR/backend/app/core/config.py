from pydantic_settings import BaseSettings
from typing import Optional, List
import os


class Settings(BaseSettings):
    # Application
    APP_NAME: str = "Assistant Éducatif UQAR"
    APP_VERSION: str = "1.0.0"
    DEBUG: bool = True
    
    # Base de données PostgreSQL
    DATABASE_URL: str = os.environ.get("DATABASE_URL", "postgresql://dujr0001:URJvSIG0fm@localhost:5432/uqar_db")    
    # ChromaDB
    CHROMA_HOST: str = os.environ.get("CHROMA_HOST", "localhost")
    CHROMA_PORT: int = int(os.environ.get("CHROMA_PORT", 8001))
    CHROMA_PERSIST_DIRECTORY: str = "./chroma_data"
    
    # Ollama (remplace vLLM pour Apple Silicon)
    OLLAMA_HOST: str = os.environ.get("OLLAMA_HOST", "127.0.0.1")
    OLLAMA_PORT: int = int(os.environ.get("OLLAMA_PORT", 11434))
    OLLAMA_MODEL: str = os.environ.get("OLLAMA_MODEL", "llama3.1:70b")
    OLLAMA_MAX_TOKENS: int = 2048
    OLLAMA_TEMPERATURE: float = 0.7
    
    # JWT et sécurité
    JWT_SECRET_KEY: str = os.environ.get("JWT_SECRET_KEY", "af477b8d25c0527311f097b7098bf98c60b34a6030294231574358ee4ecf4822")
    JWT_ALGORITHM: str = "HS256"
    JWT_ACCESS_TOKEN_EXPIRE_MINUTES: int = 30
    JWT_REFRESH_TOKEN_EXPIRE_DAYS: int = 7
    
    # Embeddings (modèle plus léger pour M1)
    EMBEDDING_MODEL: str = "sentence-transformers/all-MiniLM-L6-v2"
    EMBEDDING_DIMENSION: int = 384
    
    # Upload de fichiers
    UPLOAD_DIR: str = "./uploads"
    MAX_FILE_SIZE: int = 50 * 1024 * 1024  # 50MB
    ALLOWED_EXTENSIONS: str = ".pdf,.docx,.pptx,.txt,.md"
    
    # Pagination
    DEFAULT_PAGE_SIZE: int = 20
    MAX_PAGE_SIZE: int = 100
    
    # Rate limiting
    RATE_LIMIT_PER_MINUTE: int = 60
    
    # Logging
    LOG_LEVEL: str = "INFO"
    LOG_FILE: str = "./logs/app.log"
    
    # CORS
    ALLOWED_ORIGINS: str = os.environ.get("ALLOWED_ORIGINS", "http://localhost:3000,http://127.0.0.1:3000,http://localhost,http://10.0.30.51:3000,*")
    
    class Config:
        env_file = ".env"
        case_sensitive = True
    
    def get_allowed_extensions(self) -> List[str]:
        """Retourne la liste des extensions autorisées"""
        return [ext.strip() for ext in self.ALLOWED_EXTENSIONS.split(",")]
    
    def get_allowed_origins(self) -> List[str]:
        """Retourne la liste des origines autorisées"""
        return [origin.strip() for origin in self.ALLOWED_ORIGINS.split(",")]


# Instance globale des paramètres
settings = Settings()


# Configuration de la base de données
def get_database_url() -> str:
    return settings.DATABASE_URL


# Configuration ChromaDB
def get_chroma_config() -> dict:
    return {
        "host": settings.CHROMA_HOST,
        "port": settings.CHROMA_PORT,
        "persist_directory": settings.CHROMA_PERSIST_DIRECTORY
    }


# Configuration Ollama
def get_ollama_config() -> dict:
    return {
        "base_url": f"http://{settings.OLLAMA_HOST}:{settings.OLLAMA_PORT}",
        "model": settings.OLLAMA_MODEL,
        "max_tokens": settings.OLLAMA_MAX_TOKENS,
        "temperature": settings.OLLAMA_TEMPERATURE
    } 