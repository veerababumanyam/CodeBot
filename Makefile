.PHONY: dev build test lint typecheck migrate docker-up docker-down clean install

## Start all services in development mode
dev:
	pnpm turbo dev

## Build all workspaces
build:
	pnpm turbo build

## Run all tests
test:
	pnpm turbo test

## Lint all workspaces
lint:
	pnpm turbo lint

## Type-check all workspaces
typecheck:
	pnpm turbo typecheck

## Run database migrations
migrate:
	uv run alembic upgrade head

## Start local Docker services (PostgreSQL, Redis, NATS)
docker-up:
	docker-compose up -d

## Stop local Docker services
docker-down:
	docker-compose down

## Remove build artifacts and caches
clean:
	pnpm turbo clean || true
	find . -type d -name "__pycache__" -exec rm -rf {} + 2>/dev/null || true
	find . -type d -name "*.egg-info" -exec rm -rf {} + 2>/dev/null || true
	find . -type d -name ".turbo" -exec rm -rf {} + 2>/dev/null || true
	find . -type d -name "dist" -not -path "./.git/*" -exec rm -rf {} + 2>/dev/null || true

## Install all dependencies (Python + Node)
install:
	uv sync
	pnpm install
