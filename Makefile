# document-qa-rag — common developer commands.
# Run these from the repo root. Assumes the backend virtualenv is active
# (or that ruff/pytest/uvicorn/alembic are otherwise on PATH).

BACKEND := backend

.PHONY: help install test lint format check run migrate migration

help: ## Show this help
	@grep -E '^[a-zA-Z_-]+:.*?## .*$$' $(MAKEFILE_LIST) | \
		awk 'BEGIN {FS = ":.*?## "}; {printf "  \033[36m%-12s\033[0m %s\n", $$1, $$2}'

install: ## Install backend with dev dependencies
	cd $(BACKEND) && pip install -e ".[dev]"

test: ## Run the backend test suite
	cd $(BACKEND) && pytest

lint: ## Lint the backend with ruff
	cd $(BACKEND) && ruff check .

format: ## Auto-format the backend with ruff
	cd $(BACKEND) && ruff format .

check: lint test ## Lint then test — the same gate CI runs

run: ## Run the API locally with autoreload
	cd $(BACKEND) && uvicorn app.main:app --reload

migrate: ## Apply all pending Alembic migrations
	cd $(BACKEND) && alembic upgrade head

migration: ## Autogenerate a migration: make migration m="message"
	cd $(BACKEND) && alembic revision --autogenerate -m "$(m)"
