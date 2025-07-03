from sentence_transformers import SentenceTransformer
import numpy as np
from typing import List, Tuple, Union
import logging
import os
from pathlib import Path
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

logging.basicConfig(level=logging.INFO)

# ---- Global model cache ----
_model = None

def get_model(model_name: str = None) -> SentenceTransformer:
    """
    Load the SentenceTransformer model (singleton).
    """
    global _model
    if _model is None:
        model_name = model_name or os.getenv("EMBED_MODEL", "all-MiniLM-L6-v2")
        logging.info(f"Loading SentenceTransformer model: {model_name}")
        _model = SentenceTransformer(model_name)
    return _model


def embed_chunks(chunks: List[str], model_name: str = None) -> np.ndarray:
    """
    Generate vector embeddings for a list of text chunks.
    """
    try:
        model = get_model(model_name)
        embeddings = model.encode(chunks, convert_to_numpy=True)
        logging.info(f"Embedded {len(chunks)} chunks.")
        return embeddings
    except Exception as e:
        logging.error(f"Embedding failed: {e}")
        return np.array([])


def search_similar_chunks(
    query: str,
    chunk_embeddings: np.ndarray,
    chunks: List[str],
    top_k: int = 3,
    return_scores: bool = False,
    model_name: str = None
) -> Union[List[str], List[Tuple[str, float]]]:
    """
    Find the top_k most similar chunks to a query using cosine similarity.
    """
    try:
        model = get_model(model_name)
        query_vec = model.encode(query, convert_to_numpy=True)

        similarities = np.dot(chunk_embeddings, query_vec) / (
            np.linalg.norm(chunk_embeddings, axis=1) * np.linalg.norm(query_vec) + 1e-10
        )
        top_indices = np.argsort(similarities)[::-1][:top_k]

        if return_scores:
            return [(chunks[i], float(similarities[i])) for i in top_indices]
        else:
            return [chunks[i] for i in top_indices]
    except Exception as e:
        logging.error(f"Similarity search failed: {e}")
        return []


def save_embeddings(path: Union[str, Path], chunks: List[str], embeddings: np.ndarray):
    """
    Save chunk text and embeddings to a .npz file.
    """
    try:
        path = Path(path)
        np.savez(path, chunks=chunks, embeddings=embeddings)
        logging.info(f"Saved embeddings to {path}")
    except Exception as e:
        logging.error(f"Failed to save embeddings: {e}")


def load_embeddings(path: Union[str, Path]) -> Tuple[List[str], np.ndarray]:
    """
    Load chunk text and embeddings from a .npz file.
    """
    try:
        path = Path(path)
        data = np.load(path, allow_pickle=True)
        return data['chunks'].tolist(), data['embeddings']
    except Exception as e:
        logging.error(f"Failed to load embeddings from {path}: {e}")
        return [], np.array([])