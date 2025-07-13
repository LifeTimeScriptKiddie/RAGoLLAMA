# 🏦 Financial Advisor Suite

A comprehensive AI-powered financial advisor built with Docker, Docling, Ollama, TurboRAG, and CAG technologies. Features a 5-tab Streamlit interface for personalized financial advice, tax optimization, investment analysis, and document management.

## 🏗️ Architecture Overview

```
┌─────────────────────────────────────────────────────────────────┐
│                    FINANCIAL ADVISOR SUITE                     │
├─────────────────────────────────────────────────────────────────┤
│  Frontend: Streamlit (5 Tabs)                                  │
│  ┌─────────┬─────────┬─────────┬─────────┬─────────────────┐   │
│  │Smart    │Tax      │Invest-  │Analytics│Document         │   │
│  │Assistant│Dashboard│ments    │         │Manager          │   │
│  └─────────┴─────────┴─────────┴─────────┴─────────────────┘   │
├─────────────────────────────────────────────────────────────────┤
│  Core Intelligence Layer                                       │
│  ┌─────────────┬─────────────┬─────────────┬─────────────────┐ │
│  │TurboRAG     │CAG Engine   │Ollama Client│Document Manager │ │
│  │(Enhanced    │(Context-    │(LLM         │(Auto Processing)│ │
│  │Retrieval)   │Aware Gen)   │Integration) │                 │ │
│  └─────────────┴─────────────┴─────────────┴─────────────────┘ │
├─────────────────────────────────────────────────────────────────┤
│  Data Processing Layer                                         │
│  ┌─────────────┬─────────────┬─────────────┬─────────────────┐ │
│  │Docling      │Vector Store │Stock API    │Financial        │ │
│  │(PDF OCR)    │(FAISS)      │(Portfolio)  │Analytics        │ │
│  └─────────────┴─────────────┴─────────────┴─────────────────┘ │
├─────────────────────────────────────────────────────────────────┤
│  Storage Layer                                                 │
│  ┌─────────────┬─────────────┬─────────────┬─────────────────┐ │
│  │SQLite       │Vector       │Document     │Model            │ │
│  │(Transactions│Embeddings   │Files        │Storage          │ │
│  │& Metadata)  │             │(/docs)      │(Ollama)         │ │
│  └─────────────┴─────────────┴─────────────┴─────────────────┘ │
└─────────────────────────────────────────────────────────────────┘
```

## 🐳 Docker Container Architecture

```
┌─────────────────────────────────────────────────────────────────┐
│                        Docker Network                          │
├─────────────────────────────────────────────────────────────────┤
│                                                                 │
│  ┌─────────────────┐  ┌─────────────────┐  ┌─────────────────┐ │
│  │   Streamlit     │  │     Ollama      │  │   Open WebUI    │ │
│  │   Container     │  │   Container     │  │   Container     │ │
│  │                 │  │                 │  │                 │ │
│  │ Port: 8501      │  │ Port: 11434     │  │ Port: 3000      │ │
│  │                 │  │                 │  │                 │ │
│  │ • Streamlit App │  │ • 5 LLM Models  │  │ • Web Interface │ │
│  │ • All Core      │  │ • API Server    │  │ • Model Mgmt    │ │
│  │   Components    │  │ • Model Storage │  │                 │ │
│  └─────────────────┘  └─────────────────┘  └─────────────────┘ │
│           │                     │                     │        │
│           └─────────────────────┼─────────────────────┘        │
│                                 │                              │
├─────────────────────────────────┼──────────────────────────────┤
│           Host Volumes          │                              │
│                                 │                              │
│  ┌─────────────────┐  ┌─────────┴───────┐  ┌─────────────────┐ │
│  │   ./docs/       │  │ shared_models   │  │   ./data/       │ │
│  │                 │  │                 │  │                 │ │
│  │ • Cyber Docs    │  │ • Vector Store  │  │ • SQLite DB     │ │
│  │ • Financial     │  │ • Embeddings    │  │ • Logs          │ │
│  │ • General Docs  │  │ • FAISS Index   │  │ • Cache         │ │
│  └─────────────────┘  └─────────────────┘  └─────────────────┘ │
└─────────────────────────────────────────────────────────────────┘
```

