import asyncio
import time
from typing import List, Dict, Any, Optional, Tuple
from pathlib import Path

from apps.rag.store.vector_store import VectorStore
from apps.rag.store.ledger import IngestionLedger, IngestionStatus
from apps.rag.embeddings.embedder import Embedder
from apps.rag.embeddings.cache import EmbeddingCache
from apps.backend.core.ollama_client import get_ollama_client
from apps.backend.core.settings import settings
from apps.backend.observability.metrics import metrics

class RAGService:
    """Main RAG service orchestrating retrieval and generation."""
    
    def __init__(self):
        self.vector_store = VectorStore(
            index_dir=settings.index_dir,
            dimension=384  # sentence-transformers/all-MiniLM-L6-v2 dimension
        )
        self.ledger = IngestionLedger(settings.ledger_db_path)
        self.embedder = Embedder(settings.embedding_model)
        self.embedding_cache = EmbeddingCache(settings.cache_dir)
    
    async def query(
        self, 
        query_text: str, 
        k: int = 5,
        filters: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        """
        Perform RAG query: retrieve relevant chunks and generate response.
        """
        start_time = time.time()
        
        try:
            # Step 1: Generate query embedding
            embed_start = time.time()
            
            # Check cache first
            query_embedding = self.embedding_cache.get(query_text, settings.embedding_model)
            if query_embedding is None:
                query_embedding = self.embedder.embed_text(query_text)
                self.embedding_cache.put(query_text, settings.embedding_model, query_embedding)
            
            embedding_latency = (time.time() - embed_start) * 1000
            metrics.histogram("embedding_latency_ms", embedding_latency)
            
            # Step 2: Retrieve similar chunks
            retrieval_start = time.time()
            
            similar_chunks = self.vector_store.query(
                query_input=query_embedding,
                k=k,
                filters=filters
            )
            
            retrieval_latency = (time.time() - retrieval_start) * 1000
            metrics.histogram("retriever_latency_ms", retrieval_latency)
            
            # Step 3: Get chunk metadata and build context
            context_chunks = []
            sources = []
            
            for chunk_id, score in similar_chunks:
                chunk_meta = self.vector_store.get_chunk_metadata(chunk_id)
                if chunk_meta and not chunk_meta.get("deleted", False):
                    # TODO: Retrieve actual chunk text from storage
                    # For now, use placeholder
                    context_chunks.append(f"[Chunk {chunk_id}] Content placeholder")
                    sources.append({
                        "chunk_id": chunk_id,
                        "score": score,
                        "metadata": chunk_meta
                    })
            
            # Step 4: Generate response using Ollama
            generation_start = time.time()
            
            ollama_client = await get_ollama_client()
            
            try:
                result = await ollama_client.generate(
                    model=settings.ollama_model,
                    prompt=query_text,
                    context=context_chunks,
                    temperature=0.1
                )
                
                answer = result["response"]
                ollama_latency = result.get("total_duration", 0) / 1_000_000  # Convert nanoseconds to ms
                
            except Exception as e:
                print(f"Ollama generation error: {e}")
                answer = f"I found {len(similar_chunks)} relevant chunks, but couldn't generate a response. Error: {str(e)}"
                ollama_latency = 0
            
            metrics.histogram("ollama_latency_ms", ollama_latency)
            
            # Calculate total latency
            total_latency = (time.time() - start_time) * 1000
            
            return {
                "answer": answer,
                "sources": sources,
                "latency_ms": total_latency,
                "metrics": {
                    "embedding_latency_ms": embedding_latency,
                    "retrieval_latency_ms": retrieval_latency,
                    "ollama_latency_ms": ollama_latency,
                    "total_chunks_found": len(similar_chunks)
                }
            }
            
        except Exception as e:
            error_msg = f"RAG query failed: {str(e)}"
            print(error_msg)
            return {
                "answer": "Sorry, I encountered an error while processing your query.",
                "sources": [],
                "latency_ms": (time.time() - start_time) * 1000,
                "error": error_msg
            }
    
    async def ingest_document(
        self,
        file_path: str,
        doc_id: str,
        filename: str,
        content_hash: str,
        file_size: int = None,
        mime_type: str = None
    ) -> Dict[str, Any]:
        """
        Ingest a document through the full RAG pipeline.
        """
        try:
            # Check if document already processed
            doc_status = self.ledger.get_document_status(doc_id)
            if doc_status and doc_status["content_hash"] == content_hash:
                if doc_status["status"] == IngestionStatus.COMPLETED.value:
                    return {
                        "status": "already_processed",
                        "doc_id": doc_id,
                        "message": "Document already processed"
                    }
            
            # Add document to ledger
            self.ledger.add_document(
                doc_id=doc_id,
                filename=filename,
                content_hash=content_hash,
                file_size=file_size,
                mime_type=mime_type
            )
            
            # Run ingestion pipeline
            from apps.rag.ingestion.pipeline import IngestionPipeline
            
            pipeline = IngestionPipeline(
                chunk_size=settings.chunk_size,
                chunk_overlap=settings.chunk_overlap,
                embedding_model=settings.embedding_model,
                index_dir=settings.index_dir,
                cache_dir=settings.cache_dir,
                ledger_db_path=settings.ledger_db_path
            )
            
            result = await pipeline.process_document(
                file_path=file_path,
                doc_id=doc_id,
                filename=filename,
                content_hash=content_hash,
                file_size=file_size,
                mime_type=mime_type
            )
            
            return result
            
        except Exception as e:
            error_msg = f"Document ingestion failed: {str(e)}"
            self.ledger.update_status(doc_id, IngestionStatus.FAILED, error_msg)
            
            return {
                "status": "failed",
                "doc_id": doc_id,
                "error": error_msg
            }
    
    def get_index_info(self) -> Dict[str, Any]:
        """Get information about the current index."""
        try:
            vector_stats = self.vector_store.get_stats()
            ledger_stats = self.ledger.get_stats()
            cache_stats = self.embedding_cache.get_stats()
            
            return {
                "vector_store": vector_stats,
                "ingestion_ledger": ledger_stats,
                "embedding_cache": cache_stats,
                "last_updated": vector_stats.get("current_version")
            }
        except Exception as e:
            return {"error": str(e)}
    
    def create_snapshot(self) -> Dict[str, Any]:
        """Create a snapshot of the current index."""
        try:
            # TODO: Implement snapshot creation
            return {"status": "not_implemented", "message": "Snapshot creation not yet implemented"}
        except Exception as e:
            return {"error": str(e)}

# Singleton instance
_rag_service = None

def get_rag_service() -> RAGService:
    """Get RAG service instance."""
    global _rag_service
    if _rag_service is None:
        _rag_service = RAGService()
    return _rag_service