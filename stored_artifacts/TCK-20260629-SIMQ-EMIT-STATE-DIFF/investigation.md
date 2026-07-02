---
status: historical
layer: simulation
authority: P1
audience: agent
ticket_id: TCK-20260629-SIMQ-EMIT-STATE-DIFF
artifact_type: investigation
tags: [simq, event-extractor, state-diff]
---

# Investigation: TCK-20260629-SIMQ-EMIT-STATE-DIFF

## Current Behavior

`src/observability/event_extractor.py:EventExtractor.extract()` iterates dirty entities and
compares prior_state vs current_state. Emits 6 types: LifecycleEvent (spawn/despawn),
MovementEvent, CombatDamageEvent, CombatKillEvent, GoldTransactionEvent, QuestEvent.

Resource nodes (state.resource_nodes) are NOT iterated — no node events emitted.

## Key Field Locations

- XP: `entity.identity.evolution_points: int` (IdentityComponent, state.py:474)
- Level: `entity.identity.evolution_level: int` (state.py:473)
- Combat HP: `entity.combat.hp`, `entity.combat.max_hp: int = 100` (CombatComponent, state.py:295/298)
- Lifecycle: `entity.lifecycle.active: bool`
- Resource node: `ResourceNodeState.remaining_charges: int`, `max_charges: int` (state.py:909-910)
- State nodes: `current_state.resource_nodes: Dict[int, ResourceNodeState]` (state.py:1091)

## Events to Add and Detection Logic

| Event type | Condition | Site |
|---|---|---|
| `combat_initiated` | `prior.combat.hp == prior.combat.max_hp` AND `current.combat.hp < current.combat.max_hp` AND `current.lifecycle.active` | entity loop |
| `near_death_survival` | `current.combat.hp < current.combat.max_hp * 0.2` AND `current.lifecycle.active` AND `prior.combat.hp >= prior.combat.max_hp * 0.2` | entity loop |
| `xp_granted` | `current.identity.evolution_points > prior.identity.evolution_points` | entity loop |
| `level_up` | `current.identity.evolution_level > prior.identity.evolution_level` | entity loop |
| `resource_node_depleted` | `prior_node.remaining_charges > 0` AND `current_node.remaining_charges == 0` | resource_nodes loop |
| `resource_node_regenerated` | `prior_node.remaining_charges == 0` AND `current_node.remaining_charges > 0` | resource_nodes loop |
| `demographic_birth` | entity spawned this tick (prior_ent is None) — same site as existing spawn LifecycleEvent | entity loop |
| `demographic_mortality` | entity despawned with no attacker (prior_ent existed, entity None, no combat_upd) | entity loop |

## Parity Ledger Overlap

SIMQ-CALIBRATED-001 — status: missing (partial) — this ticket adds COMBAT and PROGRESSION events.

## Risks

- `entity.identity` may be None for non-entity objects — guard with `hasattr`
- `combat_initiated` heuristic (was-at-max-HP) can misfire if entity was healed to max then re-hit
  → acceptable for calibration; document as known approximation
- `near_death_survival` threshold (20% max_hp) — hardcode as constant in extractor (not from config)
  since EventExtractor has no access to ScoringWeights
- Resource nodes may not exist in prior_state if world was reset — guard with `.get()`
