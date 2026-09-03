---
status: active
layer: observability
authority: P1
audience: agent
ticket_id: TCK-20260903-MONITORING-DATA-CONSUMERS-GATES-DASHBOARD
phase: open
date: 2026-09-03
tags: [agent-monitoring, observability, data-quality, dashboard]
---

# TCK-20260903-MONITORING-DATA-CONSUMERS-GATES-DASHBOARD

## Title
Migrate `done_checker_static.py`'s monitoring-write check and `agent_ops_dashboard/ingest.py`'s
`DashboardCache` to the unified per-week `agent-monitoring/data/` layout, fixing the live
`DashboardCache._tools_file` ground-truth bug

## Status
OPEN

## Tier
standard

## Type
refactor

## Priority
P1

## Request Summary
Child 4 of `TCK-20260903-MONITORING-UNIFIED-WEEKLY-EPIC`. Split out from the core-consumers ticket
(child 3) deliberately, because both files here carry a different risk profile than internal
`tools/agent-monitoring/` tooling: `done_checker_static.py::check_monitoring_write_recorded` gates
every ticket's DoD closure, and `src/api/agent_ops_dashboard/ingest.py::DashboardCache` is real,
production API-facing code (not a dev tool) — both warrant independent, more careful review rather
than being folded into the larger core-consumers change.

`tools/gate_checks/done_checker_static.py::check_monitoring_write_recorded` (default args
`runs_path: Path = Path("agent-monitoring/runs.jsonl")` line 691,
`events_path: Path = Path("agent-monitoring/events.jsonl")` line 692) was explicitly out of scope for
the prior tools-only epic (it never referenced `tools.jsonl` at all) — now squarely in scope, since
this epic shards `runs`/`events` too.

`src/api/agent_ops_dashboard/ingest.py::DashboardCache.__init__` hardcodes 3 single-file paths (lines
474-476): `self._runs_file`, `self._events_file`, `self._tools_file`. **Confirmed via direct source
read this session: `self._tools_file` already points at the retired legacy
`agent-monitoring/tools.jsonl` path** — the same live bug class as `record_events.py`'s (fixed in
child 1) and `weight_sensitivity_check.py`'s (fixed in child 3). `_rebuild()` (line 521) calls
`load_jsonl_counted(self._tools_file)`, which degrades silently (no crash) to an empty `tools_all`
list, feeding `_tools_by_seq`/`_tools_by_run_recent` and ultimately the Skill Usage / cost-proxy
dashboard views with silently-wrong (empty) data since the prior epic's `git rm`.

## Scope
- `tools/gate_checks/done_checker_static.py::check_monitoring_write_recorded`: change its default
  path resolution (or the arguments callers pass) to glob `agent-monitoring/data/*/runs.jsonl` and
  `agent-monitoring/data/*/events.jsonl` (all week folders), confirming a real run/event pair exists
  anywhere in the corpus for the ticket under check — not just in one hardcoded file.
- `src/api/agent_ops_dashboard/ingest.py::DashboardCache`:
  - `_current_source_state()`: change the per-source mtime computation for `"runs.jsonl"`,
    `"events.jsonl"`, `"tools.jsonl"` keys to the max mtime across every week folder's corresponding
    file, so cache invalidation correctly fires on a write to ANY week, not just a fixed single file.
  - `_rebuild()`: change `load_jsonl_counted(self._runs_file)` / `(self._events_file)` /
    `(self._tools_file)` to read/concatenate across all week folders for each source, in ISO-week
    order.
  - **Fix the `_tools_file` bug** as an explicit, dedicated line item — restore real `tools_all`
    content from the multi-week glob.
  - Given this is real production API code, add explicit test coverage beyond "doesn't crash":
    correct aggregation across 2+ weeks, correct staleness detection from a write to a non-newest
    week, and the specific regression proving `tools_all` is non-empty against real sharded data.