## 🚀 Quick Start

### Prerequisites
- Docker and Docker Compose
- 8GB+ RAM (5.5GB+ available for containers)
- 10GB+ disk space

### 🐳 Docker Deployment Options

#### **Option 1: Development (Quick Start)**
```bash
# Clone and start immediately
git clone https://github.com/LifeTimeScriptKiddie/RAGoLLAMA.git
cd RAGoLLAMA/test5_turborag_CAG

# One-line deployment
docker compose up -d && bash pull_models.sh
```

#### **Option 2: Production Ready**
```bash
# Automated production deployment
./deploy.sh -e production

# Manual production deployment
docker compose -f docker-compose.prod.yml up -d
bash pull_models.sh
```

#### **Option 3: Production with Nginx Proxy**
```bash
# Single entry point with reverse proxy
./deploy.sh -e production -p production -n

# Access all services through http://localhost
```

#### **Option 4: Cloud Deployment**
```bash
# For AWS, GCP, Azure with monitoring
docker compose -f docker-compose.cloud.yml --profile monitoring up -d
```

### 🌐 Service Access Points
- **Open WebUI (Chat)**: http://localhost:3000
- **Streamlit (Dashboard)**: http://localhost:8501
- **Knowledge Base API**: http://localhost:8502
- **Ollama API**: http://localhost:11434

### 📋 Deployment Script Options
```bash
./deploy.sh --help                    # Show all options
./deploy.sh                          # Development deployment
./deploy.sh -e production             # Production deployment  
./deploy.sh -e production -n          # Production + Nginx proxy
./deploy.sh --no-models               # Skip model installation
```

### Adding Documents
Place documents in organized folders within `./docs/`. They will be automatically processed:
- **At startup**: All existing documents from all folders
- **Daily at 2AM**: New documents added to any folder
- **Manual scan**: Use the "Document Manager" tab

**Organized Document Structure:**
- `./docs/cyber/` - Cybersecurity, malware analysis, penetration testing materials
- `./docs/financial/` - Financial statements, tax documents, investment guides  
- `./docs/` (root) - General purpose documents and reference materials

## 🧠 Core Intelligence Components

### 1. TurboRAG (Enhanced Retrieval)
**Location**: `core/turbo_rag.py`

Enhanced retrieval-augmented generation with:
- **Semantic re-ranking** using sentence transformers
- **Combined scoring** (vector distance + semantic similarity)
- **Confidence calculation** based on retrieval scores
- **Source attribution** for transparency

```python
def retrieve_and_rank(self, query: str, k: int = 5):
    # 1. Get initial results from vector store (2x candidates)
    # 2. Re-rank using semantic similarity
    # 3. Combine original + semantic scores
    # 4. Return top-k ranked results
```

### 2. CAG Engine (Context-Aware Generation)
**Location**: `core/cag_engine.py`

Context-aware generation with conversation memory:
- **Financial context integration** (SQLite transaction data)
- **User profile personalization** (risk tolerance, age, income)
- **Conversation memory** (last 10 exchanges)
- **Query classification** (financial vs. general)

```python
def generate_context_aware_response(self, query: str, context_type: str):
    # 1. Get RAG results from TurboRAG
    # 2. Build context (financial data + user profile + conversation history)
    # 3. Generate enhanced prompt with all context
    # 4. Get LLM response via Ollama
    # 5. Update conversation history
```

### 3. Ollama Client (LLM Integration)
**Location**: `core/ollama_client.py`

Intelligent model management with:
- **Automatic model detection** on startup
- **Intelligent fallback hierarchy** (llama3.2:1b → phi3 → etc.)
- **Connection health monitoring**
- **Error handling** with user-friendly messages

### 4. Document Manager (Auto Processing)
**Location**: `core/document_manager.py`

Automated document lifecycle management:
- **SQLite tracking** (filename, hash, status, metadata)
- **Startup auto-processing** (all docs on first run)
- **Scheduled processing** (2AM daily via Python `schedule`)
- **Duplicate detection** (file hash comparison)
- **Comprehensive logging**

