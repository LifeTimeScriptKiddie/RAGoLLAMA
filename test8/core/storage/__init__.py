"""
Storage Module

Provides database storage and management for documents, chunks, and comparisons.
"""

from .sqlite_manager import SQLiteManager

__all__ = ["SQLiteManager"]