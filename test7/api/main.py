#!/usr/bin/env python3
"""
Multi-RAG API Server

FastAPI-based REST API for document processing and embedding comparison.
"""

import os
import sys
from pathlib import Path
from typing import Dict, Any, List, Optional
import logging
import json
import tempfile
import shutil

from fastapi import FastAPI, HTTPException, UploadFile, File, Query, BackgroundTasks
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse, FileResponse
from pydantic import BaseModel

# Add parent directory to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from main import MultiRAGPipeline

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Initialize FastAPI app
app = FastAPI(
    title="Multi-RAG Document Pipeline API",
    description="Cross-platform pipeline for comparing Docling vs Microsoft RAG embeddings",
    version="1.0.0"
)

# Add CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Global pipeline instance
pipeline: Optional[MultiRAGPipeline] = None


# Pydantic models
class SearchRequest(BaseModel):
    query: str
    method: str = "docling"
    limit: int = 5


class ProcessingStatus(BaseModel):
    status: str
    message: str
    document_id: Optional[int] = None


class DocumentInfo(BaseModel):
    id: int
    file_name: str
    file_type: str
    file_size: int
    num_chunks: int
    processed_at: str


class SearchResult(BaseModel):
    similarity: float
    document: Dict[str, Any]
    chunk_metadata: Dict[str, Any]
    method_used: str


@app.on_event("startup")
async def startup_event():
    """Initialize the pipeline on startup."""
    global pipeline
    try:
        pipeline = MultiRAGPipeline()
        logger.info("Multi-RAG pipeline initialized successfully")
    except Exception as e:
        logger.error(f"Failed to initialize pipeline: {e}")
        raise


@app.get("/")
async def root():
    """Root endpoint with API information."""
    return {
        "name": "Multi-RAG Document Pipeline API",
        "version": "1.0.0",
        "description": "Cross-platform pipeline for comparing Docling vs Microsoft RAG embeddings",
        "endpoints": {
            "process": "/process",
            "search": "/search",
            "documents": "/documents",
            "stats": "/stats",
            "health": "/health"
        }
    }


@app.get("/health")
async def health_check():
    """Health check endpoint."""
    try:
        if pipeline is None:
            raise HTTPException(status_code=503, detail="Pipeline not initialized")
        
        stats = pipeline.get_pipeline_stats()
        return {
            "status": "healthy",
            "pipeline_ready": True,
            "database_documents": stats.get("database", {}).get("total_documents", 0),
            "vector_store_vectors": stats.get("vector_store", {}).get("total_vectors", 0)
        }
    except Exception as e:
        raise HTTPException(status_code=503, detail=f"Health check failed: {str(e)}")


@app.post("/process")
async def process_document(
    file: UploadFile = File(...),
    compare_methods: bool = Query(True, description="Whether to compare embedding methods"),
    background_tasks: BackgroundTasks = None
):
    """
    Process a document through the Multi-RAG pipeline.
    
    Args:
        file: Document file to process
        compare_methods: Whether to perform method comparison
        
    Returns:
        Processing results
    """
    if pipeline is None:
        raise HTTPException(status_code=503, detail="Pipeline not initialized")
    
    # Validate file type
    supported_extensions = [".pdf", ".txt", ".docx", ".pptx", ".jpg", ".jpeg", ".png"]
    file_extension = Path(file.filename).suffix.lower()
    
    if file_extension not in supported_extensions:
        raise HTTPException(
            status_code=400, 
            detail=f"Unsupported file type: {file_extension}. Supported: {supported_extensions}"
        )
    
    # Save uploaded file temporarily
    temp_dir = tempfile.mkdtemp()
    temp_file_path = Path(temp_dir) / file.filename
    
    try:
        # Save file
        with open(temp_file_path, "wb") as buffer:
            shutil.copyfileobj(file.file, buffer)
        
        # Process document
        result = pipeline.process_document(str(temp_file_path), compare_methods=compare_methods)
        
        # Clean up temporary file
        shutil.rmtree(temp_dir)
        
        return JSONResponse(content=result)
        
    except Exception as e:
        # Clean up on error
        if temp_dir and Path(temp_dir).exists():
            shutil.rmtree(temp_dir)
        raise HTTPException(status_code=500, detail=f"Processing failed: {str(e)}")


@app.post("/search", response_model=List[SearchResult])
async def search_documents(request: SearchRequest):
    """
    Search for similar documents using specified embedding method.
    
    Args:
        request: Search request with query, method, and limit
        
    Returns:
        List of similar documents
    """
    if pipeline is None:
        raise HTTPException(status_code=503, detail="Pipeline not initialized")
    
    try:
        results = pipeline.search_similar(
            query_text=request.query,
            method=request.method,
            k=request.limit
        )
        
        return results
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Search failed: {str(e)}")


