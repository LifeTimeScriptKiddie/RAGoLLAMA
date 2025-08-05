# Multi-RAG Document Pipeline

A comprehensive document processing and retrieval system that compares different embedding methods (Docling vs Microsoft RAG) for optimal document understanding and retrieval.

## 🚀 Features

- **Multi-Format Document Processing**: Supports PDF, TXT, DOCX, PPTX, and images (JPG, PNG)
- **Dual Embedding Methods**: Compare Docling and Microsoft RAG embeddings
- **FAISS Vector Storage**: High-performance similarity search with HNSW indexing
- **SQLite Database**: Metadata tracking for documents, chunks, and comparisons
- **Multiple Interfaces**: CLI, REST API, Streamlit web interface, and OpenWebUI integration
- **Ollama Integration**: Local LLM inference for RAG-based question answering
- **Docker Deployment**: Complete containerized solution
- **OCR Support**: Extract text from images using Tesseract

## 📋 Quick Start

### Option 1: Local Development (macOS/Linux)

#### Prerequisites
- Python 3.8+
- pip and venv
- Optional: Homebrew (macOS)

#### Setup
```bash
git clone <repository-url>
cd multi-rag-pipeline

# Automated setup
./setup-local.sh

# Or use Makefile
make setup-local

# Activate environment
source venv/bin/activate

# Run CLI
python main.py --interface cli --config config/config-local.json

# Run API server
python main.py --interface api --config config/config-local.json
```

### Option 2: Docker Deployment

#### Prerequisites
- Docker and Docker Compose
- 8GB+ RAM recommended
- 10GB+ storage space

#### Setup
```bash
git clone <repository-url>
cd multi-rag-pipeline

# Automated deployment
./deploy.sh

# Or use Makefile
make docker-up
```

### 2. Access Interfaces

- **API Documentation**: http://localhost:8000/docs
- **Streamlit Web UI**: http://localhost:8501  
- **OpenWebUI**: http://localhost:3000
- **Ollama API**: http://localhost:11434

### 3. Process Your First Document

#### Using CLI
```bash
docker-compose exec multi-rag-app python main.py --interface cli -- process document.pdf --method both --compare
```

#### Using API
```bash
curl -X POST "http://localhost:8000/upload" \
  -H "Content-Type: multipart/form-data" \
  -F "file=@document.pdf" \
  -F "method=both" \
  -F "compare=true"
```

## 🏗️ Architecture

```
┌─────────────────┐    ┌─────────────────┐    ┌─────────────────┐
│   Documents     │    │   Embedding     │    │  Vector Store   │
│   (PDF, DOCX,   │───▶│   Methods       │───▶│   (FAISS)       │
│    TXT, etc.)   │    │ Docling/MS RAG  │    │                 │
└─────────────────┘    └─────────────────┘    └─────────────────┘
                                │
                                ▼
┌─────────────────┐    ┌─────────────────┐    ┌─────────────────┐
│   Interfaces    │    │   Comparison    │    │   Database      │
│ CLI/API/Web/UI  │◀───│    Engine       │───▶│   (SQLite)      │
└─────────────────┘    └─────────────────┘    └─────────────────┘
                                │
                                ▼
                       ┌─────────────────┐
                       │     Ollama      │
                       │  (LLM Server)   │
                       └─────────────────┘
```

## 🔧 Configuration

Configuration is managed through `config/config.json`:

```json
{
  "document_processing": {
    "max_chunk_size": 1000,
    "chunk_overlap": 200,
    "supported_formats": [".pdf", ".txt", ".docx", ".pptx", ".jpg", ".png"]
  },
  "embeddings": {
    "dimension": 384,
    "docling": {
      "model_name": "sentence-transformers/all-MiniLM-L6-v2"
    },
    "microsoft": {
      "use_mock": true
    }
  },
  "ollama": {
    "default_model": "llama2",
    "models_to_pull": ["llama2", "codellama", "mistral"]
  }
}
```

## 🖥️ Interfaces

### 1. Command Line Interface (CLI)

```bash
# Process a document
python main.py --interface cli -- process document.pdf --method both --compare

# Search documents
python main.py --interface cli -- search "machine learning" --method docling --top-k 5

# List processed documents
python main.py --interface cli -- list-documents

# Show statistics
python main.py --interface cli -- stats
```

### 2. REST API

The FastAPI server provides endpoints for:

- `POST /upload` - Upload and process documents
- `POST /search` - Search for similar content
- `GET /documents` - List processed documents
- `GET /documents/{id}/comparison` - Get comparison results
- `GET /stats` - System statistics

### 3. Streamlit Web Interface

Interactive web interface for:
- Document upload and processing
- Real-time search
- Comparison visualization
- System monitoring

