.PHONY: help build up down shell run logs clean start-ollama stop-ollama restart-ollama

.DEFAULT_GOAL := help

help: ## Show this help message
	@echo "Available commands:"
	@echo ""
	@grep -E '^[a-zA-Z_-]+:.*?## .*$$' $(MAKEFILE_LIST) | sort | awk 'BEGIN {FS = ":.*?## "}; {printf "\033[36m%-20s\033[0m %s\n", $$1, $$2}'

build: ## Build all Docker images
	docker compose -f docker-compose.yml build

shell: ## Open shell in dev container
	docker compose -f docker-compose.yml exec dev /bin/bash

up: ## Start all services (detached mode)
	docker compose -f docker-compose.yml up -d

down: ## Stop all services
	docker compose -f docker-compose.yml down

run: ## Run the Wodify booking script
	docker compose -f docker-compose.yml run --rm dev python /app/main.py

logs: ## View Ollama service logs
	docker compose -f docker-compose.yml logs -f ollama

start-ollama: ## Start Ollama service
	docker compose -f docker-compose.yml up -d ollama

stop-ollama: ## Stop Ollama service
	docker compose -f docker-compose.yml stop ollama

restart-ollama: ## Restart Ollama service
	docker compose -f docker-compose.yml restart ollama

clean: ## Stop services and remove containers
	docker compose -f docker-compose.yml down -v

stop-dev: ## Stop dev service
	docker compose -f docker-compose.yml stop dev