import json
import hashlib
from typing import Set, Dict, Iterator
from pathlib import Path
from dataclasses import dataclass

@dataclass
class DedupedChunk:
    chunk_id: str
    text: str
    sha256: str
    doc_ids: list
    order: int
    meta: Dict

class Deduper:
    """Fast fuzzy deduplication using content hashing."""
    
    def __init__(self, similarity_threshold: float = 0.95):
        self.similarity_threshold = similarity_threshold
        self.seen_hashes: Set[str] = set()
        self.chunk_registry: Dict[str, DedupedChunk] = {}
    
    def _normalize_text(self, text: str) -> str:
        """Normalize text for deduplication."""
        # Simple normalization (TODO: implement MinHash/SimHash for fuzzy dedup)
        return " ".join(text.lower().split())
    
    def _compute_content_hash(self, normalized_text: str) -> str:
        """Compute content hash for deduplication."""
        return hashlib.sha256(normalized_text.encode()).hexdigest()
    
    def deduplicate_chunk(self, chunk_data: Dict) -> Iterator[DedupedChunk]:
        """Deduplicate a single chunk."""
        
        text = chunk_data["text"]
        chunk_id = chunk_data["chunk_id"]
        doc_id = chunk_data["doc_id"]
        
        # Normalize and hash
        normalized_text = self._normalize_text(text)
        content_hash = self._compute_content_hash(normalized_text)
        
        if content_hash in self.seen_hashes:
            # Duplicate found, merge with existing
            existing_chunk = self.chunk_registry[content_hash]
            if doc_id not in existing_chunk.doc_ids:
                existing_chunk.doc_ids.append(doc_id)
            return  # Don't yield, it's a duplicate
        
        # New unique chunk
        self.seen_hashes.add(content_hash)
        deduped_chunk = DedupedChunk(
            chunk_id=chunk_id,
            text=text,
            sha256=content_hash,
            doc_ids=[doc_id],
            order=chunk_data["order"],
            meta={
                **chunk_data["meta"],
                "dedup_hash": content_hash,
                "is_deduplicated": False
            }
        )
        
        self.chunk_registry[content_hash] = deduped_chunk
        yield deduped_chunk
    
    def process_jsonl(self, input_jsonl: str, output_jsonl: str = None) -> str:
        """Process chunked JSONL and remove duplicates."""
        
        input_path = Path(input_jsonl)
        if output_jsonl is None:
            output_jsonl = input_path.parent / f"{input_path.stem}_deduped.jsonl"
        
        output_path = Path(output_jsonl)
        output_path.parent.mkdir(parents=True, exist_ok=True)
        
        # First pass: collect all chunks and deduplicate
        with open(input_path, 'r') as infile:
            for line in infile:
                chunk_data = json.loads(line.strip())
                list(self.deduplicate_chunk(chunk_data))  # Consume iterator
        
        # Second pass: write deduplicated chunks
        with open(output_path, 'w') as outfile:
            for chunk in self.chunk_registry.values():
                chunk_dict = {
                    "chunk_id": chunk.chunk_id,
                    "text": chunk.text,
                    "sha256": chunk.sha256,
                    "doc_ids": chunk.doc_ids,
                    "order": chunk.order,
                    "meta": chunk.meta
                }
                outfile.write(json.dumps(chunk_dict) + '\n')
        
        # Log deduplication stats
        total_processed = len(self.seen_hashes)
        unique_chunks = len(self.chunk_registry)
        duplicates_removed = total_processed - unique_chunks
        
        print(f"Deduplication complete:")
        print(f"  Total chunks processed: {total_processed}")
        print(f"  Unique chunks: {unique_chunks}")
        print(f"  Duplicates removed: {duplicates_removed}")
        
        return str(output_path)