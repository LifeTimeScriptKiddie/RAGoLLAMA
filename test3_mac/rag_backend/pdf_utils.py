from PyPDF2 import PdfReader
from langchain.text_splitter import RecursiveCharacterTextSplitter
import logging
from pathlib import Path
from typing import List

logging.basicConfig(level=logging.INFO)

def extract_text_from_pdf(pdf_path: Path) -> str:
    """Extract all text from a PDF file."""
    try:
        reader = PdfReader(str(pdf_path))
        text = ""
        for i, page in enumerate(reader.pages):
            try:
                extracted = page.extract_text()
                if extracted:
                    text += extracted
            except Exception as e:
                logging.warning(f"Could not extract text from page {i}: {e}")
        return text
    except Exception as e:
        logging.error(f"Failed to open PDF: {e}")
        return ""

def split_text_into_chunks(text: str, chunk_size: int = 1000, overlap: int = 150) -> List[str]:
    """Split large text into overlapping chunks for RAG models."""
    splitter = RecursiveCharacterTextSplitter(chunk_size=chunk_size, chunk_overlap=overlap)
    docs = splitter.create_documents([text])
    return [doc.page_content for doc in docs]
