---
status: historical
layer: performance
authority: P2
audience: agent
ticket_id: TCK-20260515-PERF-BASELINE
artifact_type: test_plan
tags: [perf, baseline]
---

# Test Plan - TCK-20260515-PERF-BASELINE

## Goals
- Capture the current success/failure rate of semantic tests.
- Capture the current performance metrics (TPS, compute time) across scenarios.

## Test Matrix

| Category | Command | Target |
| --- | --- | --- |
| Semantic | `pytest tests/unit/kernel tests/unit/core tests/integration/kernel tests/integration/pipeline -q` | Baseline stability |
| Performance | `pytest tests/perf -q -m perf` | Baseline metrics |

## Verification
- Reports must be generated in `reports/tests/baseline/` and `reports/perf/baseline/`.
- No source code should be modified.
