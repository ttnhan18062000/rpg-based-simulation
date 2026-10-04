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
| `PERIODIC` | Cadence tasks | YES | Tick % Cadence == 0 | Guaranteed | Deferrable (limited) |
| `OPPORTUNISTIC` | Enrichment | NO | Conditional | Best-effort | Deferrable / droppable |
| `DEFERRED` | Work debt (drain only; never produced, see below) | YES/NO | Next tick | Ordered drain | Bounded |

## Work Class Definitions

### CRITICAL
Authoritative. Essential for simulation progress. Accumulates `work_lag` if delayed. The scheduler must raise an error if CRITICAL work cannot execute — deferral is forbidden.

### PERIODIC
Authoritative (usually). Fixed cadence (e.g. economy, weather). If postponed, execution must happen in the next tick with high priority.

### OPPORTUNISTIC
Non-authoritative. Used for diagnostics, visual proposals, or traces. Runs only if there is remaining budget (profile-dependent).

### DEFERRED (Work Debt)
Designed (Milestone 4) to accumulate when prior-tick work overflowed and drain in order on the next tick, bounded by profile capacity. **Only the drain half exists.** The scheduler emits a `DEFERRED` / `DRAIN_DEBT` item for a system that already has debt greater than zero, and the executor drains it; nothing ever creates that debt. As of 2026-10-04 `work_debt` is never increased in production: nothing converts overflowed or dropped work into debt, `DRAIN_DEBT` only consumes debt that already exists, and `PressureInjector.inject_work_debt` has no caller, so every reader sees 0 (guard: `tests/integration/kernel/test_work_debt_stays_empty_in_production.py`). The field is scheduled for retirement (owner decision 2026-10-04; `TCK-20261004-WORK-DEBT-RETIRE-STEP2-CODE`, which waits for the RPG-core entry gate).

## Overflow Behavior

- **Policy (design)**: `REJECT`.
- **Reasoning (design)**: If the work backlog becomes too large, the engine must fail rather than allow an unbounded shadow registry to grow.
- **Status**: not implemented for work debt. There is no capacity check on the debt counters beyond the governor's `max_work_debt` threshold, which no production run can reach because debt is never produced (`tests/integration/kernel/test_work_debt_stays_empty_in_production.py`; retirement: `TCK-20261004-WORK-DEBT-RETIRE-STEP2-CODE`).
