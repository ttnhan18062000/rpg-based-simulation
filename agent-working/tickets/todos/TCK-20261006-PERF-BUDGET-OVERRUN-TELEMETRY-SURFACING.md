---
status: active
layer: performance
authority: P2
audience: agent
ticket_id: TCK-20261006-PERF-BUDGET-OVERRUN-TELEMETRY-SURFACING
phase: open
date: 2026-10-06
tags: [performance, observability]
---

# TCK-20261006-PERF-BUDGET-OVERRUN-TELEMETRY-SURFACING

## Title
Surface the kernel's tick-budget overrun signal wherever dropped work is surfaced today: the API engine status, the live snapshot and Prometheus

## Status
OPEN

## Tier
standard

## Type
feature

## Priority
P3

## Request Summary
A follow-up from `TCK-20261006-PERF-TICK-BUDGET-THROTTLE-REPORT-ONLY` (PR #379, merged 2026-10-06,
`33588b966`). That ticket made both wall-clock budget checks report-only. An overrun is now recorded on
`RuntimeStatus` (`budget_overrun_ms`, `budget_overrun_tick`, `total_budget_overruns`, via
`record_budget_overrun()`) and raises the watchdog alert. Its Scope 3 asked to surface the signal
where `dropped_work_delta` is surfaced "if that is a small change". It was not small, so it was left
out (that ticket's Implementation Notes, follow-up 1).

The operator view lost information in that change. Before it, an overrun showed up as `9999` in
`dropped_work_delta`, a wrong but visible number. Now `dropped_work_delta` stays 0 (see
`TCK-20261006-PERF-SCHEDULER-SHEDS-NOTHING-IN-SHIPPED-RUNS`), and overruns appear only in the log and
the watchdog alert.

Sites that show `dropped_work_delta` today (`main` at `33588b966`):
- `src/api/engine_manager.py` about line 210 (engine status payload);
- `src/observability/live/snapshot_provider.py` about line 137 (live snapshot);
- `src/observability/prometheus_collector.py` about lines 91-93 (`sim_dropped_work_delta` gauge);
- `src/engine/observability.py` about line 134 (`dropped_work_count`).

**Gate:** none of these files is in the partial lift (roadmap, "Gate definition and partial lift").
The ticket waits for the full lift, or for the owner to extend the partial lift to these four files.
None of them is a core file, and no open RPG-core ticket is known to edit them, so an extension is
plausible. Ask the owner; do not assume it.

## Scope
1. Add the overrun fields next to `dropped_work_delta` at each site above, through the existing
   presenter or schema of each site. Do not expose `RuntimeStatus` itself (repo rule: no raw domain
   objects from APIs).
2. Prometheus: a gauge for the last overrun in ms and a counter for total overruns. Follow the naming
   of the existing `sim_*` metrics.
3. Tests at each surface: the value appears when the kernel recorded an overrun, and is 0 or absent
   (match how the site handles `dropped_work_delta`) when it did not.
4. Docs: wherever the API or observability docs list `dropped_work_delta`, add the new fields.

## Out of Scope
- Any change to how overruns are detected or recorded (`kernel.py`, `runtime_status.py`).
- Feeding the overrun into any decision (PERF-D1 amendment A1: it is telemetry only).
- Frontend display.

## Acceptance Criteria
1. Each of the four sites shows the overrun next to `dropped_work_delta`, through a schema or
   presenter, and a test covers each.
2. Prometheus exposes the overrun gauge and counter, and a collector test covers both.
3. No governor, `AuthoritativeState` or game-system code reads the new fields.
4. `uv run make code-health` and `uv run make typecheck-py` report no new or worse finding.
5. The gate was lifted, or the owner extended the partial lift to these files, before any edit. The
   ticket records which.

## Related Tickets
- `TCK-20261006-PERF-TICK-BUDGET-THROTTLE-REPORT-ONLY` (done; source of this follow-up)
- `TCK-20261006-PERF-SCHEDULER-SHEDS-NOTHING-IN-SHIPPED-RUNS`

## Related Docs
- `docs/engine/deterministic_execution.md` (inputs 2 and 3, report-only)
- `docs/guidelines/intentional_divergences.md` (DEV-014)

## Related Stored Artifacts
- `agent-working/stored_artifacts/TCK-20261006-PERF-TICK-BUDGET-THROTTLE-REPORT-ONLY/`

## Related Code Areas
- `src/api/engine_manager.py`, `src/observability/live/snapshot_provider.py`,
  `src/observability/prometheus_collector.py`, `src/engine/observability.py`

## Assumptions / Open Questions
- Whether the frontend should show it is a separate question. Not this ticket.

## Implementation Notes

## Test Summary

## Files Changed

## Completion Summary
