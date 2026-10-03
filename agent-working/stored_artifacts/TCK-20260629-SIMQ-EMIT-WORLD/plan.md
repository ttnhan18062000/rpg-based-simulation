---
status: historical
layer: simulation
authority: P2
audience: agent
ticket_id: TCK-20260629-SIMQ-EMIT-WORLD
artifact_type: plan
tags: [simq, world-dynamics, event-extractor]
---

# Plan: TCK-20260629-SIMQ-EMIT-WORLD

## Ordered Steps

1. In EventExtractor.extract() entity loop — inside the existing entity loop, after cognition block:
   a. `hazard_drain_applied` — check `e_upd_ext.combat` outcome_kind:
      ```python
      combat_upd = getattr(e_upd_ext, "combat", None)
      if combat_upd and getattr(combat_upd, "outcome_kind", None) == "HAZARD":
          hp_delta = getattr(combat_upd, "hp_delta", 0)
          if hp_delta < 0:
              events.append(SimulationEvent(event_type="hazard_drain_applied", event_category="combat", ...
                  payload={"damage": int(-hp_delta)}))
      ```

2. After the entity loop and resource_node loop — add a world_updates section:
   ```python
   for rid, w_upd in (getattr(update, "world_updates", None) or {}).items():
       if getattr(w_upd, "trauma_delta", 0.0) != 0.0:
           events.append(SimulationEvent(event_type="region_trauma_delta", event_category="region",
               payload={"region_id": rid, "delta": w_upd.trauma_delta}))
       if getattr(w_upd, "owner_faction_id_set", None) is not None:
           events.append(SimulationEvent(event_type="region_ownership_changed", event_category="region",
               payload={"region_id": rid, "new_owner": str(w_upd.owner_faction_id_set)}))
       if getattr(w_upd, "kind_set", None) is not None:
           events.append(SimulationEvent(event_type="region_transformed", event_category="region",
               payload={"region_id": rid, "new_kind": w_upd.kind_set}))
   ```

3. Calamity + entity spawn from entities_add:
   ```python
   if getattr(update, "last_calamity_tick_set", None) == tick:
       events.append(SimulationEvent(event_type="calamity_spawned", event_category="lifecycle",
           payload={"tick": tick}))
   for new_ent in (getattr(update, "entities_add", None) or []):
       kind = getattr(new_ent, "kind", None)
       if kind in ("world_boss", "ancient_sentinel"):
           events.append(SimulationEvent(event_type="boss_spawned", event_category="lifecycle",
               payload={"kind": kind, "entity_id": getattr(new_ent, "id", None)}))
       elif kind == "goblin_raider":
           events.append(SimulationEvent(event_type="raid_party_spawned", event_category="lifecycle",
               payload={"kind": kind, "entity_id": getattr(new_ent, "id", None)}))
   ```

4. Write tests in `tests/unit/observability/test_event_extractor_world.py`.

## Scope Guards
- Do NOT re-emit resource_node_depleted or demographic_birth (already done in E2)
- Only emit region events when the specific field is non-zero/non-None
- calamity_spawned is global (no entity_id), boss/raid have entity_id from the new entity
