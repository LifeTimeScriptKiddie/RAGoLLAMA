import requests
import logging
from typing import Union, Dict
from config import OLLAMA_URL, OPEN_WEBUI_URL, HEADERS  # Assuming HEADERS contains authorization, e.g., {"Authorization": "Bearer <token>"}

logging.basicConfig(level=logging.INFO)

DEFAULT_TIMEOUT = 10  # seconds

# Example of how HEADERS might be defined in config.py (for context):
# import os
# HEADERS = {"Authorization": f"Bearer {os.environ.get('OPEN_WEBUI_API_KEY')}"}


def query_ollama(prompt: str, model: str = "llama3") -> str:
    """
    Send a prompt to Ollama and return the response.
    """
    url = f"{OLLAMA_URL}/api/generate"
    payload = {
        "model": model,
        "prompt": prompt,
        "stream": False
    }

    try:
        logging.info(f"Querying Ollama model '{model}'")
        res = requests.post(url, json=payload, timeout=DEFAULT_TIMEOUT)
        res.raise_for_status()
        return res.json().get("response", "")
    except requests.RequestException as e:
        logging.error(f"Ollama query failed: {type(e).__name__}: {e}")
        return f"Error: {e}"


def query_open_webui(query: str, model: str) -> Union[Dict, str]:
    """
    Send a chat message to Open WebUI and return the response.
    """
    url = f"{OPEN_WEBUI_URL}/api/chat"
    payload = {
        "messages": [{"role": "user", "content": query}],
        "model": model
    }

    try:
        logging.info(f"Querying Open WebUI with model '{model}'")
        res = requests.post(url, headers=HEADERS, json=payload, timeout=DEFAULT_TIMEOUT)
        res.raise_for_status()
        return res.json()
    except requests.RequestException as e:
        logging.error(f"Open WebUI query failed: {type(e).__name__}: {e}")
        return f"Error: {e}"


def upload_file_to_knowledge(knowledge_id: str, filepath: str) -> Union[Dict, str]:
    """
    Upload a file to a knowledge base in Open WebUI.
    """
    url = f"{OPEN_WEBUI_URL}/api/knowledge/{knowledge_id}/documents"

    try:
        with open(filepath, "rb") as f:
            files = {"file": f}
            # Use the imported HEADERS directly, handling potential missing key
            auth_header = HEADERS.get("Authorization")
            if not auth_header:
                logging.warning("Authorization header not found in HEADERS.")
            logging.info(f"Uploading '{filepath}' to knowledge base '{knowledge_id}'")
            res = requests.post(url, headers=HEADERS, files=files, timeout=DEFAULT_TIMEOUT)
            res.raise_for_status()
            return res.json()
    except FileNotFoundError:
        logging.error(f"File not found: {filepath}")
        return f"Error: File not found: {filepath}"
    except requests.RequestException as e:
        logging.error(f"File upload failed: {type(e).__name__}: {e}")
        return f"Error: {type(e).__name__}: {e}"