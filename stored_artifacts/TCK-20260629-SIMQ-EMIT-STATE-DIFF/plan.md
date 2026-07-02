---
status: historical
layer: simulation
authority: P1
audience: agent
ticket_id: TCK-20260629-SIMQ-EMIT-STATE-DIFF
artifact_type: plan
tags: [simq, event-extractor]
---

# Plan: TCK-20260629-SIMQ-EMIT-STATE-DIFF

## Ordered Steps

1. Add `_NEAR_DEATH_THRESHOLD = 0.2` constant at top of `event_extractor.py`.

2. In the entity loop (after existing kill detection, before gold events):
   a. Emit `combat_initiated` — if `prior_ent.combat.hp == prior_ent.combat.max_hp`
      AND `entity.combat.hp < entity.combat.max_hp` AND `entity.lifecycle.active`.
      Use `SimulationEvent(event_type="combat_initiated", ...)`.
   b. Emit `near_death_survival` — if current HP < 20% max AND alive AND prior HP was >= 20% max.
      Payload: `{"hp": entity.combat.hp, "max_hp": entity.combat.max_hp}`.
   c. Emit `xp_granted` — if `entity.identity.evolution_points > prior_ent.identity.evolution_points`.
      Guard with `hasattr(entity, "identity") and hasattr(prior_ent, "identity")`.
      Payload: `{"amount": delta}`.
   d. Emit `level_up` — if `entity.identity.evolution_level > prior_ent.identity.evolution_level`.
      Payload: `{"new_level": entity.identity.evolution_level}`.
   e. At spawn site: also emit `demographic_birth` (same payload as LifecycleEvent).
   f. At despawn site (prior_ent not None, entity None): also emit `demographic_mortality`
      when no attacker (no combat_upd with attacker_id on this entity).

3. After entity loop: add resource_nodes loop.
   Iterate `current_state.resource_nodes.items()`.
   For each node_id, node: get `prior_node = prior_state.resource_nodes.get(node_id)`.
   If `prior_node` is None: skip (new node this tick, not a depletion/regen event).
   Emit `resource_node_depleted` if `prior_node.remaining_charges > 0 and node.remaining_charges == 0`.
   Emit `resource_node_regenerated` if `prior_node.remaining_charges == 0 and node.remaining_charges > 0`.
   Payload for both: `{"node_id": node_id, "charges": node.remaining_charges, "max_charges": node.max_charges}`.
   Guard: only if `hasattr(current_state, "resource_nodes")`.

4. Write unit tests in `tests/unit/observability/test_event_extractor_simq.py`.
   Use minimal mock state objects per test case.

## Scope Guards

- Do NOT modify existing event emission (LifecycleEvent, CombatDamageEvent, etc.)
- Do NOT import from `src/simulation_quality/`
- Do NOT add volumization guards for the new events (calibration needs them always)
- `combat_initiated` fires once per first-hit only (at-max-HP heuristic)

## Acceptance Criteria → Steps

- `combat_initiated` emitted → step 2a
- `near_death_survival` emitted when HP crosses 20% → step 2b
- `xp_granted` with amount → step 2c
- `level_up` → step 2d
- `resource_node_depleted` / `resource_node_regenerated` → step 3
- `demographic_birth` / `demographic_mortality` → step 2e/f
- Tests cover all → step 4
