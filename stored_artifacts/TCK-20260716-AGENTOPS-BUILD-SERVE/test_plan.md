---
status: historical
layer: observability
authority: P2
audience: agent
ticket_id: TCK-20260716-AGENTOPS-BUILD-SERVE
artifact_type: test_plan
tags: [observability, agent-monitoring]
---

# Test Plan — TCK-20260716-AGENTOPS-BUILD-SERVE

## Regression Surface

This ticket adds a new Python serving module (not editing `main.py`/`ingest.py`/`models.py`) plus
Makefile targets. No `dashboard-frontend/src/**` source changes are expected (per investigation.md,
`api.ts` already uses relative fetch paths that work same-origin). All existing suites below must
stay green, unmodified.

- unit / integration (backend, must stay green, unmodified):
  - `tests/tools/test_agent_ops_dashboard_api_boundary.py` — **especially**
    `test_main_mounts_no_static_files` (the hard constraint this ticket's implementation must not
    violate — see investigation.md Risk #1), plus `test_all_five_routes_are_declared`,
    `test_typed_response_models_not_dict`, `test_agent_ops_dashboard_module_has_no_write_path`.
  - `tests/tools/test_agent_ops_dashboard_api.py`.
  - `tests/tools/test_agent_ops_dashboard_ingest.py`.
  - `tests/tools/test_agent_ops_dashboard_concurrency.py`.
  - `tests/tools/test_agent_ops_dashboard_frontend_api_surface.py` — directory-wide glob over
    `dashboard-frontend/src/**/*.{ts,tsx}`; must stay green since this ticket adds no frontend
    source files (sanity check only).
- architecture guard, must stay green (informational — does not scan
  `src/api/agent_ops_dashboard/` today, confirmed by reading its `_API_ROOTS` list; included as a
  sanity check that this ticket's new module under `src/api/agent_ops_dashboard/` does not need to
  be added to it, not because it currently exercises this ticket's surface):
  - `tests/architecture/test_api_read_model_guard.py`.
- frontend, must stay green unmodified (no UI changes in this ticket):
  - `dashboard-frontend/src/test/App.test.tsx`, `TicketsView.test.tsx`,
    `RecentActivityGantt.test.tsx`, `GanttBar.test.tsx`, `ReplayTimelineView.test.tsx`,
    `useRunsPolling.test.ts` — run via `cd dashboard-frontend && npm test` as a sanity check that
    packaging/build tooling changes did not somehow touch source; not expected to need any edits.

## New Tests Required

Per this ticket's Acceptance Criteria (`tickets/inprogress/TCK-20260716-AGENTOPS-BUILD-SERVE.md`).
All new backend tests are pytest, colocated under `tests/tools/` (the confirmed CI-gated location
for this dashboard's backend tests, per `.github/workflows/test.yml`'s "API / tools / logging"
job). A Makefile-source static guard needs no live process and can live alongside them.

- **`serve module never mutates main.app's route list at import time — StaticFiles mount lives
  outside main.py`**
  Category: architecture guard (unit)
  Verifies: AC #2's mounting mechanism, and directly protects investigation.md Risk #1's
  constraint. Imports the new serve module (e.g. `src.api.agent_ops_dashboard.serve`) at test
  collection time, then asserts (a) `main.py`'s own source still contains no `"StaticFiles("` or
  `".mount("` (duplicating `test_main_mounts_no_static_files`'s own check as a same-ticket
  guard, not relying solely on the sibling file), and (b) `main.app.routes` contains no
  `starlette.routing.Mount` instance even after the new module has been imported — proving the
  mount is not a module-level side effect against the shared `main.app` singleton.
  Location: `tests/tools/test_agent_ops_dashboard_serve.py`

- **`serve app exposes the same five typed API routes as main.app, unshadowed by the static mount`**
  Category: integration
  Verifies: AC #2/#3 — build the serve app (via a fixture repo root with a minimal fake `dist/`
  containing an `index.html`), drive it with `fastapi.testclient.TestClient`, and assert
  `GET /api/health` (or another cheap route) still returns the typed `HealthStatus` shape — proving
  the `/api/*` routes resolve correctly and are not shadowed by a catch-all StaticFiles mount
  registered before them.
  Location: `tests/tools/test_agent_ops_dashboard_serve.py`

- **`serve app returns the built index.html for the SPA's own root path`**
  Category: integration
  Verifies: AC #2 ("mounting the pre-built static SPA") — using the same fake-`dist/` fixture,
  assert `GET /` returns 200 with the fixture `index.html`'s content, proving the StaticFiles mount
  is wired to the directory `dashboard-build` produces.
  Location: `tests/tools/test_agent_ops_dashboard_serve.py`

- **`serve app raises a clear, actionable error when dist/ does not exist, not a silent 404-everything`**
  Category: unit / edge case
  Verifies: the documented dependency between `dashboard-build`'s output and `dashboard-serve`'s
  input (investigation.md Risk #3) — point the serve app builder at a repo root with no `dist/`
  directory and assert a clear exception/message is raised (naming the missing path and suggesting
  `make dashboard-build`), not a bare `RuntimeError` from `StaticFiles`'s own default
  directory-existence check with no repo-specific context, and not a silently-mounted empty
  filesystem that 404s every request without explanation.
  Location: `tests/tools/test_agent_ops_dashboard_serve.py`

- **`--port flag overrides the 8420 default; --host defaults to 127.0.0.1`**
  Category: unit
  Verifies: AC #2's "listening on port 8420 by default, configurable via a --port flag" — parse the
  new serve module's argparse parser with no args and assert `port == 8420`, `host == "127.0.0.1"`
  (per investigation.md's anti-drift hazard against widening the default bind address); parse with
  `["--port", "9001"]` and assert `port == 9001`.
  Location: `tests/tools/test_agent_ops_dashboard_serve.py`

- **`serve module contains no npm/node/subprocess-to-Node invocation`**
  Category: architecture guard (source-text scan)
  Verifies: AC #4's "Node/npm is invoked only during dashboard-install/dashboard-build/
  dashboard-dev, never at dashboard-serve runtime" — read the new serve module's source and assert
  no substring match for `"npm"`, `"node "`, or `subprocess`/`os.system` calls referencing either;
  the module's only job at runtime is `uvicorn.run(...)` over a pre-built directory.
  Location: `tests/tools/test_agent_ops_dashboard_serve.py`

- **`Makefile: new dashboard-* targets exist, are .PHONY, and do not alter the existing install/
  build/dev/serve/serve-only/clean recipes`**
  Category: architecture guard (static, source-text)
  Verifies: AC #1 — read `Makefile`'s raw text and assert: (a) `dashboard-install`,
  `dashboard-build`, `dashboard-dev`, `dashboard-serve` each appear as a target definition
  (`^dashboard-\w+:`) and are present in the `.PHONY:` line; (b) the exact recipe bodies of the
  pre-existing `install:`, `install-py:`, `install-fe:`, `build:`, `dev:`, `dev-backend:`,
  `dev-frontend:`, `serve:`, `serve-only:`, `clean:` targets are byte-identical to a fixed snapshot
  captured from this investigation (so the test fails loudly if any of them is edited/shadowed,
  rather than only checking the new targets exist).
  Location: `tests/tools/test_dashboard_makefile_targets.py`

- **`Makefile: dashboard-install/dashboard-build/dashboard-dev recipes invoke npm; dashboard-serve's
  recipe does not`**
  Category: architecture guard (static, source-text)
  Verifies: AC #4 at the Makefile-recipe level (complementary to the Python-source-text guard
  above, which covers the Python module itself) — extract each new target's recipe text and assert
  `npm`/`node`/`cd dashboard-frontend` appears in `dashboard-install`, `dashboard-build`, and
  `dashboard-dev`'s recipes, but not in `dashboard-serve`'s.
  Location: `tests/tools/test_dashboard_makefile_targets.py`

## Scoped Pytest Commands

```
pytest tests/tools/test_agent_ops_dashboard_serve.py tests/tools/test_dashboard_makefile_targets.py tests/tools/test_agent_ops_dashboard_api_boundary.py tests/tools/test_agent_ops_dashboard_api.py tests/tools/test_agent_ops_dashboard_ingest.py tests/tools/test_agent_ops_dashboard_concurrency.py tests/tools/test_agent_ops_dashboard_frontend_api_surface.py tests/architecture/test_api_read_model_guard.py -m "not slow"
```

Never: `pytest tests/`.

Frontend sanity command (no source changes expected, run to confirm):

```
cd dashboard-frontend && npm test
```

Manual/process-level verification (not pytest — AC #5 is a live port-collision check):

```
make serve &          # port 8000
make dev-frontend &    # port 5173
make docs-serve &      # port 3000
make dashboard-serve &  # port 8420 default
# confirm all four processes stay up with no bind-address errors, then stop them
```

## Anti-Drift Test Guards

1. **`test_main_mounts_no_static_files` (existing, `test_agent_ops_dashboard_api_boundary.py`)
   remains the primary backstop against the single most likely implementation mistake** — adding
   the mount directly to `main.py`. This ticket's own new guard (New Tests Required, first entry)
   is additive, not a replacement — both must pass.
2. **No Makefile target renaming/shadowing guard** (New Tests Required, Makefile byte-identical
   snapshot test) — catches an implementer "cleaning up" or reordering the existing `install`/
   `build`/`dev`/`serve` targets while adding the new ones, which AC #1 explicitly forbids.
3. **No Node/npm-at-runtime guard, at both the Python-module and Makefile-recipe level** — two
   separate tests (New Tests Required) rather than one, since AC #4's guarantee spans both layers:
   a clean `dashboard-serve` Makefile recipe that shells out to a Python module which itself
   secretly calls `subprocess.run(["npm", ...])` would pass a Makefile-only check but violate the
   AC's actual intent.
4. **No default bind-address widening guard** (`--host` defaults to `127.0.0.1`, not `0.0.0.0`) —
   protects `PROPOSAL.md` §3's explicit local-only deployment decision from silent drift during
   `--port`-flag implementation.
5. **`docs/parity_ledger/infrastructure.yaml`'s `INFRA-275` must remain byte-unmodified by this
   ticket** — its `support_boundary` already excludes this ticket's scope; if implementation work
   needs a parity ledger update, it must be a *new* entry (`INFRA-276`), not an edit to `INFRA-275`.
   No automated test enforces this (parity ledger changes are reviewed at Parity phase, not by
   pytest) — stated here so Verify/Parity does not silently accept an `INFRA-275` diff.
6. **`docker-compose.yml` must remain byte-unmodified** — no automated test; confirm via
   `git diff --stat docker-compose.yml` being empty at Verify, consistent with this ticket's hard
   Out-of-Scope guard.
