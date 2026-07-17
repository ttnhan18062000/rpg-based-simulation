---
status: active
layer: observability
authority: P1
audience: agent
tags: [documentation, observability, api-design]
---

# Agent Ops Dashboard Contract

## Purpose

The Agent Ops Dashboard backend (`src/api/agent_ops_dashboard/main.py`) is a
standalone FastAPI app — not mounted on `src/api/server.py`, the main
simulation API — exposing read-only, typed projections over `tickets/**` and
`agent-monitoring/{runs,events,tools}.jsonl` for the dashboard SPA. It never
touches `AuthoritativeState` or the tick loop; it is a separate product on a
separate port. Content here reflects the shipped state as of
TCK-20260717-AGENTOPS-DASHBOARD-DOCS — re-verify against source before relying
on exact behavior after any of the five source tickets' code changes again.

## Contract

### Backend routes (`main.py`)

| Route | Returns | Params | Backing |
|---|---|---|---|
| `GET /api/tickets` | `List[TicketSummary]` | `tier`, `layer`, `status`, `priority` (single-value); `tag` (repeatable); `lifecycle`, `q`, `sort` (default `date_desc`) | `DashboardCache.get_tickets` |
| `GET /api/runs` | `List[RunSummary]` | `limit` (1-100, default 50), `offset`, `status`, `workflow`, `since` (ISO string, compared lexically, never parsed to `datetime`) | `DashboardCache.get_runs` |
| `GET /api/runs/{run_id}` | `RunDetail`, 404 on miss | — | `DashboardCache.get_run` |
| `GET /api/runs/{run_id}/timeline` | `RunTimeline`, 404 on miss | — | `DashboardCache.get_timeline` |
| `GET /api/health` | `HealthStatus` | — | `DashboardCache.get_health` |

Every route declares `response_model=`; no raw dict or domain payload is ever
returned (`models.py`'s Pydantic models are the only shapes crossing the route
boundary).

### Response models (`models.py`)

`RunMatchSummary`, `TicketSummary` (`status` = frontmatter doc-lifecycle
field, always present; `workflow_status` = the ticket body's `## Status`
section, nullable — two distinct fields, never conflated), `RawToolCall`
(no `phase`/`agent` field at all — absent from the type, not merely
nullable), `FileTouch`, `TimelineEntry` (has its own `phase`/`agent` fields,
both nullable — distinct from `RawToolCall`), `RunSummary`, `RunDetail`
(extends `RunSummary` with `ticket_title`, `ticket_lifecycle_state`),
`RunTimeline`, `HealthStatus` (`status` field is hardcoded `"ok"`, never
derived from `unparsed_lines` counts).

### Ingest / cache (`ingest.py`)

All file reads over `tickets/**` and `agent-monitoring/*.jsonl` live in this
module — `main.py` never reads a file directly. It reuses, rather than
reimplements:
- `tools/validate_frontmatter.py`'s `extract_frontmatter` for ticket
  frontmatter.
- `tools/generate_registry.py`'s `parse_body_section`/`parse_h1_title`/
  `_strip_frontmatter` for ticket body-section fields.
- `tools/agent-monitoring/validate.py`'s tolerant `load_jsonl` (skips
  unparseable lines, continues) and its legacy status allowlists.

`DashboardCache` holds a single `threading.RLock` guarding every public
method (`get_tickets`, `get_runs`, `get_run`, `get_timeline`, `get_health`),
matching `src/api/read_model_cache.py`'s `ReadModelCache` pattern — not the
swap-based build-outside-lock alternative. `_maybe_rebuild`/`_rebuild`
re-run the full parse+join+inference pipeline under that same lock whenever
any source `mtime` changes.

`build_matching_runs` returns **every** `runs.jsonl` row matching a
`ticket_id`, sorted `start_ts` descending (rows without a `start_ts` sort
last) — never collapsed to a single match, since a ticket can legitimately
have multiple runs (retries/re-runs).

`compute_inferred_active` implements the `ACTIVE_WINDOW_MINUTES = 10`
heuristic: a `run_id` present in `tools.jsonl` but absent from the
`runs.jsonl`-derived `runs_by_id` map, whose most recent tool-call timestamp
falls within the window, is `is_inferred_active=True`. This set is
recomputed fresh on every rebuild, never carried over from a prior snapshot,
so a run that completes falls out of it on the very next rebuild.

`get_tickets`'s filtering is AND across `tier`/`layer`/`status`
(= `workflow_status`)/`priority`, OR within the `tags` selection (set
intersection). Sorting is date-only (`date_asc`/`date_desc`) — there is no
server-side sort support for tier/layer/status/priority/tag; the shipped
`TicketsView.tsx` compensates with a client-side re-order for those columns.

