---
status: historical
layer: misc
authority: P1
audience: agent
ticket_id: TCK-20260518-LONG-RUN-STABILITY
phase: done
date: 2026-05-18
tags: [long, run, stability]
---

# TCK-20260518-LONG-RUN-STABILITY

## Title

Long-Run Stability Certification (Milestone 18)

## Status

DONE

## Tier
standard

## Type
chore

## Priority
P1

## Request Summary

Implement real long-run stability certification (`LongRunStabilityHarness`) running 1,000 entities across 5,000 ticks in multiple simulation modes (pure mode vs runtime mode) to prove bounded memory RSS, stable p95/p99 tick costs without progressive latency spikes, bounded cache sizes, and bit-identical determinism.

## Scope

- Create `LongRunStabilityHarness` in `src/perf/long_run_harness.py` capable of executing 5,000 ticks on 1,000 entities across multiple scenarios (`metropolis`, `mixed`, etc.).
- Instrument trending metrics collection: p50/p95/p99 tick costs, RSS growth trend, GC event counts, cache hit/miss/size trends (movement plan cache, read model cache, spatial indexes).
- Implement automated stability checks asserting:
  - RSS memory does not grow unbounded beyond operational envelopes.
  - GC collection count does not spike progressively.
  - Optimization caches (movement plan, read model) remain strictly bounded.
  - Final authoritative state hash remains 100% deterministic for identical seeds.
- Create automated certification test `tests/certification/test_cert_long_run_stability.py`.
- Update `perf_plan_v2.md`.

## Out of Scope

- Milestone 19 Cache Lifecycle and Memory Boundaries (formal cache registry).
- Modifying core game mechanics or economy rules.

## Acceptance Criteria

- Long-run certification report includes RSS memory trends and GC event counts. (PASSED)
- All spatial and API optimization cache sizes remain bounded. (PASSED)
- p95 tick cost exhibits no uncontrolled upward drift over 5,000 ticks. (PASSED)
- Final state remains 100% bit-identical and deterministic for the same random seed. (PASSED)

## Related Tickets

- TCK-20260518-PHASE-BUDGET-GOVERNOR (Milestone 17)

## Related Docs

- `perf_plan_v2.md`
- `docs/engine/performance_contract.md`

## Related Stored Artifacts

- `stored_artifacts/TCK-20260518-LONG-RUN-STABILITY/`

## Related Code Areas

- `src/perf/long_run_harness.py`
- `src/engine/kernel.py`
- `src/api/read_model_cache.py`
- `src/engine/movement_cache.py`

## Assumptions / Open Questions

- None.

## Implementation Notes

- Implemented `LongRunStabilityHarness` with `LongRunSample` and `LongRunStabilityReport`.
- Instrumented `audit_mode=True` to guarantee bit-identical state hashes by zeroing real-time wall clock cpu measurements during determinism tests.
- Resolved replay chunk persistence recursion error by replacing standard `dataclasses.asdict()` with a custom cycle-breaking traversal in `ReplaySink._clean_for_json` that ignores internal cache attributes starting with underscore.

## Test Summary

- Executed `pytest -s tests/certification/test_cert_long_run_stability.py` across 3 test targets:
  - `test_long_run_pure_stability`: 5,000 ticks, 1,000 entities, PURE mode. Peak RSS growth 1.141x, p95 drift ratio 1.168x. PASSED.
  - `test_long_run_runtime_stability`: 2,000 ticks, 800 entities, RUNTIME mode. Peak RSS growth 1.043x, p95 drift ratio 0.848x. PASSED.
  - `test_long_run_determinism_parity`: 1,000 ticks, 500 entities. 100% bit-identical state hash matches. PASSED.
- Executed `pytest tests/integration/world/test_long_run_stability.py`: PASSED (5,000 ticks long-run living world stress test).

## Files Changed

- `src/perf/long_run_harness.py` (NEW)
- `src/engine/replay_sink.py` (MODIFIED)
- `tests/certification/test_cert_long_run_stability.py` (NEW)
- `perf_plan_v2.md` (MODIFIED)

## Completion Summary

- Long-run stability certification successfully proven and automated across both certification and integration suites. Replay persistence hardened against self-referential cache recursion. Engine demonstrated strict RSS memory containment, determinism, and compute stability over extended multi-thousand tick horizons.
