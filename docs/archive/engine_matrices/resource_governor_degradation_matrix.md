---
status: historical
layer: engine
authority: P2
audience: developer
---

# Milestone 5 Degradation Matrix

## Summary
The degradation matrix defines the exact shedding order of runtime costs. Costs are categorized by their impact on authoritative simulation semantics.

| Category | Authoritative | NORMAL | CONSTRAINED | DEGRADED | SURVIVAL |
| :--- | :--- | :--- | :--- | :--- | :--- |
| **Critical Work** | YES | Allowed | Allowed | Allowed | Allowed |
| **Periodic (Auth)** | YES | Allowed | Allowed | Allowed | Allowed |
| **Periodic (Non-Auth)**| NO | Allowed | Allowed | Allowed | **Dropped** |
| **Opportunistic** | NO | Allowed | **Reduced 50%** | **Dropped** | **Dropped** |
| **Diag Verbositiy** | NO | Full | **Minimal** | **Error-Only** | **Muted** |
| **Metric Richness** | NO | High | High | **Low** | **Muted** |

## Degradation Policy Rules

### 1. Authoritative Work Preservation
- `CRITICAL` work (Entity Actions) and `Authoritative PERIODIC` work (State Up-keep) MUST NEVER be shed. 
- High pressure on these categories must lead to **Work Debt** accumulation, not deletion.

### 2. Shedding Order (Waterfall)
1. **Diagnostic Verbosity**: Reduce string formatting and trace depth.
2. **Opportunistic Work**: Drop optional visual or non-simulation enrichments.
3. **Metric Richness**: Scale back non-essential counters and histograms.
4. **Non-Authoritative Periodic**: Drop maintenance tasks that do not affect simulation truth (e.g. log rotation, summary generation).

### 3. Recovery Behavior
- Recovery proceeds from `SURVIVAL` -> `DEGRADED` -> `CONSTRAINED` -> `NORMAL`.
- Each step requires all relevant pressure signals to be below the **Recovery Threshold** for the duration of the **Dwell Time**.

## Forbidden Behavior
- **Authoritative Skipping**: Dropping a `CRITICAL` item to save CPU is a breach of contract.
- **State Contamination**: The governor must not alter any variable inside `AuthoritativeState` as part of its protection logic.
