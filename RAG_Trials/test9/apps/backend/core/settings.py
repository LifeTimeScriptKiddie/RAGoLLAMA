from pydantic_settings import BaseSettings
from typing import Optional

class Settings(BaseSettings):
    # API Settings
    api_host: str = "0.0.0.0"
    api_port: int = 8000
    
    # Security
    jwt_secret_key: str = "your-secret-key-change-in-production"
    jwt_expire_minutes: int = 30
    
    # File upload
    max_file_size: int = 100 * 1024 * 1024  # 100MB
    upload_dir: str = "/data/raw_docs"
    
    # Vector store
    index_dir: str = "/data/index"
    cache_dir: str = "/data/cache"
    
    # Embedding
    embedding_model: str = "sentence-transformers/all-MiniLM-L6-v2"
    chunk_size: int = 512
    chunk_overlap: int = 50
    
    # Ollama
    ollama_host: str = "ollama"
    ollama_port: int = 11434
    ollama_model: str = "llama3.1:8b"
    
    # Database
    ledger_db_path: str = "/data/ledger.db"
    
    class Config:
        env_file = ".env"

settings = Settings()