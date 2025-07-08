
from pathlib import Path
import logging

logger = logging.getLogger(__name__)

# Try to import docling components, fallback if not available
try:
    from docling.document_converter import DocumentConverter
    from docling.datamodel.base_models import InputFormat
    from docling.datamodel.pipeline_options import PdfPipelineOptions
    DOCLING_AVAILABLE = True
except ImportError as e:
    logger.warning(f"Docling not fully available: {str(e)}. Will use fallback methods.")
    DOCLING_AVAILABLE = False

def ingest(file_path: str, ocr: bool = True):
    """Ingest document using docling with proper error handling"""
    
    # If docling is available, try to use it
    if DOCLING_AVAILABLE:
        try:
            # Initialize the document converter
            pipeline_options = PdfPipelineOptions()
            pipeline_options.do_ocr = ocr
            pipeline_options.do_table_structure = True
            
            doc_converter = DocumentConverter(
                format_options={
                    InputFormat.PDF: pipeline_options,
                }
            )
            
            # Convert the document
            path = Path(file_path)
            result = doc_converter.convert(path)
            
            # Extract text content
            documents = []
            for doc in result:
                # Create a simple document-like object with text content
                doc_obj = type('Document', (), {
                    'text': doc.document.export_to_markdown(),
                    'metadata': {
                        'source': str(path),
                        'pages': len(doc.document.pages) if hasattr(doc.document, 'pages') else 1,
                        'method': 'docling'
                    }
                })()
                documents.append(doc_obj)
            
            return documents
            
        except Exception as e:
            logger.error(f"Docling failed for {file_path}: {str(e)}")
            # Continue to fallback
    
    # Use fallback ingestion
    logger.info(f"Using fallback ingestion for {file_path}")
    return _fallback_ingestion(file_path)

def _fallback_ingestion(file_path: str):
    """Fallback ingestion using PyPDF2 or plain text"""
    path = Path(file_path)
    
    # Try PDF processing first
    if path.suffix.lower() == '.pdf':
        try:
            from PyPDF2 import PdfReader
            reader = PdfReader(file_path)
            text = ""
            for page in reader.pages:
                text += page.extract_text() + "\n"
            
            doc_obj = type('Document', (), {
                'text': text,
                'metadata': {'source': str(path), 'method': 'PyPDF2', 'pages': len(reader.pages)}
            })()
            return [doc_obj]
            
        except ImportError:
            logger.warning("PyPDF2 not available for fallback PDF processing")
        except Exception as e:
            logger.error(f"PyPDF2 processing failed: {str(e)}")
    
    # Try pdfminer as another fallback for PDFs
    if path.suffix.lower() == '.pdf':
        try:
            from pdfminer.high_level import extract_text
            text = extract_text(file_path)
            
            doc_obj = type('Document', (), {
                'text': text,
                'metadata': {'source': str(path), 'method': 'pdfminer'}
            })()
            return [doc_obj]
            
        except Exception as e:
            logger.warning(f"pdfminer processing failed: {str(e)}")
    
    # For text files or as last resort
    try:
        # Try different encodings
        encodings = ['utf-8', 'latin1', 'cp1252', 'iso-8859-1']
        text = None
        
        for encoding in encodings:
            try:
                with open(file_path, 'r', encoding=encoding) as f:
                    text = f.read()
                    break
            except UnicodeDecodeError:
                continue
        
        if text is None:
            # Try binary mode as last resort
            with open(file_path, 'rb') as f:
                text = f.read().decode('utf-8', errors='ignore')
        
        doc_obj = type('Document', (), {
            'text': text,
            'metadata': {'source': str(path), 'method': 'text'}
        })()
        return [doc_obj]
        
    except Exception as e:
        logger.error(f"All ingestion methods failed for {file_path}: {str(e)}")
        doc_obj = type('Document', (), {
            'text': f"Could not process file {path.name}: {str(e)}",
            'metadata': {'source': str(path), 'error': True}
        })()
        return [doc_obj]
