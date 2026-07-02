---
status: done
layer: simulation
authority: P2
audience: agent
ticket_id: TCK-20260629-SIMQ-EMIT-WORLD
phase: done
date: 2026-06-29
tags: [simq, observability, event-gap, world-dynamics]
---

# TCK-20260629-SIMQ-EMIT-WORLD

## Title
SimQ: Emit WORLD Dynamics Pillar Events from PP-22 / WD-01 through WD-15

## Status
DONE

## Tier
standard

## Type
feature

## Priority
P2

## Request Summary
WORLD pillar requires 14 event types. WorldDynamicsSystem is @staticmethod with no
event_recorder. 7 events detectable from StateUpdate fields: hazard_drain_applied,
region_trauma_delta, region_ownership_changed, region_transformed, calamity_spawned,
boss_spawned, raid_party_spawned. 4 events already done in E2 (resource_node_depleted,
resource_node_regenerated, demographic_birth, demographic_mortality). 3 events are gaps.

## Scope
Extended EventExtractor with 7 WORLD events from StateUpdate.world_updates,
StateUpdate.entities_add, StateUpdate.last_calamity_tick_set, and CombatUpdate.outcome_kind.

## Out of Scope
- `ecology_cycle_completed`, `spawn_cadence_fired`, `threat_evolved`, `camp_constructed`
  — no clear signal in StateUpdate

## Acceptance Criteria
- [x] `hazard_drain_applied` from entity combat_upd.outcome_kind=="HAZARD"
- [x] `region_trauma_delta` from world_updates.trauma_delta != 0
- [x] `region_ownership_changed` from world_updates.owner_faction_id_set
- [x] `region_transformed` from world_updates.kind_set
- [x] `calamity_spawned` from last_calamity_tick_set == tick
- [x] `boss_spawned` from entities_add with kind in ("world_boss","ancient_sentinel")
- [x] `raid_party_spawned` from entities_add with kind=="goblin_raider"
- [x] 17 unit tests pass; 853 total pass

## Related Stored Artifacts
- `stored_artifacts/TCK-20260629-SIMQ-EMIT-WORLD/`

## Related Code Areas
- `src/observability/event_extractor.py` — added hazard block (entity loop) + world section
- `tests/unit/observability/test_event_extractor_world.py` — new (17 tests)

## Files Changed
- `src/observability/event_extractor.py`
- `tests/unit/observability/test_event_extractor_world.py` — new (17 tests)
- `staging_artifacts/TCK-20260629-SIMQ-EMIT-WORLD/` → `stored_artifacts/`

## Completion Summary
7 WORLD events live. 3 events remain as gaps (ecology_cycle_completed, spawn_cadence_fired,
threat_evolved, camp_constructed). WORLD pillar will show non-zero events in calibration.
