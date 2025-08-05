"""
Common Embedder Interface

Abstract base class that defines the interface for all embedding methods.
"""

from abc import ABC, abstractmethod
from typing import List, Dict, Any, Tuple
import numpy as np


class CommonEmbedder(ABC):
    """Abstract base class for all embedding implementations."""
    
    def __init__(self, config: Dict[str, Any]):
        """
        Initialize the embedder with configuration.
        
        Args:
            config: Configuration dictionary containing model settings
        """
        self.config = config
        self.model_name = config.get("model_name", "default")
        self.cache_enabled = config.get("cache_enabled", True)
        self.model_info = {
            "model_name": self.model_name,
            "dimension": config.get("dimension", 384),
            "type": self.__class__.__name__
        }
    
    @abstractmethod
    def embed_text(self, text: str) -> np.ndarray:
        """
        Generate embedding for a single text.
        
        Args:
            text: Input text to embed
            
        Returns:
            numpy array representing the text embedding
        """
        pass
    
    @abstractmethod
    def embed_batch(self, texts: List[str]) -> List[np.ndarray]:
        """
        Generate embeddings for a batch of texts.
        
        Args:
            texts: List of input texts to embed
            
        Returns:
            List of numpy arrays representing the text embeddings
        """
        pass
    
    @abstractmethod
    def embed_document(self, document_chunks: List[str]) -> Tuple[List[np.ndarray], Dict[str, Any]]:
        """
        Generate embeddings for document chunks with metadata.
        
        Args:
            document_chunks: List of text chunks from a document
            
        Returns:
            Tuple of (embeddings list, metadata dict)
        """
        pass
    
    def calculate_similarity(self, embedding1: np.ndarray, embedding2: np.ndarray) -> float:
        """
        Calculate cosine similarity between two embeddings.
        
        Args:
            embedding1: First embedding vector
            embedding2: Second embedding vector
            
        Returns:
            Cosine similarity score between 0 and 1
        """
        # Normalize vectors
        norm1 = np.linalg.norm(embedding1)
        norm2 = np.linalg.norm(embedding2)
        
        if norm1 == 0 or norm2 == 0:
            return 0.0
        
        # Calculate cosine similarity
        similarity = np.dot(embedding1, embedding2) / (norm1 * norm2)
        return float(np.clip(similarity, 0, 1))
    
    def get_model_info(self) -> Dict[str, Any]:
        """Get information about the embedding model."""
        return self.model_info.copy()
    
    def _generate_cache_key(self, text: str) -> str:
        """Generate a cache key for the given text."""
        import hashlib
        return hashlib.md5(text.encode('utf-8')).hexdigest()
    
    def _validate_embedding(self, embedding: np.ndarray) -> bool:
        """Validate that an embedding is properly formatted."""
        if not isinstance(embedding, np.ndarray):
            return False
        if embedding.ndim != 1:
            return False
        if len(embedding) == 0:
            return False
        if np.any(np.isnan(embedding)) or np.any(np.isinf(embedding)):
            return False
        return True