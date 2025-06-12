
#--- embed_utils.py ---

from sentence_transformers import SentenceTransformer
import numpy as np

model = SentenceTransformer('all-MiniLM-L6-v2')

def embed_chunks(chunks):
    return model.encode(chunks)

def search_similar_chunks(query, chunk_embeddings, chunks, top_k=3):
    query_vec = model.encode(query)
    similarities = [np.dot(query_vec, emb) / (np.linalg.norm(query_vec) * np.linalg.norm(emb)) for emb in chunk_embeddings]
    top_indices = np.argsort(similarities)[::-1][:top_k]
    return [chunks[i] for i in top_indices]