## 📊 Data Flow Architecture

### Document Processing Pipeline
```
PDF File → Docling (OCR) → Text Chunks → Embeddings → FAISS Vector Store
    ↓              ↓           ↓            ↓              ↓
File Hash → SQLite Record → Vector Index → Search Ready → RAG Retrieval
```

### Query Processing Pipeline
```
User Query → Query Classification → TurboRAG Retrieval → Context Building → CAG Generation
     ↓              ↓                    ↓                    ↓              ↓
Chat Interface → Financial/General → Ranked Sources → Enhanced Prompt → LLM Response
```

### Financial Data Pipeline
```
Bank Statement → Statement Parser → Transaction Categorization → SQLite Storage
      ↓               ↓                      ↓                      ↓
Tax Analysis → Business Classification → Analytics Engine → Insights & Recommendations
```

## 🎯 5-Tab Streamlit Interface

### Tab 1: 🤖 Smart Assistant
- **Chat interface** with context-aware responses
- **Document upload** for immediate processing
- **Ollama model management** and status
- **User profile** setup for personalization

### Tab 2: 📊 Tax Dashboard
- **Statement upload** (PDF/CSV/OFX)
- **Transaction categorization** and business tagging
- **Tax optimization** suggestions
- **Financial insights** and deduction analysis

### Tab 3: 📈 Investments
- **Stock quotes** with real-time data
- **Portfolio analysis** with gain/loss calculations
- **Investment recommendations** by risk tolerance
- **Sample portfolio** analysis for demonstration

### Tab 4: 📊 Analytics
- **Spending analysis** with category breakdowns
- **Budget recommendations** with savings targets
- **Tax optimization insights**
- **Comprehensive financial reports**

### Tab 5: 📚 Document Manager
- **Document status** overview with processing logs
- **Manual operations** (scan, clear, export)
- **Processing statistics** and error tracking
- **System instructions** and file type support

## 🔧 Optimized Model Collection

### Memory-Optimized for 5.5GB Systems
```
qwen2.5:0.5b    (397MB)  → Ultra-fast responses
tinyllama       (637MB)  → Lightweight general tasks  
llama3.2:1b     (1.3GB)  → RECOMMENDED DEFAULT
codegemma:2b    (1.6GB)  → Programming & technical
phi3:latest     (2.2GB)  → Most capable analysis
                -------
Total:          6.1GB    → Only 1 runs at a time
```

The `pull_models.sh` script automatically installs this optimized collection based on your system's memory constraints.

## 🛡️ Error Handling & Resilience

### Docling Fallback Chain
```
Docling OCR → PyPDF2 → pdfminer → Text File → Binary + UTF-8 Decode
```

### Ollama Model Fallback
```
Requested Model → Default Model → First Available → Error Message
```

### Database Resilience
```
SQLite Connection → Check Table Exists → Create if Missing → Graceful Degradation
```

## 📁 Project Structure

```
test5_turborag_CAG/
├── core/                           # Core intelligence components
│   ├── cag_engine.py              # Context-aware generation
│   ├── turbo_rag.py               # Enhanced RAG with re-ranking
│   ├── ollama_client.py           # LLM integration
│   ├── document_manager.py        # Auto document processing
│   ├── stock_api.py               # Investment analysis
│   ├── ingestion.py               # Document ingestion with fallbacks
│   ├── vector_store.py            # FAISS vector operations
│   ├── statement_parser.py        # Financial statement parsing
│   ├── categorizer.py             # Transaction categorization
│   └── tax_optimizer.py           # Tax optimization engine
├── financial_advisor/             # Streamlit application
│   ├── app.py                     # Main 5-tab interface
│   └── analytics.py               # Financial analytics engine
├── docs/                          # Document storage (auto-processed)
│   ├── cyber/                     # Cybersecurity & malware analysis docs
│   ├── financial/                 # Financial statements & tax documents
│   └── [general files]            # Other reference materials
├── data/                          # SQLite database and logs
├── docker-compose.yml             # Container orchestration
├── pull_models.sh                 # Optimized model installer
├── .gitignore                     # Git ignore rules
└── README.md                      # This file
```

