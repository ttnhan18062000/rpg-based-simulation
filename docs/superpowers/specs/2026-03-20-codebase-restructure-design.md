---
status: archive
authority: P2
audience: historical
layer: misc
original_date: 2026-03-20
---

# Design Spec: Component-Based Codebase Restructure

This document outlines the architectural shift from a layered, monolithic structure to a modular, feature-based "Aspect.Oriented" design for the RPG simulation.

## Goals
- **Decompose God Objects**: Split `WorldLoop` (96KB) and `States` (70KB) into small, focused modules.
- **Modular Entity Model**: Refactor `Entity` from a heavy class with inheritance to a lightweight container using composition (Aspects).
- **Domain-Centric Organization**: Group logic by feature (Combat, Economy, World) rather than by technical layer (AI, Actions, Models).
- **Future-Proof Extensibility**: Allow new simulation features (e.g., Magic, Quests) to be added without modifying core framework files.

## High-Level Architecture

### Layers
1. **Platform (`src/platform/`)**: The foundation. Low-level utilities that have no "game logic" but provide necessary services (RNG, Spatial Hashing, Pathfinding).
2. **Engine (`src/engine/`)**: The simulation heartbeat. Manages the tick cycle, worker pool, and data snapshots.
3. **Core Domain (`src/core/`)**: Shared "primitives" and basic types needed by multiple features (Vec2, common enums, basic `Entity` and `Aspect` definitions).
4. **Features (`src/features/`)**: Self-contained domain modules.
   - `src/features/combat/`: Holds `CombatAspect`, Attack actions, and AI combat states.
   - `src/features/economy/`: Holds `InventoryAspect`, Trade actions, and economic persistence logic.
5. **API (`src/api/`)**: Translates simulation states into frontend-ready schemas.

## The Aspect Framework
The `Entity` class will be refactored to use a dictionary of aspects:

```python
class Entity:
    id: int
    pos: Vec2
    _aspects: dict[type[Aspect], Aspect]

    def has_aspect(self, aspect_type: type[Aspect]) -> bool:
        return aspect_type in self._aspects

    def get_aspect(self, aspect_type: type[T]) -> T:
        return self._aspects.get(aspect_type)
```

Each `Feature` defines its own `Aspect` subclass:
- `CombatAspect(Aspect)`: `hp`, `max_hp`, `atk`, `def`.
- `InventoryAspect(Aspect)`: `items`, `gold`, `weight_limit`.

## Refactoring "God Objects"

### WorldLoop Decomposition
The currently monolithic `WorldLoop` will be split into:
- **`SimulationTickRegistry`**: Manages the order of "Standard Subsystems" (e.g., spawn first, then move, then combat).
- **`SnapshotManager`**: Handles immutable copy creation for worker threads.
- **`EntityProcessor`**: Iterates entities and delegates logic to their respective aspects/actions.

### AI State Decomposition
The giant `src/ai/states.py` will be completely removed. Each state will become a standalone module in its feature folder:
- `src/features/combat/ai/attack_state.py`
- `src/features/economy/ai/trading_state.py`

## Implementation Phases
1. **Phase 1: Foundation**: Create `src/platform/` and `src/core/` base classes.
2. **Phase 2: Entity Refactor**: Implement the Aspect framework and refactor the `Entity` class.
3. **Phase 3: Feature Migration (Combat)**: Move all combat logic (models, actions, AI) into `src/features/combat/`.
4. **Phase 4: Feature Migration (Economy)**: Move all inventory and trading logic into `src/features/economy/`.
5. **Phase 5: God Object Split**: Break down `WorldLoop.py` into its constituent systems.
6. **Phase 6: Final Cleanup**: Remove old technical-layer folders and update all imports.

## Design Refinements (Implementation Details)

As of **2026-03-20**, the following refinements were made during the Phase 3 (Combat) stabilization:

### 1. Skill Action Proposals
The `ActionProposal` target format for `ActionType.USE_SKILL` must be a tuple `(skill_id, target_entity_id)` for offensive skills. This allows the `WorldLoop` to correctly set `entity.combat_target_id` before the `ActionSystem` resolves the skill.

### 2. Threat Table Unification
The `threat_table` has been moved from `CombatAspect` to `MindAspect`. This ensures all AI decision logic (including non-combat behaviors) has access to the same threat data. The `CombatSystem` remains responsible for ticking threat decay.

### 3. AoE Maneuver & Manhattan Distance
AoE skills use the `radius` property around a `center` target. Despite using a `SpatialHash` for initial broad-phase queries, precise filtering MUST use `manhattan` distance to remain consistent with the grid-based movement and range constraints.

### 4. Skill Requirements in Testing
E2E tests for high-level skills (e.g., `Whirlwind`, `Rain of Arrows`) must manually set the hero's `level` and any `mastery_req` (e.g., `shield_wall`) to ensure the AI correctly identifies the skill as "ready".

## Verification Plan
- **Unit Tests**: Each new Aspect and split system will have isolated unit tests.
- **Simulation Consistency**: Run deterministic replay tests to ensure the behavior is identical to the monolithic version.
- **API Integrity**: Use existing `test_api_payload.py` to ensure the split doesn't break the frontend interop.
