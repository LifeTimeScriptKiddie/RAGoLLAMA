"""
Multi-RAG Document Pipeline - Core Module

This module contains the core functionality for document processing,
embedding generation, vector storage, and comparison logic.
"""

__version__ = "1.0.0"
__author__ = "Multi-RAG Pipeline Team"

from . import embedding
from . import document
from . import vector
from . import storage
from . import comparison

__all__ = [
    "embedding",
    "document", 
    "vector",
    "storage",
    "comparison"
]