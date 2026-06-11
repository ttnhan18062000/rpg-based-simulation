---
status: historical
layer: performance
authority: P2
audience: agent
ticket_id: TCK-20260517-PERF-OPT-HARDENING
artifact_type: test_plan
tags: [perf, opt, hardening]
---

# Test Plan: Performance Optimization Hardening

## Automated Unit Tests
- Command: `pytest tests/unit`
- Expected: 100% pass rate (730 passed). Ensure zero regressions in regional consequences, combat, strategic, and kernel logic.

## Performance Integrity & Parity Tests
- Command: `pytest tests/perf/test_dirty_parity.py`
  - Verifies O(Dirty) vs O(N) full-scan parity.
- Command: `pytest tests/perf/test_concurrency_parity.py`
  - Verifies local vs concurrent execution parity.
- Command: `pytest tests/perf/test_profiler_integrity.py`
  - Verifies profiler and phase accounting integrity.

## Performance Benchmark & Smoke Suite
- Command: `pytest -m "perf and not slow" tests/perf`
  - Validates fast CI-safe benchmark execution without deepcopy timeouts.
- Command: `pytest -m "perf and slow" tests/perf`
  - Validates slow 5,000-entity stress benchmarks.
