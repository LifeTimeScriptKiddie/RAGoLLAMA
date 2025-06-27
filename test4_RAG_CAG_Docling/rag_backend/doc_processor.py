from pathlib import Path
import subprocess
import logging
from langchain_docling.loader import DoclingLoader, ExportType
from langchain.vectorstores import Chroma
from api import get_ollama_embedding  # You must define or import this function
#from langchain.embeddings import OpenAIEmbeddings
#from PyPDF2 import PdfReader
#from langchain.text_splitter import RecursiveCharacterTextSplitter
#from typing import List



logging.basicConfig(level=logging.INFO)


def build_vectordb_from_pdf(pdf_path: Path) -> Chroma:
    """Uses Docling to chunk a PDF and builds a Chroma vector DB using Ollama embeddings."""
    logging.info(f"Loading PDF via Docling: {pdf_path}")
    loader = DoclingLoader(file_path=[str(pdf_path)], export_type=ExportType.DOC_CHUNKS)
    docs = loader.load()

    embeddings = OllamaEmbeddings(model="nomic-embed-text")  # Or any Ollama-supported embedding model
    vectordb = Chroma.from_documents(docs, embeddings)
    return vectordb
    embeddings = get_ollama_embedding()
    vectordb = Chroma.from_documents(docs, embeddings)
    return vectordb
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


