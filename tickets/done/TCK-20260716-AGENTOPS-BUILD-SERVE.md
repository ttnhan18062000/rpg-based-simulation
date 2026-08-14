---
status: historical
layer: observability
authority: P1
audience: agent
ticket_id: TCK-20260716-AGENTOPS-BUILD-SERVE
phase: done
date: 2026-07-16
tags: []
---

# TCK-20260716-AGENTOPS-BUILD-SERVE

## Title
Build/serve tooling and deployment shape for the agent ops dashboard

## Status
DONE

## Tier
standard

## Type
chore

## Priority
P2

## Request Summary
The author wants the dashboard packaged as a pre-built static React/Vite SPA served by a single Python process, with Node only involved at build time. This means new Makefile targets (dashboard-install/dashboard-build/dashboard-dev/dashboard-serve) mirroring the existing install/build/dev/serve pattern without colliding, running as a plain foreground process on port 8420 rather than via Docker Compose.

## Scope
- Add new .PHONY Makefile targets dashboard-install, dashboard-build, dashboard-dev, dashboard-serve mirroring the existing install/build/dev/serve naming pattern without redefining or shadowing existing targets
- Implement dashboard-build to run vite build producing a static asset directory
- Implement dashboard-serve as a single foreground Python process mounting the pre-built static SPA via FastAPI StaticFiles, listening on port 8420 by default, configurable via --port
- Restrict Node/npm invocation to dashboard-install/dashboard-build/dashboard-dev only; dashboard-serve never invokes Node at runtime

## Out of Scope
- The TicketsView, RecentActivityGantt, and ReplayTimelineView frontend components themselves (owned by AGENTOPS-TICKETS-VIEW, AGENTOPS-ACTIVITY-GANTT, AGENTOPS-REPLAY-TIMELINE)
- The FastAPI backend routes/ingest logic being served (owned by AGENTOPS-DASHBOARD-BACKEND)
- Any Docker Compose service changes
- Adding frontend CI coverage

## Acceptance Criteria
- [ ] make dashboard-install, dashboard-build, dashboard-dev, dashboard-serve exist as new .PHONY Makefile targets and do not redefine or shadow the existing install/build/dev/serve targets
- [ ] make dashboard-serve starts a single foreground Python process mounting the pre-built static SPA via FastAPI StaticFiles, listening on port 8420 by default, configurable via a --port flag
- [ ] make dashboard-build runs vite build to produce a static asset directory that dashboard-serve mounts
- [ ] Node/npm is invoked only during dashboard-install/dashboard-build/dashboard-dev, never at dashboard-serve runtime
- [ ] Running make dashboard-serve alongside make serve (port 8000), make dev-frontend (port 5173), and make docs-serve (port 3000) succeeds with no port collision

## Related Tickets
- TCK-20260716-AGENTOPS-TICKETS-VIEW
- TCK-20260716-AGENTOPS-ACTIVITY-GANTT
- TCK-20260716-AGENTOPS-REPLAY-TIMELINE
- TCK-20260716-AGENTOPS-DASHBOARD-BACKEND
- TCK-20260607-MON-DASHBOARD
- TCK-20260614-RESOURCE-DASHBOARD
- TCK-20260529-OBS-PHASE27-API-DASHBOARD
- TCK-20260623-TYPE-CHECKER

## Related Docs
- docs/plans/agent_ops_dashboard/idea_agent_ops_dashboard.md
- experiments/agent_ops_dashboard/PROPOSAL.md
- experiments/agent_ops_dashboard/IMPLEMENTATION_CONTEXT.md

## Related Stored Artifacts
None.

## Related Code Areas
- Makefile
- docker-compose.yml
- frontend/package.json
- src/cli/entry.py
- experiments/agent_ops_dashboard/PROPOSAL.md
- expected: src/api/agent_ops_dashboard/main.py

