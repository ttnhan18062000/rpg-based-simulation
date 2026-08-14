---
status: historical
layer: observability
authority: P2
audience: agent
ticket_id: TCK-20260716-AGENTOPS-BUILD-SERVE
artifact_type: plan
tags: [observability, agent-monitoring]
---

# Implementation Plan — TCK-20260716-AGENTOPS-BUILD-SERVE

## Summary

Package the already-built agent-ops dashboard frontend (`dashboard-frontend/`, DONE via sibling
tickets) and already-built backend API (`src/api/agent_ops_dashboard/main.py`, DONE via
AGENTOPS-DASHBOARD-BACKEND) into a single-process production server, plus new Makefile targets to
build/install/dev/serve it. Because `test_main_mounts_no_static_files`
(`tests/tools/test_agent_ops_dashboard_api_boundary.py:61-67`) forbids any `StaticFiles(`/`.mount(`
substring or `Mount` route inside `main.py`, the StaticFiles mount lives entirely in a **new**
sibling module, `src/api/agent_ops_dashboard/serve.py`, which builds its own `FastAPI()` instance,
copies `main.app`'s routes onto it via `include_router(main_app.router)` (a read-only operation
that never appends anything to `main_app`'s own route list), and mounts `StaticFiles` on the new
instance only. The app-building function takes the pre-built `dist/` directory as an explicit
argument and is never invoked at import time, so importing `serve.py` alone (as
`test_main_mounts_no_static_files`'s sibling tests and any new architecture guard will do) never
constructs a server or mutates `main_app`. Four new `dashboard-*` Makefile targets mirror the
existing `install`/`build`/`dev`/`serve` shape under a distinct prefix, with `dashboard-serve`
depending on `dashboard-build` (mirroring the existing `serve: build` dependency edge) so the
Python process always serves fresh static assets. `dashboard-dev`'s backend half binds to `8471`
(uvicorn's `--reload` CLI form, mirroring the existing `search-server:` target's
`uvicorn tools.search_server:app --host 127.0.0.1 --port 8765 --reload` pattern verbatim) — this
is the exact value `dashboard-frontend/vite.config.ts:9`'s dev-proxy fallback already expects,
so the pre-existing placeholder becomes live wiring instead of dead code, with zero edits to
`vite.config.ts` itself. `dashboard-serve` (production) binds to `8420` by default per AC #2,
configurable via `--port`, host fixed at `127.0.0.1` (never `0.0.0.0`).

## Steps

### Step 1 — Create the new serve module: `src/api/agent_ops_dashboard/serve.py`

**Files:** `src/api/agent_ops_dashboard/serve.py` (new file)

**Change:** Create a new module with:
- A module docstring stating this module deliberately builds a *separate* `FastAPI()` instance and
  never mutates `src/api/agent_ops_dashboard/main.py`'s `app` object, per
  `test_main_mounts_no_static_files`.
- `DEFAULT_PORT = 8420`, `DEFAULT_HOST = "127.0.0.1"`.
- `DEFAULT_DIST_DIR`: computed relative to this file's own location, four parents up
  (`agent_ops_dashboard` → `api` → `src` → repo root) joined with `dashboard-frontend/dist`, so the
  default works regardless of the caller's cwd.
- `def build_app(dist_dir: Path) -> FastAPI:` — validates `dist_dir` is a directory containing
  `index.html`; if not, raises `RuntimeError` with a message naming the missing path and suggesting
  `make dashboard-build` (not a bare `StaticFiles`-internal error). On success: constructs
  `serve_app = FastAPI(title="Agent Ops Dashboard")`, imports `main.app` as `main_app` from
  `src.api.agent_ops_dashboard.main`, calls `serve_app.include_router(main_app.router)` (this reads
  `main_app.router`'s existing route list and appends copies into `serve_app`'s own router — it
  does not modify `main_app.router` itself), then `serve_app.mount("/", StaticFiles(directory=str(dist_dir), html=True), name="spa")` **after** `include_router` so the `/api/*` routes are matched
  first and the catch-all static mount only serves the SPA and its assets. Returns `serve_app`.
- `def _build_parser() -> argparse.ArgumentParser:` — `--host` (default `DEFAULT_HOST`), `--port`
  (default `DEFAULT_PORT`, `type=int`), `--dist-dir` (default `DEFAULT_DIST_DIR`, `type=Path`) —
  mirrors `src/cli/entry.py:23-24`'s flag naming convention exactly.
- `def main(argv=None) -> None:` — parses args via `_build_parser()`, calls `build_app(args.dist_dir)`,
  then `import uvicorn; uvicorn.run(app, host=args.host, port=args.port)`. The `import uvicorn` stays
  local to this function (not top-of-module) so importing the module for testing never imports/starts
  a server.
- `if __name__ == "__main__": main()` at the bottom — this is what makes
  `python3 -m src.api.agent_ops_dashboard.serve` work as a standalone entry point without touching
  `src/cli/entry.py`.
- No top-level side effects: `build_app()` is never called at module scope, so importing this module
  never touches the filesystem or constructs a server.

**Do NOT touch:** `src/api/agent_ops_dashboard/main.py`, `ingest.py`, `models.py` — do not add any
`StaticFiles(`, `.mount(`, or import-time app construction there. Do not add a `serve` subcommand to
`src/cli/entry.py`'s argparse parser — this is a standalone module, not a CLI subcommand, per
`main.py`'s own "separate product/port" docstring framing.

**Verify:** `python3 -c "from src.api.agent_ops_dashboard.serve import build_app, main; print('ok')"`
(sanity import check — real behavioral verification happens in Step 2's tests, which this step's
code must be written to satisfy).

---

### Step 2 — Add `tests/tools/test_agent_ops_dashboard_serve.py`

**Files:** `tests/tools/test_agent_ops_dashboard_serve.py` (new file)

**Change:** Add the following test functions, all exercising the module built in Step 1:
1. `test_serve_module_does_not_mutate_main_app_at_import_time` — imports
   `src.api.agent_ops_dashboard.serve`, then asserts (a) `main.py`'s own source (read directly, same
   check as `test_main_mounts_no_static_files`) contains no `"StaticFiles("` or `".mount("`
   substring, and (b) `main.app.routes` contains no `starlette.routing.Mount` instance even after
   `serve` has been imported.
