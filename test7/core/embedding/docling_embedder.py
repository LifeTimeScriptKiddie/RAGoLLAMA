"""
Docling Embedder Implementation

Uses Docling library for document processing and embedding generation.
"""

from typing import List, Dict, Any, Optional, Tuple
import numpy as np
from sentence_transformers import SentenceTransformer
import logging

from .base import CommonEmbedder

logger = logging.getLogger(__name__)


class DoclingEmbedder(CommonEmbedder):
    """Docling-based embedding implementation."""
    
    def __init__(self, config: Dict[str, Any]):
        """
        Initialize Docling embedder.
        
        Args:
            config: Configuration containing model settings
        """
        super().__init__(config)
        
        # Default to sentence-transformers model for Docling
        self.model_name = config.get("docling_model", "sentence-transformers/all-MiniLM-L6-v2")
        self.model = None
        self._load_model()
        
    def _load_model(self):
        """Load the sentence transformer model."""
        try:
            logger.info(f"Loading Docling model: {self.model_name}")
            self.model = SentenceTransformer(self.model_name)
            self.dimension = self.model.get_sentence_embedding_dimension()
            logger.info(f"Docling model loaded successfully. Dimension: {self.dimension}")
        except Exception as e:
            logger.error(f"Failed to load Docling model: {e}")
            raise
    
    def embed_text(self, text: str) -> np.ndarray:
        """
        Generate embedding for a single text using Docling approach.
        
        Args:
            text: Input text to embed
            
        Returns:
            numpy array representing the text embedding
        """
        if not self.model:
            raise RuntimeError("Docling model not loaded")
            
        try:
            # Use sentence-transformers for embedding
            embedding = self.model.encode(text, convert_to_numpy=True)
            return embedding.astype(np.float32)
        except Exception as e:
            logger.error(f"Error embedding text with Docling: {e}")
            raise
    
    def embed_batch(self, texts: List[str]) -> List[np.ndarray]:
        """
        Generate embeddings for a batch of texts.
        
        Args:
            texts: List of input texts to embed
            
        Returns:
            List of numpy arrays representing the text embeddings
        """
        if not self.model:
            raise RuntimeError("Docling model not loaded")
            
        try:
            # Batch encoding for efficiency
            embeddings = self.model.encode(texts, convert_to_numpy=True, batch_size=32)
            return [emb.astype(np.float32) for emb in embeddings]
        except Exception as e:
            logger.error(f"Error embedding batch with Docling: {e}")
            raise
    
    def embed_document(self, document_chunks: List[str]) -> Tuple[List[np.ndarray], Dict[str, Any]]:
        """
        Generate embeddings for document chunks with Docling-specific metadata.
        
        Args:
            document_chunks: List of text chunks from a document
            
        Returns:
            Tuple of (embeddings list, metadata dict)
        """
        if not document_chunks:
            return [], {}
            
        try:
            # Generate embeddings for all chunks
            embeddings = self.embed_batch(document_chunks)
            
            # Create Docling-specific metadata
            metadata = {
                "embedding_method": "docling",
                "model_name": self.model_name,
                "num_chunks": len(document_chunks),
                "dimension": self.dimension,
                "chunk_lengths": [len(chunk) for chunk in document_chunks],
                "total_text_length": sum(len(chunk) for chunk in document_chunks)
            }
            
            logger.info(f"Docling processed {len(document_chunks)} chunks")
            return embeddings, metadata
            
        except Exception as e:
            logger.error(f"Error processing document with Docling: {e}")
            raise
    
    def get_model_info(self) -> Dict[str, Any]:
        """Get detailed information about the Docling model."""
        return {
            **self.model_info,
            "framework": "sentence-transformers",
            "architecture": "transformer",
            "max_sequence_length": getattr(self.model, 'max_seq_length', 512) if self.model else None
        }