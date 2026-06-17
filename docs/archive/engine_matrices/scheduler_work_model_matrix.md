---
status: historical
layer: engine
authority: P2
audience: developer
---

# Milestone 4 Work Model Matrix

## 1. Purpose
This document defines the properties and behavioral guarantees of each work class in the engine.

| Work Class | Purpose | Authoritative? | Due Rule | Execution Guarantee | Deferral Rule |
| :--- | :--- | :--- | :--- | :--- | :--- |
| `CRITICAL` | Core Sim Logic | YES | Readiness >= 100 | Mandatory | NON-DEFERRABLE |
| `PERIODIC` | Cadence Tasks | YES | Tick % Cadence == 0 | Guaranteed | Deferrable (Limited) |
| `OPPORTUNISTIC`| Enrichment | NO | Conditional | Best-effort | Deferrable / Droppable |
| `DEFERRED` | Work Debt | YES/NO | Next Tick | Ordered Drain | Bounded |

## 2. Work Class Definitions

### CRITICAL
- **Authoritative**: YES. Essential for simulation progress.
- **Bound/Debt**: Accumulates `work_lag` if delayed (though M4 errors if delayed).
- **Regression Risk**: Simulation divergence or legal breach.

### PERIODIC
- **Authoritative**: YES (usually). Fixed cadence (e.g., economy, weather).
- **Bound/Debt**: If postponed, execution must happen in the next tick with high priority.
- **Regression Risk**: Stale world calculations.

### OPPORTUNISTIC
- **Authoritative**: NO. Used for diagnostics, visual proposals, or traces.
- **Execution**: Only runs if there is remaining budget (profile-dependent).
- **Regression Risk**: Missing observability or visual lag.

## 3. Overflow Behavior (Deferred Debt)
- **Policy**: `REJECT`.
- **Reasoning**: If the work backlog becomes too large, the engine must technically fail rather than allow an unbounded shadow registry to grow.
