# TCK-20260419-MILESTONE-A-CORE-RUNTIME

## Title
Milestone A: Core Runtime Completion (Closure)

## Status
DONE

## Request Summary
Harden the engine's core runtime into a provably deterministic single-process baseline by aligning with the 6-phase TickPhase contract and implementing canonical checkpointing.

## Scope
- Refactor `Kernel` and `TickPhase`.
- Move non-authoritative activities to post-tick hooks.
- Implement human-readable canonical state hashing.
- Harden the authoritative apply path.
- Close all placeholder core-law tests.

## Out of Scope
- Multi-worker orchestration (Milestone B).
- Persistence throughput optimization.
- Complex governance policies (beyond baseline).

## Acceptance Criteria
- [x] Kernel executes exactly 6 authoritative phases.
- [x] Persistence/Replay emission is non-authoritative and occurs after tick advancement.
- [x] Hashing uses compact canonical JSON string as the source of truth.
- [x] All state collections are sorted before hashing/apply.
- [x] No `pass` or placeholder tests remain in `tests_v2/engine/`.
- [x] 100% test pass rate for the engine suite (57/57).

## Related Tickets
- None (First major milestone of V2 hardening).

## Related Docs
- [Runtime Completion Contract](file:///home/vboxuser/Work/rpg-based-simulation/docs/engine/runtime_completion_contract_ma.md)

## Related Code Areas
- `src_v2/engine/kernel.py`
- `src_v2/engine/phases.py`
- `src_v2/engine/apply.py`
- `src_v2/engine/checkpoint.py`
- `src_v2/engine/governor.py`

## Implementation Notes
- Resolved double-recording of signals in `ResourceGovernor` and `Kernel`.
- Established a `pretty=True` debug mode for `to_canonical_json` to support drift auditing without compromising hash stability.

## Test Summary
- `pytest tests_v2/engine/`: 57 PASSED.
- Added `test_checkpoint_reproducibility.py` and `test_kernel_boundaries.py`.

## Files Changed
- `src_v2/engine/kernel.py`
- `src_v2/engine/phases.py`
- `src_v2/engine/apply.py` (Audit)
- `src_v2/engine/checkpoint.py`
- `src_v2/engine/governor.py`
- `tests_v2/engine/test_authoritative_apply.py`
- `tests_v2/engine/test_checkpoint_reproducibility.py`
- `tests_v2/engine/test_kernel_boundaries.py`
- `tests_v2/engine/test_operational_flags.py`
- `tests_v2/engine/test_simulation_kernel_contract.py`

## Completion Summary
Milestone A is closed. The engine now possesses a hard, auditable semantic baseline that satisfies the primary det-baseline goal for V2.
