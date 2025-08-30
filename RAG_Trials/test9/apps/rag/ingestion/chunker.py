import hashlib
import json
from typing import Iterator, List, Dict, Any
from dataclasses import dataclass
from pathlib import Path

@dataclass
class TextChunk:
    doc_id: str
    chunk_id: str
    text: str
    sha256: str
    order: int
    meta: Dict[str, Any]

class Chunker:
    """Deterministic text chunking."""
    
    def __init__(self, chunk_size: int = 512, chunk_overlap: int = 50):
        self.chunk_size = chunk_size
        self.chunk_overlap = chunk_overlap
    
    def chunk_text(self, text: str, doc_id: str, meta: Dict[str, Any] = None) -> Iterator[TextChunk]:
        """
        Chunk text deterministically.
        
        Expected output format per claude.md:
        {doc_id, chunk_id, text, sha256, order, meta}
        """
        if meta is None:
            meta = {}
        
        # Simple word-based chunking (TODO: implement smarter semantic chunking)
        words = text.split()
        
        if len(words) <= self.chunk_size:
            # Single chunk
            chunk_text = " ".join(words)
            chunk_hash = hashlib.sha256(chunk_text.encode()).hexdigest()
            chunk_id = f"{doc_id}_{chunk_hash[:8]}"
            
            yield TextChunk(
                doc_id=doc_id,
                chunk_id=chunk_id,
                text=chunk_text,
                sha256=chunk_hash,
                order=0,
                meta={**meta, "chunk_size": len(words)}
            )
            return
        
        # Multiple chunks with overlap
        chunk_order = 0
        start_idx = 0
        
        while start_idx < len(words):
            end_idx = min(start_idx + self.chunk_size, len(words))
            chunk_words = words[start_idx:end_idx]
            chunk_text = " ".join(chunk_words)
            
            # Generate deterministic chunk ID
            chunk_hash = hashlib.sha256(chunk_text.encode()).hexdigest()
            chunk_id = f"{doc_id}_chunk_{chunk_order:04d}_{chunk_hash[:8]}"
            
            yield TextChunk(
                doc_id=doc_id,
                chunk_id=chunk_id,
                text=chunk_text,
                sha256=chunk_hash,
                order=chunk_order,
                meta={
                    **meta,
                    "chunk_size": len(chunk_words),
                    "start_word": start_idx,
                    "end_word": end_idx
                }
            )
            
            chunk_order += 1
            
            # Move window with overlap
            if end_idx >= len(words):
                break
            start_idx = end_idx - self.chunk_overlap
    
    def process_jsonl(self, input_jsonl: str, output_jsonl: str = None) -> str:
        """Process Docling JSONL output into chunked JSONL."""
        
        input_path = Path(input_jsonl)
        if output_jsonl is None:
            output_jsonl = input_path.parent / f"{input_path.stem}_chunked.jsonl"
        
        output_path = Path(output_jsonl)
        output_path.parent.mkdir(parents=True, exist_ok=True)
        
        with open(input_path, 'r') as infile, open(output_path, 'w') as outfile:
            for line in infile:
                doc_data = json.loads(line.strip())
                
                # Extract document info
                doc_id = doc_data["doc_id"]
                text = doc_data["text"]
                meta = doc_data.get("meta", {})
                
                # Add page info to meta
                meta["page"] = doc_data.get("page", 1)
                meta["mime"] = doc_data.get("mime", "text/plain")
                meta["doc_sha256"] = doc_data.get("sha256")
                
                # Chunk the text
                for chunk in self.chunk_text(text, doc_id, meta):
                    chunk_dict = {
                        "doc_id": chunk.doc_id,
                        "chunk_id": chunk.chunk_id,
                        "text": chunk.text,
                        "sha256": chunk.sha256,
                        "order": chunk.order,
                        "meta": chunk.meta
                    }
                    outfile.write(json.dumps(chunk_dict) + '\n')
        
        return str(output_path)