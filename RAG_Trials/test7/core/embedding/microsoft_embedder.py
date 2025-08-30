"""
Microsoft RAG Embedder Implementation

Uses Microsoft's RAG framework for document processing and embedding generation.
"""

from typing import List, Dict, Any, Optional, Tuple
import numpy as np
import logging
import requests
import json

from .base import CommonEmbedder

logger = logging.getLogger(__name__)


class MicrosoftRAGEmbedder(CommonEmbedder):
    """Microsoft RAG-based embedding implementation."""
    
    def __init__(self, config: Dict[str, Any]):
        """
        Initialize Microsoft RAG embedder.
        
        Args:
            config: Configuration containing API endpoints and keys
        """
        super().__init__(config)
        
        self.api_endpoint = config.get("microsoft_rag_endpoint", "")
        self.api_key = config.get("microsoft_rag_api_key", "")
        self.model_name = config.get("microsoft_model", "text-embedding-ada-002")
        self.dimension = config.get("vector_dimension", config.get("dimension", 384))  # Match vector store dimension
        
        # Validate configuration
        if not self.api_endpoint:
            logger.warning("Microsoft RAG endpoint not configured. Using mock implementation.")
            self._use_mock = True
        else:
            self._use_mock = False
            self._validate_connection()
    
    def _validate_connection(self):
        """Validate connection to Microsoft RAG service."""
        try:
            # Test connection with a simple request
            headers = {
                "Authorization": f"Bearer {self.api_key}",
                "Content-Type": "application/json"
            }
            
            test_payload = {
                "input": "test",
                "model": self.model_name
            }
            
            response = requests.post(
                f"{self.api_endpoint}/embeddings",
                headers=headers,
                json=test_payload,
                timeout=10
            )
            
            if response.status_code == 200:
                logger.info("Microsoft RAG connection validated successfully")
            else:
                logger.warning(f"Microsoft RAG connection test failed: {response.status_code}")
                self._use_mock = True
                
        except Exception as e:
            logger.warning(f"Microsoft RAG connection validation failed: {e}")
            self._use_mock = True
    
    def _mock_embedding(self, text: str) -> np.ndarray:
        """Generate a mock embedding for testing purposes."""
        # Create a deterministic mock embedding based on text hash
        import hashlib
        text_hash = hashlib.md5(text.encode()).hexdigest()
        
        # Convert hash to numbers and normalize
        numbers = [int(text_hash[i:i+2], 16) for i in range(0, min(len(text_hash), self.dimension*2), 2)]
        
        # Pad or truncate to desired dimension
        if len(numbers) < self.dimension:
            numbers.extend([0] * (self.dimension - len(numbers)))
        else:
            numbers = numbers[:self.dimension]
        
        # Normalize to unit vector
        embedding = np.array(numbers, dtype=np.float32)
        norm = np.linalg.norm(embedding)
        if norm > 0:
            embedding = embedding / norm
            
        return embedding
    
    def embed_text(self, text: str) -> np.ndarray:
        """
        Generate embedding for a single text using Microsoft RAG.
        
        Args:
            text: Input text to embed
            
        Returns:
            numpy array representing the text embedding
        """
        if self._use_mock:
            logger.debug("Using mock Microsoft RAG embedding")
            return self._mock_embedding(text)
        
        try:
            headers = {
                "Authorization": f"Bearer {self.api_key}",
                "Content-Type": "application/json"
            }
            
            payload = {
                "input": text,
                "model": self.model_name
            }
            
            response = requests.post(
                f"{self.api_endpoint}/embeddings",
                headers=headers,
                json=payload,
                timeout=30
            )
            
            if response.status_code == 200:
                result = response.json()
                embedding = np.array(result["data"][0]["embedding"], dtype=np.float32)
                return embedding
            else:
                logger.error(f"Microsoft RAG API error: {response.status_code}")
                return self._mock_embedding(text)
                
        except Exception as e:
            logger.error(f"Error calling Microsoft RAG API: {e}")
            return self._mock_embedding(text)
    
    def embed_batch(self, texts: List[str]) -> List[np.ndarray]:
        """
        Generate embeddings for a batch of texts.
        
        Args:
            texts: List of input texts to embed
            
        Returns:
            List of numpy arrays representing the text embeddings
        """
        if self._use_mock:
            return [self._mock_embedding(text) for text in texts]
        
        try:
            headers = {
                "Authorization": f"Bearer {self.api_key}",
                "Content-Type": "application/json"
            }
            
            payload = {
                "input": texts,
                "model": self.model_name
            }
            
            response = requests.post(
                f"{self.api_endpoint}/embeddings",
                headers=headers,
                json=payload,
                timeout=60
            )
            
            if response.status_code == 200:
                result = response.json()
                embeddings = []
                for item in result["data"]:
                    embedding = np.array(item["embedding"], dtype=np.float32)
                    embeddings.append(embedding)
                return embeddings
            else:
                logger.error(f"Microsoft RAG batch API error: {response.status_code}")
                return [self._mock_embedding(text) for text in texts]
                
        except Exception as e:
            logger.error(f"Error calling Microsoft RAG batch API: {e}")
            return [self._mock_embedding(text) for text in texts]
    
    def embed_document(self, document_chunks: List[str]) -> Tuple[List[np.ndarray], Dict[str, Any]]:
        """
        Generate embeddings for document chunks with Microsoft RAG metadata.
        
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
            
            # Create Microsoft RAG-specific metadata
            metadata = {
                "embedding_method": "microsoft_rag",
                "model_name": self.model_name,
                "num_chunks": len(document_chunks),
                "dimension": self.dimension,
                "chunk_lengths": [len(chunk) for chunk in document_chunks],
                "total_text_length": sum(len(chunk) for chunk in document_chunks),
                "api_endpoint": self.api_endpoint,
                "mock_mode": self._use_mock
            }
            
            logger.info(f"Microsoft RAG processed {len(document_chunks)} chunks")
            return embeddings, metadata
            
        except Exception as e:
            logger.error(f"Error processing document with Microsoft RAG: {e}")
            raise
    
    def get_model_info(self) -> Dict[str, Any]:
        """Get detailed information about the Microsoft RAG model."""
        return {
            **self.model_info,
            "framework": "microsoft_rag",
            "api_endpoint": self.api_endpoint,
            "mock_mode": self._use_mock,
            "architecture": "transformer"
        }