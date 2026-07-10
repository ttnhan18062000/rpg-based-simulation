.PHONY: help install install-py install-fe build dev serve stop clean lint profile-api memray-profile docs-serve docs-build docs-registry tag-report docs-artifacts knowledge-index knowledge-index-update search-server search-server-docker search-server-stop search-server-logs install-hooks eval-search evaluate evaluate-full simq-full-audit simq-full-audit-full simq-full-audit-slow mcp-server-test world-list world-validate world-compile world-resolve world-inspect world-template catalog-list sim sim-debug sim-quick sim-world sim-sweep check-resources export-run retention-plan retention-clean warehouse-init warehouse-ingest typecheck-py perf-measure

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

# ── World Generation ─────────────────────────────────────
# Worldbuilding CLI: data-driven world spec authoring and compilation pipeline.
# Override WORLD to target a specific world spec folder (default: sandbox_world).

WORLD ?= sandbox_world

world-list: ## List all compiled worlds in the repository
	python3 -m src.worldbuilding.cli list

world-validate: ## Validate a world spec against compile constraints (WORLD=sandbox_world)
	python3 -m src.worldbuilding.cli validate $(WORLD)

world-compile: ## Compile a world spec into active state files (WORLD=sandbox_world)
	python3 -m src.worldbuilding.cli compile $(WORLD)

world-resolve: ## Resolve compositional world specs into compiled assets (WORLD=sandbox_world)
	python3 -m src.worldbuilding.cli resolve $(WORLD)

world-inspect: ## Inspect structural metrics of a world definition (WORLD=sandbox_world)
	python3 -m src.worldbuilding.cli inspect $(WORLD)

world-template: ## Bootstrap a starter world template (WORLD=my_world)
	python3 -m src.worldbuilding.cli create-template $(WORLD)

catalog-list: ## List catalog IDs by type (biomes, ecologies, populations, factions, regions)
	python3 tools/catalog_list.py

# ── Simulation CLI ───────────────────────────────────────
# Override TICKS, SEED, or WORLD to customise any run.
# Dynamic observability backpressure (NORMAL→PRESSURE→DEGRADED→SURVIVAL) is
# automatic — driven by EventRecorder queue fill ratio, not a CLI flag.
# Use --log-level DEBUG to increase log verbosity; it does not affect mode switching.

TICKS  ?= 200
SEED   ?= 42
CONFIG ?= data/sweeps/default.json

cli: ## Run headless simulation (200 ticks, seed 42) — legacy alias for sim
	python3 -m src cli --ticks $(TICKS) --seed $(SEED)

sim: ## Run headless simulation (TICKS=200 SEED=42 WORLD=sandbox_world)
	python3 -m src cli --ticks $(TICKS) --seed $(SEED) $(if $(filter-out sandbox_world,$(WORLD)),--world $(WORLD),)

sim-debug: ## Run simulation with DEBUG observability + verbose logging (TICKS=200 SEED=42)
	SIM_OBS_MODE=DEBUG python3 -m src cli --ticks $(TICKS) --seed $(SEED) --log-level DEBUG

sim-quick: ## Quick 20-tick smoke test (WARNING-level logs only)
	python3 -m src cli --ticks 20 --seed $(SEED) --log-level WARNING

sim-world: ## Run simulation on a specific world (WORLD=<id> TICKS=200)
	python3 -m src cli --ticks $(TICKS) --seed $(SEED) --world $(WORLD)

sim-sweep: ## Run a scenario sweep matrix (CONFIG=data/sweeps/default.json)
	python3 -m src sweep $(CONFIG)

check-resources: ## Show per-subsystem resource pressure (exit 1 if any DEGRADED)
	python3 -m src diagnostics resources

# ── Data Pipeline ────────────────────────────────────────

RUN_ID ?=

export-run: ## Export a single run artifact set to Parquet (RUN_ID=<id>)
	python3 -m src export $(RUN_ID)

retention-plan: ## Dry-run scan of expired/prunable observability files
	python3 -m src retention plan

retention-clean: ## Clean expired observability files (confirmation prompt)
	python3 -m src retention clean

warehouse-init: ## Initialise database warehouse schemas
	python3 -m src warehouse init

warehouse-ingest: ## Ingest a single run into the warehouse (RUN_ID=<id>)
	python3 -m src warehouse ingest-run $(RUN_ID)

# ── Testing ──────────────────────────────────────────────

test: ## Run all Python tests (V2)
	python3 -m pytest tests_v2/ -v --tb=short

test-quick: ## Run fast tests only (skip slow integration)
	python3 -m pytest tests/ -v --tb=short -m "not slow"

test-cov: ## Run tests with coverage report (V2)
	python3 -m pytest tests_v2/ -v --tb=short --cov=src_v2 --cov-report=term-missing

perf-measure: ## Re-measure perf tests and print proposed perf_baselines.json diff
	python3 tools/perf_guard.py measure

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

regression-baseline: ## Generate/refresh 5k-tick behavioral regression baseline (commit the result)
	python3 tools/generate_regression_baseline.py

personality-audit: ## Run 1k-tick personality→behavior calibration audit (OCEAN trait vs behavioral diversity)
	python3 tools/personality_audit.py $(if $(TICKS),--ticks $(TICKS),) $(if $(SEED),--seed $(SEED),) $(if $(WORLD),--world $(WORLD),)

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

memray-profile: ## Run certification suite under Memray (disables RLIMIT_AS; requires: pip install memray)
	python3 scripts/profile_memory.py --suite certification --memray

