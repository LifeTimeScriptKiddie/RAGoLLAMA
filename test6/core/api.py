import requests
import logging
import os
from typing import Union, Dict

# Load configuration from environment variables with defaults
OLLAMA_URL = os.environ.get("OLLAMA_BASE_URL", "http://ollama:11434")
OPEN_WEBUI_URL = os.environ.get("OPEN_WEBUI_URL", "http://open-webui:8080")
OPEN_WEBUI_TOKEN = os.environ.get("OPEN_WEBUI_TOKEN", "") # Default to empty
HEADERS = {
    "Authorization": f"Bearer {OPEN_WEBUI_TOKEN}",
    "Content-Type": "application/json"
}

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


def query_open_webui(query: str, model: str) -> str:
    """
    Send a chat message to Open WebUI using the OpenAI-compatible endpoint.
    """
    # Use the OpenAI-compatible endpoint
    url = f"{OPEN_WEBUI_URL}/v1/chat/completions"
    payload = {
        "model": model,
        "messages": [{"role": "user", "content": query}],
        "stream": False
    }

    # Note: Open WebUI's OpenAI-compatible endpoint doesn't require the Bearer token
    # in the same way if auth is disabled. We'll send it anyway.
    headers = {
        "Authorization": f"Bearer {OPEN_WEBUI_TOKEN}",
        "Content-Type": "application/json"
    }

    try:
        logging.info(f"Querying Open WebUI with model '{model}' at endpoint {url}")
        res = requests.post(url, headers=headers, json=payload, timeout=30) # Increased timeout
        res.raise_for_status()
        
        # Parse the OpenAI-compatible response
        response_json = res.json()
        content = response_json.get("choices", [{}])[0].get("message", {}).get("content", "")
        return content

    except requests.RequestException as e:
        logging.error(f"Open WebUI query failed: {type(e).__name__}: {e}")
        # Try to get more detail from the response if available
        try:
            error_detail = e.response.json()
            return f"Error: {e}. Details: {error_detail}"
        except:
            return f"Error: {e}"
    except (KeyError, IndexError) as e:
        logging.error(f"Failed to parse Open WebUI response: {e}")
        return f"Error: Could not parse the response from Open WebUI. Raw response: {res.text}"


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