### Frontend SPA structure (`dashboard-frontend/src/`)

- `App.tsx` — top-level view-switch state (`'activity' | 'tickets' | 'replay'`),
  no router library; owns `selectedRunId`, wired to each view's run-selection
  callback so a Gantt-row or Tickets-row click navigates to Replay.
- `api.ts` — TypeScript interfaces mirroring `models.py` field-for-field, plus
  typed fetch helpers (`fetchTickets`, `fetchRuns`, `fetchRunTimeline`,
  `fetchAllRunsSince`) and `useRunsPolling`, a polling hook that
  offset-loops `fetchAllRunsSince` to guard against `GET /api/runs`'s
  per-page result cap.
- `views/RecentActivityGantt.tsx` — default landing view; composes
  `useRunsPolling` with `GanttBar`/`Legend`; tracks an active→completed
  settle transition so a run's bar style change is not an instant cut.
- `views/ReplayTimelineView.tsx` — one fetch per run selection (no
  independent polling loop); renders phase-timeline segments from the
  fetched entries in order; the live-tail caption is unconditional, never
  derived from a field check (there is no `phase`/`agent` field on
  `RawToolCall` to check).
- `views/TicketsView.tsx` — fetch-and-render table over `GET /api/tickets`;
  filter changes go through the backend query params (never re-filtered
  client-side); non-date column sort is a client-side re-order over the
  already-fetched array, since the backend `sort` param is date-only.
- `components/GanttBar.tsx` — `classifyFinalStatus` buckets `DONE`→green,
  any `*_BLOCKED`/`*_FAILED`/`CONFLICTS_DETECTED`→red, else neutral gray; the
  inferred-active and authoritative-completed render branches share no CSS
  class tokens.
- `components/Legend.tsx` — reuses `GanttBar`'s status-bucket class map so
  the legend and bars can never visually diverge.
- `components/PlaybackScrubber.tsx` — takes a bare integer index range;
  imports no types from `api.ts` and has no knowledge of
  `RunTimeline`/`TimelineEntry`, so "scrub never fetches" is structural.

## Architecture Law

- **`main.py` never gains a static-file mount.** `serve.py`'s `build_app`
  constructs a *separate* `FastAPI()` instance, copies `main.py`'s routes
  onto it via `include_router` (a copy, never a mutation of `main.app`), and
  mounts `StaticFiles` only on that new instance. `main.py`'s own `app`
  object must never contain a `StaticFiles(`/`.mount(` reference. Guarded by
  `test_main_mounts_no_static_files`
  (`tests/tools/test_agent_ops_dashboard_api_boundary.py`).
- **Port allocation** (five distinct values, no collisions): `8000` — main
  simulation API's `make serve`. `8420` — `dashboard-serve` production
  (`serve.py`'s `DEFAULT_PORT`). `8471` — `dashboard-dev`'s backend half
  (`--reload`). `5174` — `dashboard-frontend`'s Vite dev server
  (`vite.config.ts`'s `server.port`). `3000` — Docusaurus `docs-serve`.
  `5173` is `frontend/`'s unrelated main-app dev port, listed only to
  disambiguate it from `5174` — never the dashboard's own port.
- **`dashboard-serve` never invokes Node or npm at runtime.** Its Makefile
  recipe is exactly `python3 -m src.api.agent_ops_dashboard.serve`; only
  `dashboard-install`, `dashboard-build`, and `dashboard-dev` invoke `npm`.
  Guarded by `test_serve_module_has_no_node_npm_invocation`
  (`tests/tools/test_agent_ops_dashboard_serve.py`) and
  `test_dashboard_serve_recipe_has_no_npm_or_node`
  (`tests/tools/test_dashboard_makefile_targets.py`).

## Known Limitation

`RawToolCall` has no `phase` or `agent` field at all — this is a genuine gap
in the type, not a nullable field. Live (in-progress) tool-call rows
therefore render an unconditional "phase unknown — run still in progress"
caption in `ReplayTimelineView.tsx` rather than any derived or guessed value.
Tracked separately as `MONITORING_INSTRUMENTATION_GAP`; not addressed by this
doc or the tickets it describes.

## Related

- Parity ledger: `docs/parity_ledger/infrastructure.yaml`, INFRA-275 (backend
  routes, ingest, cache, ticket-run join, inferred-active heuristic).
- Parity ledger: `docs/parity_ledger/infrastructure.yaml`, INFRA-276
  (`serve.py` design, Makefile targets).
- `docs/guides/agent_ops_dashboard.md` — user/developer guide: build/run/serve
  commands and a usage walkthrough for each view.
