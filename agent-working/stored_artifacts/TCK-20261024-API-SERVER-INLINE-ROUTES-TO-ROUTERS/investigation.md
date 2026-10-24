---
status: active
layer: architecture
authority: P2
audience: agent
ticket_id: TCK-20261024-API-SERVER-INLINE-ROUTES-TO-ROUTERS
artifact_type: investigation
tags: [architecture, api-design, refactor]
---

# Investigation
- `src/api/routes/state.py`, `control.py` and `health.py` are 0-byte files, added in early commits (`562116889`, `b8e7c1c3b`), never imported, never included. Left in place: for codebase-planner to ask rpg whether to delete them.
- New locations for rpg (#697): the wildcard CORS block is `src/api/server.py:184-189` (was 109); `/metrics` behind `require_admission` is `src/api/routes/engine_probes.py:25` (was `server.py:176`).
- Determinism and replay suites: no test under `tests/determinism` or `tests/replay` imports `create_v2_app` or `src.api.server`. The only importers outside `tests/api` are `tests/observability/test_metrics_export.py`, `tests/tools/test_agent_ops_dashboard_frontend_api_surface.py`, `tests/architecture/test_api_read_model_guard.py` and `tests/codebase/test_ast_grep_rules.py`; all pass.
- Pyrefly could not be synced locally: the shared venv has no `pyrefly` (`uv sync --group lint` was not run on the shared venv). The Pyrefly step is advisory and never blocks; the baseline syncs on the next run that has it.
- `tighten` and the mypy sync also dropped stale rows for `src/engine/worker_manager.py` and others, improvements already on main.