# ── Quality ──────────────────────────────────────────────

lint: ## Run linters (frontend)
	cd frontend && npm run lint

typecheck: ## Run TypeScript type checking
	cd frontend && npx tsc --noEmit

typecheck-py: ## Run Python type checking via mypy (src/ only, informational first pass)
	python3 -m mypy src/ --config-file pyproject.toml --no-error-summary || true

# ── Documentation Site ───────────────────────────────────

docs-artifacts: ## Generate stored_artifacts index pages
	python3 tools/generate_artifact_pages.py

docs-serve: docs-artifacts ## Start Docusaurus dev server (http://localhost:3000)
	cd website && npm run start

docs-build: docs-artifacts ## Build Docusaurus static site to website/build/
	cd website && npm run build

docs-registry: ## Regenerate docs/REGISTRY.yaml from frontmatter
	python3 tools/generate_registry.py

tag-report: ## Print a tag-usage report over completed tickets (pass ARGS="--json reports/tag_report.json")
	python3 tools/tag_report.py $(ARGS)

# ── Agent Monitoring ─────────────────────────────────────

agent-monitoring-retro: ## Generate current-week agent monitoring retro report
	python3 tools/agent-monitoring/generate_retro.py

agent-monitoring-validate: ## Cross-check agent monitoring integrity against working_log.csv
	python3 tools/agent-monitoring/validate.py

agent-monitoring-query: ## Query agent monitoring records (pass ARGS="--agent investigator --days 14")
	python3 tools/agent-monitoring/query.py $(ARGS)

agent-monitoring-epic-staleness: ## Report open epics with no recent child-ticket activity
	python3 tools/agent-monitoring/epic_staleness_check.py

# ── Knowledge Search ─────────────────────────────────────────────────────────
# developer env only — not CI
# Requires: pip install -e ".[knowledge]"

knowledge-index: ## Build local semantic knowledge index (developer env only — not CI)
	@echo "Building knowledge index (requires: pip install -e '.[knowledge]')..."
	SSL_CERT_FILE=/etc/ssl/certs/ca-certificates.crt SSL_CERT_DIR=/etc/ssl/certs \
	  $(shell for py in .venv/bin/python3 /home/vboxuser/Work/venv/bin/python3 python3; do [ -x "$$py" ] && echo "$$py" && break; done) \
	  tools/knowledge_search.py build

knowledge-index-update: ## Incremental reindex — only re-embeds changed/new files (fast)
	SSL_CERT_FILE=/etc/ssl/certs/ca-certificates.crt SSL_CERT_DIR=/etc/ssl/certs \
	  $(shell for py in .venv/bin/python3 /home/vboxuser/Work/venv/bin/python3 python3; do [ -x "$$py" ] && echo "$$py" && break; done) \
	  tools/knowledge_search.py build --incremental

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
	$(shell for py in .venv/bin/python3 /home/vboxuser/Work/venv/bin/python3 python3; do [ -x "$$py" ] && echo "$$py" && break; done) tools/eval_search.py

PYTHON := $(shell for py in .venv/bin/python3 /home/vboxuser/Work/venv/bin/python3 python3; do [ -x "$$py" ] && echo "$$py" && break; done)

evaluate: ## Diff current calibration data against grade anchors (no engine re-run)
	$(PYTHON) tools/evaluate_simq.py --dry-run

evaluate-full: ## Re-run engine for all fast (≤500t) scenarios and diff against grade anchors
	$(PYTHON) tools/evaluate_simq.py

simq-full-audit: ## Mechanical SimQ audit: diff calibration vs anchors, run fast regression tests, scan anchor/parity coverage gaps
	@echo "[simq-full-audit] Step 1/3: diff current calibration data against anchors (no engine re-run)"
	-$(PYTHON) tools/evaluate_simq.py --dry-run
	@echo "[simq-full-audit] Step 2/3: run fast-tier grade regression tests"
	$(PYTHON) -m pytest tests/simulation_quality/test_grade_regression.py -m "not slow" -q; test_status=$$?; \
	echo "[simq-full-audit] Step 3/3: cross-check anchor key coverage + parity ledger candidates"; \
	$(PYTHON) tools/simq_audit_gaps.py; \
	exit $$test_status

simq-full-audit-full: ## Same as simq-full-audit but re-runs the engine for all fast (<=500t) scenarios first
	-$(PYTHON) tools/evaluate_simq.py
	$(PYTHON) -m pytest tests/simulation_quality/test_grade_regression.py -m "not slow" -q; test_status=$$?; \
	$(PYTHON) tools/simq_audit_gaps.py; \
	exit $$test_status

simq-full-audit-slow: ## Slow-tier (1000t/2000t) regression check -- run after simq-full-audit passes
	$(PYTHON) -m pytest tests/simulation_quality/test_grade_regression.py -q

mcp-server-test: ## Smoke-test MCP search_docs tool via --test mode (no MCP client needed)
	@echo '{"query": "damage formula", "top_k": 3}' | \
	  $(shell for py in .venv/bin/python3 /home/vboxuser/Work/venv/bin/python3 python3; do [ -x "$$py" ] && echo "$$py" && break; done) tools/search_mcp.py --test

# ── Cleanup ──────────────────────────────────────────────

clean: ## Remove build artifacts
	rm -rf frontend/dist
	rm -rf frontend/node_modules/.tmp
	find . -type d -name __pycache__ -exec rm -rf {} + 2>/dev/null || true
