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
| **Periodic (Non-Auth)** | NO | Allowed | Allowed | Allowed | **Dropped** (mechanism only, see note 1) |
| **Opportunistic** | NO | Allowed | Allowed | **Dropped** | **Dropped** (flag only, see note 2) |
| **Diag Verbosity** | NO | Full | **Minimal** | **Error-Only** | **Muted** (value only, see note 3) |
| **Metric Richness** | NO | High | High | **Low** | **Muted** (value only, see note 3) |

The cells are the values `GovernorPolicy.from_mode` sets (`src/engine/policy.py`: `allow_non_authoritative_periodic`, `allow_opportunistic`, `diagnostic_verbosity`, `metrics_detail`). They are not all behaviour; see "Shipped behaviour" below.

## Shipped behaviour

Checked against the code on 2026-10-06 (`TCK-20261006-PERF-SCHEDULER-SHEDS-NOTHING-IN-SHIPPED-RUNS`, owner decision (c)).

- **What a mode change does today:** mode-dependent `system_cadence` and `phase_budgets` (`GovernorPolicy.from_mode`, `src/engine/policy.py`; `PhaseBudgetGovernor`, `src/engine/phase_governor.py`), `concurrency_limit` (`Kernel`, `set_concurrency_limit(self._current_policy.concurrency_limit)`, `src/engine/kernel.py`), `replay_allowed` and `replay_richness` (`src/engine/replay_manager.py` lines 90 and 94, and `Kernel._phase_persistence`), and `allow_subsystem_traces` (`replay_manager.py` line 99).
- **Note 1, non-authoritative periodic:** `allow_non_authoritative_periodic` is read at `src/engine/scheduler.py` line 103, but no `PeriodicDefinition` is registered anywhere in `src/` (`Kernel` builds its scheduler with none, `kernel.py` line 127), so nothing is dropped. `dropped_work` is 0 in shipped runs.
- **Note 2, opportunistic:** `allow_opportunistic` is read only at `scheduler.py` lines 138-139, in a branch whose body is `pass`. No opportunistic work item is produced. The CONSTRAINED cell is `Allowed` because that is the flag's value; there is no "reduced 50%" mechanism.
- **Note 3, diagnostics and metrics:** `diagnostic_verbosity` and `metrics_detail` are set per mode and have no reader in `src/`, so the Diag Verbosity and Metric Richness rows describe policy values, not behaviour.

See "Designed but unused" in `scheduler_work_model_matrix.md`; removal is folded into `TCK-20261004-WORK-DEBT-RETIRE-STEP2-CODE`.

## Degradation Policy Rules

### 1. Authoritative Work Preservation
CRITICAL work (entity actions) and authoritative PERIODIC work (state upkeep) must never be shed. High pressure on these categories must lead to **work debt** accumulation, not deletion. (Design. Today nothing converts work into debt: `work_debt` is never increased in production, see `scheduler_work_model_matrix.md`, DEFERRED.)

### 2. Shedding Order (Waterfall)
The design order. Only the replay and trace levers and the cadence, budget and concurrency changes act in shipped runs; see "Shipped behaviour".

1. **Diagnostic Verbosity**: Reduce string formatting and trace depth.
2. **Opportunistic Work**: Drop optional non-simulation enrichments.
3. **Metric Richness**: Scale back non-essential counters and histograms.
4. **Non-Authoritative Periodic**: Drop maintenance tasks that do not affect simulation truth (e.g. log rotation, summary generation).

### 3. Recovery Behavior
Recovery proceeds from SURVIVAL → DEGRADED → CONSTRAINED → NORMAL. Each step requires all relevant pressure signals to be below the recovery threshold for the duration of the dwell time.

## Forbidden Behavior

- **Authoritative Skipping**: Dropping a CRITICAL item to save CPU is a breach of contract.
- **State Contamination**: The governor must not alter any variable inside `AuthoritativeState` as part of its protection logic.
