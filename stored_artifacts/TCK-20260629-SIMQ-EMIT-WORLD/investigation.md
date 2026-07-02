---
status: historical
layer: simulation
authority: P2
audience: agent
ticket_id: TCK-20260629-SIMQ-EMIT-WORLD
artifact_type: investigation
tags: [simq, world-dynamics, event-emission]
---

# Investigation: TCK-20260629-SIMQ-EMIT-WORLD

## Pattern confirmed: WorldDynamicsSystem is @staticmethod, no event_recorder
`WorldDynamicsSystem.resolve_dynamics()` is a @staticmethod — same pattern as all other phases.

## Already done (by TCK-20260629-SIMQ-EMIT-STATE-DIFF)
- `resource_node_depleted` / `resource_node_regenerated` (node_recharged) — state diff on resource_nodes
- `demographic_birth` / `demographic_mortality` — entity spawn/despawn in entity loop

## Detectable from StateUpdate fields (new events)

### update.entities_add — direct list of new entities this tick
- `boss_spawned` — entity.kind in ("world_boss", "ancient_sentinel") in entities_add
- `raid_party_spawned` — entity.kind == "goblin_raider" in entities_add
- `calamity_spawned` — `update.last_calamity_tick_set == tick` (CalamityService sets this)

### update.world_updates[rid] — WorldUpdate per region
- `region_trauma_delta` — `world_upd.trauma_delta != 0`
- `region_ownership_changed` — `world_upd.owner_faction_id_set is not None`
- `region_transformed` — `world_upd.kind_set is not None`

### Entity loop (CombatUpdate.outcome_kind)
- `hazard_drain_applied` — `e_upd.combat.outcome_kind == "HAZARD"` and `hp_delta < 0`
  (WorldDynamicsSystem sets outcome_kind="HAZARD" on the CombatUpdate for hazard damage)

## Gaps (not detectable without phase hooks)
- `ecology_cycle_completed` — nodes_add is not distinguishable from regular node creation
- `spawn_cadence_fired` — aggregate event; entities mixed with boss/raid/calamity
- `threat_evolved` — no signal in StateUpdate
- `camp_constructed` — camp_updates only has maturity_delta and last_raid_tick_set; no construction signal

## event_category mapping
- `hazard_drain_applied` → "combat"
- `region_trauma_delta`, `region_ownership_changed`, `region_transformed` → "region"
- `calamity_spawned`, `boss_spawned`, `raid_party_spawned` → "lifecycle"
