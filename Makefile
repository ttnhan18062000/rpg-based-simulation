.PHONY: help install install-py install-fe build dev serve stop clean lint profile-api memray-profile docs-serve docs-build docs-registry tag-report docs-artifacts brainstorm-idea-index knowledge-index knowledge-index-update search-server search-server-docker search-server-stop search-server-logs install-hooks eval-search evaluate evaluate-full simq-full-audit simq-full-audit-full simq-full-audit-slow simq-corpus-diversity-slow-isolated mcp-server-test world-list world-validate world-compile world-resolve world-inspect world-template catalog-list sim sim-debug sim-quick sim-world sim-sweep check-resources export-run retention-plan retention-clean warehouse-init warehouse-ingest typecheck-py perf-measure dashboard-install dashboard-build dashboard-dev dashboard-serve ticket-stats-report test-collect agent-monitoring-index simq-corpus-registry parity-index parity-index-check simq-long-run-lifecycle-observation content-inventory codebase-health-snapshot codebase-health-scorecard codebase-health-pr-impact docs-registry-check setup-merge-drivers working-log-duplicate-check working-log-content-duplicate-check duplicate-run-record-check sidecar-attribution-coverage-check tool-call-count-mismatch-check event-seq-integrity-check monitoring-integrity-backlog-check monitoring-anomaly-validate premise-staleness-check

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

# Auto-discovers a pydantic-capable python3: a local .venv (relative, works from the main
# checkout), then worktree-independent absolute paths for known dev machines (u24desktop,
# vboxuser), then bare python3 last. Needed because git worktrees don't get their own .venv/ --
# bare python3 lacks pydantic there, so `serve`/`dev` would silently crash at backend startup
# with no indication other than every API call refusing to connect (TCK-20260825-LIVE-MAP-DEV-AUTH-AND-WS-PROXY-FIX's
# own Playwright e2e webServer hit exactly this while starting `make dev` as a subprocess).
#
# TCK-20260921-INTERPRETER-SELECTION-PROBES-INCONSISTENT: hardened to probe real capability
# (`pydantic` importable), not just existence -- `command -v "$$py"` alone would happily pick a
# candidate that exists but lacks pydantic, the exact shape TCK-20260914-VENV-NAMING-CI-PARITY-SWAP
# (PR #233) fixed in tools/start_search_mcp.sh/start_headroom_mcp.sh after a real rename made that
# script pick a broken venv silently. Decision recorded here rather than left implicit: this
# variable IS worth the same hardening, because the failure shape is identical -- a single
# candidate is picked once (here, at Makefile-parse time via `:=`; there, at script-invocation
# time) with no fallthrough if it lacks the real capability every consuming target needs. Uses
# `importlib.util.find_spec` (spec-lookup, no execution), not a full `import pydantic` -- unlike
# the shell launchers' original probe shape, this runs on *every* `make` invocation (`:=` is
# immediate, not deferred to first use), so a full import's cost would tax every unrelated target
# too; find_spec keeps that cost negligible regardless of what's chosen for capability.
PYTHON3 := $(shell for py in .venv/bin/python3 /home/u24desktop/Working/rpg-based-simulation/.venv/bin/python3 /home/vboxuser/Work/venv/bin/python3 python3; do command -v "$$py" >/dev/null 2>&1 && "$$py" -c "import importlib.util, sys; sys.exit(0 if importlib.util.find_spec('pydantic') else 1)" >/dev/null 2>&1 && echo "$$py" && break; done)

# TCK-20260914-VENV-NAMING-CI-PARITY-SWAP: dedicated interpreter resolution for the knowledge-stack
# targets (torch/sentence-transformers), independent of $(PYTHON3) -- `.venv` is now the CI-matching
# 3.13 env and does not have these deps; they live in `.venv-knowledge` (3.12) instead. Uses
# `command -v` (not `[ -x ]`) for the bare "python3" fallback -- see the PYTHON3 comment above and
# the PYTHON variable below for why `[ -x "$$py" ]` alone never resolves a bare command via PATH.
#
# TCK-20260921-INTERPRETER-SELECTION-PROBES-INCONSISTENT: hardened the same way and for the same
# reason as PYTHON3 above -- probes `sentence_transformers` real capability via
# `importlib.util.find_spec`, not existence alone. find_spec (not a full import) matters even more
# here than for PYTHON3: `sentence_transformers` pulls in `torch`, and a full import was measured
# at ~5.66s (this same ticket's own part (b) finding for tools/start_search_mcp.sh) -- paying that
# on every `make` invocation, including targets that never touch the knowledge stack, would be a
# regression on its own, not just an inconsistency fix.
PYTHON_KNOWLEDGE := $(shell for py in .venv-knowledge/bin/python3 /home/u24desktop/Working/rpg-based-simulation/.venv-knowledge/bin/python3 python3; do command -v "$$py" >/dev/null 2>&1 && "$$py" -c "import importlib.util, sys; sys.exit(0 if importlib.util.find_spec('sentence_transformers') else 1)" >/dev/null 2>&1 && echo "$$py" && break; done)

