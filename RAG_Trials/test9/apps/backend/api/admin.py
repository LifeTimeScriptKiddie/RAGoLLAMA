from fastapi import APIRouter, Depends, HTTPException
from typing import List
from apps.backend.core.auth import get_current_user, require_admin

router = APIRouter(prefix="/admin", tags=["admin"])

@router.get("/health")
async def health_check():
    """Health check endpoint."""
    return {"status": "healthy", "service": "rag-backend"}

@router.get("/ready")
async def readiness_check():
    """Readiness check endpoint."""
    # TODO: Check if FAISS index is loaded
    # TODO: Check if Ollama is responding
    return {"status": "ready"}

@router.get("/models")
async def list_models(user = Depends(require_admin)):
    """List available Ollama models."""
    from apps.backend.core.ollama_client import get_ollama_client
    
    try:
        ollama_client = await get_ollama_client()
        models = await ollama_client.list_models()
        return {"models": models}
    except Exception as e:
        raise HTTPException(500, f"Failed to get models: {str(e)}")

@router.get("/index/info")
async def index_info(user = Depends(require_admin)):
    """Get information about the current index."""
    from apps.backend.services.rag_service import get_rag_service
    
    rag_service = get_rag_service()
    return rag_service.get_index_info()

@router.post("/index/snapshot")
async def create_snapshot(user = Depends(require_admin)):
    """Create a snapshot of the current index."""
    from apps.backend.services.rag_service import get_rag_service
    
    rag_service = get_rag_service()
    return rag_service.create_snapshot()

@router.post("/index/restore/{snapshot_id}")
async def restore_snapshot(snapshot_id: str, user = Depends(require_admin)):
    """Restore index from snapshot."""
    # TODO: Restore from snapshot
    return {"status": "not_implemented"}