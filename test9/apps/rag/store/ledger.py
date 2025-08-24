import sqlite3
import json
from typing import Optional, List, Dict, Any
from pathlib import Path
from datetime import datetime
from enum import Enum

class IngestionStatus(Enum):
    PENDING = "pending"
    PROCESSING = "processing"
    COMPLETED = "completed"
    FAILED = "failed"

class IngestionLedger:
    """
    Ingestion ledger for idempotency and versioning.
    
    Tracks: doc_id, content_hash, version, status, chunks, embedding_model
    """
    
    def __init__(self, db_path: str = "/data/ledger.db"):
        self.db_path = Path(db_path)
        self.db_path.parent.mkdir(parents=True, exist_ok=True)
        self._init_db()
    
    def _init_db(self):
        """Initialize SQLite database for ingestion tracking."""
        with sqlite3.connect(self.db_path) as conn:
            conn.execute("""
                CREATE TABLE IF NOT EXISTS documents (
                    doc_id TEXT PRIMARY KEY,
                    filename TEXT NOT NULL,
                    content_hash TEXT NOT NULL,
                    file_size INTEGER,
                    mime_type TEXT,
                    upload_timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    status TEXT DEFAULT 'pending',
                    version INTEGER DEFAULT 1,
                    chunks_count INTEGER DEFAULT 0,
                    embedding_model TEXT,
                    index_version TEXT,
                    error_message TEXT,
                    metadata TEXT,
                    last_updated TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                )
            """)
            
            conn.execute("""
                CREATE TABLE IF NOT EXISTS chunks (
                    chunk_id TEXT PRIMARY KEY,
                    doc_id TEXT NOT NULL,
                    chunk_order INTEGER NOT NULL,
                    chunk_hash TEXT NOT NULL,
                    embedding_hash TEXT,
                    is_embedded BOOLEAN DEFAULT FALSE,
                    is_indexed BOOLEAN DEFAULT FALSE,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    FOREIGN KEY (doc_id) REFERENCES documents (doc_id)
                )
            """)
            
            # Indexes
            conn.execute("CREATE INDEX IF NOT EXISTS idx_doc_status ON documents(status)")
            conn.execute("CREATE INDEX IF NOT EXISTS idx_doc_content_hash ON documents(content_hash)")
            conn.execute("CREATE INDEX IF NOT EXISTS idx_chunk_doc_id ON chunks(doc_id)")
            conn.execute("CREATE INDEX IF NOT EXISTS idx_chunk_embedding ON chunks(is_embedded)")
            
            conn.commit()
    
    def add_document(self, doc_id: str, filename: str, content_hash: str, 
                    file_size: int = None, mime_type: str = None, 
                    metadata: Dict[str, Any] = None) -> bool:
        """Add document to ledger if not already exists."""
        
        with sqlite3.connect(self.db_path) as conn:
            # Check if document already exists
            cursor = conn.execute(
                "SELECT doc_id, content_hash FROM documents WHERE doc_id = ?",
                (doc_id,)
            )
            existing = cursor.fetchone()
            
            if existing:
                if existing[1] == content_hash:
                    return False  # Document already processed
                else:
                    # Content changed, increment version
                    conn.execute("""
                        UPDATE documents 
                        SET content_hash = ?, version = version + 1, 
                            status = 'pending', last_updated = CURRENT_TIMESTAMP,
                            filename = ?, file_size = ?, mime_type = ?, metadata = ?
                        WHERE doc_id = ?
                    """, (content_hash, filename, file_size, mime_type, 
                         json.dumps(metadata) if metadata else None, doc_id))
            else:
                # New document
                conn.execute("""
                    INSERT INTO documents 
                    (doc_id, filename, content_hash, file_size, mime_type, metadata)
                    VALUES (?, ?, ?, ?, ?, ?)
                """, (doc_id, filename, content_hash, file_size, mime_type,
                     json.dumps(metadata) if metadata else None))
            
            conn.commit()
            return True
    
    def update_status(self, doc_id: str, status: IngestionStatus, 
                     error_message: str = None):
        """Update document processing status."""
        with sqlite3.connect(self.db_path) as conn:
            conn.execute("""
                UPDATE documents 
                SET status = ?, error_message = ?, last_updated = CURRENT_TIMESTAMP
                WHERE doc_id = ?
            """, (status.value, error_message, doc_id))
            conn.commit()
    
    def add_chunks(self, doc_id: str, chunks: List[Dict[str, Any]]):
        """Add chunks for a document."""
        with sqlite3.connect(self.db_path) as conn:
            # Clear existing chunks for document
            conn.execute("DELETE FROM chunks WHERE doc_id = ?", (doc_id,))
            
            # Insert new chunks
            for chunk in chunks:
                conn.execute("""
                    INSERT INTO chunks 
                    (chunk_id, doc_id, chunk_order, chunk_hash)
                    VALUES (?, ?, ?, ?)
                """, (chunk["chunk_id"], doc_id, chunk["order"], chunk["sha256"]))
            
            # Update document chunks count
            conn.execute("""
                UPDATE documents 
                SET chunks_count = ?, last_updated = CURRENT_TIMESTAMP
                WHERE doc_id = ?
            """, (len(chunks), doc_id))
            
            conn.commit()
    
    def mark_chunks_embedded(self, chunk_ids: List[str], embedding_model: str):
        """Mark chunks as embedded."""
        with sqlite3.connect(self.db_path) as conn:
            placeholders = ",".join("?" * len(chunk_ids))
            conn.execute(f"""
                UPDATE chunks 
                SET is_embedded = TRUE, embedding_hash = ?
                WHERE chunk_id IN ({placeholders})
            """, [embedding_model] + chunk_ids)
            
            # Update document embedding model
            if chunk_ids:
                conn.execute("""
                    UPDATE documents 
                    SET embedding_model = ?, last_updated = CURRENT_TIMESTAMP
                    WHERE doc_id IN (
                        SELECT DISTINCT doc_id FROM chunks WHERE chunk_id IN ({})
                    )
                """.format(placeholders), [embedding_model] + chunk_ids)
            
            conn.commit()
    
    def get_document_status(self, doc_id: str) -> Optional[Dict[str, Any]]:
        """Get document status and info."""
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.execute("""
                SELECT doc_id, filename, content_hash, status, version, 
                       chunks_count, embedding_model, error_message, metadata,
                       upload_timestamp, last_updated
                FROM documents WHERE doc_id = ?
            """, (doc_id,))
            
            row = cursor.fetchone()
            if not row:
                return None
            
            return {
                "doc_id": row[0],
                "filename": row[1],
                "content_hash": row[2],
                "status": row[3],
                "version": row[4],
                "chunks_count": row[5],
                "embedding_model": row[6],
                "error_message": row[7],
                "metadata": json.loads(row[8]) if row[8] else {},
                "upload_timestamp": row[9],
                "last_updated": row[10]
            }
    
    def list_documents(self, status: IngestionStatus = None) -> List[Dict[str, Any]]:
        """List documents, optionally filtered by status."""
        with sqlite3.connect(self.db_path) as conn:
            if status:
                cursor = conn.execute("""
                    SELECT doc_id, filename, status, version, chunks_count, 
                           embedding_model, last_updated
                    FROM documents WHERE status = ?
                    ORDER BY last_updated DESC
                """, (status.value,))
            else:
                cursor = conn.execute("""
                    SELECT doc_id, filename, status, version, chunks_count, 
                           embedding_model, last_updated
                    FROM documents
                    ORDER BY last_updated DESC
                """)
            
            return [
                {
                    "doc_id": row[0],
                    "filename": row[1],
                    "status": row[2],
                    "version": row[3],
                    "chunks_count": row[4],
                    "embedding_model": row[5],
                    "last_updated": row[6]
                }
                for row in cursor.fetchall()
            ]
    
    def get_stats(self) -> Dict[str, Any]:
        """Get ledger statistics."""
        with sqlite3.connect(self.db_path) as conn:
            # Document counts by status
            cursor = conn.execute("""
                SELECT status, COUNT(*) FROM documents GROUP BY status
            """)
            status_counts = dict(cursor.fetchall())
            
            # Total chunks
            cursor = conn.execute("SELECT COUNT(*) FROM chunks")
            total_chunks = cursor.fetchone()[0]
            
            # Embedded chunks
            cursor = conn.execute("SELECT COUNT(*) FROM chunks WHERE is_embedded = TRUE")
            embedded_chunks = cursor.fetchone()[0]
            
            return {
                "total_documents": sum(status_counts.values()),
                "status_breakdown": status_counts,
                "total_chunks": total_chunks,
                "embedded_chunks": embedded_chunks,
                "embedding_progress": embedded_chunks / max(1, total_chunks)
            }