from fastapi import APIRouter, UploadFile, File, Depends, HTTPException
from typing import List
import hashlib
from pathlib import Path
from apps.backend.core.auth import get_current_user
from apps.backend.core.rate_limit import rate_limit
from apps.backend.observability.metrics import metrics

router = APIRouter(prefix="/upload", tags=["upload"])

@router.post("/document")
@rate_limit(requests=10, window=60)
async def upload_document(
    file: UploadFile = File(...),
    user = Depends(get_current_user)
):
    """Upload a document for processing and indexing."""
    
    from apps.backend.services.rag_service import get_rag_service
    from apps.backend.core.settings import settings
    import os
    
    # Validate file type
    allowed_types = ["application/pdf", "text/plain", "application/msword", 
                    "application/vnd.openxmlformats-officedocument.wordprocessingml.document"]
    if file.content_type not in allowed_types:
        raise HTTPException(400, f"Unsupported file type: {file.content_type}")
    
    # Read and hash content
    content = await file.read()
    content_hash = hashlib.sha256(content).hexdigest()
    doc_id = content_hash[:16]
    
    # Save file to storage
    upload_dir = Path(settings.upload_dir)
    upload_dir.mkdir(parents=True, exist_ok=True)
    
    file_path = upload_dir / f"{doc_id}_{file.filename}"
    with open(file_path, "wb") as f:
        f.write(content)
    
    # Ingest document
    rag_service = get_rag_service()
    result = await rag_service.ingest_document(
        file_path=str(file_path),
        doc_id=doc_id,
        filename=file.filename,
        content_hash=content_hash,
        file_size=len(content),
        mime_type=file.content_type
    )
    
    metrics.increment("documents_uploaded_total")
    
    return {
        "doc_id": doc_id,
        "filename": file.filename,
        "size": len(content),
        "content_hash": content_hash,
        "status": result["status"],
        "message": result.get("message", ""),
        "error": result.get("error")
    }