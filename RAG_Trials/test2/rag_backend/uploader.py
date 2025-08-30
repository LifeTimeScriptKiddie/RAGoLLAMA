import requests
import logging
from config import OPEN_WEBUI_URL, HEADERS
import os

logging.basicConfig(level=logging.INFO)

def list_knowledge_bases():
    url = f"{OPEN_WEBUI_URL}/api/knowledge"
    try:
        res = requests.get(url, headers=HEADERS)
        res.raise_for_status()
        return res.json()
    except requests.RequestException as e:
        logging.error(f"Error listing knowledge bases: {e}")
        return []

def create_knowledge_base(name: str, description: str = ""):
    url = f"{OPEN_WEBUI_URL}/api/knowledge"
    payload = {"name": name, "description": description}
    try:
        res = requests.post(url, headers=HEADERS, json=payload)
        res.raise_for_status()
        return res.json()
    except requests.RequestException as e:
        logging.error(f"Error creating knowledge base: {e}")
        return None

def upload_file(knowledge_id: str, filepath: str):
    url = f"{OPEN_WEBUI_URL}/api/knowledge/{knowledge_id}/documents"
    try:
        with open(filepath, "rb") as f:
            files = {"file": f}
            res = requests.post(url, headers={"Authorization": HEADERS["Authorization"]}, files=files)
            res.raise_for_status()
            return res.json()
    except requests.RequestException as e:
        logging.error(f"Error uploading file: {e}")
        return None

def sync_pdf_folder_to_knowledge(folder_path: str, knowledge_id: str):
    for filename in os.listdir(folder_path):
        if filename.endswith(".pdf"):
            full_path = os.path.join(folder_path, filename)
            result = upload_file(knowledge_id, full_path)
            logging.info(f"Uploaded {filename}: {result}")
