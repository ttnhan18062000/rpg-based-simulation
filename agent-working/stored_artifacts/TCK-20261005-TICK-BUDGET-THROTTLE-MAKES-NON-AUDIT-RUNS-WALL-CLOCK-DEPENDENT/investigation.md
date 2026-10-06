---
status: active
layer: engine
authority: P1
audience: agent
ticket_id: TCK-20261005-TICK-BUDGET-THROTTLE-MAKES-NON-AUDIT-RUNS-WALL-CLOCK-DEPENDENT
artifact_type: investigation
tags: [engine, determinism, measurement]
---

# Investigation (superseded; no investigation was run under this ticket)

The ticket was filed by the planner from two lanes' contradictory determinism results on `frontier_living_world`
(Lane B: 8 vs 10 deaths at tick 500, same seed, outside `audit_mode`; `generated_frontier_3_42` stable; Lane A: `audit_mode=True` with
`max_tick_budget_ms=1e9`, runs repeat exactly). Perf reviewed it on PR #355 and found two errors in the filed mechanism:

1. The work is dropped by the **mid-tick throttle at `kernel.py:618-626`** (every 10 results it checks wall-clock time and, outside
   `audit_mode`, sheds the rest of the tick and forces `DEGRADED`). `kernel.py:466-469`, which the ticket cited, is the end-of-tick check
   that sets a telemetry counter (the `9999` sentinel) nothing reads to change behaviour.
2. "Deterministic counter vs report-only" was already decided on 2026-10-03 (PERF-D1 inputs 2 and 3,
   `docs/engine/deterministic_execution.md`, "Canonical contract"): report-only is the answer under both contracts.

Not verified here: the throttle's behaviour was taken from perf's review, not re-read or re-run. Handed over to perf's report-only
ticket (not yet filed at closure): PR #355, comment `6000452921`.
