---
status: active
layer: observability
authority: P1
audience: agent
ticket_id: TCK-20260718-AGENTOPS-STATS-API
artifact_type: investigation
tags: []
---

# Investigation — TCK-20260718-AGENTOPS-STATS-API

## Current Behavior (file:line refs)

`src/api/agent_ops_dashboard/main.py` has 5 routes (`/api/tickets`, `/api/runs`,
`/api/runs/{run_id}`, `/api/runs/{run_id}/timeline`, `/api/health`), all
`@app.get(..., response_model=<TypedModel>)`, backed by `DashboardCache` methods that each open
`with self._lock:` first, call `self._maybe_rebuild()`, then read cached data. Simplest existing
pattern: `get_health()` (ingest.py:641-649) — no params, returns a model built from cache state
directly.

`DashboardCache.__init__`/`_rebuild()` (ingest.py:386-483): `_rebuild()` loads raw
`runs_all`/`events_all` lists via `load_jsonl_counted()`, then groups them into
`self._runs_by_id` (deduplicated — one primary record per run_id via `_primary_run_record()`)
and `self._events_by_run` (dict keyed by run_id). **The raw, ungrouped `runs_all`/`events_all`
lists are NOT currently stored as instance attributes** — they're local to `_rebuild()` and
discarded after grouping.

`tools/agent-monitoring/generate_retro.py::compute_retro_metrics(runs, events,
tickets_root=None)` (from TCK-20260718-RETRO-STATS-REFACTOR, now DONE) expects the raw,
ungrouped `runs`/`events` lists — exactly what `generate_retro.py::main()` itself passes it
(`all_runs = load_jsonl(RUNS_FILE)`, no grouping/deduplication). Feeding it `self._runs_by_id
.values()` instead of raw `runs_all` would silently deduplicate retried/re-run tickets (43 of
618 `runs.jsonl` rows share a `run_id` with another row, per the dashboard's own origin idea doc)
and produce different numbers than the CLI retro report — an inconsistency, not a design choice.

**Decision**: add `self._runs_all`/`self._events_all` as new `DashboardCache` instance
attributes, populated in `_rebuild()` alongside the existing grouped fields, so the new stats
method can feed `compute_retro_metrics()` the exact same raw data shape `generate_retro.py`'s own
CLI does.

`ingest.py` already has `_MONITORING_TOOLS_DIR` on `sys.path` (ingest.py:26-30, added for an
earlier ticket) — `from generate_retro import compute_retro_metrics` will work directly, no new
sys.path wiring needed.

## Mechanics/Engine Constraints

None — dashboard/reporting tooling, not simulation behavior.

## Parity Ledger Overlap

`docs/parity_ledger/infrastructure.yaml`'s `INFRA-275` entry (extended earlier today by
TCK-20260718-STATUS-FACET-CANONICAL and TCK-20260718-DASHBOARD-FACETS-FULLY-CANONICAL) already
tracks this dashboard's API-boundary behavior — this ticket adds a genuinely new route, so it
should extend that same entry (append to its evidence trail, matching the pattern those two
tickets already established) rather than create a new one, unless investigation during Parity
finds a cleaner separation is warranted.

## Prior Work

`get_health()` — no-parameter cache method pattern. `get_tickets()` — query-param filtering
pattern with FastAPI `Query(...)` validation in `main.py`. Neither has a period-selection
pattern like `generate_retro.py --days N`/`--all`/`--week` — this is new to this endpoint.

## Risks and Open Questions

- Route path: `/api/stats/agent-monitoring` chosen for consistency with the sibling
  TICKET-CORPUS-REPORT ticket's `/api/stats/tickets` (both under a `/api/stats/*` prefix).
- Period-selection query params: mirror `generate_retro.py`'s CLI flags as query params —
  `days: Optional[int]`, `all: bool = False`, `week: Optional[str]` — mutually exclusive,
  default to current week if none given (matching the CLI's own default).

## Anti-Drift Hazards

- Must not duplicate `compute_retro_metrics()`'s logic — import and call it directly.
- Must not read `agent-monitoring/*.jsonl` a second time outside the cache's own
  mtime-triggered rebuild cycle — reuse `self._runs_all`/`self._events_all`, don't add a
  parallel file read.
