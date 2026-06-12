---
status: active
layer: engine
authority: P1
audience: developer
---

# Resource Governor Contract (Milestone 5)

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
- `work_debt`: Total count of postponed authoritative items.
- `tick_compute_ms`: Wall-clock time of the previous kernel loop.
- `queue_utilization`: % of bounded buffer capacity used.

## Safety Guarantees
- **Isolation**: Governing state does not affect the authoritative simulation hash.
- **Determinism**: Identical pressure patterns MUST produce identical mode transitions.
- **Shedding Order**: Work is shed in the exact order defined by the Degradation Matrix.

## Non-Goals
- Real-time OS resource management (handled by external orchestrators).
- Concurrency or worker-pool scaling (Milestone 6+).
- Permanent persistence of signal history (Bounded window only).
