"""
Base Embedding Interface

Defines the common interface that all embedding implementations must follow.
"""

from abc import ABC, abstractmethod
from typing import List, Dict, Any, Optional, Tuple
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
        self.dimension = config.get("dimension", 384)
        
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
    
    def get_similarity(self, embedding1: np.ndarray, embedding2: np.ndarray) -> float:
        """
        Calculate cosine similarity between two embeddings.
        
        Args:
            embedding1: First embedding vector
            embedding2: Second embedding vector
            
        Returns:
            Cosine similarity score between 0 and 1
        """
        dot_product = np.dot(embedding1, embedding2)
        norm1 = np.linalg.norm(embedding1)
        norm2 = np.linalg.norm(embedding2)
        
        if norm1 == 0 or norm2 == 0:
            return 0.0
            
        return dot_product / (norm1 * norm2)
    
    @property
    def embedding_dimension(self) -> int:
        """Get the dimension of embeddings produced by this embedder."""
        return self.dimension
    
    @property
    def model_info(self) -> Dict[str, Any]:
        """Get information about the embedding model."""
        return {
            "model_name": self.model_name,
            "dimension": self.dimension,
            "type": self.__class__.__name__
        }