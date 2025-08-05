"""
FAISS Vector Store

Implements vector storage and similarity search using FAISS library with HNSW indexing.
"""

from typing import List, Dict, Any, Optional, Tuple
import numpy as np
import faiss
import pickle
import logging
from pathlib import Path
import json

logger = logging.getLogger(__name__)


class FAISSVectorStore:
    """FAISS-based vector storage with HNSW indexing for embeddings."""
    
    def __init__(self, config: Dict[str, Any]):
        """
        Initialize FAISS vector store.
        
        Args:
            config: Configuration dictionary
        """
        self.config = config
        self.dimension = config.get("dimension", 384)
        self.index_path = Path(config.get("faiss_index_path", "/app/cache/faiss_index"))
        self.index_type = config.get("index_type", "HNSW")
        
        # FAISS index and metadata
        self.index = None
        self.metadata = []  # Store metadata for each vector
        self.id_to_index = {}  # Map external IDs to internal index positions
        self.next_id = 0
        
        # Initialize index
        self._initialize_index()
        
        # Try to load existing index
        self._load_index()
    
    def _initialize_index(self):
        """Initialize the FAISS index based on configuration."""
        try:
            if self.index_type.upper() == "HNSW":
                # HNSW index for high-quality similarity search
                self.index = faiss.IndexHNSWFlat(self.dimension, 32)
                self.index.hnsw.efConstruction = 200
                self.index.hnsw.efSearch = 100
            elif self.index_type.upper() == "IVF":
                # IVF index for large-scale datasets
                quantizer = faiss.IndexFlatL2(self.dimension)
                self.index = faiss.IndexIVFFlat(quantizer, self.dimension, 100)
            else:
                # Default to flat index
                self.index = faiss.IndexFlatL2(self.dimension)
                
            logger.info(f"Initialized {self.index_type} FAISS index with dimension {self.dimension}")
            
        except Exception as e:
            logger.error(f"Error initializing FAISS index: {e}")
            raise
    
    def add_embeddings(self, embeddings: List[np.ndarray], metadata: List[Dict[str, Any]], 
                      document_id: str) -> List[int]:
        """
        Add embeddings to the vector store.
        
        Args:
            embeddings: List of embedding vectors
            metadata: List of metadata dicts for each embedding
            document_id: Document identifier
            
        Returns:
            List of assigned vector IDs
        """
        if not embeddings:
            return []
        
        if len(embeddings) != len(metadata):
            raise ValueError("Embeddings and metadata lists must have same length")
        
        try:
            # Convert embeddings to numpy array
            embeddings_array = np.array(embeddings, dtype=np.float32)
            
            # Validate dimensions
            if embeddings_array.shape[1] != self.dimension:
                raise ValueError(f"Embedding dimension {embeddings_array.shape[1]} doesn't match index dimension {self.dimension}")
            
            # Add to index
            start_idx = self.index.ntotal
            self.index.add(embeddings_array)
            
            # Store metadata and create ID mappings
            vector_ids = []
            for i, meta in enumerate(metadata):
                vector_id = self.next_id
                self.next_id += 1
                
                # Enhanced metadata
                enhanced_meta = {
                    **meta,
                    "vector_id": vector_id,
                    "document_id": document_id,
                    "index_position": start_idx + i,
                    "added_at": __import__("datetime").datetime.utcnow().isoformat()
                }
                
                self.metadata.append(enhanced_meta)
                self.id_to_index[vector_id] = start_idx + i
                vector_ids.append(vector_id)
            
            logger.info(f"Added {len(embeddings)} embeddings for document {document_id}")
            return vector_ids
            
        except Exception as e:
            logger.error(f"Error adding embeddings: {e}")
            raise
    
    def search(self, query_embedding: np.ndarray, k: int = 5, 
               filter_metadata: Optional[Dict[str, Any]] = None) -> List[Tuple[int, float, Dict[str, Any]]]:
        """
        Search for similar vectors.
        
        Args:
            query_embedding: Query vector
            k: Number of results to return
            filter_metadata: Optional metadata filters
            
        Returns:
            List of (vector_id, similarity_score, metadata) tuples
        """
        if self.index.ntotal == 0:
            return []
        
        try:
            # Ensure query embedding is the right shape and type
            query_vector = np.array(query_embedding, dtype=np.float32).reshape(1, -1)
            
            if query_vector.shape[1] != self.dimension:
                raise ValueError(f"Query embedding dimension {query_vector.shape[1]} doesn't match index dimension {self.dimension}")
            
            # Search in FAISS index
            similarities, indices = self.index.search(query_vector, k)
            
            results = []
            for i in range(len(indices[0])):
                idx = indices[0][i]
                score = float(similarities[0][i])
                
                # Skip invalid indices
                if idx < 0 or idx >= len(self.metadata):
                    continue
                
                meta = self.metadata[idx]
                
                # Apply metadata filters if provided
                if filter_metadata:
                    if not all(meta.get(key) == value for key, value in filter_metadata.items()):
                        continue
                
                # Convert L2 distance to similarity score (higher is better)
                similarity = 1.0 / (1.0 + score)
                
                results.append((meta["vector_id"], similarity, meta))
            
            return results
            
        except Exception as e:
            logger.error(f"Error searching vectors: {e}")
            raise
    
    def get_by_document_id(self, document_id: str) -> List[Tuple[int, Dict[str, Any]]]:
        """
        Get all vectors for a specific document.
        
        Args:
            document_id: Document identifier
            
        Returns:
            List of (vector_id, metadata) tuples
        """
        results = []
        for meta in self.metadata:
            if meta.get("document_id") == document_id:
                results.append((meta["vector_id"], meta))
        return results
    
    def delete_document(self, document_id: str) -> int:
        """
        Delete all vectors for a specific document.
        Note: FAISS doesn't support efficient deletion, so this marks as deleted.
        
        Args:
            document_id: Document identifier
            
        Returns:
            Number of vectors marked as deleted
        """
        deleted_count = 0
        for meta in self.metadata:
            if meta.get("document_id") == document_id and not meta.get("deleted", False):
                meta["deleted"] = True
                meta["deleted_at"] = __import__("datetime").datetime.utcnow().isoformat()
                deleted_count += 1
        
        logger.info(f"Marked {deleted_count} vectors as deleted for document {document_id}")
        return deleted_count
    
    def save_index(self, path: Optional[str] = None):
        """
        Save the FAISS index and metadata to disk.
        
        Args:
            path: Optional custom path, defaults to configured path
        """
        try:
            save_path = Path(path) if path else self.index_path
            save_path.mkdir(parents=True, exist_ok=True)
            
            # Save FAISS index
            index_file = save_path / "index.faiss"
            faiss.write_index(self.index, str(index_file))
            
            # Save metadata
            metadata_file = save_path / "metadata.pkl"
            with open(metadata_file, "wb") as f:
                pickle.dump({
                    "metadata": self.metadata,
                    "id_to_index": self.id_to_index,
                    "next_id": self.next_id,
                    "dimension": self.dimension,
                    "index_type": self.index_type
                }, f)
            
            # Save config
            config_file = save_path / "config.json"
            with open(config_file, "w") as f:
                json.dump(self.config, f, indent=2)
            
            logger.info(f"Saved FAISS index to {save_path}")
            
        except Exception as e:
            logger.error(f"Error saving index: {e}")
            raise
    
    def _load_index(self):
        """Load existing FAISS index and metadata from disk."""
        try:
            if not self.index_path.exists():
                logger.info("No existing index found, starting with empty index")
                return
            
            index_file = self.index_path / "index.faiss"
            metadata_file = self.index_path / "metadata.pkl"
            
            if index_file.exists() and metadata_file.exists():
                # Load FAISS index
                self.index = faiss.read_index(str(index_file))
                
                # Load metadata
                with open(metadata_file, "rb") as f:
                    data = pickle.load(f)
                    self.metadata = data["metadata"]
                    self.id_to_index = data["id_to_index"]
                    self.next_id = data["next_id"]
                
                logger.info(f"Loaded FAISS index with {self.index.ntotal} vectors from {self.index_path}")
            else:
                logger.info("Incomplete index files found, starting with empty index")
                
        except Exception as e:
            logger.warning(f"Error loading index: {e}, starting with empty index")
    
    def get_stats(self) -> Dict[str, Any]:
        """Get statistics about the vector store."""
        active_vectors = sum(1 for meta in self.metadata if not meta.get("deleted", False))
        deleted_vectors = sum(1 for meta in self.metadata if meta.get("deleted", False))
        
        unique_documents = len(set(meta.get("document_id") for meta in self.metadata 
                                 if not meta.get("deleted", False)))
        
        return {
            "total_vectors": self.index.ntotal if self.index else 0,
            "active_vectors": active_vectors,
            "deleted_vectors": deleted_vectors,
            "unique_documents": unique_documents,
            "dimension": self.dimension,
            "index_type": self.index_type,
            "index_path": str(self.index_path)
        }