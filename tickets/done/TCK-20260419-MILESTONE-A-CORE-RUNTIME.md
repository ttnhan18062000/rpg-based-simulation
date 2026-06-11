---
status: historical
layer: misc
authority: P1
audience: agent
ticket_id: TCK-20260419-MILESTONE-A-CORE-RUNTIME
phase: done
date: 2026-04-19
tags: [milestone, core, runtime]
---

# TCK-20260419-MILESTONE-A-CORE-RUNTIME

## Title
Milestone A: Core Runtime Completion (Closure)

## Status
DONE

## Tier
standard

## Type
chore

## Priority
P1

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
- [x] No `pass` or placeholder tests remain in `tests/engine/`.
- [x] 100% test pass rate for the engine suite (57/57).

## Related Tickets
- None (First major milestone of V2 hardening).

## Related Docs
- [Runtime Completion Contract](file:///home/vboxuser/Work/rpg-based-simulation/docs/engine/runtime_completion_contract_ma.md)

## Related Code Areas
- `src/engine/kernel.py`
- `src/engine/phases.py`
- `src/engine/apply.py`
- `src/engine/checkpoint.py`
- `src/engine/governor.py`

## Implementation Notes
- Resolved double-recording of signals in `ResourceGovernor` and `Kernel`.
- Established a `pretty=True` debug mode for `to_canonical_json` to support drift auditing without compromising hash stability.

## Test Summary
- `pytest tests/engine/`: 57 PASSED.
- Added `test_checkpoint_reproducibility.py` and `test_kernel_boundaries.py`.

## Files Changed
- `src/engine/kernel.py`
- `src/engine/phases.py`
- `src/engine/apply.py` (Audit)
- `src/engine/checkpoint.py`
- `src/engine/governor.py`
- `tests/engine/test_authoritative_apply.py`
- `tests/engine/test_checkpoint_reproducibility.py`
- `tests/engine/test_kernel_boundaries.py`
- `tests/engine/test_operational_flags.py`
- `tests/engine/test_simulation_kernel_contract.py`

## Completion Summary
Milestone A is closed. The engine now possesses a hard, auditable semantic baseline that satisfies the primary det-baseline goal for V2.
