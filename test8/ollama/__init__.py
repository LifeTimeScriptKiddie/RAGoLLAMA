"""
Ollama Integration Module

Provides integration with Ollama for LLM inference and
RAG-based question answering.
"""

from .client import OllamaClient

__all__ = ["OllamaClient"]