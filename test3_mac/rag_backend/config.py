# rag_backend/config.py
import os
from dotenv import load_dotenv
load_dotenv()

OLLAMA_URL = os.getenv("OLLAMA_URL", "http://localhost:11434")
OPEN_WEBUI_URL = os.getenv("OPEN_WEBUI_URL", "http://localhost:3000")
AUTH_TOKEN = os.getenv("AUTH_TOKEN", "")
HEADERS = {"Authorization": f"Bearer {AUTH_TOKEN}"}