dev: ## Start backend + frontend dev server with live map (hot reload)
	@echo "Starting backend on :8000 and frontend on :5173..."
	@echo "Open http://localhost:5173 to view the live map."
	@echo "Press Ctrl+C to stop both."
	@trap 'kill 0' INT; \
		$(PYTHON3) -m src serve --port 8000 --api-key-hashes "dev:3e90488c475fb2c2997525497f1e72e82dec6d68b5738dc7cebba4371f9f0ee2" & \
		(cd frontend && npm run dev) & \
		wait

dev-backend: ## Start only the backend server
	$(PYTHON3) -m src serve --port 8000

dev-frontend: ## Start only the frontend dev server
	cd frontend && npm run dev

# ── Production ───────────────────────────────────────────

serve: build ## Build frontend + start production server
	$(PYTHON3) -m src serve --port 8000

serve-only: ## Start production server (assumes frontend already built)
	$(PYTHON3) -m src serve --port 8000

# ── Agent Ops Dashboard ──────────────────────────────────

dashboard-install: ## Install agent ops dashboard frontend Node dependencies
	cd dashboard-frontend && npm install

dashboard-build: ## Build the agent ops dashboard frontend for production
	cd dashboard-frontend && npm run build

dashboard-dev: ## Start dashboard backend (reload) + Vite dev server concurrently
	@echo "Starting dashboard backend on :8471 and Vite dev server..."
	@echo "Press Ctrl+C to stop both."
	@trap 'kill 0' INT; \
		uvicorn src.api.agent_ops_dashboard.main:app --host 127.0.0.1 --port 8471 --reload & \
		(cd dashboard-frontend && npm run dev) & \
		wait

dashboard-serve: dashboard-build ## Build dashboard frontend + start single-process production server (port 8420)
	python3 -m src.api.agent_ops_dashboard.serve

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

test-collect: ## List and count collected Python test nodes (tests/ only; does not run tests)
	python3 -m pytest tests/ --collect-only -q

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
	python3 -m pytest tests/ -m "legacy_compat" --resource-budget large -v --tb=short

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

docs-registry-check: ## Report whether docs/REGISTRY.yaml is stale relative to a fresh regeneration
	python3 tools/generate_registry.py --check

working-log-duplicate-check: ## Report duplicate ticket_ids in tickets/working_log.csv, non-blocking
	python3 tools/gate_checks/working_log_duplicate_check.py

working-log-content-duplicate-check: ## Ratcheted check for duplicate (ticket_id, title) rows in tickets/working_log.csv
	python3 tools/gate_checks/working_log_content_duplicate_check.py

duplicate-run-record-check: ## Ratcheted check for genuinely-accidental duplicate agent-monitoring/data/*/runs.jsonl records
	python3 tools/gate_checks/duplicate_run_record_check.py

sidecar-attribution-coverage-check: ## Report tools.jsonl run_id attribution coverage (non-blocking; see module docstring)
	python3 tools/gate_checks/sidecar_attribution_coverage_check.py

tool-call-count-mismatch-check: ## Report post-fix tool_call_count vs tools.jsonl mismatches (non-blocking; see module docstring)
	python3 tools/gate_checks/tool_call_count_mismatch_check.py

event-seq-integrity-check: ## Report duplicate/gapped seq values in events.jsonl, non-blocking
	python3 tools/gate_checks/event_seq_integrity_check.py

monitoring-integrity-backlog-check: ## Ratcheted checks for working_log/run-record gaps, unusable ts, and unknown-week rows
	python3 tools/gate_checks/monitoring_integrity_backlog_check.py

monitoring-anomaly-validate: ## Aggregate coherence validator (duplicate runs, seq integrity, tool_call_count, ts shape, vocabulary)
	python3 tools/gate_checks/monitoring_anomaly_validator.py

premise-staleness-check: ## Report Related Code Areas citation resolution rate, non-blocking (pass --touched-paths for the close-time sweep)
	python3 tools/gate_checks/premise_staleness_check.py

