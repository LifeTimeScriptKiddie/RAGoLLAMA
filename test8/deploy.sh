#!/bin/bash

# Multi-RAG Document Pipeline Deployment Script
set -e

echo "🚀 Multi-RAG Document Pipeline Deployment"
echo "========================================"

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Configuration
DOCKER_COMPOSE_FILE="docker-compose.yml"
CONFIG_FILE="config/config.json"
ENV_FILE=".env"

# Functions
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

# Check if Docker and Docker Compose are installed
check_docker() {
    log_info "Checking Docker installation..."
    
    if ! command -v docker &> /dev/null; then
        log_error "Docker is not installed. Please install Docker first."
        exit 1
    fi
    
    if ! command -v docker-compose &> /dev/null; then
        log_error "Docker Compose is not installed. Please install Docker Compose first."
        exit 1
    fi
    
    log_success "Docker and Docker Compose are installed"
}

# Create necessary directories
create_directories() {
    log_info "Creating necessary directories..."
    
    mkdir -p cache/faiss
    mkdir -p cache/documents
    mkdir -p logs
    mkdir -p documents
    mkdir -p config
    
    log_success "Directories created"
}

# Create .env file if it doesn't exist
create_env_file() {
    if [ ! -f "$ENV_FILE" ]; then
        log_info "Creating .env file..."
        
        cat > "$ENV_FILE" << EOF
# Multi-RAG Document Pipeline Environment Variables

# General Configuration
LOG_LEVEL=INFO
ENVIRONMENT=production

# Database Configuration
DB_PATH=/app/cache/documents.db

# Vector Store Configuration
FAISS_INDEX_PATH=/app/cache/faiss

# Ollama Configuration
OLLAMA_URL=http://ollama:11434
OLLAMA_MODEL=llama2

# API Configuration
API_HOST=0.0.0.0
API_PORT=8000

# Streamlit Configuration
STREAMLIT_HOST=0.0.0.0
STREAMLIT_PORT=8501

# Microsoft API (Optional - set if using real Microsoft embeddings)
# MICROSOFT_API_KEY=your_api_key_here

# OpenWebUI Secret Key
WEBUI_SECRET_KEY=multi-rag-secret-key-$(date +%s)
EOF
        
        log_success ".env file created"
    else
        log_info ".env file already exists"
    fi
}

# Pull Ollama models
pull_ollama_models() {
    log_info "Pulling Ollama models..."
    
    # Start only Ollama service first
    docker-compose up -d ollama
    
    # Wait for Ollama to be ready
    log_info "Waiting for Ollama service to be ready..."
    sleep 10
    
    # Pull models
    models=("llama2" "codellama" "mistral")
    
    for model in "${models[@]}"; do
        log_info "Pulling model: $model"
        docker-compose exec ollama ollama pull "$model" || log_warning "Failed to pull $model"
    done
    
    log_success "Ollama models pulled"
}

# Build and start services
deploy_services() {
    log_info "Building and starting services..."
    
    # Build images
    docker-compose build
    
    # Start all services
    docker-compose up -d
    
    log_success "Services deployed"
}

# Check service health
check_health() {
    log_info "Checking service health..."
    
    # Wait a bit for services to start
    sleep 15
    
    # Check API health
    if curl -f http://localhost:8000/health &> /dev/null; then
        log_success "API service is healthy"
    else
        log_warning "API service health check failed"
    fi
    
    # Check Streamlit
    if curl -f http://localhost:8501 &> /dev/null; then
        log_success "Streamlit service is healthy"
    else
        log_warning "Streamlit service health check failed"
    fi
    
    # Check Ollama
    if curl -f http://localhost:11434/api/tags &> /dev/null; then
        log_success "Ollama service is healthy"
    else
        log_warning "Ollama service health check failed"
    fi
    
    # Check OpenWebUI
    if curl -f http://localhost:3000 &> /dev/null; then
        log_success "OpenWebUI service is healthy"
    else
        log_warning "OpenWebUI service health check failed"
    fi
}

# Show service information
show_services() {
    echo ""
    log_success "Deployment completed!"
    echo ""
    echo "🌐 Service URLs:"
    echo "  • API Documentation: http://localhost:8000/docs"
    echo "  • Streamlit Web UI: http://localhost:8501"
    echo "  • OpenWebUI: http://localhost:3000"
    echo "  • Ollama API: http://localhost:11434"
    echo ""
    echo "📋 Available commands:"
    echo "  • View logs: docker-compose logs -f"
    echo "  • Stop services: docker-compose down"
    echo "  • Restart services: docker-compose restart"
    echo "  • View status: docker-compose ps"
    echo ""
    echo "📁 Important directories:"
    echo "  • Documents: ./documents/ (place your files here)"
    echo "  • Cache: ./cache/ (vector indexes and database)"
    echo "  • Logs: ./logs/ (application logs)"
    echo "  • Config: ./config/ (configuration files)"
}

# Parse command line arguments
COMMAND=${1:-"deploy"}

case $COMMAND in
    "deploy")
        check_docker
        create_directories
        create_env_file
        deploy_services
        pull_ollama_models
        check_health
        show_services
        ;;
    "start")
        log_info "Starting services..."
        docker-compose up -d
        check_health
        show_services
        ;;
    "stop")
        log_info "Stopping services..."
        docker-compose down
        log_success "Services stopped"
        ;;
    "restart")
        log_info "Restarting services..."
        docker-compose restart
        check_health
        log_success "Services restarted"
        ;;
    "pull-models")
        pull_ollama_models
        ;;
    "logs")
        docker-compose logs -f
        ;;
    "status")
        docker-compose ps
        ;;
    "clean")
        log_warning "This will remove all containers, images, and volumes"
        read -p "Are you sure? (y/N) " -n 1 -r
        echo
        if [[ $REPLY =~ ^[Yy]$ ]]; then
            docker-compose down -v --rmi all
            log_success "Cleanup completed"
        else
            log_info "Cleanup cancelled"
        fi
        ;;
    "help")
        echo "Usage: $0 [COMMAND]"
        echo ""
        echo "Commands:"
        echo "  deploy      Full deployment (default)"
        echo "  start       Start services"
        echo "  stop        Stop services"
        echo "  restart     Restart services"
        echo "  pull-models Pull Ollama models"
        echo "  logs        View logs"
        echo "  status      Show service status"
        echo "  clean       Remove all containers and data"
        echo "  help        Show this help"
        ;;
    *)
        log_error "Unknown command: $COMMAND"
        echo "Use '$0 help' for available commands"
        exit 1
        ;;
esac