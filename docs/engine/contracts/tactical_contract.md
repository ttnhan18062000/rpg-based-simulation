---
status: active
layer: engine
authority: P1
audience: developer
---

# Bounded Tactical Engagement Contract

This document defines the authoritative logic for local tactical decisions in the `src` engine.

## 1. Tactical Evaluation Boundary
Tactical decisions are triggered when an entity is `active`, `alive`, and its `readiness >= 100`. 
AI logic is bounded to **Local Visibility** (Default radius: 10.0 tiles) and must not consult long-horizon strategic data.

## 2. Target Selection Rules (GAP-T01)
Targets are selected from hostiles within the visibility radius using the following deterministic priority chain:

1. **Lowest HP**: Prioritize finishing off weak targets.
2. **Closest Distance**: Prioritize immediate threats (Manhattan distance).
3. **Lowest Entity ID**: Final tie-breaker for absolute determinism.

## 3. Engagement & Pursuit Rules (GAP-T02/T04)
- **Stickiness**: Entities retain their current `target_id` if the target is still alive and within a **Stickiness Radius** (Default: 15.0).
- **Pursuit**: If a target is outside combat range but within visibility, the entity sets its navigation target to the target's current position. Tactical re-evaluation itself is cadence-gated (`SystemCadence.strategic_intelligence`, default every ~10 ticks); movement execution runs every tick and, while a real `target_id` is active in the entity's own task payload, re-derives the live target position each tick (`MovementPhase.route_movement_intent`) rather than walking to a stale snapshot from the last tactical decision (`TCK-20260809-COMBAT-PURSUIT-PER-TICK-TRACE`).

## 4. Retreat & Disengage Rules (GAP-T03)
- **Retreat Threshold**: Triggered when `hp < max_hp * 0.2`.
- **Behavior**: Entity clears current combat intent and moves towards the defined "Safe Zone" (Default: (0,0)).

## 5. Anti-Stalemate Rules (GAP-T05)
- **Deadlock Detection**: Tracks `stale_ticks` in the task payload.
- **Trigger**: If `stale_ticks > 10` without a target change or outcome, the entity forces a `STALEMATE_BREAK`.
- **Behavior**: Same as Retreat.

## 6. Known Exclusions
- **Group Coordination**: Entities currently act as individuals (group coordination not yet implemented).
- **Cover Seeking**: Static obstacle awareness is currently unsupported.
- **Kiting**: Ranged entities do not yet attempt to maintain maximum distance.

## 7. Objective Target Resolution (TCK-20260807-TOWN-RETURN-TARGET-RESOLUTION-BUG)

`TacticalDecisionSystem._resolve_target_position(state, obj)` turns a `reach_location`
objective's `target` field into a concrete world position for the Pillar 5.1 arrival-dispatch
branch (`evaluate_entity_intent`). Resolution order:

1. **Int-castable `target`**: looked up first against `state.resource_nodes`, then
   `state.buildings`. A match also yields `node_id`/`building_id`, which drive the
   INTERACT/EAT/REST arrival-dispatch branches once the entity reaches the position.
2. **Stringified coordinate `target`** (e.g. `"(3.0, 4.0)"`): parsed via `ast.literal_eval`.
3. **`target_position` fallback**: if neither above yields a position, falls back to the
   objective's own `target_position` field (set at objective-creation time from the winning
   `GoalScore.target_pos` — see `evaluate_strategic_intent()`'s `ObjectiveState(...)`
   construction). This exists because some scorers (`TownScorer`, `RecoverScorer`'s no-inn
   fallback, `ResolveBlockerScorer`'s non-coordinate blocker-id case) set `target_id` to a value
   that never parses under (1) or (2) — e.g. `TownScorer`'s literal `"town_center"` — even though
   the real target position was already known and carried on `target_position` all along.
   Mirrors `StrategicIntelligenceSystem._resolve_active_objective()`'s own "detour" case, which
   already prefers `target_position` this same way.

**Node 3 never yields `node_id`/`building_id`** — an objective resolved only via the
`target_position` fallback still navigates to the position, but arrival dispatches to a bare
idle `EntityUpdate` rather than INTERACT/EAT/REST (no ID to act on). This is accepted, disclosed
scope for this ticket: it fixes "does the entity ever navigate there," not "what happens once it
arrives" — extending arrival-dispatch for `TOWN_RETURN`/`RECOVER`/`RESOLVE_BLOCKER` project kinds
(mirroring the `GUILD` kind's own dedicated `GuildVisitPhase`,
`TCK-20260807-QUEST-GUILDACTION-DEAD-WIRING`) is a separate, not-yet-filed follow-up.