setup-merge-drivers: ## Install the local merge driver + post-merge hook that regenerate docs/REGISTRY.yaml on conflict
	git config merge.registry-regen.driver true
	git config merge.registry-regen.name "regenerate docs/REGISTRY.yaml on conflict"
	cp tools/hooks/registry_post_merge_regen.sh "$$(git rev-parse --path-format=absolute --git-path hooks)/post-merge"
	chmod +x "$$(git rev-parse --path-format=absolute --git-path hooks)/post-merge"
	@echo "[setup-merge-drivers] docs/REGISTRY.yaml merge driver + post-merge hook installed"
	@echo "[setup-merge-drivers] note: the first merge on a branch that also introduces the"
	@echo "  merge=registry-regen line in .gitattributes (i.e. pulling this line in from"
	@echo "  main for the first time) resolves without this driver -- see .gitattributes'"
	@echo "  own comment. Every subsequent merge on that branch uses it normally."
	@echo "[setup-merge-drivers] activation is per-CLONE, not versioned: a clone that never runs"
	@echo "  this target gets ordinary conflict behaviour with no warning, indistinguishable from"
	@echo "  the cold-start case above. Worktrees of this clone share .git/config and the hooks"
	@echo "  directory, so this one run covers all of them -- only a separate clone needs its own."

brainstorm-idea-index: ## Regenerate the per-idea cross-document index (docs/brainstorm/idea_index.json)
	$(PYTHON3) tools/generate_brainstorm_idea_index.py

mechanism-registry-validate: ## Validate registries/mechanisms.yaml against its 10 invariants (depends_on resolution, DAG acyclicity, layer declaration, state enum, verified.instrument enum, verified.verdict enum, implemented_by path existence, unaudited-edge declaration, missing-system, orphan-system)
	$(PYTHON3) tools/mechanism_registry/registry.py
	@echo ""
	@echo "--- Graphify cross-check (report-only, informational -- never affects this target's exit code) ---"
	@$(PYTHON3) tools/mechanism_registry/mechanism_registry_graphify_check.py

mechanism-verification-view: ## Regenerate docs/brainstorm/mechanism_verification_view.md from registries/mechanisms.yaml
	$(PYTHON3) tools/mechanism_registry/generate_mechanism_verification_view.py

mechanism-priority-view: ## Regenerate docs/brainstorm/mechanism_priority_view.md (top-N unverified, by rank x transitive dependents)
	$(PYTHON3) tools/mechanism_registry/generate_mechanism_priority_view.py

mechanism-registry-view: ## Regenerate docs/brainstorm/mechanism_registry_view.md (all mechanisms, priority + verification together, not truncated)
	$(PYTHON3) tools/mechanism_registry/generate_mechanism_registry_view.py

mechanism-system-rollup-view: ## Regenerate docs/brainstorm/mechanism_system_rollup_view.md (per-system counts vs whole-registry baseline, never a badge)
	$(PYTHON3) tools/mechanism_registry/generate_mechanism_system_rollup_view.py

territory-control-view: ## Regenerate docs/brainstorm/territory_control_management_view.md (Territory Rules against architecture.md §8's six axes)
	$(PYTHON3) tools/semantic_control_plane/generate_territory_control_view.py

mechanism-registry-html: ## Regenerate docs/brainstorm/mechanism_registry.html (generated, data-only page; never hand-edit)
	$(PYTHON3) tools/mechanism_registry/generate_mechanism_registry_html.py

mechanism-registry-html-check: ## Check docs/brainstorm/mechanism_registry.html against the real registry state (--check, writes nothing)
	$(PYTHON3) tools/mechanism_registry/generate_mechanism_registry_html.py --check

mechanism-state-caller-check: ## Report-only: flag mechanisms whose declared state disagrees with a real caller-count check (claims-as-tests phase 1)
	$(PYTHON3) tools/mechanism_registry/mechanism_state_caller_check.py

mechanism-wiring-map-classdef-check: ## Check the wiring map's Entity Operating Loop diagram classDef colouring against the real registry state
	$(PYTHON3) tools/mechanism_registry/mechanism_wiring_map_classdef.py

mechanism-status-language-check: ## Report-only: scan atlas/capabilities desc fields and wiring-map node labels for status vocabulary that belongs in the registry, not prose
	$(PYTHON3) tools/mechanism_registry/mechanism_status_language_check.py

mechanism-prose-field-drift-check: ## Report-only: flag a mechanism entry whose own verified.note claims an instrument/verdict transition that contradicts its own structured fields
	$(PYTHON3) tools/mechanism_registry/mechanism_prose_field_drift_check.py

mechanism-registry-changed-code-check: ## Report-only: flag implemented_by-cited code that changed without its mechanism's own entry changing, plus implemented_by replacements
	$(PYTHON3) tools/mechanism_registry/mechanism_registry_changed_code_check.py

