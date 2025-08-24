import os
import uuid
from fastapi import FastAPI, Depends, HTTPException, status, UploadFile, File
from fastapi.middleware.cors import CORSMiddleware
from sqlalchemy.orm import Session
from qdrant_client import QdrantClient
from typing import List

from .db import get_db, create_tables
from .models import User, Document, Embedding
from .schemas import (
    LoginRequest, LoginResponse, DocumentResponse, 
    SearchRequest, SearchResponse, SearchResult, ReindexRequest
)
from .auth import verify_password, create_access_token
from .deps import get_current_user
from .storage import upload_file, ensure_bucket_exists

app = FastAPI(title="RattGoLLAMA Ingestion API", version="1.0.0")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

QDRANT_HOST = os.getenv("QDRANT_HOST", "localhost")
QDRANT_PORT = int(os.getenv("QDRANT_PORT", "6333"))

@app.on_event("startup")
async def startup_event():
    create_tables()
    ensure_bucket_exists()

def get_qdrant_client():
    return QdrantClient(host=QDRANT_HOST, port=QDRANT_PORT)

@app.post("/auth/login", response_model=LoginResponse)
async def login(login_request: LoginRequest, db: Session = Depends(get_db)):
    user = db.query(User).filter(User.username == login_request.username).first()
    
    if not user or not verify_password(login_request.password, user.password_hash):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect username or password",
            headers={"WWW-Authenticate": "Bearer"},
        )
    
    access_token = create_access_token(
        data={"sub": user.id, "username": user.username, "roles": user.roles}
    )
    
    return LoginResponse(
        access_token=access_token,
        token_type="bearer",
        user_id=user.id,
        username=user.username,
        roles=user.roles
    )

@app.post("/upload", response_model=DocumentResponse)
async def upload_document(
    file: UploadFile = File(...),
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    if not file.filename:
        raise HTTPException(status_code=400, detail="No file selected")
    
    # Generate unique filename
    file_extension = file.filename.split('.')[-1] if '.' in file.filename else ''
    unique_filename = f"{uuid.uuid4()}.{file_extension}" if file_extension else str(uuid.uuid4())
    
    # Upload to MinIO
    file.file.seek(0)
    if not upload_file(file.file, unique_filename):
        raise HTTPException(status_code=500, detail="Failed to upload file")
    
    # Save metadata to database
    document = Document(
        filename=unique_filename,
        original_filename=file.filename,
        content_type=file.content_type or "application/octet-stream",
        size=file.size or 0,
        user_id=current_user.id,
        s3_key=unique_filename,
        status="pending"
    )
    
    db.add(document)
    db.commit()
    db.refresh(document)
    
    return DocumentResponse(
        id=document.id,
        filename=document.filename,
        original_filename=document.original_filename,
        content_type=document.content_type,
        size=document.size,
        status=document.status,
        created_at=document.created_at,
        processed_at=document.processed_at,
        error_message=document.error_message
    )

@app.get("/documents", response_model=List[DocumentResponse])
async def list_documents(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    documents = db.query(Document).filter(Document.user_id == current_user.id).all()
    
    return [
        DocumentResponse(
            id=doc.id,
            filename=doc.filename,
            original_filename=doc.original_filename,
            content_type=doc.content_type,
            size=doc.size,
            status=doc.status,
            created_at=doc.created_at,
            processed_at=doc.processed_at,
            error_message=doc.error_message
        )
        for doc in documents
    ]

@app.post("/search", response_model=SearchResponse)
async def search_documents(
    search_request: SearchRequest,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    # This is a simplified search - in production, you'd use Qdrant for vector search
    # For now, return empty results
    return SearchResponse(results=[], total=0)

@app.post("/ingest/reindex")
async def trigger_reindex(
    reindex_request: ReindexRequest,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    # Mark documents for reprocessing
    query = db.query(Document).filter(Document.user_id == current_user.id)
    
    if reindex_request.document_id:
        query = query.filter(Document.id == reindex_request.document_id)
    
    documents = query.all()
    
    for doc in documents:
        doc.status = "pending"
    
    db.commit()
    
    return {"message": f"Reindexing triggered for {len(documents)} documents"}

@app.get("/health")
async def health_check():
    return {"status": "healthy"}

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)