## 🔧 Configuration

### Environment Variables
Create a `.env` file:
```env
# Optional: Stock API key for live data
ALPHA_VANTAGE_API_KEY=your_api_key_here

# Optional: Ollama configuration
OLLAMA_BASE_URL=http://ollama:11434
```

### Model Configuration
Edit `core/ollama_client.py` to modify the model preference hierarchy:
```python
preferred_models = [
    "llama3.2:latest", "llama3.2", "llama3.1:latest",
    "phi3:latest", "phi3", "gemma:latest", "gemma",
    "qwen:latest", "qwen", "mistral:latest", "mistral"
]
```

## 🚀 Usage Examples

### 1. Financial Advice Chat
```
User: "How much should I save for retirement at age 30?"
Assistant: Based on your profile (age 30, $50k income), I recommend...
```

### 2. Document Analysis
```
User: "What does my uploaded tax document say about deductions?"
Assistant: I found several deductible expenses in your document...
```

### 3. Investment Analysis
```
User: "Analyze my portfolio risk for aggressive investor"
Assistant: Your portfolio shows 65% growth stocks, 25% bonds...
```

### 4. Tax Optimization
```
Upload bank statement → Automatic categorization → Tax insights
"You could save $1,200 in taxes by optimizing business meal deductions"
```

## 🐳 Docker Deployment Configurations

### 📋 Available Configurations

| Configuration | Purpose | Features | Use Case |
|---------------|---------|----------|----------|
| `docker-compose.yml` | Development | Hot reload, easy debugging | Local development |
| `docker-compose.prod.yml` | Production | Health checks, resource limits, security | Production deployment |
| `docker-compose.cloud.yml` | Cloud | Auto-scaling, monitoring, SSL | AWS/GCP/Azure |
| `nginx.conf` | Reverse Proxy | Single entry point, SSL termination | Production with proxy |

### 🚀 Deployment Environments

#### **Development Environment**
- **Purpose**: Local development and testing
- **Features**: Direct port access, easy debugging
- **Command**: `docker compose up -d`
- **Ports**: 3000 (WebUI), 8501 (Streamlit), 8502 (API), 11434 (Ollama)

#### **Production Environment**
- **Purpose**: Production deployment with enhanced security
- **Features**: Authentication enabled, health checks, resource limits
- **Command**: `./deploy.sh -e production`
- **Security**: Read-only mounts, restart policies, authentication required

#### **Cloud Environment**
- **Purpose**: Cloud platform deployment (AWS, GCP, Azure)
- **Features**: Auto-scaling, monitoring, external load balancer support
- **Command**: `docker compose -f docker-compose.cloud.yml up -d`
- **Optional**: Redis caching, PostgreSQL, Prometheus monitoring

### 🔧 Resource Requirements

| Environment | CPU | RAM | Disk | Network |
|-------------|-----|-----|------|---------|
| **Development** | 4 cores | 8GB | 20GB | Local |
| **Production** | 8 cores | 16GB | 50GB SSD | 1Gbps |
| **Cloud** | 4-16 cores | 16-32GB | 100GB+ | Load balanced |

### 📊 Recommended Cloud Instances

| Provider | Instance Type | vCPUs | RAM | Use Case |
|----------|---------------|-------|-----|----------|
| **AWS** | t3.xlarge | 4 | 16GB | Small production |
| **AWS** | m5.xlarge | 4 | 16GB | Balanced workload |
| **AWS** | m5.2xlarge | 8 | 32GB | High performance |
| **GCP** | n2-standard-4 | 4 | 16GB | Small production |
| **GCP** | e2-standard-4 | 4 | 16GB | Cost-optimized |
| **Azure** | Standard_D4s_v3 | 4 | 16GB | General purpose |

### 🌐 Open WebUI Integration

#### **Method 1: Upload Functions (Recommended)**
1. Access Open WebUI at http://localhost:3000
2. Go to **Settings** → **Functions**
3. Upload functions from `openwebui_functions/`:
   - `simple_financial_search.py` - Basic document search
   - `kb_status_checker.py` - Knowledge base status
   - `financial_advisor_kb.py` - Advanced features

