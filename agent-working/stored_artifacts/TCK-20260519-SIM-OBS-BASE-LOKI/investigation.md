---
status: historical
layer: misc
authority: P2
audience: agent
ticket_id: TCK-20260519-SIM-OBS-BASE-LOKI
artifact_type: investigation
tags: [sim, obs, base, loki]
---

# Investigation Notes: Observability Baselines and Loki Labels

## Current State Observations

### 1. Prometheus Endpoint Behavior
- Checked HTTP router mounting in `src/api/server.py` and `src/api/engine_manager.py`.
- Verified `/metrics` returns HTTP 404 because no endpoint exists to serve metrics yet.

### 2. Promtail Label Cardinality
- Inspected [promtail-config.yml](file:///home/vboxuser/Work/rpg-based-simulation/promtail-config.yml).
- Identified `tick` promoted as a label under `scrape_configs` -> `pipeline_stages` -> `labels`.
- This index promotion creates a new Loki stream partition every tick, which will quickly crash Loki's memory/index allocator in long runs.

### 3. Performance Benchmarks
- Found `scripts/run_benchmarks.py --smoke` which executes the standard CI-scoped smoke scenarios.
- Found `scripts/run_perf_baseline.py` which executes scaled baseline runs and saves to `reports/perf/latest.json`.
- Verified these benchmark suites are intact and clean.
