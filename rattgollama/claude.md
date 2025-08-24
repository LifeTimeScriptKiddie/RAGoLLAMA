
# Mega-Prompt for Claude

You are to generate a **ready-to-run repository** called **`rattgollama`**.
This is a small RAG system for up to \~20 users, designed to run entirely in Docker on Linux.
It uses JWT authentication, Postgres + Qdrant + MinIO for storage, and integrates with Ollama for embeddings/LLMs.
The user interfaces are **Streamlit** (custom UI) and **Open WebUI** (optional).
There is also a background worker that ingests/re-indexes uploaded documents either on demand or every 2 hours.

The repository must be structured like this:

```
rattgollama/
├── docker-compose.yml
├── .env.example
├── deploy/
│   └── Caddyfile
├── services/
│   ├── ingestion-api/
│   │   ├── Dockerfile
│   │   ├── requirements.txt
│   │   └── app/
│   │       ├── __init__.py
│   │       ├── main.py
│   │       ├── db.py
│   │       ├── models.py
│   │       ├── auth.py
│   │       ├── deps.py
│   │       ├── storage.py
│   │       └── schemas.py
│   └── worker/
│       ├── Dockerfile
│       ├── requirements.txt
│       └── worker.py
├── apps/
│   └── streamlit/
│       ├── Dockerfile
│       ├── requirements.txt
│       └── app/
│           └── main.py
└── README.md
```

---

## Global Requirements

* All services run as Docker containers, orchestrated via `docker-compose.yml`.
* Services communicate on an internal Docker network.
* JWT authentication is mandatory:

  * When a user logs in, the **ingestion-api** issues a JWT signed with a secret.
  * The JWT includes `sub` (user ID) and `roles`.
  * Streamlit and Open WebUI store the JWT and attach it as `Authorization: Bearer <token>` on each backend request.
* Database: **Postgres** for metadata, **Qdrant** for embeddings, **MinIO** for raw document files.
* LLM runtime: **Ollama**, with embedding model `nomic-embed-text` (vector size 768).
* Background worker ingests/re-indexes docs either:

  * Immediately when triggered via API (`POST /ingest/reindex`).
  * Or automatically every 2 hours (via cron-like loop).
* Reverse proxy: **Caddy**, providing TLS termination and routing.
* Hardware assumption:

  * Minimum: GPU 12GB VRAM, 32GB RAM, 8 cores, 1TB NVMe.
  * Recommended: GPU 32GB VRAM, 64GB RAM, 12–16 cores, 2–4TB NVMe.
  * Worker and Ollama containers must be configured with GPU support (`--gpus all`).

---

## Per-File Instructions

### 1. `docker-compose.yml`

* Define services:

  * `ingestion-api` (FastAPI + JWT auth).
  * `worker` (Python script that runs continuously, polls tasks, performs embedding, inserts into Qdrant/Postgres).
  * `streamlit` (UI for uploads, search, JWT login).
  * `openwebui` (community chat UI, points at Ollama + Qdrant).
  * `postgres`, `qdrant`, `minio`, `ollama`, `caddy`.
* Mount volumes for persistence:

  * Postgres: `rattgllm_pg_data`.
  * Qdrant: `rattgllm_qdrant_storage`.
  * MinIO: `rattgllm_minio_data`.
* Worker and Ollama must use GPU (`deploy.resources.reservations.devices` or `--gpus all`).

---

### 2. `.env.example`

* Template env vars:

  ```
  POSTGRES_USER=rattg_user
  POSTGRES_PASSWORD=changeme
  POSTGRES_DB=rattgllm
  JWT_SECRET=supersecretkey
  MINIO_ROOT_USER=minioadmin
  MINIO_ROOT_PASSWORD=minioadmin
  ```
* Add comments so user knows to copy to `.env`.

---

### 3. `deploy/Caddyfile`

* Reverse proxy config for:

  * `:8080` → Streamlit.
  * `/api/*` → ingestion-api.
  * `/openwebui/*` → Open WebUI.
* Enable HTTPS automatically (Caddy handles TLS).

---

### 4. `services/ingestion-api/`

* `Dockerfile`: lightweight Python base, install FastAPI + psycopg + boto3 + qdrant-client + PyJWT.
* `requirements.txt`: list FastAPI, uvicorn, SQLAlchemy, psycopg2, boto3, qdrant-client, PyJWT, pydantic.
* `app/main.py`: FastAPI app with endpoints:

  * `POST /auth/login` (returns JWT).
  * `POST /upload` (accepts file upload → store in MinIO → write metadata to Postgres).
  * `POST /ingest/reindex` (enqueue document for worker).
* `app/db.py`: SQLAlchemy session for Postgres.
* `app/models.py`: SQLAlchemy models (Users, Documents, Embeddings).
* `app/auth.py`: JWT encode/decode helpers.
* `app/deps.py`: Dependency functions (auth enforcement).
* `app/storage.py`: Upload to MinIO.
* `app/schemas.py`: Pydantic models for requests/responses.

---

### 5. `services/worker/`

* `Dockerfile`: Python base with CUDA drivers.
* `requirements.txt`: requests, qdrant-client, psycopg2, boto3, sentence-transformers, ollama-python.
* `worker.py`:

  * Poll Postgres for pending docs.
  * Fetch from MinIO.
  * Chunk with Docling.
  * Embed with Ollama (`nomic-embed-text`, 768 dims).
  * Store embeddings in Qdrant.
  * Update Postgres ingestion status.
  * Runs every 2 hours OR triggered immediately via API flag.

---

### 6. `apps/streamlit/`

* `Dockerfile`: Python base with Streamlit.
* `requirements.txt`: streamlit, requests, PyJWT.
* `app/main.py`:

  * Login form (username/password → request JWT).
  * Upload form (attach JWT, call `POST /upload`).
  * Search box (query Qdrant via ingestion-api).
  * Show results with source doc preview.
  * Sidebar banner: `rattgllm – RAG + JWT + LLM`.

---

### 7. `README.md`

* Title: **`rattgllm`**
* Overview:

  > `rattgllm` is a small RAG system for up to \~20 users. JWT-secured API and Streamlit UI. Ingestion Worker uses Docling + Ollama embeddings + Qdrant. MinIO for files, Postgres for metadata. Optional Open WebUI for general chat.
* Quickstart:

  ```
  git clone <repo>
  cd rattgllm
  cp .env.example .env
  docker compose up -d --build
  ```

  Then visit `http://localhost:8080/`.
* Document architecture diagram (Mermaid).
* Add “Open WebUI caveat”: it manages its own docs separate from rattgllm ingestion pipeline.
* Note about cron sidecar auth: in dev we use dummy JWT, in prod use API key or long-lived token.
* Note about hardware profile (GPU, RAM, CPU, Storage).

---

## Extra Notes for Claude

* All files should be syntactically valid and runnable (FastAPI endpoints, worker loop, Streamlit pages).
* Use simple username/password hardcoded in Postgres seed for now (e.g., `admin:admin`) for demo login.
* In FastAPI, protect `/upload` and `/ingest/reindex` with JWT dependency.
* In Streamlit, store JWT in `st.session_state` and attach on requests.
* Ensure Ollama calls respect GPU flag and correct model vector size (768).

---

# End of Prompt
