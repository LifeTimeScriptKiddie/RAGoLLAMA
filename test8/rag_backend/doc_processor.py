from pathlib import Path
import subprocess
import logging
from langchain_docling.loader import DoclingLoader, ExportType
from vectorizer import embed_chunks
from typing import List, Tuple
import numpy as np

logging.basicConfig(level=logging.INFO)

def build_vectordb_from_pdf(pdf_path: Path) -> Tuple[List[str], np.ndarray]:
    """Uses Docling to chunk a PDF and returns chunks with embeddings."""
    logging.info(f"Loading PDF via Docling: {pdf_path}")
    loader = DoclingLoader(file_path=[str(pdf_path)], export_type=ExportType.DOC_CHUNKS)
    docs = loader.load()
    
    # Extract text content from documents
    chunks = [doc.page_content for doc in docs]
    
    # Generate embeddings
    embeddings = embed_chunks(chunks)
    
    logging.info(f"Processed {len(chunks)} chunks from PDF")
    return chunks, embeddings
logging.basicConfig(level=logging.INFO)

def ocr_pdf(input_path: Path, output_path: Path) -> bool:
    """Convert image-based PDF to text-searchable PDF using OCRmyPDF."""
    try:
        subprocess.run(["ocrmypdf", str(input_path), str(output_path)], check=True)
        return True
    except subprocess.CalledProcessError as e:
        logging.error(f"OCR failed: {e}")
        return False

# def extract_text_from_pdf(pdf_path: Path) -> str:
#     """Extract all text from a PDF file. Falls back to OCR if needed."""
#     try:
#         reader = PdfReader(str(pdf_path))
#         text = ""
#         for i, page in enumerate(reader.pages):
#             try:
#                 extracted = page.extract_text()
#                 if extracted:
#                     text += extracted
#             except Exception as e:
#                 logging.warning(f"Could not extract text from page {i}: {e}")
#         if not text.strip():
#             logging.info("No text found. Trying OCR...")
#             ocr_output = pdf_path.parent / f"ocr_{pdf_path.name}"
#             if ocr_pdf(pdf_path, ocr_output):
#                 return extract_text_from_pdf(ocr_output)
#         return text
#     except Exception as e:
#         logging.error(f"Failed to open PDF: {e}")
#         return ""

# def split_text_into_chunks(text: str, chunk_size: int = 1000, overlap: int = 150) -> List[str]:
#     """Split large text into overlapping chunks for RAG models."""
#     splitter = RecursiveCharacterTextSplitter(chunk_size=chunk_size, chunk_overlap=overlap)
#     docs = splitter.create_documents([text])
#     return [doc.page_content for doc in docs]


