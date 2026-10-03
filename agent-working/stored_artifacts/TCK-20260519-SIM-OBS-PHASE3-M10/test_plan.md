---
status: historical
layer: engine
authority: P2
audience: agent
ticket_id: TCK-20260519-SIM-OBS-PHASE3-M10
artifact_type: test_plan
tags: [sim, obs, phase3, m10]
---

# Test Plan - Metric Window Recorder

## Unit Tests
Path: `tests/unit/observability/test_metric_window_recorder.py`
- Test `MetricWindowRecord` serialization to/from JSON.
- Test `MetricWindowAccumulator` with controlled snapshots:
  - Verify exact averages: alive entities, gold total, tick compute ms.
  - Verify max memory RSS bytes (converting MB to bytes).
  - Verify exact p95 duration math with sorted list percentile resolution.
  - Verify event/violation counts.
  - Verify dominant governor mode calculation.
  - Verify partial window flushing logic.
  - Verify handling of missing optional snapshot values.

## Integration Tests
Path: `tests/integration/observability/test_metric_windows_flow.py`
- Run a sample Kernel scenario under `LIGHT` mode.
- Verify `metric_windows.jsonl` is correctly generated under the standard run folder.
- Parse the resulting JSONL records to check for correct window tick bounds (e.g. 1-100, 101-200, or partial bounds).
- Verify state hash parity with `OFF` vs `LIGHT` modes to guarantee absolute non-interference with RNG and authoritative execution flow.
