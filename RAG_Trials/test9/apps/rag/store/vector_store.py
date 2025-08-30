import json
import pickle
from typing import List, Tuple, Optional, Dict, Any, Union
from pathlib import Path
import numpy as np
import hashlib
from datetime import datetime

class VectorStore:
    """
    FAISS-based vector store with upsert/query interface.
    
    Contract per claude.md:
    - upsert(vectors: List[(chunk_id, vector)]) -> index_version
    - query(text|vector, k, filters) -> List[(chunk_id, score)]
    """
    
    def __init__(self, index_dir: str = "/data/index", dimension: int = 384):
        self.index_dir = Path(index_dir)
        self.index_dir.mkdir(parents=True, exist_ok=True)
        
        self.dimension = dimension
        self.index = None
        self.chunk_metadata = {}  # chunk_id -> metadata
        self.current_version = None
        
        self._init_faiss()
        self._load_or_create_index()
    
    def _init_faiss(self):
        """Initialize FAISS library."""
        try:
            import faiss
            self.faiss = faiss
        except ImportError:
            raise ImportError(
                "faiss-cpu not installed. Install with: pip install faiss-cpu"
            )
    
    def _load_or_create_index(self):
        """Load existing index or create new one."""
        index_file = self.index_dir / "index.faiss"
        metadata_file = self.index_dir / "metadata.pkl"
        version_file = self.index_dir / "version.txt"
        
        if index_file.exists() and metadata_file.exists():
            # Load existing index
            try:
                self.index = self.faiss.read_index(str(index_file))
                
                with open(metadata_file, 'rb') as f:
                    self.chunk_metadata = pickle.load(f)
                
                if version_file.exists():
                    with open(version_file, 'r') as f:
                        self.current_version = f.read().strip()
                else:
                    self.current_version = "v1"
                
                print(f"Loaded index: {self.index.ntotal} vectors, version {self.current_version}")
                
            except Exception as e:
                print(f"Error loading index: {e}")
                self._create_new_index()
        else:
            self._create_new_index()
    
    def _create_new_index(self):
        """Create new FAISS index."""
        # Use IndexFlatIP for cosine similarity (with normalized vectors)
        self.index = self.faiss.IndexFlatIP(self.dimension)
        self.chunk_metadata = {}
        self.current_version = self._generate_version()
        print(f"Created new index with dimension {self.dimension}")
    
    def _generate_version(self) -> str:
        """Generate new index version."""
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        return f"v{timestamp}"
    
    def _save_index(self):
        """Save index and metadata to disk."""
        index_file = self.index_dir / "index.faiss"
        metadata_file = self.index_dir / "metadata.pkl"
        version_file = self.index_dir / "version.txt"
        
        # Save FAISS index
        self.faiss.write_index(self.index, str(index_file))
        
        # Save metadata
        with open(metadata_file, 'wb') as f:
            pickle.dump(self.chunk_metadata, f)
        
        # Save version
        with open(version_file, 'w') as f:
            f.write(self.current_version)
    
    def _normalize_vector(self, vector: np.ndarray) -> np.ndarray:
        """Normalize vector for cosine similarity."""
        norm = np.linalg.norm(vector)
        if norm == 0:
            return vector
        return vector / norm
    
    def upsert(self, vectors: List[Tuple[str, List[float]]], metadata: List[Dict[str, Any]] = None) -> str:
        """
        Insert or update vectors in the index.
        
        Args:
            vectors: List of (chunk_id, vector) tuples
            metadata: Optional metadata for each vector
            
        Returns:
            index_version: Current index version after upsert
        """
        if not vectors:
            return self.current_version
        
        # Convert to numpy arrays and normalize
        vector_data = []
        chunk_ids = []
        
        for i, (chunk_id, vector) in enumerate(vectors):
            vector_np = np.array(vector, dtype=np.float32)
            if vector_np.shape[0] != self.dimension:
                raise ValueError(f"Vector dimension {vector_np.shape[0]} doesn't match index dimension {self.dimension}")
            
            normalized_vector = self._normalize_vector(vector_np)
            vector_data.append(normalized_vector)
            chunk_ids.append(chunk_id)
            
            # Store metadata
            chunk_metadata = metadata[i] if metadata and i < len(metadata) else {}
            self.chunk_metadata[chunk_id] = {
                **chunk_metadata,
                "index_id": self.index.ntotal + i,  # FAISS internal ID
                "added_at": datetime.now().isoformat()
            }
        
        # Add to FAISS index
        vectors_np = np.vstack(vector_data)
        self.index.add(vectors_np)
        
        # Update version and save
        self.current_version = self._generate_version()
        self._save_index()
        
        print(f"Added {len(vectors)} vectors to index. Total: {self.index.ntotal}")
        return self.current_version
    
    def query(self, query_input: Union[str, List[float]], k: int = 5, 
             filters: Optional[Dict[str, Any]] = None) -> List[Tuple[str, float]]:
        """
        Query the vector store.
        
        Args:
            query_input: Query text (will be embedded) or vector
            k: Number of results to return
            filters: Optional filters (TODO: implement filtering)
            
        Returns:
            List of (chunk_id, score) tuples
        """
        if self.index.ntotal == 0:
            return []
        
        # Handle text input (requires embedder)
        if isinstance(query_input, str):
            # TODO: Integrate with embedder for text queries
            raise NotImplementedError("Text queries not yet supported. Pass vector directly.")
        
        # Convert query vector to numpy and normalize
        query_vector = np.array(query_input, dtype=np.float32).reshape(1, -1)
        query_vector = self._normalize_vector(query_vector[0]).reshape(1, -1)
        
        # Search FAISS index
        scores, indices = self.index.search(query_vector, k)
        
        # Map results back to chunk IDs
        results = []
        chunk_id_map = {meta["index_id"]: chunk_id 
                       for chunk_id, meta in self.chunk_metadata.items()}
        
        for i, (score, idx) in enumerate(zip(scores[0], indices[0])):
            if idx == -1:  # FAISS returns -1 for empty slots
                continue
                
            chunk_id = chunk_id_map.get(idx)
            if chunk_id:
                # TODO: Apply filters if provided
                results.append((chunk_id, float(score)))
        
        return results
    
    def get_chunk_metadata(self, chunk_id: str) -> Optional[Dict[str, Any]]:
        """Get metadata for a specific chunk."""
        return self.chunk_metadata.get(chunk_id)
    
    def get_stats(self) -> Dict[str, Any]:
        """Get vector store statistics."""
        return {
            "total_vectors": self.index.ntotal if self.index else 0,
            "dimension": self.dimension,
            "current_version": self.current_version,
            "index_size_bytes": (self.index_dir / "index.faiss").stat().st_size 
                               if (self.index_dir / "index.faiss").exists() else 0,
            "metadata_count": len(self.chunk_metadata)
        }
    
    def delete_chunk(self, chunk_id: str) -> bool:
        """Delete a chunk from the index (requires rebuild for FAISS)."""
        if chunk_id in self.chunk_metadata:
            # For FAISS, we need to rebuild index to truly delete
            # For now, just mark as deleted in metadata
            self.chunk_metadata[chunk_id]["deleted"] = True
            self.chunk_metadata[chunk_id]["deleted_at"] = datetime.now().isoformat()
            return True
        return False