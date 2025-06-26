import os
from dotenv import load_dotenv

# Load environment variables from .env (if it exists)
load_dotenv()

# Ollama API base URL
OLLAMA_URL = os.getenv("OLLAMA_URL", "http://localhost:11434")

# Open WebUI base URL
OPEN_WEBUI_URL = os.getenv("OPEN_WEBUI_URL", "http://localhost:3000")  # adjust if hosted elsewhere

# Authorization and headers for Open WebUI
OPEN_WEBUI_TOKEN = os.getenv("OPEN_WEBUI_TOKEN", "Bearer YOUR_OPEN_WEBUI_TOKEN")

HEADERS = {
    "Authorization": OPEN_WEBUI_TOKEN,
    "Content-Type": "application/json"
}