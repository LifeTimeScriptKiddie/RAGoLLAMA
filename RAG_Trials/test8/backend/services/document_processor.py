from pathlib import Path
from typing import List
import asyncio
import logging
import os
from langchain_docling.loader import DoclingLoader, ExportType
from langchain.text_splitter import RecursiveCharacterTextSplitter
from PyPDF2 import PdfReader

logging.basicConfig(level=logging.INFO)

class DocumentProcessor:
    """Document processing service using Docling"""
    
    async def extract_chunks(self, file_path: Path) -> List[str]:
        """Extract text chunks from a PDF document"""
        file_size = os.path.getsize(file_path) / (1024 * 1024)  # Size in MB
        logging.info(f"Processing PDF: {file_path} (Size: {file_size:.1f} MB)")
        
        try:
            # For large files (>50MB), use PyPDF2 as fallback
            if file_size > 50:
                logging.info("Large file detected, using PyPDF2 fallback")
                return await self._extract_with_pypdf2(file_path)
            else:
                logging.info("Using Docling for document processing")
                return await self._extract_with_docling(file_path)
                
        except Exception as e:
            logging.error(f"Primary extraction failed: {e}")
            logging.info("Attempting fallback extraction method")
            try:
                return await self._extract_with_pypdf2(file_path)
            except Exception as fallback_error:
                logging.error(f"Fallback extraction also failed: {fallback_error}")
                raise Exception(f"Failed to process document with both methods: {str(e)}")
    
    async def _extract_with_docling(self, file_path: Path) -> List[str]:
        """Extract chunks using Docling"""
        loader = DoclingLoader(file_path=[str(file_path)], export_type=ExportType.DOC_CHUNKS)
        docs = loader.load()
        chunks = [doc.page_content for doc in docs if doc.page_content.strip()]
        logging.info(f"Docling extracted {len(chunks)} chunks")
        return chunks
    
    async def _extract_with_pypdf2(self, file_path: Path) -> List[str]:
        """Extract chunks using PyPDF2 as fallback"""
        # Extract text from PDF
        reader = PdfReader(str(file_path))
        text = ""
        for page in reader.pages:
            text += page.extract_text() + "\n"
        
        if not text.strip():
            raise Exception("No text could be extracted from PDF")
        
        # Split into chunks
        text_splitter = RecursiveCharacterTextSplitter(
            chunk_size=1000,
            chunk_overlap=150,
            length_function=len
        )
        chunks = text_splitter.split_text(text)
        
        logging.info(f"PyPDF2 extracted {len(chunks)} chunks")
        return chunks