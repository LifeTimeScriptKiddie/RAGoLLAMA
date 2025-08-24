# RAG-Ollama System

Production-ready RAG system with Ollama integration, following the recommendations from `claude.md`.

## Quick Start (Mac)

### Prerequisites
- Docker Desktop for Mac
- Make (usually pre-installed)
- Git

### 1. Setup
```bash
make setup
```

### 2. Start Development Environment
```bash
make dev
```

This will:
- Create necessary data directories
- Start Ollama service first
- Build and start all services
- Backend API: http://localhost:8000
- Streamlit UI: http://localhost:8501  
- Grafana: http://localhost:3000 (admin/admin)

### 3. Check Status
```bash
make status
```

### 4. View Logs
```bash
make dev-logs
```

## Mac-Specific Notes

### Docker Volume Performance
- Uses Docker named volumes instead of bind mounts for better performance
- Data persists in Docker volumes: `rag_raw_docs`, `rag_index`, `rag_cache`

### Common Issues & Solutions

**1. Port Already in Use**
```bash
# Stop any existing containers
make stop
# Or kill specific ports
lsof -ti:8000 | xargs kill -9
```

**2. Docker Build Issues** 
```bash
# Clean rebuild
make clean
make dev
```

**3. Ollama Not Starting**
```bash
# Check Ollama logs
docker-compose logs ollama
```

**4. Permission Issues**
```bash
# Ensure Docker has access to directories
sudo chown -R $USER:staff data/
```

## Usage

### CLI Management
```bash
# Login (saves token for subsequent commands)
make cli-login USER=admin PASS=admin

# Check system status
make cli-status

# Upload and process a document
make cli-upload FILE=mydoc.pdf

# Query the system
make cli-query Q="What is this document about?"

# Run evaluation
make cli-eval
```

### Document Ingestion
```bash
# Via API (requires authentication)
make cli-upload FILE=mydoc.pdf

# Direct pipeline (for testing)
docker-compose exec backend python -m apps.rag.ingestion.pipeline mydoc.pdf
```

### Index Management
```bash
make snapshot                    # Create index snapshot
make restore TS=20240101_120000  # Restore from snapshot
make reindex                     # Rebuild index from cache
```

### API Testing
```bash
# Health check (public)
curl http://localhost:8000/admin/health

# Login to get JWT token
curl -X POST http://localhost:8000/auth/login \
  -H "Content-Type: application/x-www-form-urlencoded" \
  -d "username=admin&password=admin"

# Query with token
curl -H "Authorization: Bearer <token>" \
     -X POST http://localhost:8000/query/ \
     -H "Content-Type: application/json" \
     -d '{"query": "What is this document about?", "k": 5}'
```

### Authentication
Default credentials:
- **Username**: `admin`
- **Password**: `admin` 

⚠️ **Change these in production!**

## Architecture

```
┌─────────────────┐    ┌─────────────────┐    ┌─────────────────┐
│     Frontend    │    │    Backend      │    │     Ollama      │
│   (Streamlit)   │───▶│   (FastAPI)     │───▶│   (LLM Host)    │
└─────────────────┘    └─────────────────┘    └─────────────────┘
                                │
                                ▼
                       ┌─────────────────┐
                       │  RAG Pipeline   │
                       │ ┌─────────────┐ │
                       │ │ Ingestion   │ │
                       │ │ Chunking    │ │
                       │ │ Embedding   │ │
                       │ │ Vector Store│ │
                       │ └─────────────┘ │
                       └─────────────────┘
```

## Development

### Code Structure
```
apps/
├── backend/          # FastAPI application
│   ├── api/         # API endpoints
│   ├── core/        # Auth, settings, rate limiting
│   └── observability/ # Metrics, logging
├── rag/             # RAG pipeline
│   ├── ingestion/   # Document processing
│   ├── embeddings/  # Vector generation & caching
│   └── store/       # Vector store & ledger
└── frontend-*/      # Frontend applications
```

### Running Tests
```bash
make test
```

### Code Formatting
```bash
make lint
```

## Production Deployment

### Kubernetes
```bash
# Development cluster
make k8s-dev

# Production cluster  
make k8s-prod
```

### Environment Variables
Copy `.env.example` to `.env` and update:
- `JWT_SECRET_KEY`: Use 256-bit key in production
- `OLLAMA_MODEL`: Choose appropriate model size
- Resource limits based on your infrastructure

## Troubleshooting

### Mac Performance Tips
1. Increase Docker Desktop memory allocation (8GB+)
2. Enable VirtioFS for better file sharing performance
3. Use Docker volumes instead of bind mounts
4. Consider Ollama on Apple Silicon for better performance

### Monitoring
- Prometheus metrics: http://localhost:9090
- Grafana dashboards: http://localhost:3000
- Application logs: `make dev-logs`

For more detailed information, see `claude.md`.