.PHONY: help install install-py install-fe build dev serve stop clean lint

# Default
help: ## Show available commands
	@echo ""
	@echo "  RPG Simulation Engine - Task Runner"
	@echo "  ====================================="
	@echo ""
	@grep -E '^[a-zA-Z_-]+:.*?## .*$$' $(MAKEFILE_LIST) | awk 'BEGIN {FS = ":.*?## "}; {printf "  \033[36m%-16s\033[0m %s\n", $$1, $$2}'
	@echo ""

# ── Install ──────────────────────────────────────────────

install: install-py install-fe ## Install all dependencies (Python + Node)

install-py: ## Install Python dependencies
	pip install -r requirements.txt

install-fe: ## Install frontend Node dependencies
	cd frontend && npm install

# ── Build ────────────────────────────────────────────────

build: ## Build frontend for production
	cd frontend && npm run build

# ── Development ──────────────────────────────────────────

dev: ## Start backend + frontend dev server (hot reload)
	@echo "Starting backend on :8000 and frontend on :5173..."
	@echo "Press Ctrl+C to stop both."
	@trap 'kill 0' INT; \
		python -m src serve --port 8000 & \
		(cd frontend && npm run dev) & \
		wait

dev-backend: ## Start only the backend server
	python -m src serve --port 8000

dev-frontend: ## Start only the frontend dev server
	cd frontend && npm run dev

# ── Production ───────────────────────────────────────────

serve: build ## Build frontend + start production server
	python -m src serve --port 8000

serve-only: ## Start production server (assumes frontend already built)
	python -m src serve --port 8000

# ── CLI ──────────────────────────────────────────────────

cli: ## Run headless simulation (200 ticks)
	python -m src cli --ticks 200 --seed 42

# ── Quality ──────────────────────────────────────────────

lint: ## Run linters (frontend)
	cd frontend && npm run lint

typecheck: ## Run TypeScript type checking
	cd frontend && npx tsc --noEmit

# ── Cleanup ──────────────────────────────────────────────

clean: ## Remove build artifacts
	rm -rf frontend/dist
	rm -rf frontend/node_modules/.tmp
	find . -type d -name __pycache__ -exec rm -rf {} + 2>/dev/null || true
