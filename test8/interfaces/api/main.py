"""
FastAPI REST API for Multi-RAG Document Pipeline

Provides HTTP endpoints for document processing, embedding comparison,
and retrieval operations.
"""

from fastapi import FastAPI, File, UploadFile, HTTPException, BackgroundTasks
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from typing import List, Optional, Dict, Any
import json
import tempfile
import os
from pathlib import Path

from core.document.processor import DocumentProcessor
from core.embedding.docling_embedder import DoclingEmbedder
from core.embedding.microsoft_embedder import MicrosoftEmbedder
from core.vector.faiss_store import FAISSVectorStore
from core.storage.sqlite_manager import SQLiteManager
from core.comparison.comparator import EmbeddingComparator

# Pydantic models
class SearchRequest(BaseModel):
    query: str
    method: str = "docling"
    top_k: int = 5
    document_id: Optional[int] = None

class SearchResult(BaseModel):
    vector_id: int
    similarity: float
    text: str
    metadata: Dict[str, Any]

class ProcessRequest(BaseModel):
    method: str = "both"
    compare: bool = True

class DocumentInfo(BaseModel):
    id: int
    file_name: str
    file_type: str
    file_size: int
    num_chunks: int
    processed_at: str

class ComparisonResult(BaseModel):
    document_id: int
    best_method: str
    summary: str
    metrics: Dict[str, Any]

class SystemStats(BaseModel):
    database: Dict[str, Any]
    vector_store: Dict[str, Any]

# Load configuration
def load_config():
    config_path = Path("config/config.json")
    if config_path.exists():
        with open(config_path) as f:
            return json.load(f)
    return {
        "db_path": "/app/cache/documents.db",
        "faiss_index_path": "/app/cache/faiss",
        "max_chunk_size": 1000,
        "chunk_overlap": 200,
        "dimension": 384,
        "supported_formats": [".pdf", ".txt", ".docx", ".pptx", ".jpg", ".png"]
    }

