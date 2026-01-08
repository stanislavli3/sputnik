.PHONY: help install install-backend install-frontend setup dev backend frontend test lint format typecheck clean db-setup

help: ## Show this help message
	@echo "Sputnik Development Commands"
	@echo ""
	@grep -E '^[a-zA-Z_-]+:.*?## .*$$' $(MAKEFILE_LIST) | awk 'BEGIN {FS = ":.*?## "}; {printf "  \033[36m%-20s\033[0m %s\n", $$1, $$2}'

install: install-backend install-frontend ## Install all dependencies

install-backend: ## Install Python dependencies
	pip install -e ".[dev]"
	@echo "✅ Backend dependencies installed"

install-frontend: ## Install frontend dependencies
	cd frontend && npm install
	@echo "✅ Frontend dependencies installed"

setup: db-setup ## Setup development environment (install + database)
	@echo "✅ Development environment ready"

db-setup: ## Create demo database
	python scripts/setup_demo_db.py
	@echo "✅ Demo database created"

dev: ## Start both backend and frontend (requires two terminals)
	@echo "Starting development servers..."
	@echo "Backend: http://localhost:8000"
	@echo "Frontend: http://localhost:8080"
	@echo ""
	@echo "Run in separate terminals:"
	@echo "  Terminal 1: make backend"
	@echo "  Terminal 2: make frontend"

backend: ## Start backend API server
	python scripts/start_server.py

frontend: ## Start frontend dev server
	cd frontend && npm run dev

test: ## Run all tests
	pytest tests/ -v

test-backend: ## Run Python tests
	pytest tests/ -v

test-frontend: ## Run frontend tests (if configured)
	cd frontend && npm test || echo "No frontend tests configured"

lint: lint-backend lint-frontend ## Lint all code

lint-backend: ## Lint Python code
	ruff check .
	@echo "✅ Backend linting complete"

lint-frontend: ## Lint frontend code
	cd frontend && npm run lint || echo "No lint script configured"

format: format-backend format-frontend ## Format all code

format-backend: ## Format Python code
	ruff format .
	@echo "✅ Backend formatting complete"

format-frontend: ## Format frontend code
	cd frontend && npm run format || echo "No format script configured"

typecheck: ## Type check Python code
	mypy src/

clean: ## Clean build artifacts and caches
	find . -type d -name "__pycache__" -exec rm -rf {} + 2>/dev/null || true
	find . -type f -name "*.pyc" -delete
	find . -type d -name ".pytest_cache" -exec rm -rf {} + 2>/dev/null || true
	find . -type d -name ".mypy_cache" -exec rm -rf {} + 2>/dev/null || true
	find . -type d -name ".ruff_cache" -exec rm -rf {} + 2>/dev/null || true
	rm -rf dist/ build/ *.egg-info/
	cd frontend && rm -rf dist/ build/ .vite/ node_modules/.vite/
	@echo "✅ Cleanup complete"

clean-all: clean ## Clean everything including node_modules and venv
	rm -rf frontend/node_modules/
	rm -rf venv/ env/ .venv/
	@echo "✅ Full cleanup complete"

build: ## Build for production
	cd frontend && npm run build
	@echo "✅ Frontend build complete"

