---
status: active
layer: engine
authority: P1
audience: developer
---

# Resource Governor Contract

## Purpose
The Resource Governor is the engine's authoritative safety-control layer. It protects the simulation's resource envelope (CPU, Memory, Queue, Debt) by transitioning the engine through deterministic degradation modes.

## Governor Scope
- **Authoritative Preservation**: The governor MUST NOT skip or alter authoritative simulation steps (Kernel Tick, Apply Path).
- **Operational Control**: The governor MUST only shed non-authoritative costs defined in the Degradation Matrix.
- **Profile Awareness**: Thresholds are relative to the active `RuntimeProfile` limits.

## Runtime Modes
- `NORMAL`: Operation within comfort thresholds. All work allowed.
- `CONSTRAINED`: Early pressure detected. Reduce optional diagnostic overhead.
- `DEGRADED`: High pressure. Disable all optional/opportunistic work and metrics richness.
- `SURVIVAL`: Critical pressure. Only `CRITICAL` work and **Authoritative PERIODIC** work permitted. All non-authoritative maintenance is suppressed.

## Mode Transition Semantics
- **Escalation**: Immediate transition to a higher-pressure mode if ANY signal exceeds the escalation threshold.
- **De-escalation (Recovery)**: Permitted ONLY if:
  1. ALL signals are below the recovery threshold (Low-Watermark).
  2. The system has remained in the current mode for at least `N` ticks (Dwell Time / Cooldown).

## Pressure Signal Semantics
- `work_debt`: **Removed in Phase B** (`TCK-20261004-WORK-DEBT-RETIRE-STEP2-CODE`, owner decision 2026-10-04). It was a sum of per-system integer counters in `AuthoritativeState.work_debt` that nothing ever increased in production, so every reader saw 0. The state field, `StateUpdate.work_debt_updates`, `PressureSignals.work_debt_total`, `RuntimeProfile.max_work_debt`, the `DRAIN_DEBT` drain and the governors' debt thresholds are gone. No producer was built: a deterministic definition of overflowed work does not exist, and feeding wall-clock-driven shedding into one would break PERF-D1.
- `tick_compute_ms`: Wall-clock time of the previous kernel loop. It is a control signal and a report value only, never a gameplay input: since `TCK-20261003-SALIENCE-WALL-CLOCK-PRICE-COUPLING` nothing derives `compute_ratio`, `global_salience` or a price from it, and `AuthoritativeState.pressure_signals` is no longer written by the kernel (PERF-D1 amendment A1).
- `queue_utilization`: % of bounded buffer capacity used.
- `tick_cost`, `tick_budget`, `phase_cost` (optional; `None` means "use the measured value"): the cost inputs the governors compare with the profile. Under the default `LIVE` contract they are unset and `tick_compute_ms` is the cost. Under `signal_contract=CANONICAL`, `tick_cost` is a modelled reference-millisecond cost from deterministic demand counts (`src/engine/work_units.py`, `WORK_MODEL_V1`), `phase_cost` is empty (the per-phase rules have nothing to read), and `tick_compute_ms` is telemetry only. `PressureSignals.effective_tick_cost` / `effective_tick_budget` / `effective_phase_cost` are what `ResourceGovernor`, `PhaseBudgetGovernor` and the rolling average read.

## Safety Guarantees
- **Isolation**: Governing state does not affect the authoritative simulation hash.
- **Determinism**: Identical pressure patterns MUST produce identical mode transitions.
- **Shedding Order**: Work is shed in the exact order defined by the Degradation Matrix.

## Non-Goals
- Real-time OS resource management (handled by external orchestrators).
- Concurrency or worker-pool scaling.
- Permanent persistence of signal history (Bounded window only).
