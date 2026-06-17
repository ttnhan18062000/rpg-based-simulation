---
status: active
layer: engine
authority: P1
audience: developer
---

# Resource Governor Degradation Reference

Defines the exact shedding order of runtime costs under pressure. Costs are categorized by their impact on authoritative simulation semantics.

## Degradation Table

| Category | Authoritative | NORMAL | CONSTRAINED | DEGRADED | SURVIVAL |
| :--- | :--- | :--- | :--- | :--- | :--- |
| **Critical Work** | YES | Allowed | Allowed | Allowed | Allowed |
| **Periodic (Auth)** | YES | Allowed | Allowed | Allowed | Allowed |
| **Periodic (Non-Auth)** | NO | Allowed | Allowed | Allowed | **Dropped** |
| **Opportunistic** | NO | Allowed | **Reduced 50%** | **Dropped** | **Dropped** |
| **Diag Verbosity** | NO | Full | **Minimal** | **Error-Only** | **Muted** |
| **Metric Richness** | NO | High | High | **Low** | **Muted** |

## Degradation Policy Rules

### 1. Authoritative Work Preservation
CRITICAL work (entity actions) and authoritative PERIODIC work (state upkeep) must never be shed. High pressure on these categories must lead to **work debt** accumulation, not deletion.

### 2. Shedding Order (Waterfall)
1. **Diagnostic Verbosity**: Reduce string formatting and trace depth.
2. **Opportunistic Work**: Drop optional non-simulation enrichments.
3. **Metric Richness**: Scale back non-essential counters and histograms.
4. **Non-Authoritative Periodic**: Drop maintenance tasks that do not affect simulation truth (e.g. log rotation, summary generation).

### 3. Recovery Behavior
Recovery proceeds from SURVIVAL → DEGRADED → CONSTRAINED → NORMAL. Each step requires all relevant pressure signals to be below the recovery threshold for the duration of the dwell time.

## Forbidden Behavior

- **Authoritative Skipping**: Dropping a CRITICAL item to save CPU is a breach of contract.
- **State Contamination**: The governor must not alter any variable inside `AuthoritativeState` as part of its protection logic.
