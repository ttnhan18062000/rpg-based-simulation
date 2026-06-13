.PHONY: help install install-py install-fe build dev serve stop clean lint profile-api docs-serve docs-build docs-registry docs-artifacts knowledge-index knowledge-index-update search-server search-server-docker search-server-stop search-server-logs install-hooks eval-search mcp-server-test

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
		python3 -m src serve --port 8000 & \
		(cd frontend && npm run dev) & \
		wait

dev-backend: ## Start only the backend server
	python3 -m src serve --port 8000

dev-frontend: ## Start only the frontend dev server
	cd frontend && npm run dev

# ── Production ───────────────────────────────────────────

serve: build ## Build frontend + start production server
	python3 -m src serve --port 8000

serve-only: ## Start production server (assumes frontend already built)
	python3 -m src serve --port 8000

# ── Infrastructure & Testing ─────────────────────────────

docker-up: ## Start all infrastructure components via Docker Compose
	docker compose up -d

docker-down: ## Stop and remove all Docker Compose containers
	docker compose down

docker-logs: ## Tail logs for all Docker Compose containers
	docker compose logs -f

run-worker: ## Start the AI Worker Daemon locally
	uv run python3 -m src.workers.ai_worker_daemon

run-engine: ## Start the Backend Engine locally
	uv run python3 -m src serve --host 0.0.0.0 --port 8000

# ── CLI ──────────────────────────────────────────────────

cli: ## Run headless simulation (200 ticks)
	python3 -m src cli --ticks 200 --seed 42

# ── Testing ──────────────────────────────────────────────

test: ## Run all Python tests (V2)
	python3 -m pytest tests_v2/ -v --tb=short

test-quick: ## Run fast tests only (skip slow integration)
	python3 -m pytest tests/ -v --tb=short -m "not slow"

test-cov: ## Run tests with coverage report (V2)
	python3 -m pytest tests_v2/ -v --tb=short --cov=src_v2 --cov-report=term-missing

# ── Migration CI Lanes ────────────────────────────────────
# Targeted test lanes for content migration work. Each lane selects a
# focused subset of the suite using pytest -m markers.
# See docs/testing/migration_ci_lanes.md for full documentation.

lane-catalog: ## [fast] Catalog schema, adapter heuristics, reference graph, active-data-consumer
	python3 -m pytest tests/ -m "catalog or content_graph" -v --tb=short

lane-worldassembly: ## [fast] World module normalizers, assembly, provenance (excludes strict matrix)
	python3 -m pytest tests/ -m "worldassembly and not strict_matrix" -v --tb=short

lane-runtime: ## [fast] Registry bootstrap modes, scenario setup, adapter projection
	python3 -m pytest tests/ -m "registry_projection or scenario_setup" -v --tb=short

lane-strict-matrix: ## [medium] Cumulative world module matrix (end-to-end content builds)
	python3 -m pytest tests/ -m "strict_matrix" -v --tb=short

lane-legacy-regression: ## [slow] Arena, certification, legacy compat regression tests
	python3 -m pytest tests/ -m "legacy_compat" -v --tb=short

lane-architecture: ## [fast] Static architecture guards (no simulation, no catalog load)
	python3 -m pytest tests/ -m "architecture" -v --tb=short

lane-all-fast: ## [fast] All fast migration lanes combined (excludes slow and strict_matrix)
	python3 -m pytest tests/ -m "(catalog or content_graph or worldassembly or registry_projection or scenario_setup or architecture) and not strict_matrix and not slow" -v --tb=short

gate-expansion: ## Content expansion readiness gate — must pass before horizontal expansion
	python3 -m pytest tests/integration/content/test_expansion_gate.py -v --tb=short

# ── Profiling ────────────────────────────────────────────

profile: ## Run automated performance profile (500 ticks, prints report)
	python3 scripts/profile_simulation.py --ticks 500 --seed 42

profile-full: ## Run extended profile (2000 ticks, saves flamegraph-ready output)
	python3 scripts/profile_simulation.py --ticks 2000 --seed 42 --cprofile profile_output.prof

profile-memory: ## Run memory profiling (500 ticks)
	python3 scripts/profile_simulation.py --ticks 500 --seed 42 --memory

profile-api: ## Measure API payload sizes (map, static, state endpoints)
	python3 scripts/profile_api_payload.py --ticks 10 --seed 42

# ── Quality ──────────────────────────────────────────────

lint: ## Run linters (frontend)
	cd frontend && npm run lint

typecheck: ## Run TypeScript type checking
	cd frontend && npx tsc --noEmit

# ── Documentation Site ───────────────────────────────────

docs-artifacts: ## Generate stored_artifacts index pages
	python3 tools/generate_artifact_pages.py

docs-serve: docs-artifacts ## Start Docusaurus dev server (http://localhost:3000)
	cd website && npm run start

docs-build: docs-artifacts ## Build Docusaurus static site to website/build/
	cd website && npm run build

docs-registry: ## Regenerate docs/REGISTRY.yaml from frontmatter
	python3 tools/generate_registry.py

# ── Agent Monitoring ─────────────────────────────────────

agent-monitoring-retro: ## Generate current-week agent monitoring retro report
	python3 tools/agent-monitoring/generate_retro.py

agent-monitoring-validate: ## Cross-check agent monitoring integrity against working_log.csv
	python3 tools/agent-monitoring/validate.py

agent-monitoring-query: ## Query agent monitoring records (pass ARGS="--agent investigator --days 14")
	python3 tools/agent-monitoring/query.py $(ARGS)

# ── Knowledge Search ─────────────────────────────────────────────────────────
# developer env only — not CI
# Requires: pip install -e ".[knowledge]"

knowledge-index: ## Build local semantic knowledge index (developer env only — not CI)
	@echo "Building knowledge index (requires: pip install -e '.[knowledge]')..."
	python3 tools/knowledge_search.py build

knowledge-index-update: ## Incremental reindex — only re-embeds changed/new files (fast)
	python3 tools/knowledge_search.py build --incremental

search-server-docker: ## PRIMARY — start knowledge search server in Docker (persistent, survives terminal close)
	docker compose -f tools/search/docker-compose.yml up -d --build
	@echo "[search-server] Server starting on http://localhost:8765 (check logs: make search-server-logs)"

search-server-stop: ## Stop knowledge search Docker container
	docker compose -f tools/search/docker-compose.yml down

search-server-logs: ## Tail knowledge search server logs
	docker compose -f tools/search/docker-compose.yml logs -f

search-server: ## FALLBACK ONLY — start search server directly via uvicorn (exits when terminal closes)
	@echo "[search-server] Fallback mode — use make search-server-docker for persistent deployment"
	uvicorn tools.search_server:app --host 127.0.0.1 --port 8765 --reload

install-hooks: ## Install git hooks (post-commit incremental reindex when docs/ or tickets/done/ changed)
	cp tools/hooks/post-commit-reindex.sh .git/hooks/post-commit
	chmod +x .git/hooks/post-commit
	@echo "[hooks] post-commit hook installed"

eval-search: ## Run search quality evaluation — Recall@5, MRR@10 (requires knowledge-index)
	python3 tools/eval_search.py

mcp-server-test: ## Smoke-test MCP search_docs tool via --test mode (no MCP client needed)
	@echo '{"query": "damage formula", "top_k": 3}' | python3 tools/search_mcp.py --test

# ── Cleanup ──────────────────────────────────────────────

clean: ## Remove build artifacts
	rm -rf frontend/dist
	rm -rf frontend/node_modules/.tmp
	find . -type d -name __pycache__ -exec rm -rf {} + 2>/dev/null || true
