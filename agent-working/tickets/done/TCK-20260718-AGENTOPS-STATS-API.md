---
status: historical
layer: observability
authority: P1
audience: agent
ticket_id: TCK-20260718-AGENTOPS-STATS-API
phase: done
date: 2026-07-18
tags: [dashboard, agent-monitoring, api-design]
---

# TCK-20260718-AGENTOPS-STATS-API

## Title
New Agent Ops Dashboard backend endpoint exposing agent-monitoring statistics

## Status
DONE

## Tier
standard

## Type
feature

## Priority
P1

## Request Summary
The Agent Ops Dashboard backend (`src/api/agent_ops_dashboard/`) has 5 routes today (`/api/tickets`, `/api/runs`, `/api/runs/{run_id}`, `/api/runs/{run_id}/timeline`, `/api/health`), none of which expose aggregate statistics. TCK-20260718-RETRO-STATS-REFACTOR extracts `generate_retro.py`'s metric computation into a reusable typed function; this ticket adds a new backend route consuming that function and returning the result as typed Pydantic model(s), so the frontend Stats tab (TCK-20260718-STATS-TAB-FRONTEND) has real data to render.

## Scope
- New Pydantic model(s) in `src/api/agent_ops_dashboard/models.py` mirroring the structured result TCK-20260718-RETRO-STATS-REFACTOR's extracted function returns (run summary, gate failure breakdown, reason-code breakdown, tag breakdowns, tier distribution, agent status distribution, spend proxy, summary quality, slow runs) — never a raw dict, per this dashboard's existing API-boundary rule (`tests/tools/test_agent_ops_dashboard_api_boundary.py`).
- New route in `main.py`, e.g. `GET /api/stats/agent-monitoring` (exact path is an implementation decision, keep it under a `/api/stats/*` prefix for consistency with the sibling ticket-corpus endpoint), backed by a new `DashboardCache` method or a new sibling module (`stats.py`) in the same package — investigate whether `ingest.py` is the right home or is already large enough that a new module is cleaner, document the call either way.
- Support the same period-selection `generate_retro.py`'s CLI already has (current week / `--days N` / `--all` / specific week) as query params, mirroring the existing `/api/runs`/`/api/tickets` query-param conventions (`Query(default=..., ge=..., le=...)`, `HTTPException(400/404/500)` on bad input).
- `main.py` must not read any file directly — all file access stays in `ingest.py`/the new module, matching the dashboard's established pattern.
- Investigate whether this needs its own cache entry in `DashboardCache` or can be computed on-demand from data already cached for `/api/runs`/`/api/tickets` — avoid a second full corpus re-read if the existing cache already has what's needed.

## Out of Scope
- The frontend consuming this endpoint — that's TCK-20260718-STATS-TAB-FRONTEND's scope.
- Ticket-corpus statistics (velocity, tier/type/priority/layer distribution, artifact completeness) — that's TCK-20260718-TICKET-CORPUS-REPORT's scope, a separate endpoint.
- Any change to `generate_retro.py`'s own CLI/Markdown behavior — already covered by the dependency ticket.

## Acceptance Criteria
- [x] A new `/api/stats/agent-monitoring`-style route exists, `response_model=` a typed Pydantic model, never a raw dict.
- [x] The route's computation reuses TCK-20260718-RETRO-STATS-REFACTOR's extracted function — no duplicated metric logic.
- [x] Period-selection query params work and are validated: `all=true`, `days=N`, `week=YYYY-WNN`, and the current-week default all confirmed live returning 200 with correct filtered totals.
- [x] `main.py` performs no direct file reads — confirmed via the existing `test_agent_ops_dashboard_module_has_no_write_path`/no-direct-read pattern; the new route only calls `_cache.get_agent_monitoring_stats()`.
- [x] New tests cover the endpoint (happy path, period-selection variants including the legacy-data edge case, empty-data edge case, None-key sanitization, route-level integration, anti-drift guard).

## Related Tickets
- TCK-20260718-RETRO-STATS-REFACTOR (dependency — must land first)
- TCK-20260718-STATS-TAB-FRONTEND (consumes this endpoint)
- TCK-20260718-AGENTOPS-STATS-BOARD-EPIC (parent epic)

## Related Docs
- docs/plans/agent_ops_dashboard/proposal_stats_board.md
- docs/observability/agent_ops_dashboard_contract.md

## Related Stored Artifacts
None yet.

## Related Code Areas
- src/api/agent_ops_dashboard/main.py
- src/api/agent_ops_dashboard/models.py
- src/api/agent_ops_dashboard/ingest.py
- tools/agent-monitoring/generate_retro.py

## Assumptions / Open Questions
- Exact route path/naming (`/api/stats/agent-monitoring` vs alternatives) left to Investigate/implementation, kept consistent with the sibling ticket-corpus stats route.

