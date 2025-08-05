"""
Embedding Module

Provides common interface and implementations for different embedding methods
including Docling and Microsoft RAG.
"""

from .base import CommonEmbedder
from .docling_embedder import DoclingEmbedder
from .microsoft_embedder import MicrosoftRAGEmbedder

__all__ = [
    "CommonEmbedder",
    "DoclingEmbedder", 
    "MicrosoftRAGEmbedder"
]