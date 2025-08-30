#!/usr/bin/env python3
"""
Multi-RAG Document Pipeline - Main Entry Point

Cross-platform pipeline for comparing Docling vs Microsoft RAG embeddings
with support for multiple document formats and comprehensive analysis.
"""

import os
import sys
import argparse
import logging
from pathlib import Path
from typing import Dict, Any, List, Optional
import json

# Add the current directory to Python path
sys.path.insert(0, str(Path(__file__).parent))

from core.document.processor import DocumentProcessor
from core.embedding.docling_embedder import DoclingEmbedder
from core.embedding.microsoft_embedder import MicrosoftRAGEmbedder
from core.vector.faiss_store import FAISSVectorStore
from core.storage.sqlite_manager import SQLiteManager
from core.comparison.comparator import EmbeddingComparator

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.StreamHandler(sys.stdout),
        logging.FileHandler('/app/cache/multi_rag.log')
    ]
)

logger = logging.getLogger(__name__)


class MultiRAGPipeline:
    """Main pipeline for Multi-RAG document processing and comparison."""
    
    def __init__(self, config_path: str = "/app/.env"):
        """
        Initialize the Multi-RAG pipeline.
        
        Args:
            config_path: Path to configuration file
        """
        self.config = self._load_config(config_path)
        self._initialize_components()
    
    def _load_config(self, config_path: str) -> Dict[str, Any]:
        """Load configuration from environment and config file."""
        config = {
            # Document processing
            "max_chunk_size": int(os.getenv("MAX_CHUNK_SIZE", "1000")),
            "chunk_overlap": int(os.getenv("CHUNK_OVERLAP", "200")),
            "supported_formats": os.getenv("SUPPORTED_FORMATS", "pdf,txt,docx,pptx,jpg,png"),
            
            # Vector storage
            "vector_dimension": int(os.getenv("VECTOR_DIMENSION", "384")),
            "faiss_index_path": os.getenv("FAISS_INDEX_PATH", "/app/cache/faiss_index"),
            "index_type": os.getenv("INDEX_TYPE", "HNSW"),
            
            # Database
            "db_path": os.getenv("DB_PATH", "/app/cache/documents.db"),
            
            # Embedding models
            "docling_model": os.getenv("DOCLING_MODEL", "sentence-transformers/all-MiniLM-L6-v2"),
            "microsoft_rag_endpoint": os.getenv("MICROSOFT_RAG_ENDPOINT", ""),
            "microsoft_rag_api_key": os.getenv("MICROSOFT_RAG_API_KEY", ""),
            "microsoft_model": os.getenv("MICROSOFT_MODEL", "text-embedding-ada-002"),
            
            # Comparison settings
            "similarity_threshold": float(os.getenv("SIMILARITY_THRESHOLD", "0.8")),
            "analysis_metrics": os.getenv("ANALYSIS_METRICS", "cosine_similarity,euclidean_distance,pearson_correlation").split(","),
            
            # Cache and output
            "cache_dir": os.getenv("CACHE_DIR", "/app/cache"),
            "output_dir": os.getenv("OUTPUT_DIR", "/app/output")
        }
        
        # Ensure cache and output directories exist
        Path(config["cache_dir"]).mkdir(parents=True, exist_ok=True)
        Path(config["output_dir"]).mkdir(parents=True, exist_ok=True)
        
        logger.info("Configuration loaded successfully")
        return config
    
    def _initialize_components(self):
        """Initialize all pipeline components."""
        try:
            # Document processor
            self.document_processor = DocumentProcessor(self.config)
            
            # Embedding models
            self.docling_embedder = DoclingEmbedder(self.config)
            self.microsoft_embedder = MicrosoftRAGEmbedder(self.config)
            
            # Storage components
            self.vector_store = FAISSVectorStore(self.config)
            self.db_manager = SQLiteManager(self.config)
            
            # Comparison tool
            self.comparator = EmbeddingComparator(self.config)
            
            logger.info("All pipeline components initialized successfully")
            
        except Exception as e:
            logger.error(f"Error initializing pipeline components: {e}")
            raise
    
    def process_document(self, file_path: str, compare_methods: bool = True) -> Dict[str, Any]:
        """
        Process a single document through the complete pipeline.
        
        Args:
            file_path: Path to the document file
            compare_methods: Whether to compare embedding methods
            
        Returns:
            Processing results and comparison data
        """
        file_path = Path(file_path)
        if not file_path.exists():
            raise FileNotFoundError(f"Document not found: {file_path}")
        
        logger.info(f"Processing document: {file_path.name}")
        
        try:
            # Check if document already processed
            import hashlib
            with open(file_path, "rb") as f:
                file_hash = hashlib.md5(f.read()).hexdigest()
            
            existing_doc = self.db_manager.get_document_by_hash(file_hash)
            if existing_doc:
                logger.info(f"Document already processed: {file_path.name}")
                if compare_methods:
                    comparison = self.db_manager.get_comparison(existing_doc["id"])
                    return {
                        "document": existing_doc,
                        "comparison": comparison,
                        "status": "already_processed"
                    }
                return {"document": existing_doc, "status": "already_processed"}
            
            # Step 1: Extract and chunk document
            chunks, doc_metadata = self.document_processor.process_document(str(file_path))
            
            # Step 2: Add document to database
            document_id = self.db_manager.add_document(str(file_path), doc_metadata)
            
            # Step 3: Generate embeddings with both methods
            docling_embeddings, docling_metadata = self.docling_embedder.embed_document(chunks)
            microsoft_embeddings, microsoft_metadata = self.microsoft_embedder.embed_document(chunks)
            
            # Step 4: Store embeddings in vector store
            docling_vector_ids = self.vector_store.add_embeddings(
                docling_embeddings, 
                [{"chunk_index": i, "method": "docling"} for i in range(len(chunks))],
                f"doc_{document_id}_docling"
            )
            
            microsoft_vector_ids = self.vector_store.add_embeddings(
                microsoft_embeddings,
                [{"chunk_index": i, "method": "microsoft"} for i in range(len(chunks))],
                f"doc_{document_id}_microsoft"
            )
            
            # Step 5: Store embedding metadata in database
            for i, (chunk, doc_vid, ms_vid) in enumerate(zip(chunks, docling_vector_ids, microsoft_vector_ids)):
                self.db_manager.add_embeddings(
                    document_id, i, chunk, "docling", doc_vid, docling_metadata
                )
                self.db_manager.add_embeddings(
                    document_id, i, chunk, "microsoft", ms_vid, microsoft_metadata
                )
            
            result = {
                "document": self.db_manager.get_document(document_id),
                "docling_embeddings": len(docling_embeddings),
                "microsoft_embeddings": len(microsoft_embeddings),
                "status": "processed"
            }
            
            # Step 6: Compare methods if requested
            if compare_methods:
                logger.info("Comparing embedding methods...")
                comparison_results = self.comparator.compare_embeddings(
                    docling_embeddings, microsoft_embeddings, chunks
                )
                
                # Store comparison results
                comparison_id = self.db_manager.add_comparison(document_id, {
                    "docling_embeddings": [emb.tolist() for emb in docling_embeddings],
                    "microsoft_embeddings": [emb.tolist() for emb in microsoft_embeddings],
                    "comparison_results": comparison_results
                })
                
                result["comparison"] = comparison_results
                result["comparison_id"] = comparison_id
            
            # Save vector index
            self.vector_store.save_index()
            
            logger.info(f"Document processing completed: {file_path.name}")
            return result
            
        except Exception as e:
            logger.error(f"Error processing document {file_path.name}: {e}")
            raise
    
    def search_similar(self, query_text: str, method: str = "docling", k: int = 5) -> List[Dict[str, Any]]:
        """
        Search for similar documents using specified embedding method.
        
        Args:
            query_text: Query text to search for
            method: Embedding method to use ("docling" or "microsoft")
            k: Number of results to return
            
        Returns:
            List of similar documents with scores
        """
        try:
            # Generate query embedding
            if method.lower() == "docling":
                query_embedding = self.docling_embedder.embed_text(query_text)
            elif method.lower() == "microsoft":
                query_embedding = self.microsoft_embedder.embed_text(query_text)
            else:
                raise ValueError(f"Unknown embedding method: {method}")
            
            # Search in vector store
            results = self.vector_store.search(
                query_embedding, k=k, 
                filter_metadata={"method": method.lower()}
            )
            
            # Enhance results with document information
            enhanced_results = []
            for vector_id, similarity, metadata in results:
                doc_id = metadata.get("document_id", "").replace(f"_doc_", "").replace(f"_{method}", "")
                if doc_id.startswith("doc_"):
                    doc_id = int(doc_id.replace("doc_", "").split("_")[0])
                    document = self.db_manager.get_document(doc_id)
                    
                    enhanced_results.append({
                        "similarity": similarity,
                        "document": document,
                        "chunk_metadata": metadata,
                        "method_used": method
                    })
            
            return enhanced_results
            
        except Exception as e:
            logger.error(f"Error searching similar documents: {e}")
            raise
    
    def get_pipeline_stats(self) -> Dict[str, Any]:
        """Get comprehensive pipeline statistics."""
        try:
            db_stats = self.db_manager.get_stats()
            vector_stats = self.vector_store.get_stats()
            
            return {
                "database": db_stats,
                "vector_store": vector_stats,
                "models": {
                    "docling": self.docling_embedder.get_model_info(),
                    "microsoft": self.microsoft_embedder.get_model_info()
                },
                "configuration": {
                    "max_chunk_size": self.config["max_chunk_size"],
                    "vector_dimension": self.config["vector_dimension"],
                    "supported_formats": self.config["supported_formats"]
                }
            }
            
        except Exception as e:
            logger.error(f"Error getting pipeline stats: {e}")
            return {}
    
    def export_results(self, document_id: int, output_path: str):
        """Export complete results for a document."""
        try:
            document = self.db_manager.get_document(document_id)
            embeddings = self.db_manager.get_embeddings(document_id)
            comparison = self.db_manager.get_comparison(document_id)
            
            results = {
                "document": document,
                "embeddings": embeddings,
                "comparison": comparison,
                "export_timestamp": __import__("datetime").datetime.utcnow().isoformat()
            }
            
            with open(output_path, 'w') as f:
                json.dump(results, f, indent=2, default=str)
            
            logger.info(f"Results exported to {output_path}")
            
        except Exception as e:
            logger.error(f"Error exporting results: {e}")
            raise


