

import requests
import logging
from config import OPEN_WEBUI_URL, HEADERS

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


