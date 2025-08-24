import json
import hashlib
from typing import List, Dict, Any, Iterator
from pathlib import Path
from dataclasses import dataclass
import numpy as np

@dataclass
class EmbeddedChunk:
    chunk_id: str
    model: str
    vector: List[float]
    dim: int
    sha256: str

class Embedder:
    """Generate embeddings for text chunks with caching."""
    
    def __init__(self, model_name: str = "sentence-transformers/all-MiniLM-L6-v2"):
        self.model_name = model_name
        self.model = None
        self._load_model()
    
    def _load_model(self):
        """Load embedding model."""
        try:
            from sentence_transformers import SentenceTransformer
            self.model = SentenceTransformer(self.model_name)
        except ImportError:
            raise ImportError(
                "sentence-transformers not installed. "
                "Install with: pip install sentence-transformers"
            )
    
    def _compute_embedding_hash(self, text: str, model: str) -> str:
        """Compute hash for embedding cache lookup."""
        content = f"{model}:{text}"
        return hashlib.sha256(content.encode()).hexdigest()
    
    def embed_text(self, text: str) -> List[float]:
        """Generate embedding for text."""
        if self.model is None:
            self._load_model()
        
        # Generate embedding
        embedding = self.model.encode(text)
        
        # Convert to list for JSON serialization
        if isinstance(embedding, np.ndarray):
            embedding = embedding.tolist()
        
        return embedding
    
    def embed_chunk(self, chunk_data: Dict[str, Any]) -> EmbeddedChunk:
        """
        Embed a single chunk.
        
        Expected output format per claude.md:
        {chunk_id, model, vector, dim, sha256}
        """
        chunk_id = chunk_data["chunk_id"]
        text = chunk_data["text"]
        
        # Generate embedding
        vector = self.embed_text(text)
        
        # Compute embedding hash for caching
        embedding_hash = self._compute_embedding_hash(text, self.model_name)
        
        return EmbeddedChunk(
            chunk_id=chunk_id,
            model=self.model_name,
            vector=vector,
            dim=len(vector),
            sha256=embedding_hash
        )
    
    def process_jsonl(self, input_jsonl: str, output_jsonl: str = None) -> str:
        """Process deduped chunks and generate embeddings."""
        
        input_path = Path(input_jsonl)
        if output_jsonl is None:
            output_jsonl = input_path.parent / f"{input_path.stem}_embedded.jsonl"
        
        output_path = Path(output_jsonl)
        output_path.parent.mkdir(parents=True, exist_ok=True)
        
        processed_count = 0
        
        with open(input_path, 'r') as infile, open(output_path, 'w') as outfile:
            for line in infile:
                chunk_data = json.loads(line.strip())
                
                # TODO: Check embedding cache before generating
                embedded_chunk = self.embed_chunk(chunk_data)
                
                # Write embedded chunk
                embedded_dict = {
                    "chunk_id": embedded_chunk.chunk_id,
                    "model": embedded_chunk.model,
                    "vector": embedded_chunk.vector,
                    "dim": embedded_chunk.dim,
                    "sha256": embedded_chunk.sha256
                }
                outfile.write(json.dumps(embedded_dict) + '\n')
                
                processed_count += 1
                if processed_count % 100 == 0:
                    print(f"Embedded {processed_count} chunks...")
        
        print(f"Embedding complete: {processed_count} chunks processed")
        return str(output_path)