"""
SQLite Database Manager

Manages document metadata and processing results in SQLite database.
"""

import sqlite3
import json
import logging
from typing import List, Dict, Any, Optional, Tuple
from pathlib import Path
from datetime import datetime

logger = logging.getLogger(__name__)


class SQLiteManager:
    """SQLite database manager for document and embedding metadata."""
    
    def __init__(self, config: Dict[str, Any]):
        """
        Initialize SQLite database manager.
        
        Args:
            config: Configuration dictionary
        """
        self.config = config
        self.db_path = Path(config.get("db_path", "/app/cache/documents.db"))
        self.db_path.parent.mkdir(parents=True, exist_ok=True)
        
        # Initialize database
        self._initialize_database()
    
    def _initialize_database(self):
        """Create database tables if they don't exist."""
        try:
            with sqlite3.connect(self.db_path) as conn:
                conn.execute("""
                    CREATE TABLE IF NOT EXISTS documents (
                        id INTEGER PRIMARY KEY AUTOINCREMENT,
                        file_path TEXT UNIQUE NOT NULL,
                        file_name TEXT NOT NULL,
                        file_type TEXT NOT NULL,
                        file_size INTEGER NOT NULL,
                        file_hash TEXT NOT NULL,
                        text_length INTEGER,
                        num_chunks INTEGER,
                        processed_at TEXT,
                        metadata TEXT,
                        created_at TEXT DEFAULT CURRENT_TIMESTAMP
                    )
                """)
                
                conn.execute("""
                    CREATE TABLE IF NOT EXISTS embeddings (
                        id INTEGER PRIMARY KEY AUTOINCREMENT,
                        document_id INTEGER,
                        chunk_index INTEGER NOT NULL,
                        chunk_text TEXT,
                        embedding_method TEXT NOT NULL,
                        vector_id INTEGER,
                        similarity_scores TEXT,
                        metadata TEXT,
                        created_at TEXT DEFAULT CURRENT_TIMESTAMP,
                        FOREIGN KEY (document_id) REFERENCES documents (id)
                    )
                """)
                
                conn.execute("""
                    CREATE TABLE IF NOT EXISTS comparisons (
                        id INTEGER PRIMARY KEY AUTOINCREMENT,
                        document_id INTEGER,
                        docling_embeddings TEXT,
                        microsoft_embeddings TEXT,
                        similarity_matrix TEXT,
                        comparison_results TEXT,
                        created_at TEXT DEFAULT CURRENT_TIMESTAMP,
                        FOREIGN KEY (document_id) REFERENCES documents (id)
                    )
                """)
                
                # Create indexes for better performance
                conn.execute("CREATE INDEX IF NOT EXISTS idx_documents_hash ON documents(file_hash)")
                conn.execute("CREATE INDEX IF NOT EXISTS idx_embeddings_document ON embeddings(document_id)")
                conn.execute("CREATE INDEX IF NOT EXISTS idx_embeddings_method ON embeddings(embedding_method)")
                
                conn.commit()
                logger.info("Database initialized successfully")
                
        except Exception as e:
            logger.error(f"Error initializing database: {e}")
            raise
    
    def add_document(self, file_path: str, metadata: Dict[str, Any]) -> int:
        """
        Add a new document to the database.
        
        Args:
            file_path: Path to the document file
            metadata: Document metadata dictionary
            
        Returns:
            Document ID
        """
        try:
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.cursor()
                
                cursor.execute("""
                    INSERT OR REPLACE INTO documents 
                    (file_path, file_name, file_type, file_size, file_hash, 
                     text_length, num_chunks, processed_at, metadata)
                    VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
                """, (
                    file_path,
                    metadata.get("file_name", ""),
                    metadata.get("file_type", ""),
                    metadata.get("file_size", 0),
                    metadata.get("file_hash", ""),
                    metadata.get("text_length", 0),
                    metadata.get("num_chunks", 0),
                    metadata.get("processed_at", datetime.utcnow().isoformat()),
                    json.dumps(metadata)
                ))
                
                document_id = cursor.lastrowid
                conn.commit()
                
                logger.info(f"Added document {metadata.get('file_name')} with ID {document_id}")
                return document_id
                
        except Exception as e:
            logger.error(f"Error adding document: {e}")
            raise
    
    def add_embeddings(self, document_id: int, chunk_index: int, chunk_text: str,
                      embedding_method: str, vector_id: int, metadata: Dict[str, Any]) -> int:
        """
        Add embedding information to the database.
        
        Args:
            document_id: Reference to document
            chunk_index: Index of the chunk within the document
            chunk_text: The actual text chunk
            embedding_method: Method used (docling/microsoft)
            vector_id: ID in the vector store
            metadata: Additional metadata
            
        Returns:
            Embedding record ID
        """
        try:
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.cursor()
                
                cursor.execute("""
                    INSERT INTO embeddings 
                    (document_id, chunk_index, chunk_text, embedding_method, 
                     vector_id, metadata)
                    VALUES (?, ?, ?, ?, ?, ?)
                """, (
                    document_id,
                    chunk_index,
                    chunk_text,
                    embedding_method,
                    vector_id,
                    json.dumps(metadata)
                ))
                
                embedding_id = cursor.lastrowid
                conn.commit()
                
                return embedding_id
                
        except Exception as e:
            logger.error(f"Error adding embeddings: {e}")
            raise
    
    def add_comparison(self, document_id: int, comparison_data: Dict[str, Any]) -> int:
        """
        Add comparison results to the database.
        
        Args:
            document_id: Reference to document
            comparison_data: Comparison results and metadata
            
        Returns:
            Comparison record ID
        """
        try:
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.cursor()
                
                cursor.execute("""
                    INSERT INTO comparisons 
                    (document_id, docling_embeddings, microsoft_embeddings, 
                     similarity_matrix, comparison_results)
                    VALUES (?, ?, ?, ?, ?)
                """, (
                    document_id,
                    json.dumps(comparison_data.get("docling_embeddings", [])),
                    json.dumps(comparison_data.get("microsoft_embeddings", [])),
                    json.dumps(comparison_data.get("similarity_matrix", [])),
                    json.dumps(comparison_data.get("comparison_results", {}))
                ))
                
                comparison_id = cursor.lastrowid
                conn.commit()
                
                logger.info(f"Added comparison for document {document_id}")
                return comparison_id
                
        except Exception as e:
            logger.error(f"Error adding comparison: {e}")
            raise
    
    def get_document(self, document_id: int) -> Optional[Dict[str, Any]]:
        """Get document by ID."""
        try:
            with sqlite3.connect(self.db_path) as conn:
                conn.row_factory = sqlite3.Row
                cursor = conn.cursor()
                
                cursor.execute("SELECT * FROM documents WHERE id = ?", (document_id,))
                row = cursor.fetchone()
                
                if row:
                    doc = dict(row)
                    doc["metadata"] = json.loads(doc["metadata"]) if doc["metadata"] else {}
                    return doc
                return None
                
        except Exception as e:
            logger.error(f"Error getting document: {e}")
            return None
    
    def get_document_by_hash(self, file_hash: str) -> Optional[Dict[str, Any]]:
        """Get document by file hash."""
        try:
            with sqlite3.connect(self.db_path) as conn:
                conn.row_factory = sqlite3.Row
                cursor = conn.cursor()
                
                cursor.execute("SELECT * FROM documents WHERE file_hash = ?", (file_hash,))
                row = cursor.fetchone()
                
                if row:
                    doc = dict(row)
                    doc["metadata"] = json.loads(doc["metadata"]) if doc["metadata"] else {}
                    return doc
                return None
                
        except Exception as e:
            logger.error(f"Error getting document by hash: {e}")
            return None
    
    def get_embeddings(self, document_id: int, embedding_method: Optional[str] = None) -> List[Dict[str, Any]]:
        """Get embeddings for a document."""
        try:
            with sqlite3.connect(self.db_path) as conn:
                conn.row_factory = sqlite3.Row
                cursor = conn.cursor()
                
                if embedding_method:
                    cursor.execute("""
                        SELECT * FROM embeddings 
                        WHERE document_id = ? AND embedding_method = ?
                        ORDER BY chunk_index
                    """, (document_id, embedding_method))
                else:
                    cursor.execute("""
                        SELECT * FROM embeddings 
                        WHERE document_id = ?
                        ORDER BY embedding_method, chunk_index
                    """, (document_id,))
                
                embeddings = []
                for row in cursor.fetchall():
                    emb = dict(row)
                    emb["metadata"] = json.loads(emb["metadata"]) if emb["metadata"] else {}
                    embeddings.append(emb)
                
                return embeddings
                
        except Exception as e:
            logger.error(f"Error getting embeddings: {e}")
            return []
    
    def get_comparison(self, document_id: int) -> Optional[Dict[str, Any]]:
        """Get comparison results for a document."""
        try:
            with sqlite3.connect(self.db_path) as conn:
                conn.row_factory = sqlite3.Row
                cursor = conn.cursor()
                
                cursor.execute("SELECT * FROM comparisons WHERE document_id = ?", (document_id,))
                row = cursor.fetchone()
                
                if row:
                    comp = dict(row)
                    comp["docling_embeddings"] = json.loads(comp["docling_embeddings"]) if comp["docling_embeddings"] else []
                    comp["microsoft_embeddings"] = json.loads(comp["microsoft_embeddings"]) if comp["microsoft_embeddings"] else []
                    comp["similarity_matrix"] = json.loads(comp["similarity_matrix"]) if comp["similarity_matrix"] else []
                    comp["comparison_results"] = json.loads(comp["comparison_results"]) if comp["comparison_results"] else {}
                    return comp
                return None
                
        except Exception as e:
            logger.error(f"Error getting comparison: {e}")
            return None
    
    def list_documents(self, limit: int = 100, offset: int = 0) -> List[Dict[str, Any]]:
        """List all documents with pagination."""
        try:
            with sqlite3.connect(self.db_path) as conn:
                conn.row_factory = sqlite3.Row
                cursor = conn.cursor()
                
                cursor.execute("""
                    SELECT * FROM documents 
                    ORDER BY created_at DESC 
                    LIMIT ? OFFSET ?
                """, (limit, offset))
                
                documents = []
                for row in cursor.fetchall():
                    doc = dict(row)
                    doc["metadata"] = json.loads(doc["metadata"]) if doc["metadata"] else {}
                    documents.append(doc)
                
                return documents
                
        except Exception as e:
            logger.error(f"Error listing documents: {e}")
            return []
    
    def delete_document(self, document_id: int) -> bool:
        """Delete a document and all its associated data."""
        try:
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.cursor()
                
                # Delete in order due to foreign key constraints
                cursor.execute("DELETE FROM comparisons WHERE document_id = ?", (document_id,))
                cursor.execute("DELETE FROM embeddings WHERE document_id = ?", (document_id,))
                cursor.execute("DELETE FROM documents WHERE id = ?", (document_id,))
                
                conn.commit()
                
                logger.info(f"Deleted document {document_id} and associated data")
                return True
                
        except Exception as e:
            logger.error(f"Error deleting document: {e}")
            return False
    
    def get_stats(self) -> Dict[str, Any]:
        """Get database statistics."""
        try:
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.cursor()
                
                cursor.execute("SELECT COUNT(*) FROM documents")
                total_documents = cursor.fetchone()[0]
                
                cursor.execute("SELECT COUNT(*) FROM embeddings")
                total_embeddings = cursor.fetchone()[0]
                
                cursor.execute("SELECT COUNT(*) FROM comparisons")
                total_comparisons = cursor.fetchone()[0]
                
                cursor.execute("SELECT COUNT(DISTINCT embedding_method) FROM embeddings")
                unique_methods = cursor.fetchone()[0]
                
                return {
                    "total_documents": total_documents,
                    "total_embeddings": total_embeddings,
                    "total_comparisons": total_comparisons,
                    "unique_embedding_methods": unique_methods,
                    "database_path": str(self.db_path)
                }
                
        except Exception as e:
            logger.error(f"Error getting stats: {e}")
            return {}