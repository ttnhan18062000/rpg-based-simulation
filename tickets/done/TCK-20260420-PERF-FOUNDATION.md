---
status: historical
layer: performance
authority: P1
audience: agent
ticket_id: TCK-20260420-PERF-FOUNDATION
phase: done
date: 2026-04-20
tags: [perf, foundation]
---

# TCK-20260420-PERF-FOUNDATION

## Title
Benchmarking and Profiling Foundation (Milestone 3)

## Status
INPROGRESS

## Tier
standard

## Type
chore

## Priority
P1

## Request Summary
Establish a trustworthy foundation for engine performance work, including per-phase timing, stable benchmark scenarios, and initial baseline measurements.

## Scope
- Define the benchmark contract (`performance_contract.md`).
- Implement per-phase timing instrumentation in `Kernel`.
- Create stable benchmark scenarios (Idle, Movement).
- Execute baseline measurements across supported profiles.
- Identify primary hot paths for optimization.

## Out of Scope
- Optimizing unsupported gameplay sections (combat, AI).
- High-risk micro-optimizations that threaten determinism.

## Acceptance Criteria
- [ ] `performance_contract.md` defines valid measurement rules.
- [ ] `Kernel` reports per-phase timing breakdown in `PressureSignals`.
- [ ] `scripts/run_benchmarks.py` can execute stable scenarios.
- [ ] Baseline TPS/Tick-cost report exists for Class B/C.
- [ ] Hot paths are identified and ranked by evidence.

## Related Tickets
- `TCK-20260420-CORE-MOVEMENT-SLICE`

## Related Docs
- `src_overview.md`
- `src_principle.md`

## Related Stored Artifacts
- None

## Related Code Areas
- `src/engine/kernel.py`
- `src/core/governance.py`
- `src/engine/runtime_status.py`

## Assumptions / Open Questions
- We assume `time.perf_counter_ns()` provides sufficient resolution for phase-level timing in micro-ticks.

## Implementation Notes
- Will use a new `BenchmarkingHarness` separate from `CertificationHarness` for pure performance loops.

## Test Summary
- None yet.

## Files Changed
- None yet.
