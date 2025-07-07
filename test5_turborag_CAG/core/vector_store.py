
import faiss, numpy as np
from sentence_transformers import SentenceTransformer
_model = SentenceTransformer("all-MiniLM-L6-v2")
_index, _texts = None, []

def add(texts):
    global _index, _texts
    emb = _model.encode(texts)
    if _index is None:
        _index = faiss.IndexFlatL2(emb.shape[1])
    _index.add(np.array(emb, dtype=np.float32))
    _texts.extend(texts)

def query(q, k=5):
    if _index is None:
        return []
    emb = _model.encode([q])
    D, I = _index.search(np.array(emb, dtype=np.float32), k)
    return [(_texts[i], float(D[0][n])) for n, i in enumerate(I[0])]
