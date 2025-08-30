import json
import sqlite3
import hashlib
from typing import List, Optional, Dict, Any
from pathlib import Path
import pickle

class EmbeddingCache:
    """Cache for embeddings to avoid recomputation."""
    
    def __init__(self, cache_dir: str = "/data/cache"):
        self.cache_dir = Path(cache_dir)
        self.cache_dir.mkdir(parents=True, exist_ok=True)
        self.db_path = self.cache_dir / "embeddings.db"
        self._init_db()
    
    def _init_db(self):
        """Initialize SQLite database for embedding cache."""
        with sqlite3.connect(self.db_path) as conn:
            conn.execute("""
                CREATE TABLE IF NOT EXISTS embeddings (
                    cache_key TEXT PRIMARY KEY,
                    model TEXT NOT NULL,
                    text_hash TEXT NOT NULL,
                    vector_data BLOB NOT NULL,
                    dimension INTEGER NOT NULL,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                )
            """)
            
            conn.execute("""
                CREATE INDEX IF NOT EXISTS idx_model_text_hash 
                ON embeddings(model, text_hash)
            """)
            
            conn.commit()
    
    def _compute_cache_key(self, text: str, model: str) -> str:
        """Compute cache key for text and model combination."""
        content = f"{model}:{text}"
        return hashlib.sha256(content.encode()).hexdigest()
    
    def get(self, text: str, model: str) -> Optional[List[float]]:
        """Get cached embedding if available."""
        cache_key = self._compute_cache_key(text, model)
        
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.execute(
                "SELECT vector_data FROM embeddings WHERE cache_key = ?",
                (cache_key,)
            )
            row = cursor.fetchone()
            
            if row:
                # Deserialize vector
                vector_data = pickle.loads(row[0])
                return vector_data
            
            return None
    
    def put(self, text: str, model: str, vector: List[float]) -> str:
        """Store embedding in cache."""
        cache_key = self._compute_cache_key(text, model)
        text_hash = hashlib.sha256(text.encode()).hexdigest()
        vector_data = pickle.dumps(vector)
        
        with sqlite3.connect(self.db_path) as conn:
            conn.execute("""
                INSERT OR REPLACE INTO embeddings 
                (cache_key, model, text_hash, vector_data, dimension)
                VALUES (?, ?, ?, ?, ?)
            """, (cache_key, model, text_hash, vector_data, len(vector)))
            conn.commit()
        
        return cache_key
    
    def get_stats(self) -> Dict[str, Any]:
        """Get cache statistics."""
        with sqlite3.connect(self.db_path) as conn:
            # Total entries
            cursor = conn.execute("SELECT COUNT(*) FROM embeddings")
            total_count = cursor.fetchone()[0]
            
            # Model breakdown
            cursor = conn.execute("""
                SELECT model, COUNT(*) as count 
                FROM embeddings 
                GROUP BY model
            """)
            model_counts = dict(cursor.fetchall())
            
            # Cache size (approximate)
            cursor = conn.execute("SELECT page_count * page_size FROM pragma_page_count(), pragma_page_size()")
            db_size = cursor.fetchone()[0]
            
            return {
                "total_embeddings": total_count,
                "models": model_counts,
                "db_size_bytes": db_size,
                "cache_dir": str(self.cache_dir)
            }
    
    def clear(self, model: str = None):
        """Clear cache entries (optionally for specific model)."""
        with sqlite3.connect(self.db_path) as conn:
            if model:
                conn.execute("DELETE FROM embeddings WHERE model = ?", (model,))
            else:
                conn.execute("DELETE FROM embeddings")
            conn.commit()
    
    def has_embedding(self, text: str, model: str) -> bool:
        """Check if embedding exists in cache."""
        return self.get(text, model) is not None