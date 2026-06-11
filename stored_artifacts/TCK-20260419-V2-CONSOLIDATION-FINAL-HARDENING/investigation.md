---
status: historical
layer: misc
authority: P2
audience: agent
ticket_id: TCK-20260419-V2-CONSOLIDATION-FINAL-HARDENING
artifact_type: investigation
tags: [v2, consolidation, final, hardening]
---

# Investigation: Signal Semantics & Model Drift (Milestone B/M7)

## 1. Divergence: Code vs Contract (M7)

| Contract Requirement (M7 Doc) | Current Implementation (src) | Status |
|---|---|---|
| `memory_trend_mb_per_tick` | Missing | **DRIFT** |
| `tick_compute_ms_avg` | Missing | **DRIFT** |
| `queue_utilization` | Merged into `capacity_utilization` | **COMPRESSED** |
| `work_latency_ms` | Missing | **DRIFT** |
| `dropped_work_count` | Implemented as `total_dropped_work` | ALIGNED |
| `replay_backlog_kb` | Implemented | ALIGNED |

## 2. Root Cause Analysis
The current `PressureSignals` and `RuntimeStatus` models prioritized current-tick measurements for the governor's reactive policy but failed to surface the **Trending Signals** that the M7 Law (Observability) requires for "Inspectable Stability."

## 3. Recommended Correction
To achieve a "Triple-A" trust rating, the `RuntimeStatus` must transform raw tick measurements into the trending signals required by the contract. This requires:
- Calculating the moving average (EWMA or 100-tick window) for compute time.
- Calculating the delta-per-tick (Memory Trend) to detect leaks or rapid expansion.
- Disaggregating "Capacity" into explicit "Worker" and "Queue" utilization.
