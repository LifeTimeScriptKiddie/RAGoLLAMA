from sqlalchemy.orm import Session
from sqlalchemy import text
from typing import List, Optional
import asyncio
import logging
import requests
import os

from models import Document, VectorChunk
from services.embedding_service import EmbeddingService

logging.basicConfig(level=logging.INFO)

class ChatService:
    """Chat service for RAG and general conversations"""
    
    def __init__(self, db: Optional[Session]):
        self.db = db
        self.embedding_service = EmbeddingService()
        self.ollama_url = os.getenv("OLLAMA_URL", "http://ollama:11434")
    
    async def chat_with_document(
        self, 
        message: str, 
        document_id: str, 
        model: str = "llama3",
        top_k: int = 3
    ) -> str:
        """Chat with a specific document using RAG"""
        
        # Get document
        document = self.db.query(Document).filter(Document.id == document_id).first()
        if not document or document.status != "completed":
            raise Exception("Document not found or not ready")
        
        # Generate query embedding
        query_embedding = await self.embedding_service.embed_query(message)
        
        # Search for similar chunks using pgvector
        similar_chunks = await self._search_similar_chunks(
            document_id, query_embedding.tolist(), top_k
        )
        
        # Create context from retrieved chunks
        context = "\n\n".join([chunk.content for chunk in similar_chunks])
        
        # Create RAG prompt
        rag_prompt = f"""Based on the following context from the document, please answer the question.

Context:
{context}

Question: {message}

Answer:"""
        
        # Query Ollama
        response = await self._query_ollama(rag_prompt, model)
        
        return response
    
    async def general_chat(self, message: str, model: str = "llama3") -> str:
        """General chat without document context"""
        return await self._query_ollama(message, model)
    
    async def _search_similar_chunks(
        self, 
        document_id: str, 
        query_embedding: List[float], 
        top_k: int
    ) -> List[VectorChunk]:
        """Search for similar chunks using pgvector cosine similarity"""
        
        # Convert embedding to PostgreSQL vector format
        embedding_str = "[" + ",".join(map(str, query_embedding)) + "]"
        
        # SQL query for cosine similarity search
        sql = text("""
            SELECT id, document_id, content, chunk_index, created_at
            FROM vector_chunks 
            WHERE document_id = :document_id
            ORDER BY embedding <=> :query_embedding
            LIMIT :limit
        """)
        
        result = self.db.execute(sql, {
            "document_id": document_id,
            "query_embedding": embedding_str,
            "limit": top_k
        })
        
        # Convert results to VectorChunk objects
        chunks = []
        for row in result:
            chunk = VectorChunk(
                id=row.id,
                document_id=row.document_id,
                content=row.content,
                chunk_index=row.chunk_index,
                created_at=row.created_at
            )
            chunks.append(chunk)
        
        return chunks
    
    async def _query_ollama(self, prompt: str, model: str) -> str:
        """Query Ollama API"""
        url = f"{self.ollama_url}/api/generate"
        payload = {
            "model": model,
            "prompt": prompt,
            "stream": False
        }
        
        try:
            # Run HTTP request in thread pool to avoid blocking
            loop = asyncio.get_event_loop()
            response = await loop.run_in_executor(
                None,
                lambda: requests.post(url, json=payload, timeout=30)
            )
            response.raise_for_status()
            
            return response.json().get("response", "")
            
        except Exception as e:
            logging.error(f"Ollama query failed: {e}")
            raise Exception(f"AI response failed: {str(e)}")