# Initialize FastAPI app
app = FastAPI(
    title="Multi-RAG Document Pipeline API",
    description="REST API for document processing and embedding comparison",
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

# Initialize components
config = load_config()
processor = DocumentProcessor(config)
docling_embedder = DoclingEmbedder(config)
microsoft_embedder = MicrosoftEmbedder(config)
vector_store = FAISSVectorStore(config)
db_manager = SQLiteManager(config)
comparator = EmbeddingComparator(config)


@app.get("/", tags=["General"])
async def root():
    """API root endpoint"""
    return {
        "message": "Multi-RAG Document Pipeline API",
        "version": "1.0.0",
        "endpoints": {
            "health": "/health",
            "docs": "/docs",
            "upload": "/upload",
            "search": "/search",
            "documents": "/documents",
            "compare": "/documents/{document_id}/comparison",
            "stats": "/stats"
        }
    }


@app.get("/health", tags=["General"])
async def health_check():
    """Health check endpoint"""
    try:
        # Check database connection
        db_stats = db_manager.get_stats()
        
        # Check vector store
        vector_stats = vector_store.get_stats()
        
        return {
            "status": "healthy",
            "database": "connected",
            "vector_store": "ready",
            "total_documents": db_stats.get("total_documents", 0),
            "total_vectors": vector_stats.get("total_vectors", 0)
        }
    except Exception as e:
        raise HTTPException(status_code=503, detail=f"Health check failed: {str(e)}")


@app.post("/upload", response_model=Dict[str, Any], tags=["Documents"])
async def upload_document(
    background_tasks: BackgroundTasks,
    file: UploadFile = File(...),
    method: str = "both",
    compare: bool = True
):
    """Upload and process a document"""
    
    # Validate file type
    file_extension = Path(file.filename).suffix.lower()
    if file_extension not in config["supported_formats"]:
        raise HTTPException(
            status_code=400, 
            detail=f"Unsupported file format: {file_extension}"
        )
    
    # Save uploaded file temporarily
    with tempfile.NamedTemporaryFile(delete=False, suffix=file_extension) as tmp_file:
        content = await file.read()
        tmp_file.write(content)
        tmp_file_path = tmp_file.name
    
    try:
        # Process document
        chunks, metadata = processor.process_document(tmp_file_path)
        
        # Add document to database
        metadata["file_name"] = file.filename
        document_id = db_manager.add_document(tmp_file_path, metadata)
        
        # Schedule background processing
        background_tasks.add_task(
            process_embeddings_background,
            document_id, chunks, method, compare
        )
        
        return {
            "message": "Document uploaded successfully",
            "document_id": document_id,
            "file_name": file.filename,
            "num_chunks": len(chunks),
            "processing_method": method,
            "compare_methods": compare,
            "status": "processing"
        }
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Document processing failed: {str(e)}")
    
    finally:
        # Clean up temporary file
        if os.path.exists(tmp_file_path):
            os.unlink(tmp_file_path)


async def process_embeddings_background(document_id: int, chunks: List[str], method: str, compare: bool):
    """Background task to process embeddings"""
    try:
        embeddings_results = {}
        
        # Generate embeddings
        if method in ['docling', 'both']:
            docling_embeddings = docling_embedder.embed_batch(chunks)
            
            # Store embeddings in vector store
            vector_ids = vector_store.add_embeddings(
                docling_embeddings,
                [{"chunk_index": i, "text": chunk} for i, chunk in enumerate(chunks)],
                str(document_id)
            )
            
            # Store chunks in database
            for i, (chunk, vector_id) in enumerate(zip(chunks, vector_ids)):
                db_manager.add_chunk(document_id, i, chunk, "docling", vector_id)
            
            embeddings_results['docling'] = docling_embeddings
        
        if method in ['microsoft', 'both']:
            microsoft_embeddings = microsoft_embedder.embed_batch(chunks)
            
            # Store embeddings in vector store
            vector_ids = vector_store.add_embeddings(
                microsoft_embeddings,
                [{"chunk_index": i, "text": chunk} for i, chunk in enumerate(chunks)],
                str(document_id)
            )
            
            # Store chunks in database
            for i, (chunk, vector_id) in enumerate(zip(chunks, vector_ids)):
                db_manager.add_chunk(document_id, i, chunk, "microsoft", vector_id)
            
            embeddings_results['microsoft'] = microsoft_embeddings
        
        # Compare embeddings if requested
        if compare and method == 'both':
            comparison_results = comparator.compare_embeddings(
                embeddings_results['docling'],
                embeddings_results['microsoft'],
                chunks
            )
            
            # Store comparison results
            db_manager.add_comparison(document_id, comparison_results)
        
        # Save vector store
        vector_store.save_index()
        
    except Exception as e:
        print(f"Background processing failed for document {document_id}: {e}")


@app.post("/search", response_model=List[SearchResult], tags=["Search"])
async def search_documents(request: SearchRequest):
    """Search for similar document chunks"""
    try:
        # Generate query embedding
        if request.method == "docling":
            query_embedding = docling_embedder.embed_text(request.query)
        elif request.method == "microsoft":
            query_embedding = microsoft_embedder.embed_text(request.query)
        else:
            raise HTTPException(status_code=400, detail="Invalid embedding method")
        
        # Search vector store
        filter_metadata = {"document_id": str(request.document_id)} if request.document_id else None
        results = vector_store.search(query_embedding, k=request.top_k, filter_metadata=filter_metadata)
        
        # Format results
        formatted_results = []
        for vector_id, similarity, metadata in results:
            formatted_results.append(SearchResult(
                vector_id=vector_id,
                similarity=similarity,
                text=metadata.get("text", ""),
                metadata=metadata
            ))
        
        return formatted_results
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Search failed: {str(e)}")


@app.get("/documents", response_model=List[DocumentInfo], tags=["Documents"])
async def list_documents(limit: int = 100, offset: int = 0):
    """List all processed documents"""
    try:
        documents = db_manager.list_documents(limit=limit, offset=offset)
        
        return [
            DocumentInfo(
                id=doc["id"],
                file_name=doc["file_name"],
                file_type=doc["file_type"],
                file_size=doc["file_size"],
                num_chunks=doc["num_chunks"],
                processed_at=doc["processed_at"] or ""
            )
            for doc in documents
        ]
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to list documents: {str(e)}")


@app.get("/documents/{document_id}", response_model=DocumentInfo, tags=["Documents"])
async def get_document(document_id: int):
    """Get document information by ID"""
    try:
        document = db_manager.get_document(document_id)
        
        if not document:
            raise HTTPException(status_code=404, detail="Document not found")
        
        return DocumentInfo(
            id=document["id"],
            file_name=document["file_name"],
            file_type=document["file_type"],
            file_size=document["file_size"],
            num_chunks=document["num_chunks"],
            processed_at=document["processed_at"] or ""
        )
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to get document: {str(e)}")


@app.get("/documents/{document_id}/comparison", response_model=ComparisonResult, tags=["Comparison"])
async def get_comparison(document_id: int):
    """Get comparison results for a document"""
    try:
        comparison = db_manager.get_comparison(document_id)
        
        if not comparison:
            raise HTTPException(status_code=404, detail="Comparison not found")
        
        # Parse comparison results
        results = comparison['comparison_results']
        if isinstance(results, str):
            results = json.loads(results)
        
        summary = comparator.get_comparison_summary(results)
        
        return ComparisonResult(
            document_id=document_id,
            best_method=comparison['best_method'],
            summary=summary,
            metrics=results
        )
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to get comparison: {str(e)}")


@app.delete("/documents/{document_id}", tags=["Documents"])
async def delete_document(document_id: int):
    """Delete a document and all associated data"""
    try:
        # Delete from vector store
        vector_store.delete_document(str(document_id))
        
        # Delete from database
        success = db_manager.delete_document(document_id)
        
        if not success:
            raise HTTPException(status_code=404, detail="Document not found")
        
        # Save vector store changes
        vector_store.save_index()
        
        return {"message": f"Document {document_id} deleted successfully"}
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to delete document: {str(e)}")


@app.get("/stats", response_model=SystemStats, tags=["General"])
async def get_stats():
    """Get system statistics"""
    try:
        db_stats = db_manager.get_stats()
        vector_stats = vector_store.get_stats()
        
        return SystemStats(
            database=db_stats,
            vector_store=vector_stats
        )
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to get stats: {str(e)}")


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)