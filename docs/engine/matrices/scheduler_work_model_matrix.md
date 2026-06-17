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
| `DEFERRED` | Work debt | YES/NO | Next tick | Ordered drain | Bounded |

## Work Class Definitions

### CRITICAL
Authoritative. Essential for simulation progress. Accumulates `work_lag` if delayed. The scheduler must raise an error if CRITICAL work cannot execute — deferral is forbidden.

### PERIODIC
Authoritative (usually). Fixed cadence (e.g. economy, weather). If postponed, execution must happen in the next tick with high priority.

### OPPORTUNISTIC
Non-authoritative. Used for diagnostics, visual proposals, or traces. Runs only if there is remaining budget (profile-dependent).

### DEFERRED (Work Debt)
Accumulated when prior-tick work overflowed. Drained in order on the next tick. Bounded by profile capacity — overflow is rejected, never silently discarded.

## Overflow Behavior

- **Policy**: `REJECT`.
- **Reasoning**: If the work backlog becomes too large, the engine must fail rather than allow an unbounded shadow registry to grow.
