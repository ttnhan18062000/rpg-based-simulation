---
status: historical
layer: engine
authority: P2
audience: agent
ticket_id: TCK-20260520-SIM-OBS-PHASE4-M17
artifact_type: investigation
tags: [sim, obs, phase4, m17]
---

# Investigation - Milestone 17: Baseline Generator

## Pure Python Statistics Equations

Since we must avoid dependencies on external numerical libraries like `numpy` or `scipy`, we will implement clear pure-Python algorithms for all metric distributions:

1. **Percentile Calculation (Nearest Rank / Linear Interpolation)**:
   - For a sorted list of values $V$:
     - Index $i = P / 100 \times (\text{len}(V) - 1)$
     - Lower index $k = \lfloor i \rfloor$, upper index $c = \lceil i \rceil$
     - If $k == c$, return $V[k]$
     - Otherwise, interpolate: $V[k] + (i - k) \times (V[c] - V[k])$
   - This gives highly accurate percentiles matching standard statistical tools!

2. **Standard Deviation**:
   - Mean $\mu = \sum v / N$
   - Variance $\sigma^2 = \sum (v - \mu)^2 / N$ (or $N - 1$ for sample standard deviation; let's use population variance $N$ for deterministic consistency).
   - Standard Deviation $\sigma = \sqrt{\sigma^2}$.

3. **Metric Extraction**:
   - `health_score`, `critical_count`, `warning_count`, `hard_law_violation_count` are loaded from `run_index.jsonl`.
   - `tick_compute_ms_p95` and `memory_rss_bytes_max` are resolved from individual `run_report.json` files or metric timeline logs under `runs/<run_id>/run_report.json` if available.
   - If a report is not available or has no metrics (e.g. LIGHT mode), we fall back gracefully to default values (e.g. 0.0 or standard safe values).
