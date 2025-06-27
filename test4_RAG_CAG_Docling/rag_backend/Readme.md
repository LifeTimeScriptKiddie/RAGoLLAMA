Here’s your ✅ Final README.md — cleaned up, modular, and updated to reflect Streamlit and non-Streamlit use cases, Open WebUI, and flexible embedding modes.

⸻

✅ Local RAG Chatbot with Ollama, Docling, and Open WebUI

This project is a fully local Retrieval-Augmented Generation (RAG) system using:
	•	🧠 Ollama for running open-source LLMs locally
	•	📄 Docling for smart PDF/Markdown/Doc chunking
	•	🔍 sentence-transformers or Ollama for embeddings
	•	🌐 Open WebUI as the optional document/chat frontend
	•	⚙️ Optional Streamlit app (main.py) for lightweight local UI

⸻

📁 Project Structure

project-root/
├── api.py              # Prompt handler for Ollama / Open WebUI
├── config.py           # Loads .env configs
├── doc_processor.py    # Uses Docling to chunk docs
├── vectorizer.py       # Embeds chunks using local SentenceTransformer
├── ollama_embed.py     # Optional: Ollama-based LangChain embedding wrapper
├── uploader.py         # Syncs files to Open WebUI knowledge base
├── requirements.txt
├── Dockerfile
├── docker-compose.yml
└── .env


⸻

🧠 Modes of Operation

1. Streamlit UI (for testing)

streamlit run main.py

2. Open WebUI + CLI Backend

Use uploader.py, doc_processor.py, and api.py to embed docs and sync with WebUI.

⸻

🔄 Architecture Diagram

✅ Docker Build & Execution Flow

```mermaid
graph TD

A[User runs: docker-compose up] --> B[Dockerfile in backend]
B --> C[Install Python + Requirements]
C --> D[Copy all source files into /app]
D --> E[Set CMD: python uploader.py or Streamlit]

E --> F[Streamlit or CLI script runs]
F --> G[PDF/doc loaded via Docling (doc_processor.py)]
G --> H[Chunks embedded via vectorizer.py or ollama_embed.py]
H --> I[User query handled by api.py]
I --> J[Ollama queried and response returned]
```

⸻

📄 Breakdown by Script

Script	Role
main.py	Optional Streamlit front-end UI (can be removed)
doc_processor.py	Loads documents using Docling
vectorizer.py	Embeds using local SentenceTransformer
ollama_embed.py	LangChain-compatible wrapper to use Ollama’s embedding API
api.py	Queries Ollama or Open WebUI
config.py	Loads .env settings
uploader.py	Uploads .pdf, .md, .docx, .jpg, etc. to Open WebUI
requirements.txt	Python dependencies
Dockerfile	Backend container image
docker-compose.yml	Optional container orchestration


⸻

🧠 Install Ollama

brew install ollama
ollama serve

# Pull desired models
ollama pull llama3
ollama pull mistral
ollama pull codellama:7b
ollama pull phi3

# Run a model
ollama run llama3


⸻

🐳 Docker Commands

# Build and run
docker compose up --build -d

# Stop
docker compose down

# Clean everything
docker compose down --volumes --remove-orphans
docker system prune -af --volumes


⸻

🌐 Interfaces

Component	URL
Streamlit App	http://localhost:8501
Open WebUI	http://localhost:3000
Ollama API	http://localhost:11434


⸻

⚙️ .env Configuration

Example .env:

OLLAMA_URL=http://localhost:11434
OPEN_WEBUI_URL=http://localhost:3000
OPEN_WEBUI_TOKEN=Bearer your_openwebui_token
EMBED_MODEL=all-MiniLM-L6-v2


⸻

✅ Notes
	•	Works fully offline (as long as Ollama and models are pre-pulled).
	•	Supports all major doc types: .pdf, .md, .docx, .txt, .html, .csv, .jpg, .png, etc.
	•	Use vectorizer.py for local embedding OR ollama_embed.py to use Ollama.
	•	main.py is optional — you can fully operate through CLI and Open WebUI.
	•	Flexible and extendable for LangChain, Flask, FastAPI, or scheduled pipelines.

⸻