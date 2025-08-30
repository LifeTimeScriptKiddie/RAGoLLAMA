
import requests
import logging
import os
from typing import Optional, List, Dict
from config import OPEN_WEBUI_URL, HEADERS

logging.basicConfig(level=logging.INFO)

def list_knowledge_bases() -> List[Dict]:
    """Get a list of available knowledge bases from Open WebUI."""
    url = f"{OPEN_WEBUI_URL}/api/knowledge"
    try:
        res = requests.get(url, headers=HEADERS)
        res.raise_for_status()
        return res.json()
    except requests.RequestException as e:
        logging.error(f"[!] Error listing knowledge bases: {e}")
        return []

def create_knowledge_base(name: str, description: str = "") -> Optional[Dict]:
    """Create a new knowledge base in Open WebUI."""
    url = f"{OPEN_WEBUI_URL}/api/knowledge"
    payload = {"name": name, "description": description}
    try:
        res = requests.post(url, headers=HEADERS, json=payload)
        res.raise_for_status()
        return res.json()
    except requests.RequestException as e:
        logging.error(f"[!] Error creating knowledge base '{name}': {e}")
        return None

def upload_file(knowledge_id: str, filepath: str) -> Optional[Dict]:
    """Upload a single PDF file to a specified knowledge base."""
    if not os.path.isfile(filepath):
        logging.warning(f"[!] File not found: {filepath}")
        return None

    url = f"{OPEN_WEBUI_URL}/api/knowledge/{knowledge_id}/documents"
    try:
        with open(filepath, "rb") as f:
            files = {"file": f}
            headers = {"Authorization": HEADERS.get("Authorization", "")}
            res = requests.post(url, headers=headers, files=files)
            res.raise_for_status()
            return res.json()
    except requests.RequestException as e:
        logging.error(f"[!] Upload failed for '{filepath}': {e}")
        return None

def sync_pdf_folder_to_knowledge(folder_path: str, knowledge_id: str) -> None:
    """Upload all PDF files in a folder to the specified knowledge base."""
    if not os.path.isdir(folder_path):
        logging.error(f"[!] Invalid folder path: {folder_path}")
        return

    pdf_files = [f for f in os.listdir(folder_path) if f.lower().endswith(".pdf")]
    if not pdf_files:
        logging.warning(f"[!] No PDF files found in {folder_path}")
        return

    for filename in pdf_files:
        full_path = os.path.join(folder_path, filename)
        result = upload_file(knowledge_id, full_path)
        logging.info(f"[+] Uploaded {filename}: {result}")
