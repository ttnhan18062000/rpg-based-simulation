---
status: historical
layer: engine
authority: P2
audience: agent
ticket_id: TCK-20260516-ENGINE-PERFORMANCE-PHASE2
artifact_type: test_plan
tags: [engine, performance, phase2]
---

# Test Plan: Phase 2 Performance

## Automated Benchmarks
- `pytest tests/perf/test_perf_movement.py -k "100 or 500 or 1000"`
  Expected outcome: Pass with sub-100ms p95 latency.

## Sub-phase Profiling
- `python3 artifacts/profile_subphases.py`
  Expected outcome: Locomotion under 5ms, Collection under 2ms, Total tick under 15ms.

## Determinism Regression Suite
- `pytest tests/integration/kernel/test_phase2_determinism.py`
- `pytest tests/integration/kernel/test_executor_determinism.py`
- `pytest tests/integration/kernel/test_minimal_kernel.py`
