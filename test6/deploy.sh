#!/bin/bash

# Financial Advisor Suite Deployment Script
# Supports development, production, and cloud deployment

set -e

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" &> /dev/null && pwd)"
cd "$SCRIPT_DIR"

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Default values
ENVIRONMENT="development"
PROFILE=""
PULL_MODELS=true
NGINX_PROXY=false

# Function to print colored output
print_status() {
    echo -e "${BLUE}[INFO]${NC} $1"
}

print_success() {
    echo -e "${GREEN}[SUCCESS]${NC} $1"
}

print_warning() {
    echo -e "${YELLOW}[WARNING]${NC} $1"
}

print_error() {
    echo -e "${RED}[ERROR]${NC} $1"
}

# Function to show help
show_help() {
    echo "Financial Advisor Suite Deployment Script"
    echo ""
    echo "Usage: $0 [OPTIONS]"
    echo ""
    echo "OPTIONS:"
    echo "  -e, --environment ENV    Set environment (development|production) [default: development]"
    echo "  -p, --profile PROFILE    Set docker-compose profile (production)"
    echo "  -n, --nginx             Enable nginx reverse proxy"
    echo "  --no-models             Skip model pulling"
    echo "  -h, --help              Show this help message"
    echo ""
    echo "EXAMPLES:"
    echo "  $0                                    # Development deployment"
    echo "  $0 -e production                     # Production deployment"
    echo "  $0 -e production -p production -n    # Production with nginx proxy"
    echo "  $0 --no-models                       # Skip model downloading"
}

# Parse command line arguments
while [[ $# -gt 0 ]]; do
    case $1 in
        -e|--environment)
            ENVIRONMENT="$2"
            shift 2
            ;;
        -p|--profile)
            PROFILE="$2"
            shift 2
            ;;
        -n|--nginx)
            NGINX_PROXY=true
            shift
            ;;
        --no-models)
            PULL_MODELS=false
            shift
            ;;
        -h|--help)
            show_help
            exit 0
            ;;
        *)
            print_error "Unknown option: $1"
            show_help
            exit 1
            ;;
    esac
done

# Validate environment
if [[ "$ENVIRONMENT" != "development" && "$ENVIRONMENT" != "production" ]]; then
    print_error "Environment must be 'development' or 'production'"
    exit 1
fi

print_status "🚀 Starting Financial Advisor Suite deployment..."
print_status "Environment: $ENVIRONMENT"

# Check requirements
check_requirements() {
    print_status "Checking requirements..."
    
    # Check Docker
    if ! command -v docker &> /dev/null; then
        print_error "Docker is not installed. Please install Docker first."
        exit 1
    fi
    
    # Check Docker Compose
    if ! docker compose version &> /dev/null; then
        print_error "Docker Compose is not available. Please install Docker Compose."
        exit 1
    fi
    
    # Check available disk space (at least 10GB)
    available_space=$(df . | tail -1 | awk '{print $4}')
    required_space=$((10 * 1024 * 1024)) # 10GB in KB
    
    if [[ $available_space -lt $required_space ]]; then
        print_warning "Less than 10GB disk space available. This may cause issues."
    fi
    
    print_success "Requirements check passed"
}

# Setup environment
setup_environment() {
    print_status "Setting up environment..."
    
    # Create data directories
    mkdir -p data logs
    
    # Setup environment file
    if [[ "$ENVIRONMENT" == "production" ]]; then
        if [[ ! -f .env ]]; then
            print_status "Creating production environment file..."
            cp .env.production .env
            print_warning "Please edit .env file with your production settings"
        fi
    else
        # Development environment
        if [[ ! -f .env ]]; then
            print_status "Creating development environment file..."
            cat > .env << EOF
# Development Environment
OLLAMA_BASE_URL=http://ollama:11434
WEBUI_AUTH=False
WEBUI_NAME=Financial Advisor Suite (Dev)
STREAMLIT_SERVER_HEADLESS=true
LOG_LEVEL=DEBUG
EOF
        fi
    fi
    
    print_success "Environment setup complete"
}

