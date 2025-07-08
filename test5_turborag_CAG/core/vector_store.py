
import faiss, numpy as np
from sentence_transformers import SentenceTransformer
import json
from pathlib import Path
import os
import fcntl

# Note: fcntl is a Unix-specific module and will not work on Windows.
# This is acceptable for the Dockerized environment but limits portability.

_model = SentenceTransformer("all-MiniLM-L6-v2")

DATA_PATH = Path(os.environ.get("SHARED_DATA_PATH", "/app/data"))
DATA_PATH.mkdir(exist_ok=True)
INDEX_PATH = DATA_PATH / "vector_store.faiss"
TEXTS_PATH = DATA_PATH / "vector_store.json"
LOCK_PATH = DATA_PATH / "vector_store.lock"

def _load_store():
    """Loads the FAISS index and corresponding texts from disk."""
    if INDEX_PATH.exists():
        index = faiss.read_index(str(INDEX_PATH))
        if TEXTS_PATH.exists():
            with open(TEXTS_PATH, "r") as f:
                texts = json.load(f)
        else:
            texts = []
        return index, texts
    return None, []

def add(texts):
    """Adds texts to the vector store."""
    with open(LOCK_PATH, "w") as lock_file:
        fcntl.flock(lock_file, fcntl.LOCK_EX)
        
        index, stored_texts = _load_store()
        
        emb = _model.encode(texts)
        if index is None:
            d = emb.shape[1]
            if d == 0:
                fcntl.flock(lock_file, fcntl.LOCK_UN)
                return
            index = faiss.IndexFlatL2(d)
        
        index.add(np.array(emb, dtype=np.float32))
        stored_texts.extend(texts)
        
        faiss.write_index(index, str(INDEX_PATH))
        with open(TEXTS_PATH, "w") as f:
            json.dump(stored_texts, f)
            
        fcntl.flock(lock_file, fcntl.LOCK_UN)

def query(q, k=5):
    """Queries the vector store."""
    with open(LOCK_PATH, "r") as lock_file:
        fcntl.flock(lock_file, fcntl.LOCK_SH)
        
        index, texts = _load_store()
        
        if index is None:
            fcntl.flock(lock_file, fcntl.LOCK_UN)
            return []
        
        emb = _model.encode([q])
        D, I = index.search(np.array(emb, dtype=np.float32), k)
        
        fcntl.flock(lock_file, fcntl.LOCK_UN)

    results = []
    for n, i in enumerate(I[0]):
        if i < len(texts) and i < index.ntotal:
            results.append((texts[i], float(D[0][n])))
    return results