#### **Method 2: Knowledge Base API Integration**
- **API Endpoint**: http://localhost:8502
- **Search**: `/search?query=malware&limit=3`
- **Status**: `/knowledge`
- **Documents**: `/documents`

#### **Method 3: Native Open WebUI Knowledge Base**
1. In Open WebUI, go to **Knowledge** section
2. Create knowledge base: "Financial Advisor Documents"
3. Upload documents from `docs/cyber/` and `docs/financial/`

### 🔐 Production Security Checklist

- ✅ **Authentication**: Enable WebUI authentication (`WEBUI_AUTH=True`)
- ✅ **Secret Keys**: Set strong `WEBUI_SECRET_KEY`
- ✅ **Network**: Configure firewall rules
- ✅ **SSL/TLS**: Set up HTTPS with certificates
- ✅ **Updates**: Regular security updates
- ✅ **Backups**: Automated data backups
- ✅ **Monitoring**: Health checks and alerting

### 📈 Scaling and Monitoring

#### **Horizontal Scaling**
```bash
# Scale Financial Advisor service
docker compose up -d --scale financial_advisor=3
```

#### **Monitoring Stack**
```bash
# Deploy with Prometheus and Grafana
docker compose -f docker-compose.cloud.yml --profile monitoring up -d

# Access monitoring
# Grafana: http://localhost:3000
# Prometheus: http://localhost:9090
```

#### **Health Monitoring**
```bash
# Check all service health
curl http://localhost/health

# Individual health checks
curl http://localhost:8501/_stcore/health  # Streamlit
curl http://localhost:8502/               # Knowledge Base API
curl http://localhost:11434/api/version   # Ollama
```

### 🔄 Backup and Recovery

#### **Data Volumes**
```bash
# List volumes to backup
docker volume ls | grep financial

# Backup critical data
docker run --rm -v shared_models:/data -v $(pwd):/backup alpine tar czf /backup/models.tar.gz -C /data .
docker run --rm -v openwebui_data:/data -v $(pwd):/backup alpine tar czf /backup/webui.tar.gz -C /data .
```

#### **Recovery Process**
```bash
# Restore from backup
docker volume create shared_models
docker run --rm -v shared_models:/data -v $(pwd):/backup alpine tar xzf /backup/models.tar.gz -C /data
```

## 🔍 Troubleshooting

### Model Issues
```bash
# Check available models
docker exec test5_turborag_cag-ollama-1 ollama list

# Pull specific model
docker exec test5_turborag_cag-ollama-1 ollama pull llama3.2:1b

# Check model memory usage
docker stats
```

### Document Processing Issues
1. Check the **Document Manager** tab for processing logs
2. Verify PDF files are in `./docs/` folder
3. Check container logs: `docker logs test5_turborag_cag-financial_advisor-1`

### Container Issues
```bash
# Check all containers
docker compose ps

# Restart specific service
docker compose restart financial_advisor

# View logs
docker compose logs -f
```

### Deployment Issues

#### **Out of Memory Errors**
```bash
# Check memory usage
docker stats

# Free up memory
docker system prune -a

# Use smaller models
# Edit pull_models.sh to remove large models
```

#### **Port Conflicts**
```bash
# Check port usage
netstat -tlnp | grep :3000

# Change ports in docker-compose.yml
ports:
  - "3001:8080"  # Changed from 3000:8080
```

#### **SSL Certificate Issues**
```bash
# Generate self-signed certificate for testing
mkdir -p ssl
openssl req -x509 -nodes -days 365 -newkey rsa:2048 \
  -keyout ssl/key.pem -out ssl/cert.pem \
  -subj "/C=US/ST=State/L=City/O=Organization/CN=localhost"
```

#### **Cloud Deployment Issues**
```bash
# Check cloud instance resources
top
df -h
free -h

# Verify network connectivity
curl -I http://localhost:3000
curl -I http://localhost:8501

# Check cloud provider firewall/security groups
# Ensure ports 80, 443, 3000, 8501 are open
```

