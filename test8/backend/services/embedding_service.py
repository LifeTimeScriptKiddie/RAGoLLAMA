from typing import List
import numpy as np
import asyncio
import logging
from sentence_transformers import SentenceTransformer
import os

logging.basicConfig(level=logging.INFO)

class EmbeddingService:
    """Embedding generation service using SentenceTransformers"""
    
    def __init__(self):
        self.model = None
        self.model_name = os.getenv("EMBED_MODEL", "all-MiniLM-L6-v2")
    
    def _get_model(self) -> SentenceTransformer:
        """Lazy load the embedding model"""
        if self.model is None:
            logging.info(f"Loading SentenceTransformer model: {self.model_name}")
            self.model = SentenceTransformer(self.model_name)
        return self.model
    
    async def embed_chunks(self, chunks: List[str]) -> np.ndarray:
        """Generate embeddings for text chunks"""
        try:
            model = self._get_model()
            
            # Run embedding generation in thread pool to avoid blocking
            loop = asyncio.get_event_loop()
            embeddings = await loop.run_in_executor(
                None, 
                lambda: model.encode(chunks, convert_to_numpy=True)
            )
            
            logging.info(f"Generated embeddings for {len(chunks)} chunks")
            return embeddings
            
        except Exception as e:
            logging.error(f"Embedding generation failed: {e}")
            raise Exception(f"Failed to generate embeddings: {str(e)}")
    
    async def embed_query(self, query: str) -> np.ndarray:
        """Generate embedding for a single query"""
        try:
            model = self._get_model()
            
            # Run embedding generation in thread pool
            loop = asyncio.get_event_loop()
            embedding = await loop.run_in_executor(
                None,
                lambda: model.encode(query, convert_to_numpy=True)
            )
            
            return embedding
            
        except Exception as e:
            logging.error(f"Query embedding failed: {e}")
            raise Exception(f"Failed to generate query embedding: {str(e)}")