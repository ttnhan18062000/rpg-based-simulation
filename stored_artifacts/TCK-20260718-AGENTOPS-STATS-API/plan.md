---
status: active
layer: observability
authority: P1
audience: agent
ticket_id: TCK-20260718-AGENTOPS-STATS-API
artifact_type: plan
tags: []
---

# Implementation Plan — TCK-20260718-AGENTOPS-STATS-API

## Summary

Add `GET /api/stats/agent-monitoring` to the dashboard backend, returning a new typed
`AgentMonitoringStats` Pydantic model built from `tools/agent-monitoring/generate_retro.py
::compute_retro_metrics()`'s output. `DashboardCache` gains `self._runs_all`/`self._events_all`
(raw, ungrouped lists) and a new `get_agent_monitoring_stats()` method with the same
period-selection semantics as the CLI (`days`/`all`/`week`).

## Steps

### Step 1 — Store raw runs/events in `DashboardCache`

In `ingest.py`'s `_rebuild()`, add `self._runs_all = runs_all` and `self._events_all =
events_all` alongside the existing grouped-field assignments (near `self._runs_by_id = ...`).
Initialize both to `[]` in `__init__`.

### Step 2 — New Pydantic models in `models.py`

Add models mirroring `compute_retro_metrics()`'s dict shape exactly (field-for-field):
`RunSummaryStats`, `TagBreakdownRow` (subsystem: runs/done/gate_fails; skill: runs/gate_hits —
two variants or one model with `Optional[int]` gate_hits and `Optional[int]` done/gate_fails
depending on category, decide during implementation which is cleaner), `TierDistributionRow`,
`SpendProxyRow`, `SummaryQualityStats`, `SlowRunEntry`, and the top-level
`AgentMonitoringStats` model composing all of them (`run_summary`, `gate_failure_breakdown:
Dict[str, int]`, `reason_code_breakdown: Dict[str, int]`, `tag_breakdown_subsystem: Dict[str,
TagBreakdownRow]`, `tag_breakdown_skill: Dict[str, TagBreakdownRow]`, `tier_distribution:
Dict[str, TierDistributionRow]`, `agent_status_distribution: Dict[str, Dict[str, int]]`,
`spend_proxy_by_phase: Dict[str, SpendProxyRow]`, `spend_proxy_by_agent: Dict[str, SpendProxyRow]`,
`summary_quality: SummaryQualityStats`, `slow_runs: List[SlowRunEntry]`).

### Step 3 — `DashboardCache.get_agent_monitoring_stats()`

New method, same `with self._lock: self._maybe_rebuild()` opening as every other method. Params:
`days: Optional[int] = None`, `all_time: bool = False`, `week: Optional[str] = None`. Replicates
`generate_retro.py::main()`'s exact period-filter logic (import and reuse `iso_week`/
`current_week` from `generate_retro` rather than reimplementing the ISO-week math) against
`self._runs_all`/`self._events_all`, then calls `compute_retro_metrics(filtered_runs,
filtered_events, tickets_root=self._tickets_root)`, converts the returned dict into
`AgentMonitoringStats`.

### Step 4 — New route in `main.py`

```python
@app.get("/api/stats/agent-monitoring", response_model=AgentMonitoringStats)
async def get_agent_monitoring_stats(
    days: Optional[int] = None,
    all_time: bool = Query(default=False, alias="all"),
    week: Optional[str] = None,
) -> AgentMonitoringStats:
    return _cache.get_agent_monitoring_stats(days=days, all_time=all_time, week=week)
```
(`alias="all"` since `all` is a Python builtin — mirrors how other query params avoid shadowing.)

### Step 5 — Update the pinned route-enumeration test

`tests/tools/test_agent_ops_dashboard_api_boundary.py::test_all_five_routes_are_declared` — its
name and exact-set assertion both need updating to include the new route. Rename to something
accurate (e.g. `test_all_declared_routes_present`) and update the set literal — do not just add
the new path and leave the stale "five" in the function name (an TCK-20260718-STATUS-MULTILINE-FIX
-style staleness trap).

### Step 6 — New tests

Per test_plan.md: model construction, route happy-path + period-selection + empty-data +
bad-input, API-boundary extension.

## Scope Guards

- Do not modify `generate_retro.py` — only import and call `compute_retro_metrics()`.
- Do not add a second file-read path — reuse `DashboardCache`'s existing rebuild cycle.
- Do not build the frontend consumer — that's TCK-20260718-STATS-TAB-FRONTEND's scope.
- Do not touch `/api/tickets`/`/api/runs`/`/api/runs/{run_id}`/`/api/runs/{run_id}/timeline`/
  `/api/health` — purely additive.

## Dependency Map

Depends on TCK-20260718-RETRO-STATS-REFACTOR (DONE) for `compute_retro_metrics()`. Blocks
TCK-20260718-STATS-TAB-FRONTEND.

## Acceptance Criteria Map

- AC "new route, typed model, never raw dict" → Steps 2-4.
- AC "reuses TCK-20260718-RETRO-STATS-REFACTOR's function, no duplication" → Step 3.
- AC "period-selection query params work and validated" → Steps 3-4.
- AC "main.py performs no direct file reads" → Step 3 (reads only via cache).
- AC "new tests cover the endpoint" → Step 6.

## Anti-Drift Notes

`test_all_five_routes_are_declared` is a real pinned test that WILL fail once this ticket's route
is added — Step 5 addresses it head-on rather than letting it slip through as an unnoticed
failure (or worse, an unexamined test-suite-wide skip).
