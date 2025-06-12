from sentence_transformers import SentenceTransformer
import numpy as np
from typing import List
import logging

logging.basicConfig(level=logging.INFO)

# Lazy model load
_model = None
def get_model() -> SentenceTransformer:
    global _model
    if _model is None:
        logging.info("Loading SentenceTransformer model: all-MiniLM-L6-v2")
        _model = SentenceTransformer("all-MiniLM-L6-v2")
    return _model

def embed_chunks(chunks: List[str]) -> np.ndarray:
    """Generate vector embeddings for a list of text chunks."""
    try:
        model = get_model()
        embeddings = model.encode(chunks, convert_to_numpy=True)
        return embeddings
    except Exception as e:
        logging.error(f"Embedding failed: {e}")
        return np.array([])

def search_similar_chunks(query: str, chunk_embeddings: np.ndarray, chunks: List[str], top_k: int = 3) -> List[str]:
    """Find the top_k most similar chunks to the given query."""
    try:
        model = get_model()
        query_vec = model.encode(query, convert_to_numpy=True)
        similarities = np.dot(chunk_embeddings, query_vec) / (
            np.linalg.norm(chunk_embeddings, axis=1) * np.linalg.norm(query_vec) + 1e-10
        )
        top_indices = np.argsort(similarities)[::-1][:top_k]
        return [chunks[i] for i in top_indices]
    except Exception as e:
        logging.error(f"Similarity search failed: {e}")
        return []
