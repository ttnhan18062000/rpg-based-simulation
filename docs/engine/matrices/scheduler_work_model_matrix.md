---
status: active
layer: engine
authority: P1
audience: developer
---

# Scheduler Work Model Reference

Defines the properties and behavioral guarantees of each work class in the engine. Each work class has a distinct purpose, authoritative status, scheduling rule, and overflow policy.

## Work Class Summary

Only `CRITICAL` work is produced. The other three classes were removed in Phase B (`TCK-20261004-WORK-DEBT-RETIRE-STEP2-CODE`, owner decisions 2026-10-04 and 2026-10-06): their members remain in `src/core/work.py` as unused constants, and nothing schedules, executes or sheds work of those classes.

| Work Class | Purpose | Authoritative? | Due Rule | Execution Guarantee | Deferral Rule |
| :--- | :--- | :--- | :--- | :--- | :--- |
| `CRITICAL` | Core simulation logic | YES | Readiness >= 100 | Mandatory | NON-DEFERRABLE |
| `PERIODIC` | Removed in Phase B (never registered in shipped runs) | n/a | n/a | n/a | n/a |
| `OPPORTUNISTIC` | Removed in Phase B (never produced) | n/a | n/a | n/a | n/a |
| `DEFERRED` | Removed in Phase B (work debt was never produced) | n/a | n/a | n/a | n/a |

## Work Class Definitions

### CRITICAL
Authoritative. Essential for simulation progress. The scheduler must raise an error if CRITICAL work cannot execute — deferral is forbidden.

### PERIODIC, OPPORTUNISTIC, DEFERRED (work debt)
**Removed in Phase B.** They were designed in the Resource Governor milestones (M4 to M6) and never wired: `PeriodicDefinition` was never registered in `src/`, no code created opportunistic work, and nothing converted overflowed work into debt (`DRAIN_DEBT` only consumed debt that already existed, which stayed 0). The owner chose to retire them rather than build a producer (a deterministic definition of "overflowed work" does not exist, and feeding wall-clock-driven shedding into it would break PERF-D1). What was removed: the scheduler branches and `PeriodicDefinition`; the executor's `DRAIN_DEBT` handling and `SimulationDomainLogic.drain_debt`; `AuthoritativeState.work_debt` / `periodic_due_ticks` and `StateUpdate.work_debt_updates` / `periodic_updates`; the governors' debt thresholds, `PressureSignals.work_debt_total` and `RuntimeProfile.max_work_debt`; and the `GovernorPolicy` fields `allow_opportunistic`, `allow_non_authoritative_periodic`, `diagnostic_verbosity` and `metrics_detail`. See DEV-019 in `docs/guidelines/intentional_divergences.md`. The scheduler's dropped-work count stays in the accounting as a constant 0.

## Overflow Behavior

There is no deferred work, so there is nothing to overflow. The design policy (`REJECT` on an over-large backlog) was never implemented and has no remaining subject.
