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
│  │ • PDF Documents │  │ • Vector Store  │  │ • SQLite DB     │ │
│  │ • Auto-scanned  │  │ • Embeddings    │  │ • Logs          │ │
│  │ • 54 Tech Books │  │ • FAISS Index   │  │ • Cache         │ │
│  └─────────────────┘  └─────────────────┘  └─────────────────┘ │
└─────────────────────────────────────────────────────────────────┘
```

## 🚀 Quick Start

### Prerequisites
- Docker and Docker Compose
- 8GB+ RAM (5.5GB+ available for containers)
- 10GB+ disk space

### Installation

1. **Clone and setup**:
```bash
git clone https://github.com/LifeTimeScriptKiddie/RAGoLLAMA.git
cd RAGoLLAMA/test5_turborag_CAG
```

2. **Start the system**:
```bash
docker compose up -d
```

3. **Install optimized LLM models**:
```bash
bash pull_models.sh
```

4. **Access the application**:
- **Streamlit App**: http://localhost:8501
- **Ollama WebUI**: http://localhost:3000
- **Ollama API**: http://localhost:11434

### Adding Documents
Place PDF files in the `./docs/` folder. They will be automatically processed:
- **At startup**: All existing documents
- **Daily at 2AM**: New documents added to the folder
- **Manual scan**: Use the "Document Manager" tab

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