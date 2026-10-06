---
status: historical
layer: performance
authority: P2
audience: agent
artifact_type: investigation
ticket_id: TCK-20261006-PERF-TICK-BUDGET-THROTTLE-REPORT-ONLY
date: 2026-10-06
tags: [performance, determinism, engine, testing]
---

# Investigation: TCK-20261006-PERF-TICK-BUDGET-THROTTLE-REPORT-ONLY

## Live code (main 7570beb90 + planning commit)
- Mid-tick throttle: `src/engine/kernel.py` `_phase_resolution` (~618-651). Every 10 results, outside
  `audit_mode`, `elapsed > max_tick_budget_ms` records `record_dropped_work(n)`, calls
  `governor.force_mode(DEGRADED)`, routes a watchdog alert, and `break`s (drops the rest).
- End-of-tick check: `tick_once` (~463-485): after tick 5, over `min(hard_cap, max(20, 2*avg))` logs,
  calls `record_dropped_work(9999)` (sentinel) and routes a watchdog alert.
- `RuntimeStatus` (`src/engine/runtime_status.py`) is non-authoritative (M5 law, not hashed);
  `PressureSignals` (`src/core/governance.py`) is not stored in `AuthoritativeState`. The governor reads
  `tick_compute_ms` (input 1, out of scope) and `dropped_work_delta` only via telemetry.
- `ResourceGovernor.force_mode` exists only for this throttle; after the change it has no caller in `src/`.
  governor.py is not lifted for this batch, so it stays (reported, not removed).

## Design decision (typed signal)
`RuntimeStatus` gains `budget_overrun_ms: float` (this tick, replaced each tick, like
`dropped_work_delta`) and `total_budget_overruns: int`, set by `record_budget_overrun(ms)`. Not added to
`PressureSignals`, so nothing in the governor's input path or the signal history carries it, and no
gated path is touched. Surfacing in engine_manager/snapshot/Prometheus (where `dropped_work_delta` is
surfaced) is deferred as a follow-up unless small.

## Tests that leaned on the old behaviour
Recorded per test in the ticket (Implementation Notes) as the work proceeds.

## Findings during implementation (2026-10-06)
- The default `DeterministicScheduler()` registers no `PeriodicDefinition`; nothing in `src/` does. So the
  scheduler never sheds work in shipped runs, and the throttle plus the 9999 sentinel were the only source of
  `dropped_work`. After this ticket it is 0 in shipped runs. The work-debt test's precondition needed a
  non-authoritative periodic task to stay non-vacuous.
- `test_milestone_b_closure.py` fails the same on `origin/main` (164 ms per tick under its mock clock: 82 clock
  reads x 2 ms, SURVIVAL not DEGRADED; its comment says ~63 reads and ~126 ms). Pre-existing, `slow`-marked.
- The end-of-tick check runs after `_phase_advancement` moves `state.tick` on, so a per-tick count must use
  the tick captured at tick start.
- Typed signal lives on `RuntimeStatus` only (not `PressureSignals`), so no gated path changes.