@app.get("/documents", response_model=List[DocumentInfo])
async def list_documents(
    limit: int = Query(100, ge=1, le=1000, description="Number of documents to return"),
    offset: int = Query(0, ge=0, description="Number of documents to skip")
):
    """
    List processed documents with pagination.
    
    Args:
        limit: Number of documents to return
        offset: Number of documents to skip
        
    Returns:
        List of document information
    """
    if pipeline is None:
        raise HTTPException(status_code=503, detail="Pipeline not initialized")
    
    try:
        documents = pipeline.db_manager.list_documents(limit=limit, offset=offset)
        
        # Convert to response model format
        doc_info = []
        for doc in documents:
            doc_info.append({
                "id": doc["id"],
                "file_name": doc["file_name"],
                "file_type": doc["file_type"],
                "file_size": doc["file_size"],
                "num_chunks": doc["num_chunks"],
                "processed_at": doc["processed_at"]
            })
        
        return doc_info
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to list documents: {str(e)}")


@app.get("/documents/{document_id}")
async def get_document(document_id: int):
    """
    Get detailed information about a specific document.
    
    Args:
        document_id: ID of the document
        
    Returns:
        Complete document information including embeddings and comparisons
    """
    if pipeline is None:
        raise HTTPException(status_code=503, detail="Pipeline not initialized")
    
    try:
        document = pipeline.db_manager.get_document(document_id)
        if not document:
            raise HTTPException(status_code=404, detail="Document not found")
        
        embeddings = pipeline.db_manager.get_embeddings(document_id)
        comparison = pipeline.db_manager.get_comparison(document_id)
        
        return {
            "document": document,
            "embeddings": embeddings,
            "comparison": comparison
        }
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to get document: {str(e)}")


@app.get("/documents/{document_id}/export")
async def export_document(document_id: int):
    """
    Export complete document results as JSON file.
    
    Args:
        document_id: ID of the document to export
        
    Returns:
        JSON file with complete document results
    """
    if pipeline is None:
        raise HTTPException(status_code=503, detail="Pipeline not initialized")
    
    try:
        document = pipeline.db_manager.get_document(document_id)
        if not document:
            raise HTTPException(status_code=404, detail="Document not found")
        
        # Create temporary export file
        temp_dir = tempfile.mkdtemp()
        export_path = Path(temp_dir) / f"document_{document_id}_export.json"
        
        pipeline.export_results(document_id, str(export_path))
        
        return FileResponse(
            path=str(export_path),
            filename=f"document_{document_id}_export.json",
            media_type="application/json"
        )
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Export failed: {str(e)}")


@app.delete("/documents/{document_id}")
async def delete_document(document_id: int):
    """
    Delete a document and all its associated data.
    
    Args:
        document_id: ID of the document to delete
        
    Returns:
        Deletion confirmation
    """
    if pipeline is None:
        raise HTTPException(status_code=503, detail="Pipeline not initialized")
    
    try:
        # Check if document exists
        document = pipeline.db_manager.get_document(document_id)
        if not document:
            raise HTTPException(status_code=404, detail="Document not found")
        
        # Delete from vector store
        pipeline.vector_store.delete_document(f"doc_{document_id}_docling")
        pipeline.vector_store.delete_document(f"doc_{document_id}_microsoft")
        
        # Delete from database
        success = pipeline.db_manager.delete_document(document_id)
        
        if success:
            return {"status": "deleted", "document_id": document_id}
        else:
            raise HTTPException(status_code=500, detail="Failed to delete document")
            
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Deletion failed: {str(e)}")


@app.get("/stats")
async def get_stats():
    """
    Get comprehensive pipeline statistics.
    
    Returns:
        Pipeline statistics including database and vector store info
    """
    if pipeline is None:
        raise HTTPException(status_code=503, detail="Pipeline not initialized")
    
    try:
        stats = pipeline.get_pipeline_stats()
        return stats
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to get stats: {str(e)}")


@app.get("/compare/{document_id}")
async def get_comparison(document_id: int):
    """
    Get embedding comparison results for a document.
    
    Args:
        document_id: ID of the document
        
    Returns:
        Comparison results
    """
    if pipeline is None:
        raise HTTPException(status_code=503, detail="Pipeline not initialized")
    
    try:
        comparison = pipeline.db_manager.get_comparison(document_id)
        if not comparison:
            raise HTTPException(status_code=404, detail="Comparison not found for this document")
        
        return comparison
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to get comparison: {str(e)}")


if __name__ == "__main__":
    import uvicorn
    
    # Configuration
    host = os.getenv("API_HOST", "0.0.0.0")
    port = int(os.getenv("API_PORT", "8000"))
    
    # Run server
    uvicorn.run(
        "api.main:app",
        host=host,
        port=port,
        reload=False,
        log_level="info"
    )