## Out of Scope
- `tools/agent-monitoring/build_index.py`, `generate_retro.py`, `manifest.py`, `seq_offset.py`,
  `weight_sensitivity_check.py`, `retro_nudge_hook.py`, `done_ticket_monitoring_coverage.py`,
  `validate.py`, `query.py` — child 3.
- Any other `done_checker_static.py` check besides `check_monitoring_write_recorded` — this ticket
  changes only that check's path resolution, not its pass/fail logic or any other DoD condition.
- Any change to `DashboardCache`'s public method surface, its `threading.RLock()` locking pattern, or
  any presenter/API-route shape built on top of it — only the 3 source-file constants' resolution and
  the mtime/read logic that depends on them change.
- The codex subsystem (child 5) and referential-integrity tooling (child 6).

## Acceptance Criteria
- [ ] A test asserts `done_checker_static.py::check_monitoring_write_recorded` correctly finds a real
      run/event pair for a given `run_id` when that pair lives in a non-`current`, older week folder
      — not just the newest one.
- [ ] Zero unrelated functional change to any other `done_checker_static.py` check (diff scoped to
      `check_monitoring_write_recorded`'s path resolution only).
- [ ] A test proves `DashboardCache._rebuild()` aggregates `runs`/`events`/`tools` records from 2+
      week folders, not just one.
- [ ] A test proves `DashboardCache._maybe_rebuild()` correctly detects staleness from a write to a
      non-newest week folder for each of the 3 sources.
- [ ] **Regression test proving the `_tools_file` bug is fixed**: `DashboardCache._tools_all` (and
      derived `_tools_by_seq`/`_tools_by_run_recent`) is non-empty and correct against real
      post-migration multi-week `tools` data.
- [ ] No change to `DashboardCache`'s public API surface or its existing single-`RLock()` guarding
      pattern.

## Related Tickets
- TCK-20260903-MONITORING-UNIFIED-WEEKLY-EPIC (parent epic)
- TCK-20260903-MONITORING-DATA-WRITE-PATH-UNIFY (child 1)
- TCK-20260903-MONITORING-DATA-MIGRATION (child 2 — hard prerequisite)
- TCK-20260903-MONITORING-DATA-CONSUMERS-CORE (child 3 — independent, file-disjoint, parallelizable
  with this ticket once child 2 lands)
- TCK-20260818-STANDARD-KGMCP-CACHE-ATTRIBUTION-AND-SKILL-USAGE-DASHBOARD (or equivalent — the ticket
  that wired `_tools_all` retention into `DashboardCache` for Skill Usage; directly relevant context
  for why this bug's blast radius includes the Skill Usage dashboard view, confirm exact ticket ID at
  implementation time).
- TCK-20260902-MONITORING-SHARD-CONSUMERS — confirmed `done_checker_static.py` out of scope for the
  tools-only epic; this ticket is the direct follow-up that brings it into scope now that
  `runs`/`events` shard too.

## Related Docs
None beyond code-level accuracy — no doc currently claims `DashboardCache`'s internal file-resolution
shape (that's an implementation detail, not documented API behavior).

## Related Stored Artifacts
None yet.

## Related Code Areas
- `tools/gate_checks/done_checker_static.py` (lines ~691-692, `check_monitoring_write_recorded`)
- `src/api/agent_ops_dashboard/ingest.py` (lines 474-476, 497-521, `DashboardCache`)

## Assumptions / Open Questions
- Assumes child 2 (migration) has landed.
- `DashboardCache` is explicitly called out by the requester's original context as "real production
  API-facing code, not just a dev tool" — this ticket's test coverage bar is intentionally higher
  (explicit staleness/aggregation tests, not just no-crash smoke tests) to match that risk profile.
- `layer: observability` matches this repo's established pattern; `dashboard` tag added specifically
  for the `agent_ops_dashboard/ingest.py` portion of this ticket's scope.

## Implementation Notes

## Test Summary

## Files Changed

## Completion Summary
