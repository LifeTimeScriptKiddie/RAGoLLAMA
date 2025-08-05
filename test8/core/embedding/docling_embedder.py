"""
Docling Embedder Implementation

Uses Docling framework for document processing and embedding generation.
"""

from typing import List, Dict, Any, Tuple
import numpy as np
import logging
from .base import CommonEmbedder

logger = logging.getLogger(__name__)


class DoclingEmbedder(CommonEmbedder):
    """Docling-based embedding implementation."""
    
    def __init__(self, config: Dict[str, Any]):
        """
        Initialize Docling embedder.
        
        Args:
            config: Configuration containing Docling model settings
        """
        super().__init__(config)
        
        self.model_name = config.get("docling_model", "sentence-transformers/all-MiniLM-L6-v2")
        self.dimension = config.get("dimension", 384)
        
        # Initialize the model
        self._load_model()
        
        # Update model info
        self.model_info.update({
            "framework": "docling",
            "architecture": "transformer",
            "max_sequence_length": 256
        })
    
    def _load_model(self):
        """Load the Docling/SentenceTransformers model."""
        try:
            from sentence_transformers import SentenceTransformer
            
            logger.info(f"Loading Docling model: {self.model_name}")
            self.model = SentenceTransformer(self.model_name)
            
            # Get actual dimension from model
            sample_embedding = self.model.encode("test")
            self.dimension = len(sample_embedding)
            self.model_info["dimension"] = self.dimension
            
            logger.info(f"Docling model loaded successfully. Dimension: {self.dimension}")
            
        except ImportError:
            logger.error("sentence-transformers not installed. Please install: pip install sentence-transformers")
            raise
        except Exception as e:
            logger.error(f"Failed to load Docling model: {e}")
            raise
    
    def embed_text(self, text: str) -> np.ndarray:
        """
        Generate embedding for a single text using Docling.
        
        Args:
            text: Input text to embed
            
        Returns:
            numpy array representing the text embedding
        """
        if not text or not text.strip():
            return np.zeros(self.dimension, dtype=np.float32)
        
        try:
            # Generate embedding
            embedding = self.model.encode(text, convert_to_numpy=True)
            
            # Validate embedding
            if not self._validate_embedding(embedding):
                logger.warning(f"Invalid embedding generated for text: {text[:50]}...")
                return np.zeros(self.dimension, dtype=np.float32)
            
            return embedding.astype(np.float32)
            
        except Exception as e:
            logger.error(f"Error generating Docling embedding: {e}")
            return np.zeros(self.dimension, dtype=np.float32)
    
    def embed_batch(self, texts: List[str]) -> List[np.ndarray]:
        """
        Generate embeddings for a batch of texts.
        
        Args:
            texts: List of input texts to embed
            
        Returns:
            List of numpy arrays representing the text embeddings
        """
        if not texts:
            return []
        
        # Filter out empty texts
        valid_texts = [text if text and text.strip() else "empty" for text in texts]
        
        try:
            # Generate batch embeddings
            embeddings = self.model.encode(valid_texts, convert_to_numpy=True, batch_size=32)
            
            # Validate and convert to list
            result = []
            for i, embedding in enumerate(embeddings):
                if self._validate_embedding(embedding):
                    result.append(embedding.astype(np.float32))
                else:
                    logger.warning(f"Invalid embedding at index {i}")
                    result.append(np.zeros(self.dimension, dtype=np.float32))
            
            return result
            
        except Exception as e:
            logger.error(f"Error generating Docling batch embeddings: {e}")
            return [np.zeros(self.dimension, dtype=np.float32) for _ in texts]
    
    def embed_document(self, document_chunks: List[str]) -> Tuple[List[np.ndarray], Dict[str, Any]]:
        """
        Generate embeddings for document chunks with Docling metadata.
        
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
            "framework": "docling",
            "sentence_transformers_model": self.model_name,
            "supports_batch": True,
            "max_sequence_length": getattr(self.model, 'max_seq_length', 256)
        }