semantic-control-plane-drift-check: ## Report-only: flag M1 mapping rows whose cited code or mapped mechanism's verdict changed since the row's own review date
	$(PYTHON3) tools/semantic_control_plane/mapping_drift_check.py

mechanism-atlas-check: ## Check the atlas's mapped card badge cls values against the real registry state (--check, writes nothing)
	$(PYTHON3) tools/mechanism_registry/mechanism_atlas_regenerate.py --check

mechanism-atlas-regenerate: ## Fix the atlas's mapped card badge cls values to match the real registry state (surgical: cls only, never touches prose)
	$(PYTHON3) tools/mechanism_registry/mechanism_atlas_regenerate.py

mechanism-capabilities-check: ## Check the capabilities page's mapped card tier values against the real registry state (--check, writes nothing)
	$(PYTHON3) tools/mechanism_registry/mechanism_capabilities_regenerate.py --check

mechanism-capabilities-regenerate: ## Fix the capabilities page's mapped card tier/tierLabel values to match the real registry state (surgical: never touches title/desc)
	$(PYTHON3) tools/mechanism_registry/mechanism_capabilities_regenerate.py

simq-corpus-registry: ## Regenerate config/simulation_quality/corpus_registry.yaml from real world/profile/anchor data
	python3 tools/generate_corpus_registry.py

tag-report: ## Print a tag-usage report over completed tickets (pass ARGS="--json reports/tag_report.json")
	python3 tools/tag_report.py $(ARGS)

ticket-stats-report: ## Print a ticket-corpus stats report (velocity/tier/priority/layer/artifact-completeness) (pass ARGS="--json reports/ticket_stats_report.json")
	python3 tools/ticket_stats_report.py $(ARGS)

# ── Agent Monitoring ─────────────────────────────────────

agent-monitoring-retro: ## Generate current-week agent monitoring retro report
	python3 tools/agent-monitoring/generate_retro.py

agent-monitoring-consolidate: ## Fold per-ticket monitoring shard files into the canonical per-week files (on demand; also runs automatically before every retro)
	python3 tools/agent-monitoring/monitoring_consolidation.py

agent-monitoring-validate: ## Cross-check agent monitoring integrity against working_log.csv
	python3 tools/agent-monitoring/validate.py

agent-monitoring-query: ## Query agent monitoring records (pass ARGS="--agent investigator --days 14")
	python3 tools/agent-monitoring/query.py $(ARGS)

agent-monitoring-weight-check: ## Required check before proposing a cost_proxy.py weight change (pass ARGS='--candidate-weights "{...}"')
	python3 tools/agent-monitoring/weight_sensitivity_check.py $(ARGS)

agent-monitoring-epic-staleness: ## Report open epics with no recent child-ticket activity
	python3 tools/agent-monitoring/epic_staleness_check.py

status-drift-check: ## Report ## Status body-text drift in tickets/done/ and lowercase final_status in runs.jsonl
	python3 tools/gate_checks/status_drift_check.py

codebase-health-baseline: ## Print a live LoC/churn/dependency baseline snapshot (on-demand only — not CI)
	python3 tools/codebase_health_baseline.py

codebase-health-impact: ## Print a change-impact report for a source path (pass ARGS="src/engine/pipeline.py") (on-demand only — not CI)
	python3 tools/code_health_impact.py $(ARGS)

codebase-health-snapshot: ## Append a codebase-health metrics snapshot to agent-monitoring/codebase_health_history.jsonl (on-demand only — not CI)
	python3 tools/codebase_health_snapshot.py snapshot $(ARGS)

codebase-health-scorecard: ## Print a per-dimension trend scorecard over codebase-health history (on-demand only — not CI)
	python3 tools/codebase_health_snapshot.py scorecard $(ARGS)

codebase-health-pr-impact: ## Print a batched PR/AI change-impact report for one or more source paths (pass ARGS="path1 path2 ...") (on-demand only — not CI)
	python3 tools/pr_impact_report.py $(ARGS)

agent-monitoring-index: ## Rebuild the derived read-only SQLite index over agent-monitoring JSONL logs (on-demand only — not CI)
	$(shell for py in .venv/bin/python3 /home/vboxuser/Work/venv/bin/python3 python3; do [ -x "$$py" ] && echo "$$py" && break; done) \
	  tools/agent-monitoring/build_index.py

parity-index: ## Rebuild the derived read-only SQLite index over docs/parity_ledger/*.yaml (on-demand only — not CI)
	python3 tools/parity_index.py build