#### **Performance Issues**
```bash
# Monitor resource usage
docker stats --format "table {{.Container}}\t{{.CPUPerc}}\t{{.MemUsage}}"

# Optimize model selection
docker exec test5_turborag_cag-ollama-1 ollama list

# Scale services if needed
docker compose up -d --scale financial_advisor=2
```

## 🐳 Complete Deployment Summary

### 🎯 **Deployment Options Comparison**

| Feature | Development | Production | Cloud | 
|---------|-------------|------------|--------|
| **Setup Complexity** | ⭐ Simple | ⭐⭐ Medium | ⭐⭐⭐ Advanced |
| **Security** | Basic | Enhanced | Enterprise |
| **Monitoring** | Logs only | Health checks | Full stack |
| **Scalability** | Single instance | Multi-instance | Auto-scaling |
| **SSL/HTTPS** | No | Optional | Required |
| **Backup** | Manual | Automated | Cloud backup |
| **Cost** | Free | Low | Variable |

### 🚀 **Quick Deploy Commands**

```bash
# 🔧 Development (Current setup)
docker compose up -d && bash pull_models.sh

# 🏭 Production
./deploy.sh -e production

# 🌐 Production with Proxy
./deploy.sh -e production -p production -n

# ☁️ Cloud with Monitoring  
docker compose -f docker-compose.cloud.yml --profile monitoring up -d

# 🔄 Update deployment
docker compose pull && docker compose up -d --force-recreate
```

### 📊 **Post-Deployment Verification**

```bash
# ✅ Check all services
curl http://localhost:3000    # Open WebUI
curl http://localhost:8501    # Streamlit  
curl http://localhost:8502    # Knowledge Base API
curl http://localhost:11434   # Ollama API

# ✅ Verify models loaded
docker exec test5_turborag_cag-ollama-1 ollama list

# ✅ Check document processing
curl http://localhost:8502/knowledge | jq '.total_documents'

# ✅ Test knowledge base integration
# Upload kb_status_checker.py to Open WebUI and ask "What's my knowledge base status?"
```

### 🎉 **Success Indicators**

Your deployment is successful when:
- ✅ All containers show "healthy" status
- ✅ Open WebUI loads at http://localhost:3000  
- ✅ Streamlit dashboard loads at http://localhost:8501
- ✅ Knowledge Base API responds at http://localhost:8502
- ✅ 56+ documents are processed and searchable
- ✅ LLM models respond to queries
- ✅ Open WebUI functions can access your document knowledge base

## 🏗️ Development

### Adding New Features
1. **Core Intelligence**: Add to `core/` directory
2. **UI Components**: Modify `financial_advisor/app.py`
3. **Analytics**: Extend `financial_advisor/analytics.py`

### Testing Document Processing
```bash
python test_ingestion.py
```

### Adding New Models
1. Edit `pull_models.sh` to add new models
2. Update fallback hierarchy in `core/ollama_client.py`
3. Test memory usage with `docker stats`

## 📈 Performance Optimization

### Memory Management
- Only one LLM model loads at a time
- Document embeddings cached in FAISS
- SQLite for lightweight data storage
- Automatic cleanup of temporary files

### Processing Speed
- TurboRAG re-ranking for better results
- Cached embeddings for faster retrieval
- Background document processing
- Efficient vector operations

## 🤝 Contributing

1. Fork the repository
2. Create a feature branch: `git checkout -b feature-name`
3. Make changes and test thoroughly
4. Commit: `git commit -m "Add feature-name"`
5. Push: `git push origin feature-name`
6. Create a Pull Request

## 📝 License

This project is licensed under the MIT License - see the LICENSE file for details.

## 🙏 Acknowledgments

- **Docling** for advanced PDF processing with OCR
- **Ollama** for local LLM inference
- **Streamlit** for the interactive web interface
- **FAISS** for efficient vector search
- **Sentence Transformers** for embeddings
- **Claude Code** for development assistance

## 📞 Support

For issues and questions:
1. Check the **Document Manager** tab for system status
2. Review container logs: `docker compose logs`
3. Create an issue on GitHub with system details

---

**🎯 Built for memory-efficient systems while providing enterprise-level financial advisory capabilities!**