# rag_backend/config.py
import os
from dotenv import load_dotenv
load_dotenv()

OLLAMA_URL = os.getenv("OLLAMA_URL", "http://ollama:11434")
OPEN_WEBUI_URL = os.getenv("OPEN_WEBUI_URL", "http://open-webui:8080")
HEADERS = {
    "Authorization": os.getenv("OPEN_WEBUI_TOKEN", "Bearer dummy_token"),
    "Content-Type": "application/json"
}
