# RAG Backend with Open WebUI + Ollama

This is a modular Retrieval-Augmented Generation (RAG) backend that integrates with **Open WebUI** and **Ollama**. It supports:

- Uploading and syncing PDFs to Open WebUI knowledge bases
- Querying via Ollama API
- Development interface via Streamlit

## 🧱 Structure

- `config.py`: Environment-based configuration
- `api.py`: REST API interactions with Ollama and Open WebUI
- `pdf_utils.py`: PDF parsing and chunking
- `embed_utils.py`: Optional local embedding + search
- `uploader.py`: Knowledge base management and file uploads
- `main.py`: Dev/testing UI with Streamlit

## 🐳 Usage

### 1. Build the container
```bash
docker build -t rag-backend .
```

### 2. Run with environment variables
```bash
docker run --env-file .env -p 8501:8501 rag-backend
```

### 3. Sync PDFs to Knowledge Base
```python
from uploader import sync_pdf_folder_to_knowledge
sync_pdf_folder_to_knowledge("./pdfs", knowledge_id="your_knowledge_id")
```

## 📋 Notes
- Ollama must be running on port 11434
- Open WebUI must have a valid token (set in `.env`)
- All sensitive tokens should be securely stored in production (not in `.env` in repo)
