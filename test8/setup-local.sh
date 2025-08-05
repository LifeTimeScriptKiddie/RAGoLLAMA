#!/bin/bash

# Local Development Setup Script for macOS/Linux
set -e

echo "🔧 Multi-RAG Pipeline Local Development Setup"
echo "============================================"

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

log_info() {
    echo -e "${BLUE}ℹ️  $1${NC}"
}

log_success() {
    echo -e "${GREEN}✅ $1${NC}"
}

log_warning() {
    echo -e "${YELLOW}⚠️  $1${NC}"
}

log_error() {
    echo -e "${RED}❌ $1${NC}"
}

# Check Python version
check_python() {
    log_info "Checking Python version..."
    
    if command -v python3 &> /dev/null; then
        PYTHON_CMD="python3"
    elif command -v python &> /dev/null; then
        PYTHON_CMD="python"
    else
        log_error "Python is not installed"
        exit 1
    fi
    
    PYTHON_VERSION=$($PYTHON_CMD --version 2>&1 | cut -d' ' -f2)
    MAJOR_VERSION=$(echo $PYTHON_VERSION | cut -d'.' -f1)
    MINOR_VERSION=$(echo $PYTHON_VERSION | cut -d'.' -f2)
    
    if [ $MAJOR_VERSION -eq 3 ] && [ $MINOR_VERSION -ge 8 ]; then
        log_success "Python $PYTHON_VERSION is compatible"
    else
        log_error "Python 3.8+ is required (found $PYTHON_VERSION)"
        exit 1
    fi
}

# Create virtual environment
create_venv() {
    log_info "Creating virtual environment..."
    
    if [ ! -d "venv" ]; then
        $PYTHON_CMD -m venv venv
        log_success "Virtual environment created"
    else
        log_info "Virtual environment already exists"
    fi
}

# Activate virtual environment and install packages
install_deps() {
    log_info "Installing dependencies..."
    
    # Activate virtual environment
    source venv/bin/activate
    
    # Upgrade pip
    pip install --upgrade pip
    
    # Install dependencies
    pip install -r requirements-dev.txt
    
    log_success "Dependencies installed"
}

# Install system dependencies (macOS)
install_system_deps() {
    if [[ "$OSTYPE" == "darwin"* ]]; then
        log_info "Installing macOS system dependencies..."
        
        # Check if Homebrew is installed
        if command -v brew &> /dev/null; then
            # Install tesseract for OCR
            if ! brew list tesseract &> /dev/null; then
                log_info "Installing tesseract..."
                brew install tesseract
                log_success "Tesseract installed"
            else
                log_info "Tesseract already installed"
            fi
            
            # Install libmagic for file type detection
            if ! brew list libmagic &> /dev/null; then
                log_info "Installing libmagic..."
                brew install libmagic
                log_success "libmagic installed"
            else
                log_info "libmagic already installed"
            fi
        else
            log_warning "Homebrew not found. Please install manually:"
            log_warning "- tesseract: brew install tesseract"
            log_warning "- libmagic: brew install libmagic"
        fi
    else
        log_info "Linux detected - please ensure these are installed:"
        log_info "- tesseract-ocr"
        log_info "- libmagic1"
    fi
}

# Create directories
create_directories() {
    log_info "Creating directories..."
    
    mkdir -p cache/{faiss,documents}
    mkdir -p logs
    mkdir -p documents
    mkdir -p config
    
    log_success "Directories created"
}

# Create local config
create_local_config() {
    if [ ! -f "config/config-local.json" ]; then
        log_info "Creating local configuration..."
        
        cat > config/config-local.json << 'EOF'
{
  "general": {
    "log_level": "INFO",
    "environment": "development"
  },
  "database": {
    "db_path": "./cache/documents.db"
  },
  "document_processing": {
    "max_chunk_size": 1000,
    "chunk_overlap": 200,
    "supported_formats": [".pdf", ".txt", ".docx", ".pptx", ".jpg", ".png"]
  },
  "embeddings": {
    "dimension": 384,
    "docling": {
      "model_name": "sentence-transformers/all-MiniLM-L6-v2",
      "batch_size": 16,
      "cache_embeddings": true
    },
    "microsoft": {
      "use_mock": true,
      "batch_size": 8
    }
  },
  "vector_store": {
    "faiss_index_path": "./cache/faiss",
    "index_type": "HNSW",
    "dimension": 384
  },
  "comparison": {
    "similarity_threshold": 0.7,
    "comparison_metrics": ["cosine"]
  },
  "ollama": {
    "ollama_url": "http://localhost:11434",
    "default_model": "llama2",
    "timeout": 30,
    "max_retries": 3
  },
  "api": {
    "host": "127.0.0.1",
    "port": 8000,
    "cors_origins": ["http://localhost:8501"],
    "max_file_size": "50MB"
  },
  "streamlit": {
    "host": "127.0.0.1",
    "port": 8501,
    "api_base_url": "http://localhost:8000"
  },
  "cache": {
    "faiss_index_path": "./cache/faiss",
    "documents_cache_path": "./cache/documents",
    "logs_path": "./logs"
  }
}
EOF
        
        log_success "Local configuration created"
    else
        log_info "Local configuration already exists"
    fi
}

# Install Ollama (optional)
install_ollama() {
    if ! command -v ollama &> /dev/null; then
        log_info "Ollama not found. Install instructions:"
        if [[ "$OSTYPE" == "darwin"* ]]; then
            log_info "macOS: Download from https://ollama.ai or use: brew install ollama"
        else
            log_info "Linux: curl -fsSL https://ollama.ai/install.sh | sh"
        fi
        log_warning "Ollama is optional but recommended for RAG functionality"
    else
        log_success "Ollama is installed"
        
        # Pull default model
        log_info "Pulling default model (llama2)..."
        ollama pull llama2 || log_warning "Failed to pull llama2 model"
    fi
}

# Show usage instructions
show_usage() {
    echo ""
    log_success "Local development setup completed!"
    echo ""
    echo "🚀 Quick Start:"
    echo "  1. Activate virtual environment: source venv/bin/activate"
    echo "  2. Run CLI: python main.py --interface cli --config config/config-local.json"
    echo "  3. Run API: python main.py --interface api --config config/config-local.json"
    echo "  4. Run Streamlit: python main.py --interface streamlit --config config/config-local.json"
    echo ""
    echo "📋 Example commands:"
    echo "  # Process a document"
    echo "  python main.py -i cli -c config/config-local.json -- process documents/sample.pdf --method both"
    echo ""
    echo "  # Start API server"
    echo "  python main.py -i api -c config/config-local.json"
    echo ""
    echo "  # Search documents"
    echo "  python main.py -i cli -c config/config-local.json -- search \"your query\""
    echo ""
    echo "📁 Place your documents in: ./documents/"
    echo "📊 View logs in: ./logs/"
    echo "⚙️  Configuration: ./config/config-local.json"
}

# Main execution
case ${1:-"setup"} in
    "setup")
        check_python
        create_directories
        create_venv
        install_system_deps
        install_deps
        create_local_config
        install_ollama
        show_usage
        ;;
    "clean")
        log_info "Cleaning up..."
        rm -rf venv cache logs
        log_success "Cleanup completed"
        ;;
    "help")
        echo "Usage: $0 [COMMAND]"
        echo ""
        echo "Commands:"
        echo "  setup    Set up local development environment (default)"
        echo "  clean    Remove virtual environment and cache"
        echo "  help     Show this help"
        ;;
    *)
        log_error "Unknown command: $1"
        echo "Use '$0 help' for available commands"
        exit 1
        ;;
esac