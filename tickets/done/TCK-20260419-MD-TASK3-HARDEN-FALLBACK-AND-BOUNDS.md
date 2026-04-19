# TCK-20260419-MD-TASK3-HARDEN-FALLBACK-AND-BOUNDS

## Title
Harden fallback, failure handling, and bounded execution controls

## Status
OPEN

## Request Summary
Ensure that the concurrency layer handles failures, queue saturation, and pressure signals with production-grade robustness.

## Scope
- Harden `WorkerManager.execute_batch` to guarantee result production for every packet.
- Implement exhaustive error wrapping for local fallback execution.
- Ensure worker exceptions are transformed into deterministic authoritative no-ops.
- Synchronize worker pressure signals with the Governor's evaluation loop.

## Out of Scope
- Performance optimization of the pool itself.
- Changing the Governor's mode transition logic (Milestone B is frozen).

## Acceptance Criteria
- 100% of submitted packets result in a `WorkerResult` (SUCCESS or FAILURE).
- Local fallback results include `compute_time_ns` and status metadata.
- Internal worker crashes do not leak into the Kernel; they produce `ResultStatus.FAILURE`.
- Pressure signals correctly reflect peak queue and worker utilization.

## Related Tickets
- TCK-20260419-MD-TASK2-HARDEN-PROTOCOL-AND-COMMIT-LAW (DONE)

## Related Docs
- docs/engine/bounded_concurrency_contract_md.md

## Related Stored Artifacts
- None

## Related Code Areas
- src_v2/engine/worker_manager.py
- src_v2/engine/kernel.py
- tests_v2/engine/test_fallback_hardening.py

## Assumptions / Open Questions
- None.

## Implementation Notes
- Use `_wrap_work` for both concurrent and local paths.
- Catch `Future.result()` exceptions in the batch collector.

## Test Summary
- New test suite: `tests_v2/engine/test_fallback_hardening.py`.

## Files Changed
- TBD

## Completion Summary
- TBD
