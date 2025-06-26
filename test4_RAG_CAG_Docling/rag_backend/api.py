import requests
import logging
from config import OLLAMA_URL, OPEN_WEBUI_URL, HEADERS

logging.basicConfig(level=logging.INFO)


def query_ollama(prompt: str, model: str = "llama3") -> str:
    """
    Send a prompt to Ollama and return the response.

    :param prompt: The text prompt to send
    :param model: The model to query (default: llama3)
    :return: The response from Ollama or error string
    """
    try:
        url = f"{OLLAMA_URL}/api/generate"
        payload = {
            "model": model,
            "prompt": prompt,
            "stream": False
        }
        res = requests.post(url, json=payload)
        res.raise_for_status()
        return res.json()["response"]
    except requests.RequestException as e:
        logging.error(f"Ollama query failed: {e}")
        return f"Error: {e}"


def query_open_webui(query: str, model: str) -> dict | str:
    """
    Send a chat message to Open WebUI and return the response.

    :param query: The user message
    :param model: The model to use
    :return: JSON response or error string
    """
    try:
        url = f"{OPEN_WEBUI_URL}/api/chat"
        payload = {
            "messages": [{"role": "user", "content": query}],
            "model": model
        }
        res = requests.post(url, headers=HEADERS, json=payload)
        res.raise_for_status()
        return res.json()
    except requests.RequestException as e:
        logging.error(f"Open WebUI query failed: {e}")
        return f"Error: {e}"


def upload_file_to_knowledge(knowledge_id: str, filepath: str) -> dict | str:
    """
    Upload a file to a knowledge base in Open WebUI.

    :param knowledge_id: Target knowledge base ID
    :param filepath: Path to the file to upload
    :return: JSON response or error string
    """
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
