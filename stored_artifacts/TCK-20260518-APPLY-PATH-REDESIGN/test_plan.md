# Test Plan - Milestone 14 ApplyPath Structural Redesign

## Unit Tests (`tests/unit/optimization/test_apply_plan_builder.py`)
- Verify `ApplyPlanBuilder.build_plan` correctly groups navigation, combat, inventory, and strategic updates.
- Verify no-op updates produce empty change plans.
- Verify cache invalidation hints are correctly flagged when dirty sets or specific updates are present.

## Integration Parity Tests (`tests/integration/optimization/test_apply_plan_parity.py`)
- Apply a complex `StateUpdate` across 500 entities using both the old `_apply_entity_update_to_dict` logic and the new `ApplyPlan` + `ApplyPath` execution.
- Assert exact match on all entity attributes, state hashes, and telemetry metrics.

## Performance Tests (`tests/perf/test_apply_plan_perf.py`)
- Benchmark `ApplyPath.apply_generation` with and without `ApplyPlan` precomputation across 1,000 entities with active movement and combat.
- Assert lower execution time and reduced p95 latency.