2. `test_serve_app_exposes_same_five_routes_as_main_app` — using a `tmp_path` fixture with a fake
   `dist/index.html`, call `build_app(tmp_path)`, drive it with `fastapi.testclient.TestClient`, and
   assert `GET /api/health` returns 200 with a body matching the `HealthStatus` shape (proves the
   `/api/*` routes are not shadowed by the static mount).
3. `test_serve_app_returns_index_html_for_spa_root` — same fixture, assert `GET /` returns 200 with
   the fixture `index.html`'s exact content.
4. `test_serve_app_raises_clear_error_when_dist_dir_missing` — call `build_app(tmp_path / "nonexistent")`
   and assert a `RuntimeError` is raised whose message contains the missing path string and mentions
   `dashboard-build`.
5. `test_serve_argparse_port_and_host_defaults` — call `_build_parser().parse_args([])` and assert
   `port == 8420`, `host == "127.0.0.1"`; call `_build_parser().parse_args(["--port", "9001"])` and
   assert `port == 9001`.
6. `test_serve_module_has_no_node_npm_invocation` — read `serve.py`'s own source text and assert no
   substring match for `"npm"`, `"node "`, `"subprocess"`, or `"os.system"`.

**Do NOT touch:** `tests/tools/test_agent_ops_dashboard_api_boundary.py` (existing regression test —
must stay byte-unmodified; this ticket's new guard is additive, not a replacement).

**Verify:** `pytest tests/tools/test_agent_ops_dashboard_serve.py -m "not slow"` — all 6 tests pass.

---

### Step 3 — Add the four `dashboard-*` Makefile targets

**Files:** `Makefile`

**Change:**
1. Append `dashboard-install dashboard-build dashboard-dev dashboard-serve` to the end of the single
   existing `.PHONY:` line (`Makefile:1`) — do not add a second `.PHONY:` line.
2. Add a new section (e.g. after the existing "Production" section, `Makefile:43-49`, or in a new
   `# ── Agent Ops Dashboard ──` block) with:
   ```makefile
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
   ```
   `dashboard-dev`'s `uvicorn ... --port 8471 --reload` form mirrors the existing `search-server:`
   target (`Makefile:278-280`) verbatim in style, and `8471` matches
   `dashboard-frontend/vite.config.ts:9`'s existing dev-proxy fallback default exactly — no
   `vite.config.ts` edit needed. `dashboard-serve: dashboard-build` mirrors the existing
   `serve: build` dependency edge (`Makefile:45-46`) so `make dashboard-serve` always serves a fresh
   build; `--port` is passed through by re-invoking `python3 -m src.api.agent_ops_dashboard.serve`
   directly (which itself defaults to `8420`/`127.0.0.1` per Step 1) — a developer wanting a
   different port runs the module directly with `--port`, matching how `serve-only` (`Makefile:48-49`)
   already documents a "just run it" escape hatch.

**Do NOT touch:** the existing `install`, `install-py`, `install-fe`, `build`, `dev`, `dev-backend`,
`dev-frontend`, `serve`, `serve-only`, `clean` targets — no reordering, no recipe edits, no target
renaming. Do not touch `docker-compose.yml`. Do not add a `.github/workflows/test.yml` frontend CI
job.

**Verify:** `make dashboard-install`, `make dashboard-build` run manually and succeed (produces
`dashboard-frontend/dist/index.html`); full automated verification happens in Step 4.

---

### Step 4 — Add `tests/tools/test_dashboard_makefile_targets.py`

**Files:** `tests/tools/test_dashboard_makefile_targets.py` (new file)

**Change:** Add static, source-text-only tests over `Makefile`'s raw content (no live process, no
`make` invocation):
1. `test_dashboard_targets_exist_and_are_phony` — read `Makefile` text, assert
   `dashboard-install:`, `dashboard-build:`, `dashboard-dev:`, `dashboard-serve:` each appear as a
   target definition (regex `^dashboard-\w+:`), and each of the four names appears in the
   `.PHONY:` line.
