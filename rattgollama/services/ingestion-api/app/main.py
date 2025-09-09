import os
import uuid
from fastapi import FastAPI, Depends, HTTPException, status, UploadFile, File
from fastapi.middleware.cors import CORSMiddleware
from sqlalchemy.orm import Session
from qdrant_client import QdrantClient
from qdrant_client.models import Filter, FieldCondition, MatchValue
from typing import List
import requests

from .db import get_db, create_tables
from .models import User, Document, Embedding
from .schemas import (
    LoginRequest, LoginResponse, DocumentResponse, 
    SearchRequest, SearchResponse, SearchResult, ReindexRequest,
    UserCreateRequest, UserResponse
)
from .auth import verify_password, create_access_token, get_password_hash
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
OLLAMA_HOST = os.getenv("OLLAMA_HOST", "localhost")
OLLAMA_PORT = int(os.getenv("OLLAMA_PORT", "11434"))
EMBEDDING_MODEL = os.getenv("EMBEDDING_MODEL", "nomic-embed-text")
COLLECTION_NAME = os.getenv("QDRANT_COLLECTION", "documents")

@app.on_event("startup")
async def startup_event():
    create_tables()
    ensure_bucket_exists()

def get_qdrant_client():
    return QdrantClient(host=QDRANT_HOST, port=QDRANT_PORT)

def get_query_embedding(text: str) -> List[float]:
    try:
        url = f"http://{OLLAMA_HOST}:{OLLAMA_PORT}/api/embeddings"
        resp = requests.post(url, json={"model": EMBEDDING_MODEL, "prompt": text}, timeout=30)
        resp.raise_for_status()
        data = resp.json()
        return data.get("embedding")
    except Exception as e:
        print(f"Error getting embedding from Ollama: {e}")
        return None

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
    query = search_request.query.strip()
    if not query:
        return SearchResponse(results=[], total=0)

    embedding = get_query_embedding(query)
    if not embedding:
        # Gracefully degrade with empty result set
        return SearchResponse(results=[], total=0)

    client = get_qdrant_client()
    try:
        qdrant_results = client.search(
            collection_name=COLLECTION_NAME,
            query_vector=embedding,
            limit=search_request.limit,
            with_payload=True
        )
    except Exception as e:
        print(f"Error querying Qdrant: {e}")
        return SearchResponse(results=[], total=0)

    results: List[SearchResult] = []
    for r in qdrant_results:
        payload = r.payload or {}
        doc_id = payload.get("document_id")
        if doc_id is None:
            continue
        # Enforce per-user access by checking document ownership
        doc = db.query(Document).filter(Document.id == doc_id, Document.user_id == current_user.id).first()
        if not doc:
            continue
        results.append(SearchResult(
            content=payload.get("content", ""),
            score=float(r.score) if hasattr(r, 'score') else 0.0,
            document_id=doc_id,
            filename=payload.get("filename", doc.original_filename),
            chunk_index=int(payload.get("chunk_index", 0))
        ))

    return SearchResponse(results=results, total=len(results))

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

@app.post("/admin/users", response_model=UserResponse)
async def create_user(
    user_request: UserCreateRequest,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    # Only admin users can create users
    if current_user.roles != "admin":
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Only administrators can create users"
        )
    
    # Check if user already exists
    existing_user = db.query(User).filter(User.username == user_request.username).first()
    if existing_user:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Username already exists"
        )
    
    # Create new user
    hashed_password = get_password_hash(user_request.password)
    new_user = User(
        username=user_request.username,
        password_hash=hashed_password,
        roles=user_request.roles
    )
    
    db.add(new_user)
    db.commit()
    db.refresh(new_user)
    
    return UserResponse(
        id=new_user.id,
        username=new_user.username,
        roles=new_user.roles,
        created_at=new_user.created_at
    )

@app.get("/admin/users", response_model=List[UserResponse])
async def list_users(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    # Only admin users can list users
    if current_user.roles != "admin":
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Only administrators can list users"
        )
    
    users = db.query(User).all()
    return [
        UserResponse(
            id=user.id,
            username=user.username,
            roles=user.roles,
            created_at=user.created_at
        )
        for user in users
    ]

@app.delete("/admin/users/{username}")
async def delete_user(
    username: str,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    # Only admin users can delete users
    if current_user.roles != "admin":
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Only administrators can delete users"
        )
    
    # Prevent deleting yourself
    if current_user.username == username:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Cannot delete your own account"
        )
    
    user = db.query(User).filter(User.username == username).first()
    if not user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="User not found"
        )
    
    db.delete(user)
    db.commit()
    
    return {"message": f"User '{username}' deleted successfully"}

@app.get("/health")
async def health_check():
    return {"status": "healthy"}

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
