from sqlalchemy.orm import Session
from pathlib import Path
from typing import List, Optional
import asyncio
import logging

from models import Document, VectorChunk
from services.embedding_service import EmbeddingService
from services.document_processor import DocumentProcessor

logging.basicConfig(level=logging.INFO)

class DocumentService:
    def __init__(self, db: Session):
        self.db = db
        self.embedding_service = EmbeddingService()
        self.doc_processor = DocumentProcessor()
    
    async def process_document(self, file_path: Path, filename: str, content_type: str) -> Document:
        """Process a document and store its embeddings"""
        
        # Create document record
        document = Document(
            filename=filename,
            content_type=content_type,
            status="processing"
        )
        self.db.add(document)
        self.db.commit()
        self.db.refresh(document)
        
        try:
            # Extract chunks from document
            logging.info(f"Processing document: {filename}")
            chunks = await self.doc_processor.extract_chunks(file_path)
            
            # Generate embeddings
            logging.info(f"Generating embeddings for {len(chunks)} chunks")
            embeddings = await self.embedding_service.embed_chunks(chunks)
            
            # Store chunks and embeddings
            for i, (chunk_text, embedding) in enumerate(zip(chunks, embeddings)):
                vector_chunk = VectorChunk(
                    document_id=document.id,
                    content=chunk_text,
                    embedding=embedding.tolist(),  # Convert numpy array to list
                    chunk_index=i
                )
                self.db.add(vector_chunk)
            
            # Update document status
            document.status = "completed"
            self.db.commit()
            
            logging.info(f"Document processed successfully: {filename}")
            return document
            
        except Exception as e:
            # Update document status to failed
            document.status = "failed"
            self.db.commit()
            logging.error(f"Document processing failed: {e}")
            raise
    
    def list_documents(self) -> List[Document]:
        """List all documents"""
        return self.db.query(Document).order_by(Document.created_at.desc()).all()
    
    def get_document(self, document_id: str) -> Optional[Document]:
        """Get a document by ID"""
        return self.db.query(Document).filter(Document.id == document_id).first()
    
    def delete_document(self, document_id: str) -> bool:
        """Delete a document and its chunks"""
        document = self.get_document(document_id)
        if document:
            self.db.delete(document)
            self.db.commit()
            return True
        return False