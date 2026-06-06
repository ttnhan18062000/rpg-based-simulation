# TCK-20260418-RESOURCE-KERNEL-M2

## Title
Milestone 2: Minimal Deterministic Single-Thread Kernel

## Status
DONE

## Tier
standard

## Type
chore

## Priority
P1

## Request Summary
Build the smallest correct runtime that obeys the Milestone 1 contract and proves deterministic execution.

## Scope
- Implement single-thread `Kernel.tick_once()` orchestration.
- Implement `WorldTime` progression (passive) vs `Readiness` gating (active).
- Implement singular `ApplyPath` for authoritative mutation.
- Implement `CheckpointService` for stable state hashing.
- Pin with deterministic enforcement tests in `tests/`.

## Out of Scope
- Scheduler optimization.
- Replay persistence.
- Resource governor (throttling).
- Concurrency/Workers.
- Adaptive degradation.

## Acceptance Criteria
- [x] Runnable `Kernel` with explicit phase execution.
- [x] Passive systems advance even in quiet ticks.
- [x] Entity action allowed only if `Readiness` threshold met.
- [x] All mutation flows through the `ApplyPath`.
- [x] Bit-identical checkpoints for same seed/inputs.
- [x] 100% test pass in `tests/`.

## Related Tickets
- TCK-20260418-RESOURCE-KERNEL-M1 (DONE)

## Related Docs
- `docs/engine/simulation_kernel_contract_m1.md`
- `resource_implementation_milestone_2.md`

## Related Stored Artifacts
- `stored_artifacts/TCK-20260418-RESOURCE-KERNEL-M1/`

## Related Code Areas
- `src/engine/`
- `src/core/`
- `tests/`

## Assumptions / Open Questions
- Checkpoint hashing will use canonical JSON serialization of the authoritative dict.
- Passive systems are represented as a registry of functions and their corresponding state in `AuthoritativeState`.

## Implementation Notes
- Follow the Step 5 strategy: Docs -> Types -> Tests -> Shell (Implementation).

## Test Summary
- 20 tests passed in tests/.
- test_reproducibility confirmed 10/10 identical hashes.
- test_generation_isolation confirmed immutability.

## Files Changed
- src/ (updates)
- tests/ (new engine tests)
- docs/engine/ (M2 specs)

## Completion Summary
Milestone 2 finalized. Minimal single-thread kernel is fully executable and provably deterministic. Generation-based apply path and canonical hashing are in place.
