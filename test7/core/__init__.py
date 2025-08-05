"""
Multi-RAG Document Pipeline Core Module

This module provides the core functionality for document processing,
embedding generation, vector storage, and comparison between different
RAG implementations (Docling vs Microsoft RAG).
"""

__version__ = "1.0.0"
__author__ = "Multi-RAG Pipeline Team"

from .embedding.base import CommonEmbedder
from .embedding.docling_embedder import DoclingEmbedder
from .embedding.microsoft_embedder import MicrosoftRAGEmbedder
from .document.processor import DocumentProcessor
from .vector.faiss_store import FAISSVectorStore
from .storage.sqlite_manager import SQLiteManager
from .comparison.comparator import EmbeddingComparator

__all__ = [
    "CommonEmbedder",
    "DoclingEmbedder", 
    "MicrosoftRAGEmbedder",
    "DocumentProcessor",
    "FAISSVectorStore",
    "SQLiteManager",
    "EmbeddingComparator"
]