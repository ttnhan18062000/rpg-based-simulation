---
status: historical
layer: simulation
authority: P1
audience: agent
ticket_id: TCK-20260629-SIMQ-EMIT-STATE-DIFF
artifact_type: test_plan
tags: [simq, event-extractor]
---

# Test Plan: TCK-20260629-SIMQ-EMIT-STATE-DIFF

## New Tests (tests/unit/observability/test_event_extractor_simq.py)

- `test_combat_initiated_emitted_on_first_hit` — entity at max HP prior, HP reduced this tick
- `test_combat_initiated_not_emitted_when_already_damaged` — HP was already below max prior tick
- `test_near_death_survival_emitted_when_hp_crosses_20pct` — HP was 25% prior, 15% now
- `test_near_death_survival_not_emitted_when_already_near_death` — HP was 10% prior, 5% now
- `test_near_death_survival_not_emitted_when_dead` — HP crosses 0, entity inactive
- `test_xp_granted_emitted_on_evolution_points_increase`
- `test_xp_granted_amount_correct_in_payload`
- `test_level_up_emitted_on_evolution_level_increase`
- `test_resource_node_depleted_emitted` — charges 3→0
- `test_resource_node_regenerated_emitted` — charges 0→2
- `test_resource_node_no_event_when_unchanged` — charges 3→3
- `test_demographic_birth_emitted_on_spawn`
- `test_demographic_mortality_emitted_on_despawn_without_attacker`
- `test_demographic_mortality_not_emitted_on_combat_kill` — attacker_id present

## Scoped Pytest Commands
pytest tests/unit/observability/test_event_extractor_simq.py -q
pytest tests/simulation_quality/ -q --no-header -m "not slow"
