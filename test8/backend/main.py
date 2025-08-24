from fastapi import FastAPI, File, UploadFile, HTTPException, Depends
from fastapi.middleware.cors import CORSMiddleware
from sqlalchemy.orm import Session
import asyncio
from pathlib import Path
import tempfile
import os
from typing import List, Optional
import uuid
import logging
import traceback

from database import get_db, init_db
from models import Document, VectorChunk
from schemas import DocumentResponse, ChatRequest, ChatResponse, DocumentListResponse
from services.document_service import DocumentService
from services.chat_service import ChatService

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

app = FastAPI(
    title="RAG Backend API", 
    version="1.0.0",
    # Increase request size limits for large PDFs
    docs_url="/docs",
    redoc_url="/redoc"
)

# CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Initialize database on startup
@app.on_event("startup")
async def startup_event():
    init_db()

@app.get("/")
async def root():
    return {"message": "RAG Backend API is running"}

@app.get("/health")
async def health_check():
    return {"status": "healthy"}

# Document management endpoints
@app.post("/documents/upload", response_model=DocumentResponse)
async def upload_document(
    file: UploadFile = File(...),
    db: Session = Depends(get_db)
):
    """Upload and process a document"""
    logger.info(f"Starting upload for file: {file.filename}, size: {file.size if hasattr(file, 'size') else 'unknown'}")
    
    if not file.filename.endswith('.pdf'):
        raise HTTPException(status_code=400, detail="Only PDF files are supported")
    
    tmp_path = None
    try:
        # Save uploaded file temporarily
        with tempfile.NamedTemporaryFile(delete=False, suffix=".pdf") as tmp_file:
            content = await file.read()
            logger.info(f"Read {len(content)} bytes from uploaded file")
            tmp_file.write(content)
            tmp_path = Path(tmp_file.name)
        
        logger.info(f"Saved file to temporary path: {tmp_path}")
        
        # Process document
        doc_service = DocumentService(db)
        document = await doc_service.process_document(
            file_path=tmp_path,
            filename=file.filename,
            content_type=file.content_type or "application/pdf"
        )
        
        # Clean up temp file
        os.unlink(tmp_path)
        logger.info(f"Document processed successfully: {document.id}")
        
        return DocumentResponse(
            id=document.id,
            filename=document.filename,
            status=document.status,
            created_at=document.created_at,
            chunk_count=len(document.chunks)
        )
        
    except Exception as e:
        logger.error(f"Document processing failed: {str(e)}")
        logger.error(f"Traceback: {traceback.format_exc()}")
        
        # Clean up temp file if it exists
        if tmp_path and tmp_path.exists():
            try:
                os.unlink(tmp_path)
            except Exception as cleanup_error:
                logger.error(f"Failed to cleanup temp file: {cleanup_error}")
        
        raise HTTPException(status_code=500, detail=f"Document processing failed: {str(e)}")

@app.get("/documents", response_model=DocumentListResponse)
async def list_documents(db: Session = Depends(get_db)):
    """List all uploaded documents"""
    doc_service = DocumentService(db)
    documents = doc_service.list_documents()
    
    return DocumentListResponse(
        documents=[
            DocumentResponse(
                id=doc.id,
                filename=doc.filename,
                status=doc.status,
                created_at=doc.created_at,
                chunk_count=len(doc.chunks)
            ) for doc in documents
        ]
    )

@app.get("/documents/{document_id}", response_model=DocumentResponse)
async def get_document(document_id: str, db: Session = Depends(get_db)):
    """Get document details"""
    doc_service = DocumentService(db)
    document = doc_service.get_document(document_id)
    
    if not document:
        raise HTTPException(status_code=404, detail="Document not found")
    
    return DocumentResponse(
        id=document.id,
        filename=document.filename,
        status=document.status,
        created_at=document.created_at,
        chunk_count=len(document.chunks)
    )

@app.delete("/documents/{document_id}")
async def delete_document(document_id: str, db: Session = Depends(get_db)):
    """Delete a document and its embeddings"""
    doc_service = DocumentService(db)
    success = doc_service.delete_document(document_id)
    
    if not success:
        raise HTTPException(status_code=404, detail="Document not found")
    
    return {"message": "Document deleted successfully"}

# Chat endpoints
@app.post("/chat/document", response_model=ChatResponse)
async def chat_with_document(
    request: ChatRequest,
    db: Session = Depends(get_db)
):
    """Chat with a specific document using RAG"""
    if not request.document_id:
        raise HTTPException(status_code=400, detail="Document ID is required for document chat")
    
    chat_service = ChatService(db)
    response = await chat_service.chat_with_document(
        message=request.message,
        document_id=request.document_id,
        model=request.model,
        top_k=request.top_k
    )
    
    return ChatResponse(
        response=response,
        document_id=request.document_id
    )

@app.post("/chat/general", response_model=ChatResponse)
async def general_chat(request: ChatRequest):
    """General chat without document context"""
    chat_service = ChatService(None)
    response = await chat_service.general_chat(
        message=request.message,
        model=request.model
    )
    
    return ChatResponse(response=response)

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)