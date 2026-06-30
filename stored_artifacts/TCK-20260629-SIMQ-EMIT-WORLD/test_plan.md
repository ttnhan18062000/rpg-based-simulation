---
status: historical
layer: simulation
authority: P2
audience: agent
ticket_id: TCK-20260629-SIMQ-EMIT-WORLD
artifact_type: test_plan
tags: [simq, world-dynamics, event-extractor]
---

# Test Plan: TCK-20260629-SIMQ-EMIT-WORLD

## New Tests (tests/unit/observability/test_event_extractor_world.py)

- `test_hazard_drain_applied_emitted` — combat_upd outcome_kind==HAZARD, hp_delta<0
- `test_hazard_drain_not_emitted_for_normal_combat` — outcome_kind=COMBAT_DAMAGE
- `test_region_trauma_delta_emitted` — world_updates has trauma_delta != 0
- `test_region_trauma_delta_not_emitted_when_zero` — trauma_delta == 0.0
- `test_region_ownership_changed_emitted` — world_updates has owner_faction_id_set
- `test_region_transformed_emitted` — world_updates has kind_set
- `test_calamity_spawned_emitted` — last_calamity_tick_set == tick
- `test_calamity_not_emitted_when_tick_mismatch` — last_calamity_tick_set != tick
- `test_boss_spawned_emitted_for_world_boss` — entities_add has kind==world_boss
- `test_boss_spawned_emitted_for_ancient_sentinel` — entities_add has kind==ancient_sentinel
- `test_raid_party_spawned_emitted` — entities_add has kind==goblin_raider
- `test_regular_spawn_no_world_event` — entities_add has kind==hero → no boss/raid event

## Scoped Pytest Commands

pytest tests/unit/observability/test_event_extractor_world.py -q
pytest tests/unit/observability/ -q --no-header -m "not slow"
