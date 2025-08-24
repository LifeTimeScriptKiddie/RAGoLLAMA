.PHONY: help dev build clean ingest reindex snapshot restore eval k8s-dev k8s-prod

help: ## Show this help message
	@echo "RAG-Ollama Makefile"
	@echo "Available targets:"
	@awk 'BEGIN {FS = ":.*##"} /^[a-zA-Z_-]+:.*##/ { printf "  %-15s %s\n", $$1, $$2 }' $(MAKEFILE_LIST)

dev: ## Start development environment with docker-compose
	@echo "Starting development environment..."
	@if [ ! -f .env ]; then cp .env.example .env; fi
	@echo "Creating data directories..."
	@mkdir -p data/{raw_docs,index,cache,index_snapshots}
	@echo "Starting Docker services..."
	docker-compose up --build -d ollama
	@echo "Waiting for Ollama to be ready..."
	@sleep 10
	docker-compose up --build -d
	@echo "Services starting..."
	@echo "Backend will be available at http://localhost:8000"
	@echo "Streamlit UI will be available at http://localhost:8501"
	@echo "Grafana will be available at http://localhost:3000 (admin/admin)"

dev-logs: ## Show logs from development containers
	docker-compose logs -f

stop: ## Stop development environment
	docker-compose down

build: ## Build all Docker images
	docker-compose build

clean: ## Clean up containers, volumes, and data
	docker-compose down -v
	docker system prune -f
	rm -rf data/

# Document ingestion
ingest: ## Ingest a document (usage: make ingest FILE=path/to/document.pdf)
ifndef FILE
	@echo "Usage: make ingest FILE=path/to/document.pdf"
	@exit 1
endif
	@echo "Ingesting document: $(FILE)"
	docker-compose exec backend python -m apps.rag.ingestion.docling_runner $(FILE)

# Index management  
reindex: ## Rebuild FAISS index from embedding cache
	@echo "Rebuilding index from cache..."
	docker-compose exec backend python -m apps.rag.store.vector_store --rebuild

snapshot: ## Create index snapshot
ifndef NAME
	$(eval NAME := snapshot_$(shell date +%Y%m%d_%H%M%S))
endif
	@echo "Creating index snapshot: $(NAME)"
	mkdir -p data/index_snapshots/$(NAME)
	cp -r data/index/* data/index_snapshots/$(NAME)/
	@echo "Snapshot created: data/index_snapshots/$(NAME)"

restore: ## Restore from index snapshot (usage: make restore TS=20240101_120000)
ifndef TS
	@echo "Usage: make restore TS=20240101_120000"
	@echo "Available snapshots:"
	@ls -1 data/index_snapshots/ 2>/dev/null || echo "No snapshots found"
	@exit 1
endif
	@echo "Restoring index from snapshot: $(TS)"
	cp -r data/index_snapshots/$(TS)/* data/index/
	@echo "Index restored from snapshot: $(TS)"

# Evaluation
eval: ## Run evaluation harness
	@echo "Running evaluation..."
	docker-compose exec backend python -m apps.rag.evals.run_eval

# Kubernetes deployment
k8s-dev: ## Deploy to Kubernetes development environment
	@echo "Deploying to Kubernetes (dev)..."
	kubectl apply -k deployments/overlays/dev

k8s-prod: ## Deploy to Kubernetes production environment
	@echo "Deploying to Kubernetes (prod)..."
	kubectl apply -k deployments/overlays/prod

k8s-delete: ## Delete Kubernetes deployment
	kubectl delete -k deployments/overlays/dev

# Utilities
logs: ## Show application logs
	docker-compose logs -f backend

shell: ## Open shell in backend container
	docker-compose exec backend /bin/bash

test: ## Run tests
	docker-compose exec backend python -m pytest

lint: ## Run linting
	docker-compose exec backend python -m black apps/
	docker-compose exec backend python -m isort apps/
	docker-compose exec backend python -m flake8 apps/

# Status and monitoring
status: ## Show system status
	@echo "=== Docker Compose Status ==="
	docker-compose ps
	@echo ""
	@echo "=== Index Statistics ==="
	docker-compose exec backend python -c "from apps.rag.store.ledger import IngestionLedger; print(IngestionLedger().get_stats())" 2>/dev/null || echo "Ledger not accessible"

metrics: ## Show Prometheus metrics
	@echo "Prometheus metrics available at: http://localhost:9090"
	@echo "Grafana dashboard available at: http://localhost:3000"

# CLI Commands
cli-login: ## Login to RAG system (usage: make cli-login USER=admin PASS=admin)
	@if [ -z "$(USER)" ] || [ -z "$(PASS)" ]; then echo "Usage: make cli-login USER=admin PASS=admin"; exit 1; fi
	python scripts/rag_cli.py login $(USER) $(PASS)

cli-status: ## Show system status
	python scripts/rag_cli.py status --detailed

cli-upload: ## Upload document (usage: make cli-upload FILE=path/to/doc.pdf)
ifndef FILE
	@echo "Usage: make cli-upload FILE=path/to/document.pdf"
	@exit 1
endif
	python scripts/rag_cli.py upload $(FILE)

cli-query: ## Query system (usage: make cli-query Q="your question")
ifndef Q
	@echo "Usage: make cli-query Q=\"What is this document about?\""
	@exit 1
endif
	python scripts/rag_cli.py query "$(Q)"

cli-eval: ## Run evaluation harness
	python scripts/rag_cli.py eval

# Installation
install-deps: ## Install Python dependencies
	pip install -r requirements.txt

setup: ## Initial setup
	@echo "Setting up RAG-Ollama project..."
	cp .env.example .env
	mkdir -p data/{raw_docs,index,cache,index_snapshots}
	@echo "Setup complete! Edit .env file and run 'make dev' to start."