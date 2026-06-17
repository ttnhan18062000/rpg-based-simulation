---
status: active
layer: engine
authority: P1
audience: developer
---

# Observability Contract

## Purpose
This contract ensures the engine is inspectable without observability itself becoming a resource hazard. Adhering to these laws prevents "forensic bloat" and ensures diagnostics remain subordinate to the resource envelope.

## 1. Profile-Aware Observability
- **Budget Compliance**: Observability logic (sampling, trending, surfacing) must not exceed the profile's `max_observability_budget_percent`.
- **Waterfall Degradation**: When system pressure hits `DEGRADED`, observability richness must be automatically reduced (e.g., stop tracing, increase sampling interval).

## 2. Required Runtime Signals
The following signals must be exposed in a stable `RuntimeSnapshot`:
- `profile_name`: Current active profile.
- `runtime_mode`: NORMAL, CONSTRAINED, DEGRADED, SURVIVAL.
- `memory_rss_mb`: Current real memory usage.
- `memory_trend_mb_per_tick`: Moving average delta of memory usage.
- `tick_compute_ms_avg`: Moving average of total compute time per tick.
- `work_latency_ms`: Observed latency between schedule and execution for critical items.
- `queue_utilization`: $0.0 - 1.0$ ratio for action and work queues.
- `dropped_work_count`: Total count of optional work items shed due to pressure.
- `replay_backlog_kb`: Size of the `ReplayBuffer` currently in memory.

## 3. Bounded Trending Law
- **No Unbounded History**: Moving averages and trends must use fixed-size rolling windows (default last 100 samples) or EWMA.
- **Fixed Overhead**: Observability data structures must not grow with run duration.

## 4. Sampling Cadence Law
- **Periodic Sampling**: Real RSS (`psutil`) is sampled every $N$ ticks (default 10).
- **Profile Controlled**: High-performance profiles may increase $N$ to minimize overhead; diagnostic profiles may decrease $N$ for higher resolution.

## 5. Non-Authoritative Boundary
- Errors in observability (sampling failure, trend overflow) **must not stall** the simulation tick.
- Observability logic **must not mutate** the `AuthoritativeState`.
- Authoritative execution must never take a dependency on a surfaced signal.

## 6. Stability of Surfaced State
- **Naming**: Signal names in the snapshot are frozen.
- **Meaning**: The units and derivation of signals must remain consistent across versions.
