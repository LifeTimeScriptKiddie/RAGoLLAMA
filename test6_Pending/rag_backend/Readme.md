


# ✅ Local RAG Chatbot with Ollama, Docling, and Open WebUI

This project is a fully local Retrieval-Augmented Generation (RAG) system that combines:

- 🧠 **Ollama** – Local LLM engine (e.g. llama3, mistral)
- 📄 **Docling** – Intelligent document chunking (PDF, DOCX, MD, HTML, images)
- 🔍 **Embeddings** – Local SentenceTransformers or Ollama-based
- 🌐 **Open WebUI** – Web interface for chat and knowledge base
- ⚙️ **Backend CLI scripts** – Fully automated, Streamlit optional

---

## 📁 Project Structure

project-root/
├── api.py              # Sends prompts to Ollama or Open WebUI
├── config.py           # Loads API keys and base URLs from .env
├── doc_processor.py    # Uses Docling to chunk PDFs/docs
├── vectorizer.py       # Embeds chunks using SentenceTransformers
├── ollama_embed.py     # LangChain-compatible wrapper to embed via Ollama API
├── uploader.py         # Batch uploads files to Open WebUI knowledge base
├── requirements.txt    # Python dependencies
├── Dockerfile          # Cron-enabled backend container image
├── crontab.txt         # Runs uploader.py at 2 AM EST daily
├── docker-compose.yml  # Orchestrates Ollama, Open WebUI, and backend
└── .env                # Configuration

---

## 🧠 How This Program Works

```mermaid
flowchart TD

A[Start docker-compose up] --> B[Dockerfile builds backend]
B --> C[Requirements installed]
C --> D[All scripts copied to /app]
D --> E[cron -f runs inside container]
E --> F[2:00 AM EST hits]
F --> G[uploader.py starts]
G --> H[Docling chunks all files in ./docs]
H --> I[Chunks embedded via vectorizer.py or ollama_embed.py]
I --> J[upload_file() sends to Open WebUI]
J --> K[Data visible and searchable via http://localhost:3000]
```

⸻

📄 Breakdown by Script

Script	Role
main.py	(Optional) Streamlit UI
doc_processor.py	Uses Docling to parse & chunk docs
vectorizer.py	Local SentenceTransformer-based embedding
ollama_embed.py	Embedding using Ollama API (LangChain compatible)
api.py	Query handler to Ollama / Open WebUI
uploader.py	Uploads .pdf, .md, .docx, .jpg, etc. to Open WebUI
config.py	Loads .env variables
crontab.txt	Schedules uploader for 2 AM EST
Dockerfile	Builds backend with cron and uploader setup
docker-compose.yml	Brings up Open WebUI, Ollama, and the backend container


⸻

🧠 Ollama Setup. --> This will automatically pulled in. 

brew install ollama
ollama serve

# Pull models
ollama pull llama3
ollama pull mistral
ollama pull codellama:7b
ollama pull phi3

# Run a model manually
ollama run llama3


⸻

🐳 Docker Commands

# Build and start everything in the background
docker compose up --build -d
# Stop services
docker compose down
# List running containers
docker ps
# Access a container shell
docker exec -it <container_name> bash (or sh)
# Run a one-time command
docker exec -it <container_name> <command>
# Restart a container
docker restart <container_name>
# View container logs
docker logs <container_name>
# Stop a container
docker stop <container_name>
# Remove a container
docker rm -f <container_name>
# Clean everything
docker compose down --volumes --remove-orphans
docker system prune -af --volumes


⸻

🕑 Scheduling (Cron at 2 AM EST)
	•	uploader.py will run automatically every night at 2:00 AM EST inside the backend container
	•	All supported files in ./docs/ will be uploaded to Open WebUI
	•	Log is saved to ./docs/upload.log

⸻

🌐 Interfaces

Component	URL
Open WebUI	http://localhost:3000
Ollama API	http://localhost:11434
Backend Logs	./docs/upload.log


⸻

⚙️ .env Configuration

OLLAMA_URL=http://ollama:11434
OPEN_WEBUI_URL=http://open-webui:3000
OPEN_WEBUI_TOKEN=Bearer your_openwebui_token_here

UPLOAD_FOLDER_PATH=./docs
DEFAULT_KB_NAME=AutoKB
DEFAULT_KB_DESC=Uploaded by uploader.py

EMBED_BACKEND=sentence-transformer
EMBED_MODEL=all-MiniLM-L6-v2


⸻

✅ Notes
	•	📦 Works fully offline (after Ollama models are pulled)
	•	🧠 Supports .pdf, .md, .docx, .txt, .html, .csv, .jpg, .png, .epub, .gif, etc.
	•	🧱 Uses LangChain-compatible embedding OR Ollama embedding
	•	🌐 Frontend is handled by Open WebUI, backend is CLI-first
	•	🔄 Easily extensible into LangChain, FastAPI, or production pipelines

⸻

✅ Tip: Everything auto-syncs overnight at 2 AM. Just drop files into ./docs/, and they’ll be available in Open WebUI the next morning.
