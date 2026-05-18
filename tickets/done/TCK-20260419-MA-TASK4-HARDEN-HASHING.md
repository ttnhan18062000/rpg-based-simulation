# TCK-20260419-MA-TASK4-HARDEN-HASHING

## Title
Audit and harden canonical hashing

## Status
DONE

## Request Summary
Finalize the `CanonicalStateHasher` to ensure it only includes authoritative fields and that it is fully deterministic. Ensure that non-authoritative state (governance, replay, transients) is strictly excluded and verify hash reproducibility.

## Scope
- [x] Audit `CanonicalStateHasher` against the Milestone A law set.
- [x] Ensure strict exclusion of non-authoritative fields.
- [x] Deep-sort nested dictionaries in `properties` if they exist.
- [x] Verify RNG checkpoint serialization stability.
- [x] Add "Hash Isolation" tests proving that external state changes do not affect the authoritative hash.

## Out of Scope
- Implementing hash-based replay validation (Milestone C).
- Changes to the RNG logic itself.

## Acceptance Criteria
- [x] Hasher only processes `AuthoritativeState`.
- [x] Hash is identical regardless of dictionary insertion order.
- [x] Hash is stable even when `Kernel` or `RuntimeStatus` transients change.
- [x] RNG internal state is canonically serialized.

## Related Tickets
- `TCK-20260419-MA-TASK1-FREEZE-LAW` (Predecessor)

## Related Docs
- `runtime_completion_contract_ma.md`
- `ma_test_matrix.md`

## Related Stored Artifacts
- `stored_artifacts/TCK-20260419-MA-TASK4-HARDEN-HASHING/investigation.md`
- `stored_artifacts/TCK-20260419-MA-TASK4-HARDEN-HASHING/plan.md`
- `stored_artifacts/TCK-20260419-MA-TASK4-HARDEN-HASHING/test_plan.md`

## Related Code Areas
- `src/engine/checkpoint.py`
- `src/core/state.py`
- `src/platform/rng.py`

## Assumptions / Open Questions
- None.

## Implementation Notes
- Hardened `CanonicalStateHasher.to_canonical_data` to be explicit about field ordering and Truth Isolation.
- Explicitly documented that RNG state (tuples) are converted to lists by `json.dumps`, which is canonical and stable.
- Verified that `json.dumps(..., sort_keys=True)` recursively handles nested dictionary sorting in `properties`.

## Test Summary
- `test_hash_construction_order_invariance`: PASSED
- `test_hash_compact_vs_pretty`: PASSED
- `test_property_sorting_in_hash`: PASSED
- `test_deep_property_sorting`: PASSED
- `test_hash_isolation`: PASSED
- `test_rng_hash_reproducibility`: PASSED

## Files Changed
- `src/engine/checkpoint.py`
- `tests/engine/test_checkpoint_reproducibility.py`

## Completion Summary
- Successfully audited and hardened canonical hashing. The `CanonicalStateHasher` now provides a trustworthy, deterministic proof of simulation identity. It is provably isolated from non-authoritative transients and correctly handles deep nested collections and the RNG internal state.
