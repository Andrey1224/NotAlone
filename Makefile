.PHONY: help up down restart logs clean install fmt lint test migrate migrate-create shell

help: ## Show this help message
	@echo 'Usage: make [target]'
	@echo ''
	@echo 'Available targets:'
	@awk 'BEGIN {FS = ":.*?## "} /^[a-zA-Z_-]+:.*?## / {printf "  %-15s %s\n", $$1, $$2}' $(MAKEFILE_LIST)

install: ## Install dependencies
	pip install -e ".[dev]"

up: ## Start all services
	docker compose -f deploy/compose.yml up -d --build

down: ## Stop all services
	docker compose -f deploy/compose.yml down

restart: down up ## Restart all services

logs: ## Show logs from all services
	docker compose -f deploy/compose.yml logs -f

logs-api: ## Show API logs
	docker compose -f deploy/compose.yml logs -f api

logs-bot: ## Show bot logs
	docker compose -f deploy/compose.yml logs -f bot

logs-worker: ## Show worker logs
	docker compose -f deploy/compose.yml logs -f worker

clean: ## Clean up containers and volumes
	docker compose -f deploy/compose.yml down -v
	find . -type d -name __pycache__ -exec rm -rf {} +
	find . -type f -name "*.pyc" -delete

fmt: ## Format code
	ruff check --fix .
	black .
	isort .

lint: ## Lint code
	mypy .
	ruff check .

test: ## Run tests
	pytest -v --cov=. --cov-report=html

migrate: ## Apply database migrations
	alembic upgrade head

migrate-create: ## Create a new migration
	@read -p "Enter migration message: " msg; \
	alembic revision --autogenerate -m "$$msg"

shell: ## Open Python shell with app context
	python -i -c "from core import *; from models import *"

dev-api: ## Run API in development mode
	uvicorn apps.api.main:app --reload --port 8000

dev-bot: ## Run bot in development mode
	python -m apps.bot.bot
