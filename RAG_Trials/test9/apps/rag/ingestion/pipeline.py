#!/usr/bin/env python3
"""
Complete RAG ingestion pipeline orchestrator.

Orchestrates the full pipeline:
1. Docling document processing
2. Text chunking  
3. Deduplication
4. Embedding generation (with cache)
5. Vector store indexing
6. Ledger updates
"""

import asyncio
import json
import time
from pathlib import Path
from typing import Dict, Any, List
import sys

# Add project root to Python path
sys.path.insert(0, str(Path(__file__).parent.parent.parent.parent))

from apps.rag.ingestion.docling_runner import DoclingRunner
from apps.rag.ingestion.chunker import Chunker
from apps.rag.ingestion.deduper import Deduper
from apps.rag.embeddings.embedder import Embedder
from apps.rag.embeddings.cache import EmbeddingCache
from apps.rag.store.vector_store import VectorStore
from apps.rag.store.ledger import IngestionLedger, IngestionStatus

class IngestionPipeline:
    """Complete ingestion pipeline orchestrator."""
    
    def __init__(
        self,
        chunk_size: int = 512,
        chunk_overlap: int = 50,
        embedding_model: str = "sentence-transformers/all-MiniLM-L6-v2",
        index_dir: str = "/data/index",
        cache_dir: str = "/data/cache", 
        ledger_db_path: str = "/data/ledger.db",
        temp_dir: str = "/tmp/rag_processing"
    ):
        self.chunk_size = chunk_size
        self.chunk_overlap = chunk_overlap
        self.embedding_model = embedding_model
        self.temp_dir = Path(temp_dir)
        self.temp_dir.mkdir(parents=True, exist_ok=True)
        
        # Initialize components
        self.docling_runner = DoclingRunner(str(self.temp_dir / "docling"))
        self.chunker = Chunker(chunk_size=chunk_size, chunk_overlap=chunk_overlap)
        self.deduper = Deduper()
        self.embedder = Embedder(embedding_model)
        self.embedding_cache = EmbeddingCache(cache_dir)
        self.vector_store = VectorStore(index_dir, dimension=384)
        self.ledger = IngestionLedger(ledger_db_path)
    
    async def process_document(
        self,
        file_path: str,
        doc_id: str,
        filename: str,
        content_hash: str,
        file_size: int = None,
        mime_type: str = None
    ) -> Dict[str, Any]:
        """
        Process a single document through the complete pipeline.
        """
        
        start_time = time.time()
        
        try:
            print(f"Starting ingestion pipeline for document: {filename} (ID: {doc_id})")
            
            # Update status to processing
            self.ledger.update_status(doc_id, IngestionStatus.PROCESSING)
            
            # Step 1: Document processing with Docling
            print("Step 1: Document processing...")
            docling_output = self.docling_runner.process_to_jsonl(
                file_path, 
                str(self.temp_dir / f"{doc_id}_docling.jsonl")
            )
            
            # Step 2: Chunking
            print("Step 2: Text chunking...")
            chunked_output = self.chunker.process_jsonl(
                docling_output,
                str(self.temp_dir / f"{doc_id}_chunked.jsonl")
            )
            
            # Step 3: Deduplication
            print("Step 3: Deduplication...")
            deduped_output = self.deduper.process_jsonl(
                chunked_output,
                str(self.temp_dir / f"{doc_id}_deduped.jsonl")
            )
            
            # Step 4: Load chunks for embedding
            chunks_for_embedding = []
            with open(deduped_output, 'r') as f:
                for line in f:
                    chunk_data = json.loads(line.strip())
                    chunks_for_embedding.append(chunk_data)
            
            print(f"Step 4: Embedding generation for {len(chunks_for_embedding)} chunks...")
            
            # Step 5: Generate embeddings with caching
            embedded_chunks = []
            cache_hits = 0
            cache_misses = 0
            
            for chunk_data in chunks_for_embedding:
                chunk_text = chunk_data["text"]
                chunk_id = chunk_data["chunk_id"]
                
                # Check cache first
                cached_embedding = self.embedding_cache.get(chunk_text, self.embedding_model)
                
                if cached_embedding is not None:
                    cache_hits += 1
                    vector = cached_embedding
                else:
                    cache_misses += 1
                    vector = self.embedder.embed_text(chunk_text)
                    self.embedding_cache.put(chunk_text, self.embedding_model, vector)
                
                embedded_chunks.append({
                    "chunk_id": chunk_id,
                    "vector": vector,
                    "metadata": {
                        "doc_id": doc_id,
                        "text": chunk_text,
                        "order": chunk_data["order"],
                        "chunk_hash": chunk_data["sha256"],
                        "original_meta": chunk_data.get("meta", {})
                    }
                })
            
            print(f"Embedding complete. Cache hits: {cache_hits}, Cache misses: {cache_misses}")
            
            # Step 6: Update vector store
            print("Step 6: Updating vector index...")
            
            vectors_for_upsert = [
                (chunk["chunk_id"], chunk["vector"]) 
                for chunk in embedded_chunks
            ]
            
            metadata_for_upsert = [
                chunk["metadata"] 
                for chunk in embedded_chunks
            ]
            
            index_version = self.vector_store.upsert(vectors_for_upsert, metadata_for_upsert)
            
            # Step 7: Update ledger
            print("Step 7: Updating ingestion ledger...")
            
            # Add chunks to ledger
            chunks_for_ledger = [
                {
                    "chunk_id": chunk["chunk_id"],
                    "order": chunk["metadata"]["order"],
                    "sha256": chunk["metadata"]["chunk_hash"]
                }
                for chunk in embedded_chunks
            ]
            
            self.ledger.add_chunks(doc_id, chunks_for_ledger)
            
            # Mark chunks as embedded
            chunk_ids = [chunk["chunk_id"] for chunk in embedded_chunks]
            self.ledger.mark_chunks_embedded(chunk_ids, self.embedding_model)
            
            # Update document status to completed
            self.ledger.update_status(doc_id, IngestionStatus.COMPLETED)
            
            # Cleanup temp files
            self._cleanup_temp_files(doc_id)
            
            total_time = time.time() - start_time
            
            result = {
                "status": "completed",
                "doc_id": doc_id,
                "filename": filename,
                "chunks_processed": len(embedded_chunks),
                "index_version": index_version,
                "processing_time_seconds": total_time,
                "cache_stats": {
                    "hits": cache_hits,
                    "misses": cache_misses,
                    "hit_rate": cache_hits / max(1, cache_hits + cache_misses)
                }
            }
            
            print(f"✅ Document processing completed in {total_time:.2f}s")
            print(f"   Processed {len(embedded_chunks)} chunks")
            print(f"   Cache hit rate: {result['cache_stats']['hit_rate']:.2%}")
            
            return result
            
        except Exception as e:
            error_msg = f"Pipeline failed: {str(e)}"
            print(f"❌ {error_msg}")
            
            # Update ledger with error
            self.ledger.update_status(doc_id, IngestionStatus.FAILED, error_msg)
            
            # Cleanup temp files
            self._cleanup_temp_files(doc_id)
            
            return {
                "status": "failed",
                "doc_id": doc_id,
                "error": error_msg,
                "processing_time_seconds": time.time() - start_time
            }
    
    def _cleanup_temp_files(self, doc_id: str):
        """Clean up temporary processing files."""
        try:
            temp_files = [
                self.temp_dir / f"{doc_id}_docling.jsonl",
                self.temp_dir / f"{doc_id}_chunked.jsonl", 
                self.temp_dir / f"{doc_id}_deduped.jsonl"
            ]
            
            for temp_file in temp_files:
                if temp_file.exists():
                    temp_file.unlink()
                    
        except Exception as e:
            print(f"Warning: Failed to cleanup temp files: {e}")
    
    def get_pipeline_stats(self) -> Dict[str, Any]:
        """Get pipeline statistics."""
        
        try:
            ledger_stats = self.ledger.get_stats()
            vector_stats = self.vector_store.get_stats()
            cache_stats = self.embedding_cache.get_stats()
            
            return {
                "ledger": ledger_stats,
                "vector_store": vector_stats,
                "embedding_cache": cache_stats,
                "pipeline_config": {
                    "chunk_size": self.chunk_size,
                    "chunk_overlap": self.chunk_overlap,
                    "embedding_model": self.embedding_model
                }
            }
        except Exception as e:
            return {"error": str(e)}

