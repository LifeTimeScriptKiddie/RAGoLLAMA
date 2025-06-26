from sentence_transformers import SentenceTransformer
import numpy as np
from typing import List, Tuple, Union
import logging
import os

logging.basicConfig(level=logging.INFO)

# ---- Configurable global model cache ----
_model = None

def get_model(model_name: str = "all-MiniLM-L6-v2") -> SentenceTransformer:
    """
    Load the SentenceTransformer model (only once per session).
    :param model_name: The HuggingFace model name to load.
    :return: SentenceTransformer model instance
    """
    global _model
    if _model is None:
        logging.info(f"Loading SentenceTransformer model: {model_name}")
        _model = SentenceTransformer(model_name)
    return _model

def embed_chunks(chunks: List[str], model_name: str = "all-MiniLM-L6-v2") -> np.ndarray:
    """
    Generate vector embeddings for a list of text chunks.
    :param chunks: List of text strings
    :param model_name: Optional model name
    :return: Numpy array of embeddings
    """
    try:
        model = get_model(model_name)
        embeddings = model.encode(chunks, convert_to_numpy=True)
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
    model_name: str = "all-MiniLM-L6-v2"
) -> Union[List[str], List[Tuple[str, float]]]:
    """
    Find the top_k most similar chunks to the given query using cosine similarity.
    :param query: User input/question
    :param chunk_embeddings: Numpy array of precomputed chunk embeddings
    :param chunks: Original text chunks
    :param top_k: Number of top matches to return
    :param return_scores: If True, return (chunk, score) tuples
    :param model_name: Optional model name override
    :return: List of matching chunks or (chunk, score) tuples
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

# Optional utility: Save/load embeddings to disk
def save_embeddings(path: str, chunks: List[str], embeddings: np.ndarray):
    np.savez(path, chunks=chunks, embeddings=embeddings)
    logging.info(f"Saved embeddings to {path}")

def load_embeddings(path: str) -> Tuple[List[str], np.ndarray]:
    data = np.load(path, allow_pickle=True)
    return data['chunks'].tolist(), data['embeddings']