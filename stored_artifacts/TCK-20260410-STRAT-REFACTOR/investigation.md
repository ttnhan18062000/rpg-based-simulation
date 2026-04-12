# Investigation: TCK-20260410-STRAT-REFACTOR

## Identified Drift
1. **Model Inconsistency**: `StrategicKnowledgeIngestionService` attempted to emit `blockers_add_or_update`, but `StrategicUpdate` lacked this field, leading to runtime failures or data loss.
2. **Architectural Leakage**: `SocialStateApplicator` was directly mutating the world and entity narrative state, bypassing the `ActionSystem`. This violates AOA Pillar 3 (Authoritative Application).
3. **Cognition Mutation**: `BeliefService` was performing in-place decays and merges on entity memory. If executed during a worker-side appraisal on a snapshot, this could corrupt the cache or cause non-deterministic behavior.

## Root Cause Analysis
- The strategic layer was developed quickly, leading to "pragmatic" mutation shortcuts that bypassed the intent-based update loop.
- Circular dependencies in `src/actions/base.py` prevented some models (like `TurningPointRecord`) from being fully resolved in `model_rebuild`, discouraging their use in updates.

---

# Test Plan: TCK-20260410-STRAT-REFACTOR

## Unit Tests
- `StrategicState`: Verify that `blockers` list is correctly initialized and supports ID-based indexing.
- `StrategicUpdate`: Verify that `blockers_add_or_update` and `blockers_remove` fields are correctly typed and serializable.

## Integration Tests
- **Purity Scan**: Use `tests/test_strategic_consistency.py` to prove that `SocialStateApplicator` and `BeliefService.decay_stale_beliefs` do not mutate the inputs.
- **Authoritative Flow**: Verify that the `ActionSystem` correctly interprets the new updates and merges them into the entity state.
- **Snapshot Isolation**: Create a nested strategic project with objectives and blockers, snapshot it, mutate the update intents, apply them, and verify the original snapshot remains bit-for-bit identical.

## Success Criteria
- 100% pass on `tests/test_strategic_consistency.py`.
- 100% pass on existing strategic regression tests (e.g., `tests/integration/ai/test_strategic_reprioritization.py`).
