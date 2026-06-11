---
status: historical
layer: engine
authority: P1
audience: agent
ticket_id: TCK-20260512-PERF-STAGGERED-SCHEDULER
phase: done
date: 2026-05-12
tags: [perf, staggered, scheduler]
---

# TCK-20260512-PERF-STAGGERED-SCHEDULER

## Title

Implement Staggered Entity Execution in DeterministicScheduler

## Status

OPEN

## Tier
standard

## Type
chore

## Priority
P1

## Request Summary

Optimize kernel throughput by gating ENTITY_BRAIN and ENTITY_ACT (idle) work items using SystemCadence.

## Scope

- Modify `DeterministicScheduler.select_work` to accept `SystemCadence`.
- Implement staggered gating for `ENTITY_BRAIN` and `ENTITY_ACT` (when payload is empty) based on `system_cadence.strategic_intelligence`.
- Ensure critical actions (MOVE, non-empty ACT) are not gated (remain per-tick for responsiveness).

## Out of Scope

- Gating movement or combat resolution.
- Modifying worker logic.

## Acceptance Criteria

- `ENTITY_BRAIN` work is only scheduled according to cadence.
- Benchmark `IDLE_1000` shows significant reduction in work items scheduled.
- Benchmark `STRATEGIC_500` meets performance targets (or gets closer).

## Related Tickets

- None

## Related Docs

- `docs/performance_scenarios.md`

## Related Stored Artifacts

- `stored_artifacts/performance_implementation.md`

## Related Code Areas

- `src/engine/scheduler.py`
- `src/engine/kernel.py`

## Implementation Notes

- Use `should_run(tick, entity_id, cadence)` logic.
- Default cadence should be used if none provided.

## Test Summary

- Run `scripts/run_perf_optimized.py` and verify average latency reduction.

## Files Changed

- TBD

## Completion Summary

- TBD