# Deploy services
deploy_services() {
    print_status "Deploying services..."
    
    # Choose docker-compose file
    COMPOSE_FILE="docker-compose.yml"
    if [[ "$ENVIRONMENT" == "production" ]]; then
        COMPOSE_FILE="docker-compose.prod.yml"
    fi
    
    # Build profile arguments
    PROFILE_ARGS=""
    if [[ -n "$PROFILE" ]]; then
        PROFILE_ARGS="--profile $PROFILE"
    fi
    
    # Stop existing services
    print_status "Stopping existing services..."
    docker compose -f "$COMPOSE_FILE" down
    
    # Pull latest images
    print_status "Pulling latest images..."
    docker compose -f "$COMPOSE_FILE" pull
    
    # Build custom images
    print_status "Building Financial Advisor image..."
    docker compose -f "$COMPOSE_FILE" build financial_advisor
    
    # Start services
    print_status "Starting services..."
    docker compose -f "$COMPOSE_FILE" up -d $PROFILE_ARGS
    
    print_success "Services deployed"
}

# Install models
install_models() {
    if [[ "$PULL_MODELS" == "true" ]]; then
        print_status "Installing Ollama models..."
        
        # Wait for Ollama to be ready
        print_status "Waiting for Ollama to be ready..."
        timeout=300  # 5 minutes
        elapsed=0
        
        while ! docker exec $(docker ps -q -f name=ollama) ollama list &> /dev/null; do
            if [[ $elapsed -ge $timeout ]]; then
                print_error "Timeout waiting for Ollama to start"
                exit 1
            fi
            sleep 5
            elapsed=$((elapsed + 5))
            echo -n "."
        done
        echo ""
        
        # Run model installation script
        if [[ -f pull_models.sh ]]; then
            print_status "Running model installation script..."
            bash pull_models.sh
        else
            print_warning "pull_models.sh not found, skipping model installation"
        fi
        
        print_success "Models installed"
    else
        print_status "Skipping model installation"
    fi
}

# Verify deployment
verify_deployment() {
    print_status "Verifying deployment..."
    
    # Check container health
    services=("ollama" "open-webui" "financial_advisor")
    
    for service in "${services[@]}"; do
        container_name=$(docker ps -q -f name="$service")
        if [[ -n "$container_name" ]]; then
            print_success "$service container is running"
        else
            print_error "$service container is not running"
            return 1
        fi
    done
    
    # Check service endpoints
    print_status "Checking service endpoints..."
    
    # Give services time to start
    sleep 10
    
    # Check Ollama
    if curl -s http://localhost:11434/api/version > /dev/null; then
        print_success "Ollama API is responding"
    else
        print_warning "Ollama API is not responding yet"
    fi
    
    # Check Open WebUI
    if curl -s http://localhost:3000 > /dev/null; then
        print_success "Open WebUI is responding"
    else
        print_warning "Open WebUI is not responding yet"
    fi
    
    # Check Streamlit
    if curl -s http://localhost:8501 > /dev/null; then
        print_success "Streamlit is responding"
    else
        print_warning "Streamlit is not responding yet"
    fi
    
    # Check Knowledge Base API
    if curl -s http://localhost:8502 > /dev/null; then
        print_success "Knowledge Base API is responding"
    else
        print_warning "Knowledge Base API is not responding yet"
    fi
}

# Show deployment summary
show_summary() {
    print_success "🎉 Deployment complete!"
    echo ""
    echo "📋 Service URLs:"
    echo "   Open WebUI (Chat):      http://localhost:3000"
    echo "   Streamlit (Dashboard):  http://localhost:8501"
    echo "   Knowledge Base API:     http://localhost:8502"
    echo "   Ollama API:            http://localhost:11434"
    
    if [[ "$NGINX_PROXY" == "true" ]]; then
        echo "   Nginx Proxy:           http://localhost:80"
    fi
    
    echo ""
    echo "📚 Quick Start:"
    echo "   1. Open http://localhost:3000 for the chat interface"
    echo "   2. Create an admin account in Open WebUI"
    echo "   3. Upload the functions from openwebui_functions/"
    echo "   4. Start chatting with your knowledge base!"
    echo ""
    echo "🔧 Management Commands:"
    echo "   View logs:    docker compose logs -f"
    echo "   Stop:         docker compose down"
    echo "   Restart:      docker compose restart"
    echo "   Status:       docker ps"
    echo ""
    
    if [[ "$ENVIRONMENT" == "production" ]]; then
        print_warning "Production deployment notes:"
        echo "   - Update .env with your production settings"
        echo "   - Configure SSL certificates for HTTPS"
        echo "   - Set up backup procedures for data volumes"
        echo "   - Monitor resource usage and scale as needed"
    fi
}

# Main deployment flow
main() {
    check_requirements
    setup_environment
    deploy_services
    install_models
    verify_deployment
    show_summary
}

# Run main function
main