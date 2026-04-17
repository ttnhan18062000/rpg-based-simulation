# Design Spec: Combat and Movement Milestone 1 — Core Rulebook and Engine-Time Refactor

**Date**: 2026-04-17
**Status**: DRAFT (Awaiting Spec Review)

## 1. Purpose
Define and implement a deterministic, authoritative rulebook for spatial legality and world-time progression. This milestone establishes the foundation for all subsequent combat and movement improvements.

## 2. Architecture
The design follows the **Service-Oriented** approach with **Authority-Boundary Enforcement**.

### 2.1 LegalityService
A single, centralized authority for spatial rules located in `src/core/logic/legality_service.py`.

**Responsibilities**:
- **Manhattan Distance**: Authoritative calculation for range, movement, and AoE.
- **Orthogonal Adjacency**: Validity check for melee and engagement.
- **Occupancy**: Verification of unit-per-tile constraints.
- **AoE Legality**: Range-to-center, LOS-to-center, and Manhattan-splash validation.

### 2.2 Authority Boundaries
The LegalityService will be invoked at three critical points:
1. **Validation**: During `ActionProposal.validate` (e.g., `CombatAction.validate`).
2. **Authority**: During `ActionSystem.apply` (re-validation before updates are generated).
3. **Intelligence**: Used by AI workers to narrow their search space (read-only).

### 2.3 LocationTarget (Option C)
To support AoE and positional targeting, a new target type will be introduced:
- `LocationTarget(pos: Vector2)`
- This wrapper ensures `ActionProposal.target` remains well-typed while supporting disparate target types (Entities vs. Tiles).

## 3. Spatial Rules
- **Distance**: Manhattan Distance (`abs(dx) + abs(dy)`) is the universal metric.
- **Adjacency**: A target is adjacent if and only if Manhattan distance is exactly `1`.
- **Occupancy**: Exactly one entity per tile.
- **Movement Blocking**: Occupied tiles are impassable.
- **Pass-through**: No ally or enemy pass-through is allowed.
- **AoE Radius**: Splash effects use Manhattan distance from the impact center.

## 4. Timing and Lifecycle Rules
- **No Quiet-Tick skipping**: Every world tick progresses the simulation, even if no action is proposed.
- **Separation of Concerns**:
    - **World-Time**: Advancements in `PreSystemsPhase` (passive effects, decay, counters).
    - **Entity Turns**: Evaluated in `SchedulingPhase` using `next_act_at`.
- **Passive Progression**: Must occur every tick regardless of entity readiness.

## 5. Components and Data Flow

### 5.1 LegalityService Contract
```python
class LegalityService:
    @staticmethod
    def is_adjacent(a: Vector2, b: Vector2) -> bool:
        return a.manhattan(b) == 1

    @staticmethod
    def is_in_range(attacker: Vector2, target: Vector2, weapon_range: int) -> bool:
        return attacker.manhattan(target) <= weapon_range

    @staticmethod
    def is_occupied(pos: Vector2, world: "WorldState") -> bool:
        return world.is_occupied(pos)

    @staticmethod
    def is_aoe_legal(origin: Vector2, impact: Vector2, range: int, world: "WorldState") -> bool:
        if origin.manhattan(impact) > range: return False
        return world.grid.has_line_of_sight(origin, impact)
```

### 5.2 Updated Engine Loop
`WorldLoop._step()` runs phases in order. 
`PreSystemsPhase` will be audited to ensure it contains all time-dependent logic that must progress on every tick.

## 6. Testing Strategy
- **Rule-Contract Tests**: Isolated tests for `LegalityService` using exact input/output pairs.
- **Lifecycle Tests**: Proof that passive effects (e.g., Poison damage) apply correctly on ticks where NO actions are taken.
- **Determinism Tests**: Verify that identical seeds and inputs produce bit-identical world states across Milestone 1 rules.

## 7. Non-Goals (Milestone 1)
- No diagonal movement or adjacency.
- No ally pass-through.
- No anti-stalemate or kiting heuristics.
- No speed rebalancing.
