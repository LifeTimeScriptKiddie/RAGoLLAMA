
import requests
import logging
from config import OLLAMA_URL, OPEN_WEBUI_URL, HEADERS

logging.basicConfig(level=logging.INFO)

def query_ollama(prompt, model="llama3"):
    try:
        url = f"{OLLAMA_URL}/api/generate"
        res = requests.post(url, json={"model": model, "prompt": prompt, "stream": False})
        res.raise_for_status()
        return res.json()["response"]
    except requests.RequestException as e:
        logging.error(f"Ollama query failed: {e}")
        return f"Error: {e}"

def query_open_webui(query, model):
    try:
        url = f"{OPEN_WEBUI_URL}/api/chat"
        payload = {"messages": [{"role": "user", "content": query}], "model": model}
        res = requests.post(url, headers=HEADERS, json=payload)
        res.raise_for_status()
        return res.json()
    except requests.RequestException as e:
        logging.error(f"Open WebUI query failed: {e}")
        return f"Error: {e}"

def upload_file_to_knowledge(knowledge_id, filepath):
    try:
        url = f"{OPEN_WEBUI_URL}/api/knowledge/{knowledge_id}/documents"
        with open(filepath, "rb") as f:
            files = {"file": f}
            res = requests.post(url, headers={"Authorization": HEADERS["Authorization"]}, files=files)
            res.raise_for_status()
            return res.json()
    except requests.RequestException as e:
        logging.error(f"File upload failed: {e}")
        return f"Error: {e}"
