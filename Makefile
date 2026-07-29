# ============================================
# Predicta - Common Development Tasks
# ============================================

.PHONY: help install install-dev run test lint format migrate migration seed clean docker-up docker-down

help: ## Show this help message
	@echo "Predicta - Available commands:"
	@grep -E '^[a-zA-Z_-]+:.*?## .*$$' $(MAKEFILE_LIST) | awk 'BEGIN {FS = ":.*?## "}; {printf "  \033[36m%-20s\033[0m %s\n", $$1, $$2}'

# ============================================
# Setup
# ============================================
install: ## Install backend production dependencies
	cd backend && pip install -r requirements.txt

install-dev: ## Install backend + development dependencies
	cd backend && pip install -r requirements.txt -r requirements-dev.txt

# ============================================
# Run
# ============================================
run: ## Run backend in development mode (with auto-reload)
	cd backend && uvicorn app.main:app --reload --host 0.0.0.0 --port 8000

# ============================================
# Database
# ============================================
migrate: ## Apply all pending Alembic migrations
	cd backend && alembic upgrade head

migration: ## Create a new Alembic migration (use msg="description")
	cd backend && alembic revision --autogenerate -m "$(msg)"

migration-empty: ## Create an empty Alembic migration (use msg="description")
	cd backend && alembic revision -m "$(msg)"

seed: ## Generate synthetic dataset for testing
	cd backend && python scripts/generate_dataset.py

# ============================================
# Quality
# ============================================
test: ## Run test suite with coverage
	cd backend && pytest --cov=app --cov-report=term-missing

lint: ## Run linter (ruff)
	cd backend && ruff check app/

format: ## Auto-format code (ruff + black-compatible)
	cd backend && ruff check --fix app/ && ruff format app/

typecheck: ## Run static type checker
	cd backend && mypy app/

# ============================================
# Docker
# ============================================
docker-up: ## Start all services with docker-compose
	docker-compose up -d

docker-down: ## Stop all services
	docker-compose down

docker-logs: ## Tail logs from all services
	docker-compose logs -f

# ============================================
# Cleanup
# ============================================
clean: ## Remove cache files and build artifacts
	find . -type d -name "__pycache__" -exec rm -rf {} + 2>/dev/null || true
	find . -type d -name ".pytest_cache" -exec rm -rf {} + 2>/dev/null || true
	find . -type d -name ".ruff_cache" -exec rm -rf {} + 2>/dev/null || true
	find . -type d -name ".mypy_cache" -exec rm -rf {} + 2>/dev/null || true
	rm -rf backend/htmlcov backend/.coverage backend/coverage.xml 2>/dev/null || true
