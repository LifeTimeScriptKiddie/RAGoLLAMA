# Multi-RAG Document Pipeline - Development Commands

.PHONY: help setup-local setup-docker clean test lint run-cli run-api run-streamlit docker-build docker-up docker-down

# Default target
help:
	@echo "Multi-RAG Document Pipeline - Available Commands"
	@echo "================================================"
	@echo ""
	@echo "Development:"
	@echo "  setup-local     Set up local development environment"
	@echo "  setup-docker    Set up Docker environment"
	@echo "  clean          Clean up generated files"
	@echo "  test           Run tests"
	@echo "  lint           Run code linting"
	@echo ""
	@echo "Local Development:"
	@echo "  run-cli        Run CLI interface"
	@echo "  run-api        Run API server"
	@echo "  run-streamlit  Run Streamlit web interface"
	@echo ""
	@echo "Docker:"
	@echo "  docker-build   Build Docker images"
	@echo "  docker-up      Start Docker services"
	@echo "  docker-down    Stop Docker services"
	@echo ""
	@echo "Example usage:"
	@echo "  make setup-local"
	@echo "  make run-api"
	@echo "  make docker-up"

# Local Development Setup
setup-local:
	@echo "Setting up local development environment..."
	./setup-local.sh setup

# Docker Setup
setup-docker:
	@echo "Setting up Docker environment..."
	./deploy.sh deploy

# Clean up
clean:
	@echo "Cleaning up..."
	rm -rf venv __pycache__ .pytest_cache
	rm -rf cache logs
	find . -name "*.pyc" -delete
	find . -name "__pycache__" -type d -exec rm -rf {} +

# Test
test:
	@echo "Running tests..."
	@if [ -d "venv" ]; then \
		source venv/bin/activate && python -m pytest tests/; \
	else \
		echo "Virtual environment not found. Run 'make setup-local' first."; \
	fi

# Lint
lint:
	@echo "Running linting..."
	@if [ -d "venv" ]; then \
		source venv/bin/activate && \
		black --check . && \
		isort --check-only . && \
		flake8 .; \
	else \
		echo "Virtual environment not found. Run 'make setup-local' first."; \
	fi

# Format code
format:
	@echo "Formatting code..."
	@if [ -d "venv" ]; then \
		source venv/bin/activate && \
		black . && \
		isort .; \
	else \
		echo "Virtual environment not found. Run 'make setup-local' first."; \
	fi

# Local Development - CLI
run-cli:
	@if [ -d "venv" ]; then \
		source venv/bin/activate && \
		python main.py --interface cli --config config/config-local.json; \
	else \
		echo "Virtual environment not found. Run 'make setup-local' first."; \
	fi

# Local Development - API
run-api:
	@if [ -d "venv" ]; then \
		source venv/bin/activate && \
		python main.py --interface api --config config/config-local.json; \
	else \
		echo "Virtual environment not found. Run 'make setup-local' first."; \
	fi

# Local Development - Streamlit
run-streamlit:
	@if [ -d "venv" ]; then \
		source venv/bin/activate && \
		python main.py --interface streamlit --config config/config-local.json; \
	else \
		echo "Virtual environment not found. Run 'make setup-local' first."; \
	fi

# Docker Commands
docker-build:
	@echo "Building Docker images..."
	docker-compose build

docker-up:
	@echo "Starting Docker services..."
	docker-compose up -d

docker-down:
	@echo "Stopping Docker services..."
	docker-compose down

docker-logs:
	@echo "Showing Docker logs..."
	docker-compose logs -f

# Process a sample document (requires setup)
demo:
	@echo "Running demo..."
	@if [ -d "venv" ]; then \
		source venv/bin/activate && \
		echo "Place a document in ./documents/ and run:"; \
		echo "python main.py -i cli -c config/config-local.json -- process documents/your-file.pdf --method both --compare"; \
	else \
		echo "Virtual environment not found. Run 'make setup-local' first."; \
	fi

# Install development dependencies
install-dev:
	@if [ -d "venv" ]; then \
		source venv/bin/activate && \
		pip install -r requirements-dev.txt; \
	else \
		echo "Virtual environment not found. Run 'make setup-local' first."; \
	fi

# Check system dependencies
check-deps:
	@echo "Checking system dependencies..."
	@python --version || echo "Python not found"
	@docker --version || echo "Docker not found"
	@docker-compose --version || echo "Docker Compose not found"
	@ollama --version || echo "Ollama not found (optional)"