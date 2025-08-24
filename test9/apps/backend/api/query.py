from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel
from typing import List, Optional
from apps.backend.core.auth import get_current_user
from apps.backend.core.rate_limit import rate_limit
from apps.backend.observability.metrics import metrics
import time

router = APIRouter(prefix="/query", tags=["query"])

class QueryRequest(BaseModel):
    query: str
    k: Optional[int] = 5
    filters: Optional[dict] = None

class QueryResponse(BaseModel):
    answer: str
    sources: List[dict]
    latency_ms: float

@router.post("/", response_model=QueryResponse)
@rate_limit(requests=20, window=60)
async def query_documents(
    request: QueryRequest,
    user = Depends(get_current_user)
):
    """Query the document index and generate response."""
    
    from apps.backend.services.rag_service import get_rag_service
    
    rag_service = get_rag_service()
    
    # Perform RAG query
    result = await rag_service.query(
        query_text=request.query,
        k=request.k,
        filters=request.filters
    )
    
    metrics.increment("queries_total")
    metrics.histogram("query_latency_ms", result["latency_ms"])
    
    return QueryResponse(
        answer=result["answer"],
        sources=result["sources"],
        latency_ms=result["latency_ms"]
    )