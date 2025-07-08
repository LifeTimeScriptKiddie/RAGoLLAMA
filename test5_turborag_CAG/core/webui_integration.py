"""
Open WebUI Integration for Document Knowledge Base
Provides API endpoints to make our embedded documents available to Open WebUI
"""

from fastapi import FastAPI, HTTPException, Depends
from typing import List, Dict, Any, Optional
import sqlite3
import json
from datetime import datetime
try:
    from .vector_store import query as vector_query
    from .document_manager import document_manager
except ImportError:
    # Handle case when running as standalone
    from vector_store import query as vector_query
    from document_manager import document_manager
import logging

logger = logging.getLogger(__name__)

# Create FastAPI app for knowledge base integration
app = FastAPI(title="Financial Advisor Knowledge Base", version="1.0.0")

class DocumentResponse:
    """Response model for document metadata"""
    def __init__(self, doc_data: Dict[str, Any]):
        self.id = doc_data.get('filename', '')
        self.filename = doc_data['filename']
        self.status = doc_data['status'] 
        self.processed_at = doc_data.get('processed_at', '')
        self.file_size = doc_data.get('file_size', 0)
        self.metadata = doc_data.get('metadata', {})
        self.error_message = doc_data.get('error_message')

class KnowledgeBaseResponse:
    """Response model for knowledge base info"""
    def __init__(self):
        self.id = "financial_advisor_kb"
        self.name = "Financial Advisor Knowledge Base"
        self.description = "Embedded documents from cyber security and financial materials"
        self.documents = []
        self.total_documents = 0
        self.successful_documents = 0
        self.error_documents = 0

@app.get("/")
async def root():
    """Health check endpoint"""
    return {"status": "online", "service": "Financial Advisor Knowledge Base"}

@app.get("/test")
async def test_vector_search():
    """Test endpoint to debug vector search"""
    try:
        results = vector_query("test", k=2)
        return {
            "results": results,
            "results_type": str(type(results)),
            "first_result_type": str(type(results[0])) if results else None,
            "first_result": str(results[0]) if results else None
        }
    except Exception as e:
        return {"error": str(e)}

@app.get("/knowledge")
async def get_knowledge_base():
    """Get knowledge base metadata and document list"""
    try:
        documents = document_manager.get_document_status()
        
        kb_response = KnowledgeBaseResponse()
        kb_response.total_documents = len(documents)
        kb_response.successful_documents = len([d for d in documents if d['status'] == 'success'])
        kb_response.error_documents = len([d for d in documents if d['status'] == 'error'])
        
        # Convert documents to response format
        kb_response.documents = [DocumentResponse(doc).__dict__ for doc in documents]
        
        return {
            "id": kb_response.id,
            "name": kb_response.name,
            "description": kb_response.description,
            "total_documents": kb_response.total_documents,
            "successful_documents": kb_response.successful_documents,
            "error_documents": kb_response.error_documents,
            "documents": kb_response.documents,
            "updated_at": datetime.now().isoformat()
        }
        
    except Exception as e:
        logger.error(f"Error getting knowledge base: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Error accessing knowledge base: {str(e)}")

@app.get("/search")
async def search_documents(query: str, limit: int = 5):
    """Search through embedded documents"""
    try:
        if not query.strip():
            raise HTTPException(status_code=400, detail="Query cannot be empty")
        
        # Use our existing vector search
        results = vector_query(query, k=limit)
        
        if not results:
            return {
                "query": query,
                "results": [],
                "total_results": 0,
                "message": "No matching documents found"
            }
        
        # Format results for Open WebUI
        formatted_results = []
        for i, result in enumerate(results):
            # Handle tuple format from vector_store: (text, distance)
            if isinstance(result, tuple) and len(result) == 2:
                text, distance = result
                formatted_results.append({
                    "id": f"result_{i}",
                    "content": text[:1000],  # Limit content length
                    "score": 1.0 / (1.0 + distance),  # Convert distance to similarity score
                    "metadata": {"distance": distance},
                    "source": "vector_store"
                })
            else:
                # Handle other formats (shouldn't happen with current vector_store)
                formatted_results.append({
                    "id": f"result_{i}",
                    "content": str(result)[:1000],
                    "score": 0.0,
                    "metadata": {"raw_result": str(result)},
                    "source": "unknown"
                })
        
        return {
            "query": query,
            "results": formatted_results,
            "total_results": len(formatted_results),
            "timestamp": datetime.now().isoformat()
        }
        
    except Exception as e:
        logger.error(f"Error searching documents: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Search error: {str(e)}")

@app.get("/documents")
async def get_documents(status: Optional[str] = None):
    """Get list of all documents with optional status filter"""
    try:
        documents = document_manager.get_document_status()
        
        if status:
            documents = [d for d in documents if d['status'] == status]
        
        return {
            "documents": [DocumentResponse(doc).__dict__ for doc in documents],
            "total": len(documents),
            "filtered_by": status,
            "timestamp": datetime.now().isoformat()
        }
        
    except Exception as e:
        logger.error(f"Error getting documents: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Error getting documents: {str(e)}")

@app.get("/documents/{document_id}")
async def get_document(document_id: str):
    """Get specific document details"""
    try:
        documents = document_manager.get_document_status()
        document = next((d for d in documents if d['filename'] == document_id), None)
        
        if not document:
            raise HTTPException(status_code=404, detail="Document not found")
        
        return DocumentResponse(document).__dict__
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error getting document {document_id}: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Error getting document: {str(e)}")

@app.post("/refresh")
async def refresh_knowledge_base():
    """Manually refresh the knowledge base by scanning for new documents"""
    try:
        results = document_manager.scan_and_process_documents()
        
        return {
            "message": "Knowledge base refreshed successfully",
            "results": results,
            "timestamp": datetime.now().isoformat()
        }
        
    except Exception as e:
        logger.error(f"Error refreshing knowledge base: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Error refreshing knowledge base: {str(e)}")

# Additional endpoint for Open WebUI function integration
@app.get("/function/search")
async def function_search(query: str):
    """Search function for Open WebUI function calling"""
    try:
        results = vector_query(query, k=3)
        
        if not results:
            return {"answer": "No relevant information found in the knowledge base."}
        
        # Combine top results into a comprehensive answer
        context_parts = []
        for result in results[:3]:
            # Handle tuple format from vector_store: (text, distance)
            if isinstance(result, tuple) and len(result) == 2:
                text, distance = result
                context_parts.append(text[:500])  # Limit each piece
            else:
                context_parts.append(str(result)[:500])
        
        combined_context = "\n\n".join(context_parts)
        
        return {
            "answer": f"Based on the knowledge base:\n\n{combined_context}",
            "sources": len(results),
            "query": query
        }
        
    except Exception as e:
        logger.error(f"Error in function search: {str(e)}")
        return {"answer": f"Error searching knowledge base: {str(e)}"}

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8502)