---
status: active
layer: combat
authority: P1
audience: developer
---

# Combat and Movement Overhaul: Authoritative Specification

This document serves as the final, consolidated rulebook for the Combat and Movement system overhaul. It aggregates all rules, mechanics, and implementation standards established across Milestones 1 through 7.

---

## 1. Spatial and Timing Model (Milestone 1)

### Distance Metric
- **Manhattan Distance**: All distance checks (weapon range, vision, movement) use $L_1$ distance ($|x_1 - x_2| + |y_1 - y_2|$).
- **Orthogonal Adjacency**: Adjacency is strictly defined as cardinal neighbors (Up, Down, Left, Right). Diagonal movement and adjacency are not supported.

### Timing and Readiness
- **World-Time vs. Internal Readiness**: The simulation clock progresses in discrete "Ticks". Each entity has a `readiness` (derived from their speed `spd`) that determines when they are allowed to propose an action.
- **Speed as Tempo**: Higher speed translates to shorter intervals between moves, effectively giving fast entities "double turns" relative to slower ones.

---

## 2. Combat Interaction (Milestone 2)

### Engagement State
- **Orthogonal Engagement**: An entity is considered "engaged" if it is orthogonally adjacent to one or more hostiles.
- **Engagement Stickiness**: AI evaluators apply a utility bonus (`STICKINESS_UTILITY_BONUS`) to prioritize the current target, preventing unnecessary target jitter.

### Opportunity Attacks (OA)
- **Trigger**: Any movement from an engaged tile to a position NOT adjacent to the same hostile triggers an Opportunity Attack.
- **Constraint**: OAs are free attacks executed by the engine, not requiring readiness from the attacker.

### Anti-Stalemate Logic
- **Oscillation Detection**: The system tracks the recent position history. If a two-tile oscillation (A -> B -> A -> B) is detected, the AI is forced to break the loop or the engine intervenes.

---

## 3. Movement and Congestion (Milestone 3)

### Intention-Driven Movement
- **MovementIntention**: Every move must carry an intention (e.g., `RETREAT`, `PURSUIT`, `GUARD`).
- **Priority Yielding**: When two entities compete for the same tile, the entity with higher priority intention (e.g., `RETREAT`) or lower `entity_id` (tie-break) wins the tile.

### Congestion Responses
- **WAIT**: Stay in place for 1 tick.
- **SIDESTEP**: Attempt to move to a cardinal neighbor that maintains proximity to the path.
- **YIELD**: Higher priority allies are given right-of-way.

---

## 4. Tactical AI Heuristics (Milestone 4)

### Tactical Roles
- **Melee Striker**: Prioritizes closing to adjacency.
- **RANGED_SKIRMISHER**: Prioritizes maintaining maximum weapon range ("Kiting").
- **SUPPORT_HEALER**: Prioritizes staying near allies but away from direct engagement.

### Safe-Shot Logic
- **Condition**: Ranged entities prefer to attack only when no enemies are orthogonally adjacent, ensuring situational awareness before committing to a shot.

### Group Spacing
- **Ally Preservation**: Ranged/Support entities avoid stacking adjacent to each other to minimize AOE risk and maintain tactical depth.

---

## 5. Fatigue and Consequences (Milestone 5)

### Stamina Pressure
- **Exhaustion State**: Entities with < 15% stamina are marked as `EXHAUSTED`, suffering severe movement and attack penalties (e.g., -50% Speed).
- **Global Costs**: Every active move (Attack, Move) consumes stamina. Resting/Sleeping recovers it.

### Combat Consequences
- **Injury/Scarring**: Severe damage can inflict persistent consequences that outlast the combat encounter, affecting long-term stats.

---

## 6. Arena and Regression (Milestone 6)

### Automation Harness
- **Snapshot Support**: The `ArenaRunner` can execute scenarios from a deterministic starting state.
- **Metric Service**: Captures win-rates, kill-counts, and TPS for every scenario run.

### Regression Testing
- **Scenario Matrix**: A core set of balanced scenarios (e.g., 1v1 Melee, 1v1 Ranged, 2v2 Mixed) is used as the oracle for behavioral regressions.

---

## 7. Observability and Rollout (Milestone 7)

### Structured Observability
- **ActionReason Model**: Every action or intent update includes a structured `ActionReason` object.
- **ReasonCode Enum**: Canonical identifiers (e.g., `OCCUPANCY_VIOLATION`, `OUT_OF_RANGE`) for automated analysis.
- **Reason-Text Property**: Human-readable summaries derived from the code and metadata for logs and entity inspection.

### Feature Flags (Rollout Hardening)
- **Granular Control**: Major system families can be toggled via `overhaul_features` in `SimulationConfig`:
    - `use_legality_v2`: Enforces refined spatial/timing legality.
    - `use_combat_interaction_v2`: Enforces engagement and opportunity attack rules.
    - `use_movement_model_v2`: Enforces intention-driven movement and congestion logic.
    - `use_tactical_evaluator_v2`: Enforces heuristic tactical roles and safe-shot logic.

---

## 8. Authoritative Services

- **LegalityService**: Rulebook implementation for spatial/timing bounds.
- **CombatInteractionService**: Authority for engagement and OA state.
- **MovementModel**: Coordinator for congestion and planning.
- **TacticalEvaluator**: Canonical AI heuristic host.
- **MetricService**: Orchestrator for behavioral and performance metrics.
