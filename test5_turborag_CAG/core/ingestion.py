
from pathlib import Path
from docling import DoclingDocument

def ingest(file_path: str, ocr: bool = True):
    doc = DoclingDocument.from_file(Path(file_path), ocr=ocr)
    return [doc]
