---
status: historical
layer: engine
authority: P2
audience: agent
ticket_id: TCK-20260520-SIM-OBS-PHASE4-M18
artifact_type: investigation
tags: [sim, obs, phase4, m18]
---

# Investigation - Milestone 18: Baseline Comparator and Drift Detector

## Outliers and Drift Formulas

1. **Outliers detection**:
   - Outliers are identified when:
     - `health_score` is less than `baseline.metrics["health_score"].p10`
     - `anomaly_count` is greater than `baseline.metrics["anomaly_count"].p95`
     - `memory_rss_bytes_max` is greater than `baseline.metrics["memory_rss_bytes_max"].p95`
   - Identifying outlier seeds is crucial for balance sweeps to catch regression issues that only manifest on certain seeds (such as deadlock, resource starvation, etc.).

2. **Drift magnitude & direction**:
   - For each core metric (e.g. `health_score`, `tick_compute_ms_p95`, `memory_rss_bytes_max`, `anomaly_count`):
     - `magnitude = sweep_mean - baseline_mean`
     - Direction of drift:
       - **Health Score**: If `magnitude < 0`, the direction is `DEGRADED`. If `magnitude > 0`, it is `IMPROVED`.
       - **Tick Compute Time**: If `magnitude > 0`, the direction is `DEGRADED`. If `magnitude < 0`, it is `IMPROVED`.
       - **Memory RSS**: If `magnitude > 0`, the direction is `DEGRADED`. If `magnitude < 0`, it is `IMPROVED`.
       - **Anomaly Count**: If `magnitude > 0`, the direction is `DEGRADED`. If `magnitude < 0`, it is `IMPROVED`.
       - If `magnitude == 0` or very close to zero, it is `STABLE`.
