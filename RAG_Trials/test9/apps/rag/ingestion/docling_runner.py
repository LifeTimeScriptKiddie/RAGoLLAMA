import hashlib
import json
from pathlib import Path
from typing import Iterator, Dict, Any
from dataclasses import dataclass

@dataclass
class DocumentChunk:
    doc_id: str
    page: int
    text: str
    mime: str
    sha256: str
    meta: Dict[str, Any]

class DoclingRunner:
    """Document processing using Docling."""
    
    def __init__(self, output_dir: str = "/data/processed"):
        self.output_dir = Path(output_dir)
        self.output_dir.mkdir(parents=True, exist_ok=True)
    
    def process_document(self, file_path: str, doc_id: str = None) -> Iterator[DocumentChunk]:
        """
        Process document and yield chunks.
        
        Expected output format per claude.md:
        {doc_id, page, text, mime, sha256, meta}
        """
        file_path = Path(file_path)
        
        if not file_path.exists():
            raise FileNotFoundError(f"Document not found: {file_path}")
        
        # Generate doc_id if not provided
        if doc_id is None:
            with open(file_path, 'rb') as f:
                content_hash = hashlib.sha256(f.read()).hexdigest()
                doc_id = content_hash[:16]
        
        # TODO: Integrate actual Docling processing
        # For now, simple text extraction placeholder
        
        try:
            # Placeholder: Read as text file
            with open(file_path, 'r', encoding='utf-8') as f:
                content = f.read()
                
            # Calculate content hash
            content_bytes = content.encode('utf-8')
            content_hash = hashlib.sha256(content_bytes).hexdigest()
            
            # Create single chunk (TODO: implement proper chunking with Docling)
            yield DocumentChunk(
                doc_id=doc_id,
                page=1,
                text=content,
                mime="text/plain",  # TODO: detect proper MIME type
                sha256=content_hash,
                meta={
                    "filename": file_path.name,
                    "size": len(content_bytes),
                    "source": "docling_runner"
                }
            )
            
        except UnicodeDecodeError:
            # Handle binary files (PDF, etc.)
            # TODO: Implement proper Docling integration for PDF/DOC processing
            raise NotImplementedError("Binary file processing not yet implemented")
    
    def process_to_jsonl(self, file_path: str, output_file: str = None) -> str:
        """Process document and save to JSONL file."""
        
        if output_file is None:
            doc_name = Path(file_path).stem
            output_file = self.output_dir / f"{doc_name}_chunks.jsonl"
        
        output_path = Path(output_file)
        output_path.parent.mkdir(parents=True, exist_ok=True)
        
        with open(output_path, 'w') as f:
            for chunk in self.process_document(file_path):
                chunk_dict = {
                    "doc_id": chunk.doc_id,
                    "page": chunk.page,
                    "text": chunk.text,
                    "mime": chunk.mime,
                    "sha256": chunk.sha256,
                    "meta": chunk.meta
                }
                f.write(json.dumps(chunk_dict) + '\n')
        
        return str(output_path)