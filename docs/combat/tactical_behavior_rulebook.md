---
status: historical
layer: combat
authority: P2
audience: developer
---

# Tactical Behavior Rulebook (Milestone 4)

## Purpose
This rulebook defines how entities use combat and movement primitives deliberately to achieve tactical advantages.

## Tactical Layer Boundaries
Tactical AI does not dictate *what* goal an entity has (e.g., Combat vs Wander), but *how* it executes that goal spatially. It consumes the authoritative `MovementModel` and `ActionSystem` without bypassing their constraints.

## Safe-Shot Semantics
A "Safe Shot" is an attack opportunity that does not compromise the attacker's immediate survival or future positioning.
- **Criteria**:
    1. Attacker is at or near its ideal range.
    2. Attacker has at least one free adjacent tile not threatened by immediate melee engagement.
    3. (Ranged) Attacker is not currently in a "pinned" or "blocked" corner.
- **Heuristic**: Prefer attacks where `dist == ideal_range` and `manhattan(nearest_melee_threat) > 1`.

## Distance-Management Semantics
Entities select one of four modes based on their role and the relative threat of their target:
- **CLOSE**: Move to minimum range (Melee default).
- **MAINTAIN**: Stay within weapon range, but maximize distance (Ranged default).
- **WIDEN**: Move away to increase distance (used when target is too close for a ranged role).
- **HOLD**: Do not move; wait for target to enter range or stay in a defensible position.

## Tactical Retreat Semantics
A retreat is "tactical" (rather than panic) when triggered by appraisal of the local situation:
- **Outnumbered**: Multiple enemies within engagement range vs one ally.
- **HP Threshold**: Damage taken exceeds recovery capacity.
- **Position Loss**: Chokepoint or defensible line is breached.
- **Effect**: Switch `MovementIntention` to `RETREAT` and target a known safe zone or home territory.

## Role-Sensitive Behavior Semantics
- **MELEE_STRIKER**: Aggressive `CLOSE` mode, high commitment to current target.
- **RANGED_SKIRMISHER**: `MAINTAIN` or `WIDEN` modes, high use of `Safe-Shot` logic.
- **SUPPORT_HEALER**: Stays behind Vanguards, prioritizes distance and line-of-sight to allies.
- **RETREAT_BIASED**: Lower threshold for switching to `RETREAT` intention.

## Small-Group Coordination Scope
- **Spacing**: Ranged entities avoid standing adjacent to each other if free tiles are available.
- **Lane Discipline**: Ally $A$ avoids a lane if Ally $B$ is already pursuing a target through it, preventing "logjams".

## Determinism Rules
Tactical evaluation must be purely derived from `AIContext` (Snapshot + Actor state). It must produce the same `TacticalMode` for the same input state, regardless of execution order.