def main():
    """Main CLI entry point."""
    parser = argparse.ArgumentParser(description="Multi-RAG Document Pipeline")
    parser.add_argument("command", choices=["process", "search", "stats", "export"], 
                       help="Command to execute")
    parser.add_argument("--file", "-f", help="Document file path (for process)")
    parser.add_argument("--query", "-q", help="Search query text (for search)")
    parser.add_argument("--method", "-m", choices=["docling", "microsoft"], 
                       default="docling", help="Embedding method (for search)")
    parser.add_argument("--limit", "-l", type=int, default=5, help="Number of results (for search)")
    parser.add_argument("--document-id", "-d", type=int, help="Document ID (for export)")
    parser.add_argument("--output", "-o", help="Output file path (for export)")
    parser.add_argument("--no-compare", action="store_true", help="Skip method comparison")
    parser.add_argument("--config", "-c", default="/app/.env", help="Configuration file path")
    parser.add_argument("--verbose", "-v", action="store_true", help="Enable verbose logging")
    
    args = parser.parse_args()
    
    if args.verbose:
        logging.getLogger().setLevel(logging.DEBUG)
    
    try:
        # Initialize pipeline
        pipeline = MultiRAGPipeline(args.config)
        
        if args.command == "process":
            if not args.file:
                print("Error: --file is required for process command")
                sys.exit(1)
            
            result = pipeline.process_document(args.file, compare_methods=not args.no_compare)
            print(json.dumps(result, indent=2, default=str))
            
        elif args.command == "search":
            if not args.query:
                print("Error: --query is required for search command")
                sys.exit(1)
            
            results = pipeline.search_similar(args.query, args.method, args.limit)
            print(json.dumps(results, indent=2, default=str))
            
        elif args.command == "stats":
            stats = pipeline.get_pipeline_stats()
            print(json.dumps(stats, indent=2, default=str))
            
        elif args.command == "export":
            if not args.document_id or not args.output:
                print("Error: --document-id and --output are required for export command")
                sys.exit(1)
            
            pipeline.export_results(args.document_id, args.output)
            print(f"Results exported to {args.output}")
            
    except Exception as e:
        logger.error(f"Pipeline execution failed: {e}")
        sys.exit(1)


if __name__ == "__main__":
    main()