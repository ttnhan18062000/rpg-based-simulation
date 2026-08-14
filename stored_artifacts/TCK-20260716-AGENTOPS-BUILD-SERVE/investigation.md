---
status: historical
layer: observability
authority: P2
audience: agent
ticket_id: TCK-20260716-AGENTOPS-BUILD-SERVE
artifact_type: investigation
tags: [observability, agent-monitoring]
---

# Investigation — TCK-20260716-AGENTOPS-BUILD-SERVE

## Current Behavior

**Makefile (`Makefile:1-340`) — the pattern this ticket must mirror, not redefine.**
- `.PHONY` line (`Makefile:1`) is one long space-separated list — the four new targets
  (`dashboard-install dashboard-build dashboard-dev dashboard-serve`) must be appended to this
  existing list, not declared in a second `.PHONY:` line.
- Existing full-stack shape: `install` → `install-py` + `install-fe` (`Makefile:14-20`); `build`
  (`Makefile:24-25`, `cd frontend && npm run build`); `dev` (`Makefile:29-35`, backend + Vite dev
  server concurrently via `trap 'kill 0' INT` + `&`/`wait`); `dev-backend`/`dev-frontend`
  (`Makefile:37-41`, single-process variants); `serve` (`Makefile:45-46`, depends on `build` then
  starts the Python process); `serve-only` (`Makefile:48-49`, assumes already built, no `build`
  dependency). `clean` (`Makefile:336-339`) removes `frontend/dist` and `node_modules/.tmp`.
- `python3 -m src serve --port 8000` (`Makefile:38,46,49,66`) is the exact CLI convention any new
  `--port`-flag tooling should mirror in flag naming (though this ticket's process is a separate
  script, not a new `src.cli.entry` subcommand — see Risks #6).

**`src/cli/entry.py` — the `--port` flag convention, not a file this ticket should modify.**
- `srv.add_argument("--port", type=int, default=8000)` (`entry.py:24`), `--host` defaults to
  `"127.0.0.1"` (`entry.py:23`, i.e. localhost-only by default, not `0.0.0.0`).
- `_run_serve` (`entry.py:257-279`) is the exact "build profile, `uvicorn.run(app, host=..., 
  port=...)`" shape to mirror for the new dashboard-serve entry point's own `uvicorn.run(...)` call
  — same `uvicorn` package, same `--host`/`--port` argparse naming, same `logger.info(f"Starting
  ... on {host}:{port}")` pattern (`entry.py:278`). Nothing here needs editing; `src/api/server.py`
  and `src.cli.entry`'s `serve` subcommand are a different product (the simulation engine), and
  `src/api/agent_ops_dashboard/main.py`'s own docstring (below) already states this dashboard is
  "a separate product/port."

**`docker-compose.yml` — confirmed no dashboard service exists, and this ticket must not add one**
(Out of Scope: "Any Docker Compose service changes"). Ports already claimed by this file:
`8000` (backend, `BACKEND_PORT`), `6379` (redis), `5672`/`15672` (rabbitmq), `8080` (frontend,
`FRONTEND_PORT`), `9090` (prometheus), `3000` (grafana, `GRAFANA_PORT` — same default as
`docs-serve`'s Docusaurus port, a pre-existing, unrelated port overlap only material if both
`docker-up` and `docs-serve` run simultaneously; irrelevant to this ticket's AC #5, which names
only `serve`/`dev-frontend`/`docs-serve`, not any Docker service).

**`src/api/agent_ops_dashboard/main.py` (23 lines, `TCK-20260716-AGENTOPS-DASHBOARD-BACKEND`,
DONE) — the FastAPI app this ticket must mount static files onto, from outside this file.**
- Module docstring (`main.py:1-8`) states explicitly: *"Not mounted on `src/api/server.py` (the
  main simulation API) — a separate product/port... No StaticFiles mount here (owned by the
  sibling AGENTOPS-BUILD-SERVE ticket)."* This is a forward-looking design note this ticket
  fulfills — but see the hard test constraint below on exactly *how*.
