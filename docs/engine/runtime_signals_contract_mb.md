# Milestone B: Runtime Signals and Governor Law

## 1. Purpose
This document defines the authoritative operational law for the v2 engine. Milestone B closes the gap between architectural presence and operational truth, ensuring that monitoring, degradation, and recovery are based on real, bounded accounting rather than estimates or placeholders.

## 2. Scope of Milestone B
- **In-Scope**: Real signal accounting (Queue, Worker, Replay, Debt), Bounded signal history (Rolling math), Deterministic governor transitions (Hysteresis), Governance-state isolation.
- **Out-of-Scope**: Full lifecycle hardening (C), Bounded concurrency trust (D).

## 3. Runtime Signal Catalog
Every signal that influences a `GovernorMode` transition must be defined and truthful.

| Signal Name | Source Module | Accounting Type | Window Type |
| :--- | :--- | :--- | :--- |
| `tick_compute_ms` | `Kernel` | Instantaneous | N/A |
| `tick_compute_ms_avg` | `RuntimeStatus` | Calculated | Rolling (5-tick) |
| `memory_rss_mb` | `SignalCollector` | Sampled (OS) | Instantaneous |
| `memory_trend` | `SignalCollector` | Calculated | Rolling (5-sample) |
| `worker_utilization` | `WorkerManager` | **Peak Inflight** | Per-Tick |
| `queue_utilization` | `WorkerManager` | **Peak Depth** | Per-Tick |
| `work_debt_total` | `AuthoritativeState` | Absolute | Instantaneous |
| `replay_backlog_kb` | `ReplayManager` | Absolute | Instantaneous |

## 4. Signal Boundedness Law
- **History Retention**: All signal history in `RuntimeStatus` must be strictly bounded (e.g., `maxlen=100`).
- **Trend Math**: Trends and averages must not grow unbounded or rely on full-session cumulative sums.
- **Deterministic Sampling**: RSS/Memory sampling cadence must be constant and profile-declared to ensure predictable overhead.

## 5. Governor Transition Law
Transitions between `NORMAL`, `DEGRADED`, and `SURVIVAL` must follow these rules:

### Escalation (Immediate)
- Escalation occurs in the **SAME TICK** that a signal exceeds a Profile threshold.
- No dwell time or windowing is required for escalation; safety first.

### Recovery (Gated)
- Recovery occurs only if:
    1. **Stability Window**: All signals remain below the `recovery_watermark` (default 0.8) for the duration of the `confidence_window_ticks`.
    2. **Dwell Time**: Minimum `dwell_time_ticks` since the last transition has passed.
- Recovery moves down exactly **one level at a time**.

## 6. Anti-Thrashing Law
- **Hysteresis**: The recovery threshold is always strictly lower than the escalation threshold (`threshold * watermark`).
- **Confidence Requirement**: A single sample below threshold does NOT trigger recovery. Only a stable window of confirmed "Low Pressure" permits de-escalation.

## 7. Governance Isolation Law
- **Truth Separation**: `RuntimeMode`, `PressureSignals`, and all operational status fields are **NON-AUTHORITATIVE**.
- **No Contamination**: These fields must NOT be included in `AuthoritativeState` or the `CanonicalStateHasher` input.
- **One-Way Influence**: Operational state influences *what* work is selected (Tactical), but never *how* work applies (Strategic).

## 8. Non-Goals
- Real-world wall-clock determinism.
- Network-level signal truth.
- Hardware-specific performance profiling beyond RSS/Compute.

## 9. Completion Confirmation
Milestone B is complete when the single-process path operates under these truthful signals without oscillation or semantic drift.

**Status: DRAFT / UNDER IMPLEMENTATION**
**Date: 2026-04-19**
