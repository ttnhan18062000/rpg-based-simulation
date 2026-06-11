---
status: historical
layer: misc
authority: P2
audience: agent
ticket_id: TCK-20260519-SIM-OBS-BASE-LOKI
artifact_type: test_plan
tags: [sim, obs, base, loki]
---

# Test Plan: TCK-20260519-SIM-OBS-BASE-LOKI

## Automated Tests

### 1. Static Label Cardinality Validation
- Create `tests/logging/test_loki_cardinality.py`.
- Tests to write:
  - `test_promtail_labels_are_safe()`: Loads `promtail-config.yml` using `pyyaml` (or standard string parsing if dependencies are strict) and checks that no high-cardinality label keys (`tick`, `entity_id`, `worker_id`, `causal_id`, `transaction_id`) exist in the list of pipeline stage labels.
  - `test_formatter_serializes_fields()`: Unit-tests `JsonFormatter` directly by passing mock log records containing `tick`, `component`, `worker_id`, and `entity_id` to verify that they are successfully encoded in the JSON string payload.

## Manual Verification
- Execute:
  ```bash
  python3 scripts/run_benchmarks.py --smoke
  python3 scripts/run_perf_baseline.py
  ```
- Compare the output reports against standard expected outputs.