2. `test_existing_targets_unmodified` — a fixed snapshot (captured from the actual pre-change
   `Makefile` at implementation time) of the exact recipe bodies of `install:`, `install-py:`,
   `install-fe:`, `build:`, `dev:`, `dev-backend:`, `dev-frontend:`, `serve:`, `serve-only:`,
   `clean:`; assert each target's current recipe text in `Makefile` is byte-identical to the
   snapshot.
3. `test_dashboard_serve_recipe_has_no_npm_or_node` — extract each new target's recipe text (the
   indented lines following its `target:` line up to the next blank line or next target); assert
   `npm`, `node`, and `cd dashboard-frontend` appear in `dashboard-install`, `dashboard-build`, and
   `dashboard-dev`'s recipes, but assert none of `npm`/`node`/`cd dashboard-frontend` appears in
   `dashboard-serve`'s recipe (its only line is `python3 -m src.api.agent_ops_dashboard.serve`, plus
   its `dashboard-build` prerequisite which is a separate `make` invocation, not part of this
   recipe's own text).

**Do NOT touch:** any other file. This step is Makefile-text-only.

**Verify:** `pytest tests/tools/test_dashboard_makefile_targets.py -m "not slow"` — all 3 tests pass.

---

### Step 5 — Anti-drift regression guard: confirm the existing boundary test and full regression
surface stay green

**Files:** none changed in this step — verification only.

**Change:** Run the full scoped regression command from `test_plan.md` and confirm every suite is
green, with special attention to the two hazards named in the ticket investigation:
```
pytest tests/tools/test_agent_ops_dashboard_serve.py tests/tools/test_dashboard_makefile_targets.py tests/tools/test_agent_ops_dashboard_api_boundary.py tests/tools/test_agent_ops_dashboard_api.py tests/tools/test_agent_ops_dashboard_ingest.py tests/tools/test_agent_ops_dashboard_concurrency.py tests/tools/test_agent_ops_dashboard_frontend_api_surface.py tests/architecture/test_api_read_model_guard.py -m "not slow"
```
Explicitly confirm, by reading the assertion output (not just exit code):
1. `test_agent_ops_dashboard_api_boundary.py::test_main_mounts_no_static_files` passes unmodified —
   `main.py`'s source still has zero `StaticFiles(`/`.mount(` substrings and `main.app.routes` has
   zero `Mount` instances, even with `serve.py` now present as a sibling module in the same package
   (this test does not import `serve.py`, but Step 2's new
   `test_serve_module_does_not_mutate_main_app_at_import_time` covers the case where `serve` *is*
   imported — both must be green).
2. `test_agent_ops_dashboard_api_boundary.py::test_agent_ops_dashboard_module_has_no_write_path` still
   passes — this test globs `_SRC_ROOT.glob("*.py")` (i.e. **every** `.py` file in
   `src/api/agent_ops_dashboard/`, which now automatically includes the new `serve.py`) and asserts no
   `.write_text(`/`.write_bytes(`/`.open(` attribute calls anywhere in that directory. `serve.py` as
   written in Step 1 makes no such calls — confirm this explicitly rather than assuming.
3. `test_agent_ops_dashboard_serve.py::test_serve_module_has_no_node_npm_invocation` passes — the new
   serve module never invokes Node/npm at runtime (source-text scan), satisfying AC #4's "never at
   dashboard-serve runtime" clause independently of the Makefile-level guard in Step 4.
