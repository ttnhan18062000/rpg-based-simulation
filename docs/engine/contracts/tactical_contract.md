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
- **Pursuit**: If a target is outside combat range but within visibility, the entity sets its navigation target to the target's current position.

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
