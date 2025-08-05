Here is your full Claude CLI–ready prompt, formatted for structured input, using markdown, YAML, and clear task-based instructions:

⸻

✅ Claude CLI Prompt: Cross-Platform Multi-RAG Document Pipeline

# SYSTEM:
You are a senior systems architect and Python developer. You will be given structured requirements to generate a modular, Dockerized document processing system. The system must extract content from user-uploaded documents, embed that content using both Docling and Microsoft RAG, compare results, and pass the best context to Ollama for LLM response generation. Ensure the design is cross-platform (Linux/macOS) and supports extensibility.

# USER:
Below are the structured requirements. Please do the following:

## ✅ TASKS
1. Generate a project folder structure with core modules for:
   - embedding (docling, microsoft)
   - document processing
   - vector storage (FAISS)
   - SQLite tracking
   - comparison logic
   - main execution file

2. Write:
   - `Dockerfile` (base: `python:3.11-slim`, with required dependencies)
   - `docker-compose.yml` that mounts volumes for `/docs`, `/models`, `/cache`

3. Stub out key Python files as empty classes or function skeletons for each module.

4. Make the system ready to run on both Linux and macOS via Docker.

---

## 📦 System Requirements (YAML format)

```yaml
platform:
  cross_platform: true
  operating_systems:
    - macOS
    - Linux
  containerization: docker-compose
  volumes:
    - ./docs:/app/docs
    - ./models:/app/models
    - ./cache:/app/cache

document_formats:
  supported:
    - .pdf
    - .txt
    - .docx
    - .pptx
    - .jpg
    - .png

embedding:
  sources:
    - docling
    - microsoft_rag
  comparison:
    - cosine_similarity
    - generation_diff
  interface: CommonEmbedder
  vector_store: FAISS
  faiss_index: HNSW
  cache: enabled (hash-based)

llm_inference:
  engine: ollama
  models:
    - qwen
    - codellama
    - mistral
    - ollama
    - arena

storage:
  sqlite:
    tables:
      - documents
      - chunks
      - comparisons
  ollama_model_storage: ./models
  processed_document_storage: ./docs

execution:
  interface:
    - CLI
    - REST API (Flask or FastAPI)
    - Optional: Streamlit web UI


⸻

🧾 OUTPUT EXPECTED
	•	Python project folder structure
	•	Dockerfile
	•	docker-compose.yml
	•	main.py and module stubs