4. No existing test file listed above required any edit to pass — if any did, stop and re-examine
   Step 1–4 for scope drift before proceeding.

**Do NOT touch:** `tests/tools/test_agent_ops_dashboard_api_boundary.py`,
`tests/tools/test_agent_ops_dashboard_api.py`, `tests/tools/test_agent_ops_dashboard_ingest.py`,
`tests/tools/test_agent_ops_dashboard_concurrency.py`,
`tests/tools/test_agent_ops_dashboard_frontend_api_surface.py`,
`tests/architecture/test_api_read_model_guard.py` — all must remain byte-unmodified.

**Verify:** the pytest command above exits 0 with all listed suites reporting pass, zero skips due
to collection errors.

---

### Step 6 — Manual port-collision verification (AC #5)

**Files:** none changed — process-level manual verification only, not pytest (no live-process test
exists or is required for this AC per `test_plan.md`).

**Change:** Run, in sequence or backgrounded:
```
make serve &          # port 8000
make dev-frontend &    # port 5173
make docs-serve &      # port 3000
make dashboard-serve &  # port 8420 default
```
Confirm all four processes stay up with no "address already in use" / bind errors, then stop them
(`kill` the backgrounded jobs — do not leave orphaned processes running after verification).

**Do NOT touch:** no files change in this step.

**Verify:** all four processes bind successfully and stay running; no port-collision error in any
process's stdout/stderr.

## Scope Guards

- Do not add `StaticFiles(`, `.mount(`, or any static-file-serving code to
  `src/api/agent_ops_dashboard/main.py`. The mount lives exclusively in the new
  `src/api/agent_ops_dashboard/serve.py`.
- Do not modify `src/api/agent_ops_dashboard/ingest.py` or `models.py` — owned by
  `AGENTOPS-DASHBOARD-BACKEND` (DONE), Out of Scope for this ticket.
- Do not modify any file under `dashboard-frontend/src/**` (views, components, `api.ts`, `App.tsx`)
  — owned by sibling tickets (`AGENTOPS-TICKETS-VIEW`, `-ACTIVITY-GANTT`, `-REPLAY-TIMELINE`), all
  DONE.
- Do not modify `dashboard-frontend/vite.config.ts` — the `8471` dev-proxy default already matches
  `dashboard-dev`'s chosen backend port (Step 3); no edit is needed or in scope.
- Do not redefine, reorder, or shadow the existing `install`, `install-py`, `install-fe`, `build`,
  `dev`, `dev-backend`, `dev-frontend`, `serve`, `serve-only`, `clean` Makefile targets. New targets
  use the `dashboard-*` prefix exclusively.
- Do not modify `docker-compose.yml` — explicitly Out of Scope.
- Do not add a new subcommand to `src/cli/entry.py`'s argparse parser, and do not otherwise edit
  `src/cli/entry.py` — the dashboard's serving process is a standalone module
  (`python3 -m src.api.agent_ops_dashboard.serve`), mirroring only `entry.py`'s `--host`/`--port`
  flag *naming convention*, not its subcommand structure.
- Do not add any frontend CI job to `.github/workflows/test.yml` — explicitly Out of Scope.
- Do not widen the default bind host beyond `127.0.0.1` anywhere in this ticket's new code —
  `dashboard-serve`'s default host is `127.0.0.1`, matching `src/cli/entry.py:23`'s own default and
  `PROPOSAL.md` §3's local-only deployment decision.
- Do not edit `docs/parity_ledger/infrastructure.yaml`'s `INFRA-275` entry — it explicitly excludes
  this ticket's scope in its own `support_boundary` text. A new `INFRA-276` entry is added later by
  `parity-updater`, outside this plan's steps.

## Dependency Map

- Step 1 (serve module) has no dependency on other steps — it can be written and manually
  sanity-checked first.
- Step 2 (serve module tests) depends on Step 1 — the tests exercise `build_app`, `_build_parser`,
  and `main` as defined there.
- Step 3 (Makefile targets) has no code dependency on Steps 1–2, but `dashboard-serve`'s recipe body
  (`python3 -m src.api.agent_ops_dashboard.serve`) references the module name from Step 1, so Step 3
  should land after Step 1 exists (ordering, not a hard test dependency).
- Step 4 (Makefile tests) depends on Step 3 — it asserts against the exact target/recipe text Step 3
  writes.
- Step 5 (anti-drift regression guard) depends on Steps 1–4 all being complete — it is the
  integration checkpoint across the whole change.
