.PHONY: help install test lint format run clean migrate

help:  ## Show this help message
	@echo "Task Tracker API - Development Commands"
	@echo ""
	@grep -E '^[a-zA-Z_-]+:.*?## .*$$' $(MAKEFILE_LIST) | sort | awk 'BEGIN {FS = ":.*?## "}; {printf "\033[36m%-20s\033[0m %s\n", $$1, $$2}'

install:  ## Install dependencies
	cd backend && uv sync --dev

test:  ## Run tests with coverage
	cd backend && uv run pytest app/test_main.py -v --cov=app --cov-report=term-missing

test-quick:  ## Run tests without coverage
	cd backend && uv run pytest app/test_main.py -v

lint:  ## Run linter (ruff)
	cd backend && uv run ruff check app/

lint-fix:  ## Run linter with auto-fix
	cd backend && uv run ruff check app/ --fix

format:  ## Format code with ruff
	cd backend && uv run ruff format app/

format-check:  ## Check code formatting
	cd backend && uv run ruff format --check app/

run:  ## Run development server
	cd backend && uv run uvicorn app.main:app --reload

run-prod:  ## Run production server
	cd backend && uv run uvicorn app.main:app --host 0.0.0.0 --port 8000

migrate:  ## Run database migrations
	cd backend && uv run alembic upgrade head

migrate-create:  ## Create new migration (use MSG="description")
	cd backend && uv run alembic revision --autogenerate -m "$(MSG)"

clean:  ## Clean up generated files
	find . -type d -name "__pycache__" -exec rm -rf {} +
	find . -type f -name "*.pyc" -delete
	find . -type d -name ".pytest_cache" -exec rm -rf {} +
	find . -type d -name ".ruff_cache" -exec rm -rf {} +
	cd backend && rm -f test.db coverage.xml .coverage

setup-hooks:  ## Install pre-commit hooks
	cd backend && uv run pre-commit install

check-all: lint format-check test  ## Run all checks (lint + format + test)

dev-setup: install setup-hooks  ## Complete development setup
	@echo "✅ Development environment ready!"
	@echo "Run 'make run' to start the server"