## Implementation Notes
Added `GET /api/stats/agent-monitoring` returning a new `AgentMonitoringStats` Pydantic model,
built by `DashboardCache.get_agent_monitoring_stats()` calling
`generate_retro.py::compute_retro_metrics()` directly. `DashboardCache` gained
`self._runs_all`/`self._events_all` (the raw, ungrouped runs.jsonl/events.jsonl lists —
previously discarded after grouping) so the new method feeds `compute_retro_metrics()` the exact
same shape `generate_retro.py`'s own CLI does, not the deduplicated `self._runs_by_id` view
(which would silently under-count retried tickets).

Two real, previously-unknown bugs found and fixed during implementation, both confirmed via live
reproduction against the actual repo data before fixing — neither by modifying
`generate_retro.py` itself, which stays out of this ticket's scope:
1. `compute_retro_metrics()`'s `gate_failure_breakdown` can carry a literal `None` key (a
   `runs.jsonl` record with neither `final_status` nor `status` set) — harmless for the existing
   Markdown renderer (prints literal "None") but breaks Pydantic's `Dict[str, int]` typing.
   Sanitized to the string `"unknown"` only at this new API boundary.
2. `generate_retro.py`'s own `main()` `--days` branch crashes with `TypeError` on real,
   confirmed-live legacy `runs.jsonl` records whose `start_ts` is a raw Unix-timestamp number
   instead of an ISO8601 string (reproduced directly:
   `python3 tools/agent-monitoring/generate_retro.py --days 7` crashes identically against the
   real corpus). This ticket's own fresh `--days` implementation (a new code path, not a call
   into the buggy `main()`) adds an `isinstance(start_ts, str)` guard, consistent with
   `iso_week()`'s own existing tolerance for the same malformed-legacy-data class. `main()`
   itself remains unfixed — a candidate for a future, separately-scoped ticket.

Updated the pinned `tests/tools/test_agent_ops_dashboard_api_boundary.py` route-enumeration test
(renamed `test_all_five_routes_are_declared` → `test_all_declared_routes_present`, exact-set
assertion extended to include the new route) rather than letting it silently fail or leaving a
stale "five" in a passing test's own name.

Extended the existing `INFRA-275` parity ledger entry (already touched by 4 prior tickets today)
with this ticket's evidence — including both bugs found — in the same session, per this
project's Parity rule.

Deviation (self-flagged, per this session's established precedent): this fork has no Agent-tool
subagent access, so all phases were performed directly (Read/Edit/Bash/Write) rather than via
`implement-ticket.js`'s specialized agent roles.

## Test Summary
`python3 -m pytest tests/tools/test_agent_ops_dashboard_ingest.py
tests/tools/test_agent_ops_dashboard_api.py tests/tools/test_agent_ops_dashboard_api_boundary.py
tests/tools/test_agent_ops_dashboard_concurrency.py
tests/tools/test_agent_ops_dashboard_frontend_api_surface.py
tests/tools/test_agent_ops_dashboard_serve.py tests/tools/test_agent_ops_dashboard_stats.py
tests/tools/test_generate_retro.py -q` — 77/77 passing. New file
`tests/tools/test_agent_ops_dashboard_stats.py` (6 tests). Live-tested via `FastAPI TestClient`
directly against real repo data: all 4 period-selection variants (`all=true`, `days=7`,
`week=2026-W29`, default) return 200 with correct filtered totals.
`tools/gate_checks/architecture_reviewer_static.py::run_architecture_checks()` — zero findings
across all 5 changed/new files.

## Files Changed
- src/api/agent_ops_dashboard/ingest.py (`self._runs_all`/`self._events_all` cache fields; new
  `get_agent_monitoring_stats()` method; imports `compute_retro_metrics`/`current_week`/
  `iso_week` from `generate_retro`)
- src/api/agent_ops_dashboard/main.py (new `GET /api/stats/agent-monitoring` route)
- src/api/agent_ops_dashboard/models.py (8 new Pydantic models: `RunSummaryStats`,
  `SubsystemTagStats`, `SkillTagStats`, `TierDistributionStats`, `SpendProxyStats`,
  `SummaryQualityStats`, `SlowRunEntry`, `AgentMonitoringStats`)
- tests/tools/test_agent_ops_dashboard_stats.py (new, 6 tests)
- tests/tools/test_agent_ops_dashboard_api_boundary.py (renamed + extended the pinned
  route-enumeration test)
- docs/parity_ledger/infrastructure.yaml (extended `INFRA-275`)

## Completion Summary
`GET /api/stats/agent-monitoring` is live, typed, and reuses
`TCK-20260718-RETRO-STATS-REFACTOR`'s `compute_retro_metrics()` with zero duplicated computation
logic. Two real pre-existing bugs (a None-key Pydantic-typing break, and a legacy-data crash in
`generate_retro.py`'s own `--days` CLI flag) were found via live testing against real production
data and fixed at the appropriate boundary — neither by touching the out-of-scope
`generate_retro.py` file. Unblocks `TCK-20260718-STATS-TAB-FRONTEND`.