- Step 6 (manual port verification) depends on Step 3 (`dashboard-serve` must exist and depend on
  `dashboard-build`) and should run last, after Step 5's automated suite is green.

## Acceptance Criteria Map

| AC from ticket | Implemented by step(s) | Verified by test |
|---|---|---|
| AC #1 — `make dashboard-install/-build/-dev/-serve` exist as new `.PHONY` targets, no shadowing of existing targets | Step 3 | `tests/tools/test_dashboard_makefile_targets.py::test_dashboard_targets_exist_and_are_phony`, `::test_existing_targets_unmodified` |
| AC #2 — `make dashboard-serve` starts a single foreground process mounting the pre-built static SPA via FastAPI `StaticFiles`, port 8420 default, `--port`-configurable | Step 1, Step 3 | `tests/tools/test_agent_ops_dashboard_serve.py::test_serve_app_exposes_same_five_routes_as_main_app`, `::test_serve_app_returns_index_html_for_spa_root`, `::test_serve_argparse_port_and_host_defaults` |
| AC #3 — `make dashboard-build` runs `vite build` producing the static asset directory `dashboard-serve` mounts | Step 3, Step 1 (`build_app`'s `dist_dir` argument) | `tests/tools/test_agent_ops_dashboard_serve.py::test_serve_app_raises_clear_error_when_dist_dir_missing` (proves the dependency is real, not silently ignored); manual `make dashboard-build` run in Step 3 |
| AC #4 — Node/npm invoked only during `dashboard-install`/`-build`/`-dev`, never at `dashboard-serve` runtime | Step 1 (module has zero npm/node references), Step 3 (Makefile recipe separation) | `tests/tools/test_agent_ops_dashboard_serve.py::test_serve_module_has_no_node_npm_invocation`, `tests/tools/test_dashboard_makefile_targets.py::test_dashboard_serve_recipe_has_no_npm_or_node` |
| AC #5 — `make dashboard-serve` alongside `make serve`/`make dev-frontend`/`make docs-serve` has no port collision | Step 3 (distinct port 8420), Step 6 (manual verification) | Manual process check in Step 6 (no automated test per `test_plan.md`) |

## Anti-Drift Notes

- `test_main_mounts_no_static_files` (`tests/tools/test_agent_ops_dashboard_api_boundary.py:61-67`)
  is the single hardest constraint in this ticket — it is not this ticket's test to edit, and the
  most naive implementation (adding `app.mount(...)` directly inside `main.py`) fails it immediately.
  Step 1's design (separate `FastAPI()` instance, `include_router` instead of mutating `main_app`,
  no import-time app construction) satisfies it structurally, not by coincidence — do not "simplify"
  Step 1 by mounting `StaticFiles` onto the imported `main_app` object directly, even inside a
  function — that still risks the same object being imported and inspected by other tests with a
  `Mount` route attached if the function is ever called before those tests run.
- `test_agent_ops_dashboard_module_has_no_write_path`
  (`tests/tools/test_agent_ops_dashboard_api_boundary.py:70-79`) globs **every** `.py` file in
  `src/api/agent_ops_dashboard/`, so the new `serve.py` is automatically in its scope the moment it
  is created — it does not need to be added to any allowlist, but its source must never call
  `.write_text(`, `.write_bytes(`, or `.open(` as an attribute call. `uvicorn.run(...)` and
  `StaticFiles(...)` do not trigger this (they are not attribute calls named `open`/`write_text`/
  `write_bytes` in this module's own AST), but be aware this guard exists and would fire if the
  module's own code ever gains a stray `Path(...).open(...)` call.
- `dashboard-frontend/vite.config.ts`'s `8471` dev-proxy default and `dashboard-serve`'s `8420`
  production port are two intentionally different values for two different processes
  (`dashboard-dev`'s live-reload backend vs. `dashboard-serve`'s static-SPA production server) — do
  not "fix" `8471` to match `8420`, and do not edit `vite.config.ts` at all; Step 3 makes `8471` a
  live, correct value by binding `dashboard-dev`'s backend to it, which is the resolution this plan
  chose.
- `INFRA-275` (`docs/parity_ledger/infrastructure.yaml`) must remain byte-unmodified through every
  step of this plan — its own `support_boundary` text already excludes this ticket's scope. Adding
  `INFRA-276` happens after this plan's steps are complete, via `parity-updater`, not as a plan step
  here.
- `docker-compose.yml` must remain byte-unmodified — no automated test enforces this; confirm via
  `git diff --stat docker-compose.yml` being empty at Verify.
