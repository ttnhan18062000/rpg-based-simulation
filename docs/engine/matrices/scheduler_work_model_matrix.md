---
status: active
layer: engine
authority: P1
audience: developer
---

# Scheduler Work Model Reference

Defines the properties and behavioral guarantees of each work class in the engine. Each work class has a distinct purpose, authoritative status, scheduling rule, and overflow policy.

## Work Class Summary

| Work Class | Purpose | Authoritative? | Due Rule | Execution Guarantee | Deferral Rule |
| :--- | :--- | :--- | :--- | :--- | :--- |
| `CRITICAL` | Core simulation logic | YES | Readiness >= 100 | Mandatory | NON-DEFERRABLE |
| `PERIODIC` | Cadence tasks (no instance in shipped runs, see "Designed but unused") | YES | Tick % Cadence == 0 | Guaranteed | Deferrable (limited) |
| `OPPORTUNISTIC` | Enrichment (no producer in shipped runs) | NO | Conditional | Best-effort | Deferrable / droppable |
| `DEFERRED` | Work debt (drain only; never produced, see below) | YES/NO | Next tick | Ordered drain | Bounded |

## Work Class Definitions

### CRITICAL
Authoritative. Essential for simulation progress. Accumulates `work_lag` if delayed. The scheduler must raise an error if CRITICAL work cannot execute — deferral is forbidden.

### PERIODIC
Authoritative (usually). Fixed cadence (e.g. economy, weather). If postponed, execution must happen in the next tick with high priority.

### OPPORTUNISTIC
Non-authoritative. Used for diagnostics, visual proposals, or traces. Runs only if there is remaining budget (profile-dependent). **Designed, never produced:** no code creates opportunistic work (`allow_opportunistic` is read only at `src/engine/scheduler.py` lines 138-139, in an empty branch).

### DEFERRED (Work Debt)
Designed (Milestone 4) to accumulate when prior-tick work overflowed and drain in order on the next tick, bounded by profile capacity. **Only the drain half exists.** The scheduler emits a `DEFERRED` / `DRAIN_DEBT` item for a system that already has debt greater than zero, and the executor drains it; nothing ever creates that debt. As of 2026-10-04 `work_debt` is never increased in production: nothing converts overflowed or dropped work into debt, `DRAIN_DEBT` only consumes debt that already exists, and `PressureInjector.inject_work_debt` has no caller, so every reader sees 0 (guard: `tests/integration/kernel/test_work_debt_stays_empty_in_production.py`). The field is scheduled for retirement (owner decision 2026-10-04; `TCK-20261004-WORK-DEBT-RETIRE-STEP2-CODE`, which waits for the RPG-core entry gate).

## Designed but unused

The periodic and opportunistic shedding path was designed (Resource Governor milestones M4 to M6) and never wired. Checked 2026-10-06 (`TCK-20261006-PERF-SCHEDULER-SHEDS-NOTHING-IN-SHIPPED-RUNS`; owner decision: keep the code, document it):

- `PeriodicDefinition` (`src/engine/scheduler.py`) is never registered in `src/`: `Kernel` builds `DeterministicScheduler()` with no definitions (`kernel.py` line 127) and `scheduler.py` line 31 is the only place `_periodic_defs` is assigned. It is instantiated only in tests. So the scheduler sheds nothing in shipped runs and `dropped_work` is 0.
- `allow_opportunistic` has an empty branch (`scheduler.py` lines 138-139).
- `diagnostic_verbosity` and `metrics_detail` (`GovernorPolicy`) have no reader.
- `periodic_updates` (`src/core/updates.py`) has no producer, so `AuthoritativeState.periodic_due_ticks` never advances, and the executor has no branch for periodic work kinds.

The unit tests of the mechanism (`tests/unit/core/test_degradation_order.py` and others) are valid specs but register their own definitions. Removal of this path, including the hashed `periodic_due_ticks`, is folded into `TCK-20261004-WORK-DEBT-RETIRE-STEP2-CODE`.

## Overflow Behavior

- **Policy (design)**: `REJECT`.
- **Reasoning (design)**: If the work backlog becomes too large, the engine must fail rather than allow an unbounded shadow registry to grow.
- **Status**: not implemented for work debt. There is no capacity check on the debt counters beyond the governor's `max_work_debt` threshold, which no production run can reach because debt is never produced (`tests/integration/kernel/test_work_debt_stays_empty_in_production.py`; retirement: `TCK-20261004-WORK-DEBT-RETIRE-STEP2-CODE`).
