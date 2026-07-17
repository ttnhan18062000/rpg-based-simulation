---
status: active
layer: observability
authority: P1
audience: developer
tags: [documentation, observability, api-design]
---

# Agent Ops Dashboard

A read-only visual viewer over `tickets/` and `agent-monitoring/*.jsonl` — recent
run activity, per-run replay, and a filterable ticket table. It is purely
presentational: it never mutates `tickets/`, `agent-monitoring/`, or any
`AuthoritativeState`, and it is not itself a source of truth for anything it
displays. Written as of TCK-20260717-AGENTOPS-DASHBOARD-DOCS — commands,
ports, and behavior below reflect the shipped state at that point; re-check
against source if any of the five source tickets' code has changed since.

## What it is

Five prior tickets built this feature end to end: a standalone FastAPI backend
over the ticket corpus and agent-monitoring logs, a React/Vite single-page app
with three views, and build/serve tooling to package both into one process.
See `docs/observability/agent_ops_dashboard_contract.md` for the technical
reference (API contract, cache/ingest design, frontend structure, hard
constraints).

## Build / run / serve

| Command | What it does | Port(s) |
|---|---|---|
| `make dashboard-install` | `cd dashboard-frontend && npm install` | — |
| `make dashboard-build` | `cd dashboard-frontend && npm run build` | — |
| `make dashboard-dev` | Backend (`uvicorn src.api.agent_ops_dashboard.main:app --reload`) and the Vite dev server, concurrently | Backend `8471`, Vite dev server `5174` |
| `make dashboard-serve` | Depends on `dashboard-build`; single foreground process serving API + built SPA together | `8420` |

For disambiguation only (this guide does not cover these): the main
simulation API's own `make serve` runs on `8000`, and Docusaurus's
`make docs-serve` runs on `3000`. The main game-UI app's unrelated `make dev`
frontend runs on `5173` — not to be confused with the dashboard's own Vite dev
port, `5174`.

## Using the three views

The header nav switches between three views; there is no URL router, so
navigation state is local to the page session.

### Recent Activity Gantt

The default landing view. Shows recent runs as horizontal bars over a rolling
time window. Solid, color-coded bars represent authoritative `runs.jsonl`
rows (green = `DONE`, red = any `*_BLOCKED`/`*_FAILED`/`CONFLICTS_DETECTED`
status, gray = anything else). A visually distinct hatched fill marks
inferred-live runs — ones with recent `tools.jsonl` activity but no
`runs.jsonl` row yet, i.e. still in progress. When an inferred-live run
completes, its bar transitions to the solid authoritative style rather than
cutting over instantly. Clicking a row navigates to the Replay Timeline view
for that run.

### Replay Timeline

A scrubbable phase/tool-call playback for one run, plus a files-touched
panel. Selecting a run (via Gantt row click, or directly) fetches its full
timeline once; the playback scrubber itself never re-fetches — it only moves
through the already-loaded entries. For a run still in progress, any
tool-call activity beyond the last known phase is shown with the caption
"(phase unknown — run still in progress)" rather than a guessed phase or
agent name — see Known Limitation below.

### Tickets view

A filterable, sortable table over the ticket corpus. Filters are single-select
per dimension for tier/layer/status/priority, and multi-select for tags —
this matches the backend's actual query-parameter shape (each of the first
four accepts one value; only `tag` is repeatable). Filtering across
dimensions is AND (a ticket must match every active filter); filtering within
the tag selection is OR (a ticket matches if it has any selected tag).
Clicking the date column header re-sorts via the backend (the only
server-side sort dimension); clicking any other column header (tier, layer,
status, priority, tag) re-orders the already-fetched rows client-side — the
backend does not support server-side sorting on those dimensions. Each row
links to its matching run(s) in Replay Timeline.

## Known limitation

Live (in-progress) tool-call rows have no `phase` or `agent` label — the
underlying data type has no such fields at all for live entries, not merely
empty ones. The Replay Timeline view renders the honest
"phase unknown — run still in progress" caption for these rows unconditionally.
This is a known, tracked gap (`MONITORING_INSTRUMENTATION_GAP`), not something
this dashboard works around or guesses at.

## See also

- `docs/observability/agent_ops_dashboard_contract.md` — technical reference:
  API contract, cache/ingest design, frontend SPA structure, hard design
  constraints.
- `docs/parity_ledger/infrastructure.yaml` — see INFRA-275 (backend) and
  INFRA-276 (build/serve tooling) for the verified evidence trail.
