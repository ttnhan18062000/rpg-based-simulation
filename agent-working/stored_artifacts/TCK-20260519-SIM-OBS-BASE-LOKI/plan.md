---
status: historical
layer: misc
authority: P2
audience: agent
ticket_id: TCK-20260519-SIM-OBS-BASE-LOKI
artifact_type: plan
tags: [sim, obs, base, loki]
---

# Implementation Plan: TCK-20260519-SIM-OBS-BASE-LOKI

## Objectives
1. Capture reproducible pre-observability baseline compute times, TPS, and final state hashes.
2. Safe-harden Promtail label configurations to prevent Loki index ingestion crashes.

## Proposed Strategy

### Step 1: Pre-observability Baseline Capture (Milestone 0)
- Capture Git hash before modifying files.
- Run `python3 scripts/run_benchmarks.py --smoke` and `python3 scripts/run_perf_baseline.py` to establish exact compute baselines and state hashes.
- Save output JSON files to `reports/perf/`.

### Step 2: Loki Cardinality Hardening (Milestone 2)
- Relabel stage modification in `promtail-config.yml`:
  ```yaml
  - labels:
      level:
      component:
  ```
  (Explicitly remove the `tick` line).
- Verify `JsonFormatter` in `src/logging/formatter.py` continues to serialize `tick` and `entity_id` to the JSON message payload so it remains fully queryable inside Loki via json parsing:
  ```logql
  {container="rpg-sim"} | json | tick = "42"
  ```
- Write a robust unit test suite to statically parse `promtail-config.yml` and assert that no dynamic labels (`tick`, `entity_id`, etc.) are promoted.
