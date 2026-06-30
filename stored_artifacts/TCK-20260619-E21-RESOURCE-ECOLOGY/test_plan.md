---
ticket_id: TCK-20260619-E21-RESOURCE-ECOLOGY
phase: test_plan
date: 2026-06-20
---

# Test Plan: Resource Ecology Regeneration

## Unit Tests (new file: tests/unit/world/test_resource_ecology.py)

Written in E21B:

### test_resource_node_regen_fixed_rate
- Build a `ResourceNodeState` with `remaining_charges=1`, `max_charges=5`, `regen_rate_per_tick=2`
- Simulate 2 ecology ticks
- Assert `remaining_charges` increases by 2 per tick (capped at `max_charges`)

### test_resource_node_does_not_exceed_max_charges
- Node with `remaining_charges=4`, `max_charges=5`, `regen_rate_per_tick=3`
- After 1 regen tick: assert `remaining_charges == 5` (not 7)

### test_resource_depleted_event_emitted
- Node with `remaining_charges=1`; apply harvest that takes last charge
- Assert `RESOURCE_DEPLETED` event is in resulting `StateUpdate` events

### test_resource_recovered_event_emitted
- Node with `remaining_charges=0`, `regen_rate_per_tick=1`
- After 1 ecology tick: assert `RESOURCE_RECOVERED` event emitted
- After 2 ecology ticks: assert event NOT emitted again (already recovered)

## Unit Tests (new file: tests/unit/domains/adventure/test_depletion_scoring.py)

Written in E21C:

### test_harvesting_score_decreases_with_depletion
- Full node: `remaining_charges=max_charges=5`; call `AdventureRouteScorer.score()` for `GATHER_RESOURCE` route
- Depleted node: `remaining_charges=1`, `max_charges=5`
- Assert depleted score ≤ 0.5 × full score

### test_empty_node_scores_zero_benefit
- Node with `remaining_charges=0`
- Assert `expected_benefit` component is 0 for that node's harvest route

## Integration Tests (new file: tests/integration/scenarios/test_resource_depletion.py)

Written in E21D:

### test_depletion_and_recovery_in_1000_tick_run
- @pytest.mark.slow @pytest.mark.integration
- 1000-tick run with at least one resource-rich world (set regen_rate_per_tick=1 on test nodes)
- Assert: `RESOURCE_DEPLETED` appears in world events AND `RESOURCE_RECOVERED` appears after it

### test_regional_scarcity_rises_after_depletion
- After depletion window: assert `RegionalPressureModel` scarcity field is higher than pre-depletion baseline
- (Can be asserted on the world_emergence models directly, no full simulation needed)

## Validation Commands
```bash
# Unit suite (fast)
pytest tests/unit/world/test_resource_ecology.py -x -v
pytest tests/unit/domains/adventure/test_depletion_scoring.py -x -v

# Integration (slow)
pytest tests/integration/scenarios/test_resource_depletion.py -x -v -m slow

# Regression — verify no existing tests broken
pytest tests/unit/resource/ -x -v
pytest tests/unit/world/ -x -v
```
