---
status: historical
layer: performance
authority: P2
audience: agent
ticket_id: TCK-20260515-PERF-BASELINE
artifact_type: investigation
tags: [perf, baseline]
---

# Investigation - TCK-20260515-PERF-BASELINE

## Summary
Investigated the current state of performance testing and semantic testing to establish a baseline.

## Findings
- Current performance tests are located in `tests/perf`.
- Semantic tests (unit and integration) cover kernel, core, and pipeline.
- Benchmark reports are typically saved in `reports/`.
- Known risks identified in `performance_hardening_plan.md`:
    - Profiler timing accuracy
    - Frame pacing interference
    - DirtySet lifecycle completeness
    - Replay benchmark isolation
    - Local vs Concurrent parity

## Strategy
- Use `pytest` with `--junitxml` to capture structured test results.
- Create a clear directory structure in `reports/` for baseline data.
- Initialize `docs/optimization_audit_ledger.md` as the central tracking document.