### 4. OpenWebUI Integration

Chat interface with RAG capabilities powered by Ollama.

## 📊 Embedding Comparison

The system compares two embedding methods:

### Docling Embeddings
- **Model**: sentence-transformers/all-MiniLM-L6-v2
- **Strengths**: Fast, lightweight, good for general text
- **Use Case**: Quick prototyping, general document search

### Microsoft RAG Embeddings  
- **Model**: Azure Cognitive Services (or mock implementation)
- **Strengths**: Domain-specific, enterprise-grade
- **Use Case**: Production deployments, specialized domains

### Comparison Metrics

1. **Discriminative Power**: How well embeddings distinguish between different chunks
2. **Semantic Coherence**: Correlation with text similarity
3. **Internal Consistency**: Similarity within method results
4. **Performance**: Speed and resource usage

## 🐳 Docker Deployment

### Services

- **multi-rag-app**: Main application (API + CLI)
- **streamlit-ui**: Web interface
- **ollama**: LLM inference server
- **open-webui**: Chat interface

### Management Commands

```bash
# Deploy everything
./deploy.sh deploy

# Start services
./deploy.sh start

# Stop services
./deploy.sh stop

# View logs
./deploy.sh logs

# Check status
./deploy.sh status

# Clean up
./deploy.sh clean
```

## 📁 Directory Structure

```
multi-rag-pipeline/
├── core/                     # Core modules
│   ├── document/            # Document processing
│   ├── embedding/           # Embedding methods
│   ├── vector/              # Vector storage
│   ├── storage/             # Database management
│   └── comparison/          # Comparison logic
├── interfaces/              # User interfaces
│   ├── cli/                 # Command line
│   ├── api/                 # REST API
│   ├── streamlit/           # Web interface
│   └── openwebui/           # OpenWebUI integration
├── ollama/                  # Ollama client
├── config/                  # Configuration files
├── cache/                   # Vector indexes and database
├── documents/               # Input documents
├── logs/                    # Application logs
├── main.py                  # Main entry point
├── deploy.sh               # Deployment script
├── docker-compose.yml      # Docker services
├── Dockerfile             # Container definition
└── requirements.txt       # Python dependencies
```

## 🔍 Example Usage

### Processing Documents

```python
from core.document.processor import DocumentProcessor
from core.embedding.docling_embedder import DoclingEmbedder
from core.vector.faiss_store import FAISSVectorStore

# Initialize components
processor = DocumentProcessor(config)
embedder = DoclingEmbedder(config)
vector_store = FAISSVectorStore(config)

# Process document
chunks, metadata = processor.process_document("document.pdf")
embeddings = embedder.embed_batch(chunks)
vector_ids = vector_store.add_embeddings(embeddings, metadata, "doc1")
```

### Searching Documents

```python
# Search for similar content
query_embedding = embedder.embed_text("machine learning")
results = vector_store.search(query_embedding, k=5)

for vector_id, similarity, metadata in results:
    print(f"Similarity: {similarity:.3f}, Text: {metadata['text'][:100]}...")
```

### RAG Query with Ollama

```python
from ollama.client import OllamaClient

client = OllamaClient(config)
result = client.rag_query(
    question="What is machine learning?",
    context_chunks=retrieved_chunks,
    model="llama2"
)
print(result["answer"])
```

## 🚨 Troubleshooting

### Common Issues

1. **Ollama Connection Failed**
   ```bash
   # Check if Ollama is running
   docker-compose logs ollama
   
   # Restart Ollama service
   docker-compose restart ollama
   ```

2. **Memory Issues**
   ```bash
   # Check memory usage
   docker stats
   
   # Reduce chunk size in config
   "max_chunk_size": 500
   ```

3. **Slow Processing**
   ```bash
   # Use smaller embedding models
   "model_name": "sentence-transformers/all-MiniLM-L6-v2"
   
   # Increase batch size
   "batch_size": 64
   ```

### Logs

```bash
# View all logs
docker-compose logs -f

# View specific service logs
docker-compose logs -f multi-rag-app
docker-compose logs -f ollama
```

## 🤝 Contributing

1. Fork the repository
2. Create a feature branch
3. Make your changes
4. Add tests
5. Submit a pull request

## 📄 License

This project is licensed under the MIT License - see the LICENSE file for details.

## 🙏 Acknowledgments

- [Sentence Transformers](https://www.sbert.net/) for embedding models
- [FAISS](https://faiss.ai/) for similarity search
- [Ollama](https://ollama.ai/) for LLM inference
- [Streamlit](https://streamlit.io/) for web interface
- [FastAPI](https://fastapi.tiangolo.com/) for REST API