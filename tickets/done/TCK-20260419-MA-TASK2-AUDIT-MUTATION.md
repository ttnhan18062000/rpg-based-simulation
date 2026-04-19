# TCK-20260419-MA-TASK2-AUDIT-MUTATION

## Title
Audit and close all authoritative mutation paths

## Status
DONE

## Request Summary
Make the authoritative apply path singular, explicit, and provably exclusive. Ensure no hidden mutation paths exist through aliasing of nested mutable collections.

## Scope
- [x] Audit all state mutation paths (Kernel, Scheduler, Workers).
- [x] Remove direct mutations outside of `ApplyPath`.
- [x] Harden `ApplyPath` to ensure deterministic ordering of all collection updates.
- [x] Implement immutability and aliasing tests.

## Out of Scope
- Redesigning work classes or state models.
- Deep-freezing every object (unless necessary for law closure).

## Acceptance Criteria
- [x] Singular apply path enforced.
- [x] No direct mutation found in audit or added in refactor.
- [x] Deterministic ordering of entity/resource/periodic/debt updates.
- [x] Tests prove prior-state purity and anti-aliasing.

## Related Tickets
- `TCK-20260419-MA-TASK1-FREEZE-LAW` (Predecessor)

## Related Docs
- `runtime_completion_contract_ma.md`
- `ma_test_matrix.md`

## Related Stored Artifacts
- `stored_artifacts/TCK-20260419-MA-TASK2-AUDIT-MUTATION/investigation.md`
- `stored_artifacts/TCK-20260419-MA-TASK2-AUDIT-MUTATION/plan.md`
- `stored_artifacts/TCK-20260419-MA-TASK2-AUDIT-MUTATION/test_plan.md`

## Related Code Areas
- `src_v2/engine/apply.py`
- `src_v2/engine/kernel.py`
- `src_v2/core/state.py`
- `src_v2/core/updates.py`

## Assumptions / Open Questions
- Assumption: `properties` dictionary in `EntityState` is the main target for aliasing issues.

## Implementation Notes
- Hardened `ApplyPath._apply_entity_update` to be explicit about dictionary cloning.
- Refactored `Kernel._phase_collection` to use `replace(subject, properties=dict(subject.properties))` when creating `WorkerPacket`. This ensures that even if a worker mutates the `subject` reference (within-tick), it doesn't leak into the kernel's authoritative reference.
- Created `tests_v2/engine/test_no_hidden_mutation.py` to prove these laws.

## Test Summary
- `test_prior_state_purity_deep_properties`: PASSED
- `test_no_mutation_leak_from_worker_snapshot`: PASSED
- `test_apply_determinism_sorting`: PASSED
- `test_auth_state_is_frozen`: PASSED
- `test_entity_state_is_frozen`: PASSED

## Files Changed
- `src_v2/engine/apply.py`
- `src_v2/engine/kernel.py`
- `tests_v2/engine/test_no_hidden_mutation.py`

## Completion Summary
- Successfully audited and closed mutation paths. The `ApplyPath` is now the singular authoritative entry point, and the `Kernel` now protects the state during the collection phase by passing entity snapshots to workers. This ensures absolute prior-state purity and anti-aliasing.
