from pydantic import BaseModel
from datetime import datetime
from typing import List, Optional
from uuid import UUID

# Request schemas
class ChatRequest(BaseModel):
    message: str
    document_id: Optional[str] = None
    model: str = "llama3"
    top_k: int = 3

# Response schemas
class DocumentResponse(BaseModel):
    id: UUID
    filename: str
    status: str
    created_at: datetime
    chunk_count: int
    
    class Config:
        from_attributes = True

class DocumentListResponse(BaseModel):
    documents: List[DocumentResponse]

class ChatResponse(BaseModel):
    response: str
    document_id: Optional[str] = None
    sources: Optional[List[str]] = None