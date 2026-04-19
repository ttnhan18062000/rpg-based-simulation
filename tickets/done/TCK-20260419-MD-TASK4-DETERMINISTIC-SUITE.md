# TCK-20260419-MD-TASK4-DETERMINISTIC-SUITE

## Title
Complete deterministic test suite and Real Domain Slice for Milestone D

## Status
DONE

## Request Summary
Provide final certification that the V2 concurrency layer is bit-identical to the single-thread model under high pressure and non-deterministic execution noise, and replace placeholder logic with a real domain slice.

## Scope
- [x] Implement a high-pressure determinism stress test.
- [x] Verify that neighbor context view is bit-identical across local/concurrent runs.
- [x] Prove that random worker completion orders do NOT affect the final state.
- [x] Implement a "Real Domain Slice" (Movement) in the simulation worker (Task 4 official requirement).

## Out of Scope
- Performance benchmarks (this is about correctness).

## Acceptance Criteria
- [x] `test_milestone_d_closure.py` passes with 100% bit-identical state after high-pressure concurrent execution.
- [x] `ENTITY_MOVE` logic computes clamped steps and matches local execution.
- [x] No ProtocolViolationErrors under normal high-load conditions.

## Related Tickets
- TCK-20260419-MD-TASK3-HARDEN-FALLBACK-AND-BOUNDS (DONE)

## Related Docs
- docs/engine/bounded_concurrency_contract_md.md
- resource_handbook.md
- resource_high_level_v3.md

## Related Code Areas
- src_v2/engine/kernel.py
- src_v2/engine/worker_logic.py
- src_v2/engine/worker_manager.py

## Implementation Notes
- Implemented `_handle_movement` in `worker_logic.py` to calculate clamped steps towards a target position.
- Updated `Kernel._phase_collection` to white-list `ENTITY_MOVE` for concurrent execution.
- Forced randomized `time.sleep` in the stress test worker pool to guarantee chaotic completion orders.

## Test Summary
- `tests_v2/engine/test_milestone_d_closure.py`: High-pressure determinism equivalence (Passed).

## Files Changed
- [src_v2/engine/worker_logic.py](file:///home/vboxuser/Work/rpg-based-simulation/src_v2/engine/worker_logic.py)
- [src_v2/engine/kernel.py](file:///home/vboxuser/Work/rpg-based-simulation/src_v2/engine/kernel.py)
- [tests_v2/engine/test_milestone_d_closure.py](file:///home/vboxuser/Work/rpg-based-simulation/tests_v2/engine/test_milestone_d_closure.py)

## Completion Summary
- Successfully completed Milestone D hardening. The concurrency layer is now proven equivalent to the single-threaded baseline using real domain logic (Movement). All protocol and commit laws are enforced and verified.
