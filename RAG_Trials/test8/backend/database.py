from sqlalchemy import create_engine, text
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker
import os
from pathlib import Path

# Database configuration
DATABASE_URL = os.getenv("DATABASE_URL", "postgresql://rag_user:rag_password@postgres:5432/rag_db")

engine = create_engine(DATABASE_URL)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

Base = declarative_base()

def get_db():
    """Database session dependency"""
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

def init_db():
    """Initialize database and enable pgvector extension"""
    try:
        # Import models to ensure they're registered with Base
        from models import Document, VectorChunk
        
        # Enable pgvector extension first
        with engine.connect() as conn:
            conn.execute(text("CREATE EXTENSION IF NOT EXISTS vector"))
            conn.commit()
        
        # Create tables
        Base.metadata.create_all(bind=engine)
            
        print("Database initialized successfully")
    except Exception as e:
        print(f"Database initialization failed: {e}")
        raise