async def main():
    """CLI interface for the ingestion pipeline."""
    
    import argparse
    
    parser = argparse.ArgumentParser(description="RAG Ingestion Pipeline")
    parser.add_argument("file_path", help="Path to document to ingest")
    parser.add_argument("--doc-id", help="Document ID (auto-generated if not provided)")
    parser.add_argument("--stats", action="store_true", help="Show pipeline statistics")
    
    args = parser.parse_args()
    
    if args.stats:
        pipeline = IngestionPipeline()
        stats = pipeline.get_pipeline_stats()
        print(json.dumps(stats, indent=2))
        return
    
    # Process document
    file_path = Path(args.file_path)
    if not file_path.exists():
        print(f"Error: File not found: {file_path}")
        return 1
    
    # Generate doc ID if not provided
    doc_id = args.doc_id
    if not doc_id:
        import hashlib
        with open(file_path, 'rb') as f:
            content_hash = hashlib.sha256(f.read()).hexdigest()
            doc_id = content_hash[:16]
    
    pipeline = IngestionPipeline()
    
    result = await pipeline.process_document(
        file_path=str(file_path),
        doc_id=doc_id,
        filename=file_path.name,
        content_hash="manual_ingest",  # Would normally come from upload
        file_size=file_path.stat().st_size
    )
    
    print("\nFinal Result:")
    print(json.dumps(result, indent=2))
    
    return 0 if result["status"] == "completed" else 1

if __name__ == "__main__":
    exit_code = asyncio.run(main())
    sys.exit(exit_code)