from pydantic import BaseModel
from datetime import datetime
from typing import Optional, List

class LoginRequest(BaseModel):
    username: str
    password: str

class LoginResponse(BaseModel):
    access_token: str
    token_type: str
    user_id: int
    username: str
    roles: str

class DocumentResponse(BaseModel):
    id: int
    filename: str
    original_filename: str
    content_type: str
    size: int
    status: str
    created_at: datetime
    processed_at: Optional[datetime]
    error_message: Optional[str]

class SearchRequest(BaseModel):
    query: str
    limit: int = 10

class SearchResult(BaseModel):
    content: str
    score: float
    document_id: int
    filename: str
    chunk_index: int

class SearchResponse(BaseModel):
    results: List[SearchResult]
    total: int

class ReindexRequest(BaseModel):
    document_id: Optional[int] = None  # If None, reindex all documents

class UserCreateRequest(BaseModel):
    username: str
    password: str
    roles: str = "user"

class UserResponse(BaseModel):
    id: int
    username: str
    roles: str
    created_at: datetime