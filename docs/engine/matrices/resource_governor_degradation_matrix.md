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

Critical (entity) work is the only work class the scheduler produces, and no mode sheds it. The other categories this table used to list (authoritative and non-authoritative periodic work, opportunistic work, diagnostic verbosity and metric richness) were rows of `GovernorPolicy` fields that nothing read, or work classes nothing produced. They were removed in Phase B (`TCK-20261004-WORK-DEBT-RETIRE-STEP2-CODE`; DEV-019 in `docs/guidelines/intentional_divergences.md`).

## Shipped behaviour

Checked against the code on 2026-10-06 (`TCK-20261006-PERF-SCHEDULER-SHEDS-NOTHING-IN-SHIPPED-RUNS`, owner decision (c)), and updated when the never-wired path was removed.

- **What a mode change does today:** mode-dependent `system_cadence` and `phase_budgets` (`GovernorPolicy.from_mode`, `src/engine/policy.py`; `PhaseBudgetGovernor`, `src/engine/phase_governor.py`), `concurrency_limit` (`Kernel`, `set_concurrency_limit(self._current_policy.concurrency_limit)`, `src/engine/kernel.py`), `replay_allowed` and `replay_richness` (`src/engine/replay_manager.py` lines 90 and 94, and `Kernel._phase_persistence`), and `allow_subsystem_traces` (`replay_manager.py` line 99).
- **Nothing is shed.** The scheduler has no periodic, deferred or opportunistic branch, so it drops nothing and `dropped_work` is a constant 0; a mode change acts only through the levers in the bullet above.

## Degradation Policy Rules

### 1. Authoritative Work Preservation
CRITICAL work (entity actions) must never be shed. There is no work debt: the mechanism the original design used to defer overflowing work was never produced and was removed in Phase B.

### 2. Shedding Order (Waterfall)
The levers that act in shipped runs, as listed in "Shipped behaviour": replay richness and subsystem traces first, then cadence, phase budgets, scan policy and the concurrency limit as the mode escalates. The design's diagnostic-verbosity, opportunistic, metric-richness and non-authoritative-periodic steps no longer exist.

### 3. Recovery Behavior
Recovery proceeds from SURVIVAL → DEGRADED → CONSTRAINED → NORMAL. Each step requires all relevant pressure signals to be below the recovery threshold for the duration of the dwell time.

## Forbidden Behavior

- **Authoritative Skipping**: Dropping a CRITICAL item to save CPU is a breach of contract.
- **State Contamination**: The governor must not alter any variable inside `AuthoritativeState` as part of its protection logic.