- `app = FastAPI(title="Agent Ops Dashboard API")` (`main.py:24`), five typed routes
  (`/api/tickets` L29, `/api/runs` L52, `/api/runs/{run_id}` L63, `/api/runs/{run_id}/timeline`
  L71, `/api/health` L79), all `response_model=`-typed Pydantic schemas — matches the repo's
  "never expose raw domain models" API rule already.

**CRITICAL constraint confirmed by direct read — an existing regression test forbids mounting
`StaticFiles` inside `main.py` itself:**
`tests/tools/test_agent_ops_dashboard_api_boundary.py::test_main_mounts_no_static_files`
(`test_agent_ops_dashboard_api_boundary.py:64-70`):
```python
def test_main_mounts_no_static_files():
    from starlette.routing import Mount
    source = (_SRC_ROOT / "main.py").read_text(encoding="utf-8")
    assert "StaticFiles(" not in source
    assert ".mount(" not in source
    assert not any(isinstance(route, Mount) for route in main.app.routes)
```
This test is part of this ticket's own regression surface (must stay green) and directly forbids
the most naive implementation (`app.mount("/", StaticFiles(...))` added to `main.py`'s module
body). The StaticFiles mount must live in a **new, separate module** (e.g.
`src/api/agent_ops_dashboard/serve.py`) that either builds its own `FastAPI()` instance and
includes `main.app`'s routes, or performs the mount against `main.app` only inside a function that
is never executed at import time (so importing `main` in isolation — which is exactly what this
test and every other `tests/tools/test_agent_ops_dashboard_*` file does — never sees a `Mount`
route or a `.mount(`/`StaticFiles(` substring in `main.py`'s own source). `git grep -n
"StaticFiles\|\.mount("` across `src/` confirms zero matches today — the ticket's own Assumption
is still true, and the reason it is a "new implementation, not a copy of proven code" is now
sharpened by this specific test boundary, not just the absence of a StaticFiles precedent.

**`dashboard-frontend/` — confirmed build/dev/test tooling, already DONE by sibling tickets.**
- `package.json` scripts (`dashboard-frontend/package.json:6-11`): `dev` (`vite`), `build` (`tsc -b
  && vite build`), `test` (`vitest run`), `preview` (`vite preview`) — no `lint` script defined
  here (unlike `frontend/package.json`, which has one), consistent with "Adding frontend CI
  coverage" being Out of Scope for this ticket too.
- `vite.config.ts:1-32`: dev server `port: 5174` (distinct from `frontend/`'s Vite default 5173,
  already non-colliding). `server.proxy['/api']` targets
  `process.env.VITE_DASHBOARD_API_TARGET ?? 'http://127.0.0.1:8471'` (`vite.config.ts:9`) — **the
  inline comment (`vite.config.ts:6-8`) explicitly names this ticket** ("The dashboard backend's
  confirmed serve port (8420) is AGENTOPS-BUILD-SERVE's to wire up; this dev-only default is a
  placeholder"). `8471` does not match the confirmed `8420` serve port — see Risks #2, this is an
  unresolved discrepancy the plan must address, not silently ignore.
- No `build.outDir` override anywhere in `vite.config.ts` — Vite's documented default output
  directory is `dist/` (relative to the project root, i.e. `dashboard-frontend/dist/`), consistent
  with `dashboard-frontend/.gitignore:11` already ignoring `dist`/`dist-ssr`. `dashboard-build`'s
  `vite build` therefore produces `dashboard-frontend/dist/` without any new Vite config change.
- `dashboard-frontend/src/api.ts` — every fetch call uses a **relative** path (`fetch('/api/tickets?...')`,
  `fetch('/api/runs?...')`, `fetch('/api/runs/${runId}/timeline')`) — confirms the built SPA
  requires zero base-URL/CORS configuration to work once served same-origin by the FastAPI
  process this ticket builds; no frontend source changes are needed for AC #2/#3 to work, only the
  serving wrapper.

**`docs/parity_ledger/infrastructure.yaml` — `INFRA-275` explicitly excludes this ticket's scope.**
`INFRA-275` (`infrastructure.yaml:4478-4527`, `status: verified`, `priority: P2`) covers the
Dashboard backend's five typed routes, cache/lock pattern, and join logic. Its own
`support_boundary` field (`infrastructure.yaml:4524-4527`) states verbatim: *"Excludes frontend,
build/serve tooling (AGENTOPS-BUILD-SERVE), the live phase/agent null-labeling gap... and
agent-monitoring retention/rotation."* This is a positive confirmation that `INFRA-275` should
**not** be edited by this ticket — a **new** parity ledger entry is needed (see Parity Ledger
Overlap). `INFRA-275` is also the highest-numbered `INFRA-*` entry in the file as of this
investigation, so the next entry is `INFRA-276`.

## Mechanics / Engine Constraints

None apply. This is build/deployment tooling over an already-built, already-parity-tracked FastAPI
backend and a pre-built static SPA — it never touches `AuthoritativeState`, the tick loop, or any
`docs/mechanics/`-governed formula. Same conclusion every sibling ticket in this batch
(`AGENTOPS-DASHBOARD-BACKEND`, `-ACTIVITY-GANTT`, `-REPLAY-TIMELINE`, `-TICKETS-VIEW`) already
reached independently. The one repo-wide architecture rule that *does* apply — "API/routes present
shaped read models through presenters/schemas, not raw domain objects" — is already satisfied by
`main.py`'s existing typed routes; this ticket's job is purely to make those routes and the static
SPA reachable from one process, not to change what they return.

## Parity Ledger Overlap

- **`INFRA-275`** (`docs/parity_ledger/infrastructure.yaml:4478`) — `status: verified`, `priority:
  P2`. Explicitly excludes this ticket's scope in its own `support_boundary` text (quoted above).
  **Do not edit `INFRA-275`.**
- **No existing entry covers build/serve tooling for this dashboard.** A new entry —
  `INFRA-276` (next sequential ID) — must be added once implementation lands (this is
  `parity-updater`'s job post-implementation, not this investigation's), documenting: the new
  Makefile targets, the new serve-entry-point module and its StaticFiles-mount location (proving
  it is *not* inside `main.py`, mirroring how `INFRA-275`'s own evidence cites
  `test_main_mounts_no_static_files` implicitly via the boundary test file), and the port/`--port`
  flag contract.
- **No P0 entries anywhere in this area** — `INFRA-275` is P2, and no P0 entry exists for
  build/serve tooling — so no `test_path` gate is mandatory for ticket close, but the new entry
  should still cite real `test_path` values (matching every other `INFRA-27x` entry's convention)
  once tests exist.

## Prior Work

- `TCK-20260716-AGENTOPS-DASHBOARD-BACKEND` (done) — built `main.py`/`ingest.py`/`models.py`,
  deliberately deferred the StaticFiles mount and added the regression test
  (`test_main_mounts_no_static_files`) that now constrains this ticket's implementation shape.
  Its own `plan.md:300` states verbatim: *"No `Makefile` changes, no
  `dashboard-install`/`dashboard-build`/`dashboard-dev`/`dashboard-serve`"* — confirms this ticket
  is the sole owner of that surface, not a continuation of already-started work.
- `TCK-20260716-AGENTOPS-ACTIVITY-GANTT`, `-REPLAY-TIMELINE`, `-TICKETS-VIEW` (all done) — built
  the `dashboard-frontend/` scaffold and all three views this ticket's `dashboard-build`/
  `dashboard-serve` targets package. None of the three touched `Makefile`, `docker-compose.yml`, or
  any serving/mounting code (confirmed by `grep -rn "dashboard-install\|dashboard-build\|dashboard-serve"`
  across `tickets/`/`docs/`/`stored_artifacts/` returning only doc references, no implementation
  diffs) — this ticket has no in-repo code precedent for the specific StaticFiles-mount pattern,
  only the design-doc guidance in `PROPOSAL.md` §5b / `IMPLEMENTATION_CONTEXT.md` §4 and the
  Makefile's own `install`/`build`/`dev`/`serve` shape to mirror structurally.
- `experiments/agent_ops_dashboard/PROPOSAL.md` §5b and `IMPLEMENTATION_CONTEXT.md` §4 — the
  design-phase investigation this ticket's own ACs were lifted from verbatim (port `8420`
  confirmed free on the dev machine, target Makefile shape, "plain foreground process, not
  Docker" decision, `tests/tools/` as the eventual backend test location). No new investigation
  needed to re-derive these — already evidence-backed in that document.
- No prior ticket in this repo has added a `StaticFiles` mount anywhere (confirmed zero
  `StaticFiles`/`.mount(` matches across all of `src/` before this ticket) — genuinely new
  implementation territory for this codebase, not a pattern to copy from elsewhere in `src/api/`.

## Risks and Open Questions

1. **(Blocking, must be pinned down before implementation) The StaticFiles mount cannot live
   inside `main.py`.** `test_main_mounts_no_static_files` is an existing, unmodifiable-by-this-
   ticket regression test (`main.py`/`ingest.py`/`models.py` are Out of Scope per this ticket's
   own boundaries — they belong to `AGENTOPS-DASHBOARD-BACKEND`). The plan must specify a concrete
   new module (e.g. `src/api/agent_ops_dashboard/serve.py`) that either (a) constructs a *new*
   `FastAPI()` instance, includes `main.app`'s routes onto it, and mounts `StaticFiles` on that new
   instance, or (b) mounts `StaticFiles` directly onto the imported `main.app` object but only
   inside a `run()`/`main()` function gated behind `if __name__ == "__main__":`, never at module
   import time — so that any test importing `main` (or even importing the new `serve` module
   without invoking its entry function) still observes zero `Mount` routes on `main.app`. Option
   (b) mutates a shared singleton at runtime, which is a real design smell even though it would
   technically pass the existing test; option (a) is cleaner and does not depend on import-time
   ordering. Not resolved here — the plan must state which.
2. **`vite.config.ts`'s dev-proxy default target (`8471`) does not match the confirmed production
   serve port (`8420`).** The comment at `vite.config.ts:6-8` says `8420` is this ticket's to
   "wire up," but the actual default fallback in the proxy config is a different, unexplained
   number (`8471`). Two live options: (a) leave `8471` as an intentionally-distinct dev-only
   placeholder (a developer running `dashboard-dev` must set
   `VITE_DASHBOARD_API_TARGET=http://127.0.0.1:8420` or whatever port the dev-mode backend
   actually runs on), or (b) have `dashboard-dev`'s backend process bind to `8420` by default so
   the existing `8471` fallback is simply dead code that should be corrected to `8420` for
   consistency. This ticket's AC only pins `dashboard-serve`'s port (`8420`, `--port`-configurable)
   — it does not specify what port `dashboard-dev`'s backend half should use. Flagging as a real
   open decision, not assumed either way.
3. **Whether `dashboard-serve` auto-triggers `dashboard-build` (mirroring `serve: build`) or
   assumes a pre-built `dist/` (mirroring `serve-only`) is not explicit in the ticket's Scope/AC.**
   AC #4 ("Node/npm is invoked only during dashboard-install/dashboard-build/dashboard-dev, never
   at dashboard-serve *runtime*") is satisfiable either way — a Make dependency edge
   (`dashboard-serve: dashboard-build`) runs `npm` during the `make` invocation, before the Python
   process starts, which is not "at runtime" of that process. The plan should state explicitly
   which shape is chosen (a `serve`-style auto-build dependency, or a `serve-only`-style
   already-built assumption with a clear failure message if `dist/` is missing) rather than leaving
   it to implementer discretion.
4. **Frontend has zero CI coverage today (inherited gap) — confirmed still true**, no
  `.github/workflows/test.yml` job runs anything under `dashboard-frontend/` or `frontend/`. This
  ticket's own Out of Scope explicitly excludes "Adding frontend CI coverage," so this is a
  confirmed non-issue for this ticket, not a new gap it introduces.
5. **This ticket has no independent value until the other four batch tickets exist** (per the
   ticket's own Assumptions) — confirmed true and now moot: all four (`DASHBOARD-BACKEND`,
   `ACTIVITY-GANTT`, `REPLAY-TIMELINE`, `TICKETS-VIEW`) are DONE as of this investigation, so this
   ticket is unblocked.
6. **Whether the new serve entry point should be invoked as a `python3 -m
   src.api.agent_ops_dashboard.serve --port 8420`-style module, or a plain script path, is not
   specified by the ticket.** Given `main.py`'s own docstring states this dashboard is "a separate
   product/port" from the simulation engine's `src.cli.entry` `serve` subcommand, and this ticket's
   Related Code Areas lists `src/cli/entry.py` only as a naming/flag-convention reference (not a
   file whose subparsers should gain a new `dashboard-serve` subcommand), the strong implication is
   a standalone module under `src/api/agent_ops_dashboard/`, not a new `src.cli.entry` subcommand.
   The plan should state this explicitly so the implementer doesn't default to bolting a new
   subparser onto `entry.py` instead.

## Anti-Drift Hazards

- **Do not add `StaticFiles`/`.mount(` to `src/api/agent_ops_dashboard/main.py`** — breaks
  `test_main_mounts_no_static_files` immediately and violates that file's own documented
  API-only/independently-testable contract. The mount belongs in a new sibling module.
- **Do not modify `src/api/agent_ops_dashboard/ingest.py` or `models.py`** — both are Out of Scope,
  owned by `AGENTOPS-DASHBOARD-BACKEND` (already DONE).
- **Do not modify `dashboard-frontend/src/**`** (views, components, `api.ts`, `App.tsx`) — the
  three UI views are DONE and owned by sibling tickets; this ticket only builds/serves their
  output.
- **Do not redefine or shadow the existing `install`/`install-py`/`install-fe`/`build`/`dev`/
  `dev-backend`/`dev-frontend`/`serve`/`serve-only`/`clean` Makefile targets** — new targets must
  use the distinct `dashboard-*` prefix throughout, appended to (not replacing) the existing
  `.PHONY` list.
- **Do not modify `docker-compose.yml`** — explicitly Out of Scope ("Any Docker Compose service
  changes").
- **Do not add a new subcommand to `src/cli/entry.py`'s argparse parser** — mirror its `--host`/
  `--port` flag *naming convention* only (per Risk #6); the dashboard's serving process is a
  separate script/module, not a `src.cli.entry` subcommand, consistent with `main.py`'s own
  "separate product/port" framing.
- **Do not add frontend CI wiring to `.github/workflows/test.yml`** — explicitly Out of Scope.
- **Default host must stay `127.0.0.1` (localhost-only), not `0.0.0.0`** — matches both
  `src/cli/entry.py`'s own default and `PROPOSAL.md` §3's explicit "Deployment: Local-only...
  binds to localhost" decision; do not silently widen the bind address while adding the `--port`
  flag.
- **Do not edit `docs/parity_ledger/infrastructure.yaml`'s `INFRA-275` entry** — it explicitly
  excludes this ticket's scope in its own text; add a new `INFRA-276` entry instead (post-
  implementation, via `parity-updater`).