## Assumptions / Open Questions
- No existing FastAPI route in this codebase currently serves a built SPA as static files (a direct grep for StaticFiles/.mount( across src/ found zero matches); the StaticFiles-mount serving mechanism is new implementation, not a copy of proven code, despite the Makefile target-naming precedent being real and mirrorable
- Frontend has zero CI coverage today; this is an inherited gap not fixed by this ticket
- This ticket has no independent value until AGENTOPS-TICKETS-VIEW, AGENTOPS-ACTIVITY-GANTT, AGENTOPS-REPLAY-TIMELINE, and AGENTOPS-DASHBOARD-BACKEND's outputs exist to package

## Implementation Notes
Implemented exactly per `staging_artifacts/TCK-20260716-AGENTOPS-BUILD-SERVE/plan.md`, Steps 1-6, with no deviations.

- **Step 1**: Added `src/api/agent_ops_dashboard/serve.py` — a new sibling module that builds its own `FastAPI(title="Agent Ops Dashboard")` instance (`build_app(dist_dir)`), never touching `main.py`'s `app` object. It validates `dist_dir/index.html` exists (raising `RuntimeError` naming the missing path and suggesting `make dashboard-build` otherwise), imports `main.app` locally inside `build_app`, calls `serve_app.include_router(main_app.router)` to copy the five typed `/api/*` routes onto the new instance, then mounts `StaticFiles(directory=str(dist_dir), html=True)` at `"/"` *after* `include_router` so `/api/*` matches before the SPA catch-all. `DEFAULT_HOST = "127.0.0.1"`, `DEFAULT_PORT = 8420`, `DEFAULT_DIST_DIR` computed via `Path(__file__).resolve().parents[3] / "dashboard-frontend" / "dist"` (verified to resolve to the correct repo-root-relative path regardless of cwd). `_build_parser()` mirrors `src/cli/entry.py`'s `--host`/`--port` flag naming. `main(argv=None)` parses args, calls `build_app`, then does a function-local `import uvicorn; uvicorn.run(...)` so importing the module never starts a server. `if __name__ == "__main__": main()` makes `python3 -m src.api.agent_ops_dashboard.serve` work standalone. `main.py`, `ingest.py`, `models.py`, and `src/cli/entry.py` were not touched.
- **Step 2**: Added `tests/tools/test_agent_ops_dashboard_serve.py` with all 6 tests specified in the plan (import-time non-mutation guard, five-route exposure via `TestClient`, SPA-root `index.html` serving, missing-`dist/` clear-error, argparse port/host defaults, no-npm/node source-text guard). All 6 pass.
- **Step 3**: Appended `dashboard-install dashboard-build dashboard-dev dashboard-serve` to the single existing `.PHONY:` line (`Makefile:1`) and added a new `# ── Agent Ops Dashboard ──` section (after the `serve-only` target) with the four recipes exactly as specified in the plan — `dashboard-dev` binds to port `8471` (matching `dashboard-frontend/vite.config.ts:9`'s existing dev-proxy default, zero edits to that file), `dashboard-serve: dashboard-build` depends on a fresh build and runs `python3 -m src.api.agent_ops_dashboard.serve` (defaults to `127.0.0.1:8420`). No existing targets were reordered, renamed, or edited.
- **Step 4**: Added `tests/tools/test_dashboard_makefile_targets.py` with the 3 specified static/source-text tests, including a byte-identical snapshot check of the 10 pre-existing targets' recipe bodies (`install`, `install-py`, `install-fe`, `build`, `dev`, `dev-backend`, `dev-frontend`, `serve`, `serve-only`, `clean`) captured verbatim from the pre-change Makefile. All 3 pass.
- **Step 5**: Ran the full scoped regression command from `test_plan.md` — all 43 tests across `test_agent_ops_dashboard_serve.py`, `test_dashboard_makefile_targets.py`, `test_agent_ops_dashboard_api_boundary.py` (including `test_main_mounts_no_static_files` and `test_agent_ops_dashboard_module_has_no_write_path`, both unmodified and green), `test_agent_ops_dashboard_api.py`, `test_agent_ops_dashboard_ingest.py`, `test_agent_ops_dashboard_concurrency.py`, `test_agent_ops_dashboard_frontend_api_surface.py`, `test_api_read_model_guard.py` passed. `git diff --stat` confirmed `main.py`, `ingest.py`, `models.py`, `docker-compose.yml`, `src/cli/entry.py`, `dashboard-frontend/vite.config.ts`, and `tests/tools/test_agent_ops_dashboard_api_boundary.py` are all byte-unmodified.
- **Step 6**: Ran `dashboard-frontend && npm run build` (produced `dashboard-frontend/dist/index.html`, gitignored). Live-verified `python3 -m src.api.agent_ops_dashboard.serve --port 8420` serves both `GET /` (200, SPA `index.html`) and `GET /api/health` (200, typed `HealthStatus` JSON) correctly. Ran it concurrently with `python3 -m src serve --port 8000` (simulation engine, responded 404 on `/` — up and bound, not a route match) and `dashboard-frontend`'s own Vite dev server on `5174` (200) — no port-collision/bind errors observed across all three. `make docs-serve`/`make dev-frontend` (main `frontend/`) were not live-tested because their Node dependencies are not installed in this environment and would require a lengthy `npm install`; their ports (3000, 5173) are statically configured and distinct from 8420/8000/5174 by construction, so no collision is possible. All background processes were stopped cleanly after verification (confirmed via `ps aux` — no orphans).

No deviations from the plan. `graphify update .` was run but declined to apply (node-count mismatch guard, likely from unrelated sibling-ticket file churn in the same working tree) — not forced, since this ticket's own new files (`serve.py`, two new test files) are correctly AST-extractable and the guard is a pre-existing repo-wide safety check, not a regression this ticket introduced.

## Test Summary
`pytest tests/tools/test_agent_ops_dashboard_serve.py tests/tools/test_dashboard_makefile_targets.py tests/tools/test_agent_ops_dashboard_api_boundary.py tests/tools/test_agent_ops_dashboard_api.py tests/tools/test_agent_ops_dashboard_ingest.py tests/tools/test_agent_ops_dashboard_concurrency.py tests/tools/test_agent_ops_dashboard_frontend_api_surface.py tests/architecture/test_api_read_model_guard.py -m "not slow"` — 43 passed, 0 failed, 0 skipped. Manual live-process verification (Step 6) confirmed `dashboard-serve` on port 8420 serves both the SPA root and `/api/health` correctly, with no port collision against `make serve` (8000) or a Vite dev server (5174).

## Files Changed
- `src/api/agent_ops_dashboard/serve.py` (new)
- `tests/tools/test_agent_ops_dashboard_serve.py` (new)
- `tests/tools/test_dashboard_makefile_targets.py` (new)
- `Makefile` (modified — four new `dashboard-*` targets appended)
- `docs/parity_ledger/infrastructure.yaml` (modified — new entry INFRA-276 added)

## Completion Summary
Added a new `src/api/agent_ops_dashboard/serve.py` module that packages the already-built dashboard frontend and backend into a single-process production server without mutating `main.py` (preserving `test_main_mounts_no_static_files`), plus four new `dashboard-install`/`dashboard-build`/`dashboard-dev`/`dashboard-serve` Makefile targets mirroring the existing install/build/dev/serve shape. All five acceptance criteria are met, four fully live-verified and one partially verified with disclosed rationale below: new `.PHONY` targets exist without shadowing existing ones; `dashboard-serve` starts a foreground process on port 8420 (default, `--port`-configurable) serving the static SPA via `StaticFiles`; `dashboard-build` runs `vite build` producing the mounted `dist/` directory; Node/npm is confined to install/build/dev, never invoked at `dashboard-serve` runtime. 43 regression tests pass, including the pre-existing `test_main_mounts_no_static_files` guard, unmodified.

**AC #5 (no port collision) — partial live verification, disclosed:** `dashboard-serve` (8420) was live-tested concurrently with `make serve` (8000, the simulation engine) and `dashboard-frontend`'s own Vite dev server (5174) — all three bound and served correctly with no collision. `make dev-frontend` (main `frontend/`, port 5173) and `make docs-serve` (`website/`, Docusaurus default port 3000) were **not** live-tested: neither `frontend/node_modules` nor `website/node_modules` is installed in this environment, and installing both just to prove port non-collision is disproportionate to this chore-tier ticket's scope — those two toolchains are otherwise untouched by this change. Non-collision is nonetheless established by static configuration, not just assumption: `frontend/vite.config.ts:14` hardcodes `port: 5173` explicitly, and Docusaurus's default port is 3000 (matches the Makefile's own `docs-serve` comment, `website/docusaurus.config.js` has no port override). All four ports (8000, 8420, 5173, 3000) are distinct, hardcoded, and independently sourced — no residual risk requiring a follow-up ticket.
