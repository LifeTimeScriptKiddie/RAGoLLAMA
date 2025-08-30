# Multi-RAG Document Pipeline

> Cross-platform pipeline for comparing Docling vs Microsoft RAG embeddings with comprehensive document processing and analysis capabilities.

[![Python 3.11+](https://img.shields.io/badge/python-3.11+-blue.svg)](https://www.python.org/downloads/)
[![Docker](https://img.shields.io/badge/docker-ready-brightgreen.svg)](https://www.docker.com/)
[![FastAPI](https://img.shields.io/badge/FastAPI-0.104+-green.svg)](https://fastapi.tiangolo.com/)
[![Streamlit](https://img.shields.io/badge/Streamlit-1.28+-red.svg)](https://streamlit.io/)

## 🎯 Overview

The Multi-RAG Document Pipeline is a comprehensive system that processes documents through multiple embedding methods and provides detailed comparative analysis. It supports various document formats and offers multiple interfaces for interaction.

### Key Features

- **🔄 Dual Embedding Comparison**: Compare Docling vs Microsoft RAG embeddings
- **📄 Multi-Format Support**: PDF, DOCX, PPTX, TXT, and image files with OCR
- **🔍 Vector Search**: FAISS-powered similarity search with HNSW indexing
- **📊 Comprehensive Analytics**: Statistical analysis, clustering, and PCA insights
- **🌐 Multiple Interfaces**: CLI, REST API, and interactive web dashboard
- **🐳 Docker Ready**: Complete containerization with service orchestration
- **💾 Persistent Storage**: SQLite database for metadata and FAISS for vectors

## 🏗️ Application Structure

```
test7/
├── 📁 core/                           # Core processing modules
│   ├── 📁 document/                   # Document processing
│   │   ├── __init__.py
│   │   └── processor.py               # Multi-format document processor
│   ├── 📁 embedding/                  # Embedding implementations
│   │   ├── __init__.py
│   │   ├── base.py                    # Abstract embedder base class
│   │   ├── docling_embedder.py        # Docling implementation
│   │   └── microsoft_embedder.py      # Microsoft RAG implementation
│   ├── 📁 vector/                     # Vector storage
│   │   ├── __init__.py
│   │   └── faiss_store.py             # FAISS vector store with HNSW
│   ├── 📁 storage/                    # Database management
│   │   ├── __init__.py
│   │   └── sqlite_manager.py          # SQLite database manager
│   └── 📁 comparison/                 # Embedding comparison
│       ├── __init__.py
│       └── comparator.py              # Comprehensive comparison engine
├── 📁 api/                            # REST API
│   ├── __init__.py
│   └── main.py                        # FastAPI application
├── 📁 cache/                          # Runtime cache directory
│   ├── faiss_index/                   # FAISS vector indices
│   ├── documents.db                   # SQLite database
│   └── multi_rag.log                  # Application logs
├── 📁 output/                         # Export output directory
├── main.py                            # CLI interface and main pipeline
├── streamlit_app.py                   # Interactive web dashboard
├── requirements.txt                   # Python dependencies
├── Dockerfile                         # Container configuration
├── docker-compose.yml                 # Multi-service orchestration
├── .env                              # Environment configuration
└── README.md                         # This documentation
```

### Core Components

#### 🔧 **Document Processing (`core/document/`)**
- **Multi-format support**: PDF, DOCX, PPTX, TXT, images
- **OCR capabilities**: Text extraction from images using Tesseract
- **Intelligent chunking**: Configurable text segmentation with overlap
- **Metadata extraction**: File properties, hash verification, processing stats

#### 🧠 **Embedding Systems (`core/embedding/`)**
- **Docling Embedder**: Uses sentence-transformers for local processing
- **Microsoft RAG Embedder**: API integration with fallback mock implementation
- **Common Interface**: Unified embedding interface with similarity calculations
- **Batch Processing**: Efficient bulk embedding generation

#### 🎯 **Vector Storage (`core/vector/`)**
- **FAISS Integration**: High-performance similarity search
- **HNSW Indexing**: Hierarchical Navigable Small World graphs
- **Metadata Management**: Rich metadata storage and filtering
- **Persistent Storage**: Index serialization and loading

#### 💾 **Database Management (`core/storage/`)**
- **SQLite Backend**: Lightweight, serverless database
- **Document Tracking**: Complete document lifecycle management
- **Embedding Metadata**: Method-specific embedding information
- **Comparison Results**: Detailed analysis result storage

#### 📊 **Comparison Engine (`core/comparison/`)**
- **Statistical Analysis**: Mean, variance, distribution comparisons
- **Clustering Analysis**: K-means clustering and silhouette scores
- **Dimensional Analysis**: PCA and intrinsic dimensionality estimation
- **Similarity Metrics**: Cosine, Euclidean, Pearson, Spearman correlations

## 🚀 Quick Start

### Prerequisites

- Docker and Docker Compose
- Python 3.11+ (for local development)
- Git

### 1. Clone and Setup

```bash
git clone <repository-url>
cd test7
```

### 2. Configure Environment

```bash
# Copy and edit environment configuration
cp .env.example .env
# Edit .env with your API keys and preferences
```

### 3. Start with Docker

```bash
# Start all services
docker-compose up -d

# Check service status
docker-compose ps
```

### 4. Access Interfaces

- **Web Dashboard**: http://localhost:8501
- **REST API**: http://localhost:8000
- **API Documentation**: http://localhost:8000/docs

## 💻 Usage Examples

### CLI Interface

```bash
# Process a document
python main.py process --file document.pdf

# Search similar documents
python main.py search --query "machine learning" --method docling --limit 5

# Get pipeline statistics
python main.py stats

# Export document results
python main.py export --document-id 1 --output results.json
```

### REST API

```bash
# Upload and process document
curl -X POST "http://localhost:8000/process" \
  -H "accept: application/json" \
  -H "Content-Type: multipart/form-data" \
  -F "file=@document.pdf" \
  -F "compare_methods=true"

# Search documents
curl -X POST "http://localhost:8000/search" \
  -H "Content-Type: application/json" \
  -d '{
    "query": "artificial intelligence",
    "method": "docling",
    "limit": 5
  }'

# Get pipeline statistics
curl -X GET "http://localhost:8000/stats"
```

### Python API

```python
from main import MultiRAGPipeline

# Initialize pipeline
pipeline = MultiRAGPipeline()

# Process document
result = pipeline.process_document("document.pdf", compare_methods=True)

# Search similar documents
results = pipeline.search_similar("machine learning", method="docling", k=5)

# Get comparison results
comparison = pipeline.db_manager.get_comparison(document_id)
```

## 📊 Web Dashboard Features

### 📄 **Document Processing**
- Drag-and-drop file upload
- Real-time processing status
- Embedding method comparison toggle
- Detailed processing results

### 🔍 **Document Search**
- Natural language queries
- Method selection (Docling/Microsoft)
- Similarity scoring
- Result filtering and sorting

### 📚 **Document Management**
- Complete document library
- Batch operations
- Export functionality
- Detailed metadata views

### 📈 **Analytics & Insights**
- Processing timeline charts
- File type distributions
- Embedding similarity heatmaps
- Statistical comparisons
- Performance metrics

## 🔧 Configuration

### Environment Variables

```bash
# Document Processing
MAX_CHUNK_SIZE=1000
CHUNK_OVERLAP=200
SUPPORTED_FORMATS=pdf,txt,docx,pptx,jpg,png

# Vector Storage
VECTOR_DIMENSION=384
FAISS_INDEX_PATH=/app/cache/faiss_index
INDEX_TYPE=HNSW

# Database
DB_PATH=/app/cache/documents.db

# Embedding Models
DOCLING_MODEL=sentence-transformers/all-MiniLM-L6-v2
MICROSOFT_RAG_ENDPOINT=https://api.openai.com/v1
MICROSOFT_RAG_API_KEY=your_api_key_here
MICROSOFT_MODEL=text-embedding-ada-002

# Comparison Settings
SIMILARITY_THRESHOLD=0.8
ANALYSIS_METRICS=cosine_similarity,euclidean_distance,pearson_correlation

# Service Ports
API_PORT=8000
STREAMLIT_PORT=8501
OLLAMA_PORT=11434
```

### Docker Services

```yaml
services:
  multi-rag:           # Main application
  ollama:              # LLM service
  volumes:
    - cache_data       # Persistent storage
    - output_data      # Export directory
```

## 🧪 API Reference

### Core Endpoints

| Method | Endpoint | Description |
|--------|----------|-------------|
| `POST` | `/process` | Upload and process document |
| `POST` | `/search` | Search similar documents |
| `GET` | `/documents` | List all documents |
| `GET` | `/documents/{id}` | Get document details |
| `GET` | `/documents/{id}/export` | Export document data |
| `DELETE` | `/documents/{id}` | Delete document |
| `GET` | `/stats` | Get pipeline statistics |
| `GET` | `/compare/{id}` | Get comparison results |
| `GET` | `/health` | Health check |

### Response Examples

**Document Processing Response:**
```json
{
  "document": {
    "id": 1,
    "file_name": "document.pdf",
    "file_type": "pdf",
    "num_chunks": 15,
    "processed_at": "2024-01-15T10:30:00Z"
  },
  "docling_embeddings": 15,
  "microsoft_embeddings": 15,
  "comparison": {
    "summary": {...},
    "assessment": {...}
  },
  "status": "processed"
}
```

**Search Response:**
```json
[
  {
    "similarity": 0.892,
    "document": {
      "id": 1,
      "file_name": "research_paper.pdf"
    },
    "chunk_metadata": {...},
    "method_used": "docling"
  }
]
```

## 🔍 Comparison Analysis

### Embedding Methods

| Feature | Docling | Microsoft RAG |
|---------|---------|---------------|
| **Model** | sentence-transformers | text-embedding-ada-002 |
| **Dimension** | 384 | 1536 |
| **Processing** | Local | API-based |
| **Cost** | Free | Paid API |
| **Speed** | Fast | Network dependent |
| **Accuracy** | Good | Excellent |

### Analysis Metrics

- **Cosine Similarity**: Measures angular similarity between vectors
- **Euclidean Distance**: Measures geometric distance in vector space
- **Pearson Correlation**: Linear relationship between embeddings
- **Spearman Correlation**: Monotonic relationship assessment
- **Statistical Analysis**: Distribution comparisons and normalization
- **Clustering Analysis**: Grouping behavior evaluation
- **Dimensional Analysis**: PCA and intrinsic dimensionality

## 🛠️ Development

### Local Setup

```bash
# Create virtual environment
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate

# Install dependencies
pip install -r requirements.txt

# Set up environment
cp .env.example .env

# Run components
python main.py stats                    # CLI
uvicorn api.main:app --reload          # API
streamlit run streamlit_app.py         # Dashboard
```

### Testing

```bash
# Run basic functionality test
python main.py process --file test_document.pdf

# Test API endpoints
curl http://localhost:8000/health

# Test search functionality
python main.py search --query "test" --method docling
```

### Adding New Features

1. **New Document Format**: Extend `DocumentProcessor` class
2. **New Embedding Method**: Implement `CommonEmbedder` interface
3. **New Analysis Metric**: Add to `EmbeddingComparator`
4. **New API Endpoint**: Add to `api/main.py`

## 📈 Performance Optimization

### Vector Storage
- **HNSW Parameters**: Tune `efConstruction` and `efSearch`
- **Index Type**: Choose between HNSW, IVF, or Flat based on data size
- **Batch Processing**: Process multiple documents simultaneously

### Database
- **Indexing**: Automatic indexes on frequently queried columns
- **Batch Operations**: Bulk insert/update operations
- **Connection Pooling**: Efficient database connection management

### Memory Management
- **Chunking**: Configurable chunk sizes for large documents
- **Streaming**: Process large files without loading entirely in memory
- **Cleanup**: Automatic temporary file cleanup

## 🔒 Security Considerations

- **API Keys**: Store securely in environment variables
- **File Validation**: Strict file type and size checking
- **Input Sanitization**: Clean user inputs before processing
- **Access Control**: Implement authentication for production use
- **Rate Limiting**: Prevent API abuse
- **Data Privacy**: No data retention in mock mode

## 🐛 Troubleshooting

### Common Issues

**Docker Services Won't Start**
```bash
# Check logs
docker-compose logs multi-rag
docker-compose logs ollama

# Restart services
docker-compose restart
```

**API Connection Errors**
```bash
# Check service health
curl http://localhost:8000/health

# Verify ports
docker-compose ps
```

**Embedding Failures**
```bash
# Check model availability
python -c "from sentence_transformers import SentenceTransformer; print('OK')"

# Verify API keys
echo $MICROSOFT_RAG_API_KEY
```

**Memory Issues**
```bash
# Reduce chunk size
export MAX_CHUNK_SIZE=500

# Monitor usage
docker stats
```

## 📋 Requirements

### System Requirements
- **CPU**: 2+ cores recommended
- **RAM**: 4GB minimum, 8GB recommended
- **Storage**: 2GB for models and cache
- **Network**: Internet access for Microsoft RAG API

### Dependencies
- **Python**: 3.11+
- **Docker**: 20.10+
- **Docker Compose**: 2.0+

### Optional
- **GPU**: CUDA support for faster local embeddings
- **Tesseract**: For OCR functionality (included in Docker)

## 🤝 Contributing

1. Fork the repository
2. Create a feature branch (`git checkout -b feature/amazing-feature`)
3. Commit your changes (`git commit -m 'Add amazing feature'`)
4. Push to the branch (`git push origin feature/amazing-feature`)
5. Open a Pull Request

## 📄 License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

## 🙏 Acknowledgments

- **Docling**: Advanced document processing capabilities
- **Microsoft RAG**: State-of-the-art embedding technology
- **FAISS**: Efficient vector similarity search
- **FastAPI**: Modern, fast web framework for APIs
- **Streamlit**: Intuitive web app framework
- **Sentence Transformers**: Easy-to-use embedding models

## 📞 Support

For support, please:
1. Check the [troubleshooting section](#🐛-troubleshooting)
2. Review existing [issues](../../issues)
3. Create a new issue with detailed information

---

**Built with ❤️ for document analysis and embedding comparison**