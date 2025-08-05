"""
Vector Storage Module

Provides FAISS-based vector storage for embeddings with
efficient similarity search capabilities.
"""

from .faiss_store import FAISSVectorStore

__all__ = ["FAISSVectorStore"]