parity-index-check: ## Report whether parity-index/parity.db is stale relative to live docs/parity_ledger/*.yaml
	python3 tools/parity_index.py check-staleness

simq-long-run-lifecycle-observation: ## Run the 5000-tick combined SimQ + entity-lifecycle observation across the curated 6-world sample
	python3 tools/simq_long_run_observation.py

content-inventory: ## Regenerate config/content_inventory.json from real data/content/ counts
	python3 tools/generate_content_inventory.py

# ── Knowledge Search ─────────────────────────────────────────────────────────
# developer env only — not CI
# Requires: pip install -e ".[knowledge]"

knowledge-index: ## Build local semantic knowledge index (developer env only — not CI)
	@echo "Building knowledge index (requires: pip install -e '.[knowledge]')..."
	SSL_CERT_FILE=/etc/ssl/certs/ca-certificates.crt SSL_CERT_DIR=/etc/ssl/certs HF_HUB_ETAG_TIMEOUT=120 \
	  $(PYTHON_KNOWLEDGE) \
	  tools/knowledge_search.py build

knowledge-index-update: ## Incremental reindex — only re-embeds changed/new files (fast)
	SSL_CERT_FILE=/etc/ssl/certs/ca-certificates.crt SSL_CERT_DIR=/etc/ssl/certs HF_HUB_ETAG_TIMEOUT=120 \
	  $(PYTHON_KNOWLEDGE) \
	  tools/knowledge_search.py build --incremental

kgmcp-bootstrap: parity-index knowledge-index ## Rebuild all local, gitignored Knowledge Gateway MCP caches for a fresh environment (see docs/guidelines/agent_working_environment.md)
	@echo "parity-index/parity.db and knowledge-index/{knowledge.db,bm25.pkl,embeddings_cache.pkl} rebuilt."
	@echo "knowledge-index/retrieval_cache.db (KGMCP Level 1/2 cache) has no bootstrap step -- it"
	@echo "self-initializes empty on the first real knowledge_context/knowledge_status call and warms"
	@echo "up from there. See docs/guidelines/agent_working_environment.md for full detail."

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
	$(PYTHON_KNOWLEDGE) tools/eval_search.py

# [ -x "$$py" ] only resolves an absolute/relative path to a literal file -- it never does a
# PATH lookup for a bare command name, so "python3" alone always failed this check even when a
# real python3 was on PATH (confirmed: CI has no .venv/bin/python3 and no
# /home/vboxuser/... path, so this loop silently produced an EMPTY PYTHON on every CI runner,
# breaking every $(PYTHON)-using target with "sh: 1: -m: not found" -- masked until now because
# the "slow" CI job's own `needs:` gate had never let it run to completion before).
# command -v correctly resolves bare "python3" via PATH as well as absolute/relative paths.
PYTHON := $(shell for py in .venv/bin/python3 /home/vboxuser/Work/venv/bin/python3 python3; do command -v "$$py" >/dev/null 2>&1 && echo "$$py" && break; done)

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

simq-corpus-diversity-slow-isolated: ## [slow] Run test_corpus_diversity.py's -m slow guards as isolated per-test subprocesses (no cumulative-session-load carryover, TCK-20260715-SIMQ-CORPUS-DIVERSITY-SESSION-LOAD-FLAKE)
	@nodeids=$$($(PYTHON) -m pytest tests/unit/worldassembly/test_corpus_diversity.py -m slow --resource-budget large --collect-only -q | grep '::' || true); \
	nodeid_count=$$(echo "$$nodeids" | grep -c '::' || true); \
	if [ "$$nodeid_count" -lt 32 ]; then \
	  echo "ERROR: expected >=32 tests from test_corpus_diversity.py -m slow, collected $$nodeid_count -- aborting, not silently passing (collection failure, marker drift, import error, or misconfiguration)"; \
	  exit 1; \
	fi; \
	status=0; \
	for nodeid in $$nodeids; do \
	  echo "[isolated] $$nodeid"; \
	  $(PYTHON) -m pytest "$$nodeid" --resource-budget large --tb=short -q || status=1; \
	done; \
	exit $$status

mcp-server-test: ## Smoke-test MCP search_docs tool via --test mode (no MCP client needed)
	@echo '{"query": "damage formula", "top_k": 3}' | \
	  $(PYTHON_KNOWLEDGE) tools/search_mcp.py --test

# ── Cleanup ──────────────────────────────────────────────

clean: ## Remove build artifacts
	rm -rf frontend/dist
	rm -rf frontend/node_modules/.tmp
	find . -type d -name __pycache__ -exec rm -rf {} + 2>/dev/null || true
