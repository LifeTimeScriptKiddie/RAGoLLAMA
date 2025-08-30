import os
from dotenv import load_dotenv

# Load environment variables from .env file
load_dotenv()

# Ollama API
OLLAMA_URL = os.getenv("OLLAMA_BASE_URL", os.getenv("OLLAMA_URL", "http://127.0.0.1:11434")).rstrip("/")
OLLAMA_EMBEDDING_URL = os.getenv("OLLAMA_EMBEDDING_URL", f"{OLLAMA_URL}/api/embeddings")

# Open WebUI API  
OPEN_WEBUI_URL = os.getenv("OPEN_WEBUI_URL", "http://127.0.0.1:3000").rstrip("/")
OPEN_WEBUI_TOKEN = os.getenv("OPEN_WEBUI_TOKEN", "Bearer YOUR_OPEN_WEBUI_TOKEN")

# Request headers for Open WebUI
HEADERS = {
    "Authorization": OPEN_WEBUI_TOKEN,
    "Content-Type": "application/json"
}