---
content_type: doc
status: historical
layer: misc
authority: P2
audience: agent
tags: [core, stabilization]
---

# Design: Core AOA Stabilization (TCK-20260330)

## 1. Core Structural Hardening (Burn and Rebuild)
The foundational data models in `src/core/entities/entity.py` will be refactored to eliminate the dynamic aspect registry and all legacy property shims.

### 1.1 `Entity` Composite Root
- **Typed Aspect Fields**: Replace `aspects: dict[str, Any]` with mandatory typed fields for `identity`, `spatial`, `combat`, `progression`, `mind`, and optional `inventory`.
- **Purge Properties**: Remove all `@property` shims that alias aspect fields (e.g., `entity.hp`, `entity.pos`, `entity.faction`).
- **Constructor Refactor**: Remove positional argument support and custom `__init__` logic that handles legacy initialization patterns.
- **Presenter Split**: Extract any serialization methods (`to_slim_schema`, etc.) into a separate `EntityPresenter` class in the API layer.

### 1.2 `MindAspect` Decomposition
To prevent the "dumping ground" syndrome, `MindAspect` will be refactored into a collection of specialized nested Pydantic models:
- **`DecisionState`**: Stores `ai_state`, `goal_cooldowns`, `boredom_multipliers`, and `goal_switch_count`.
- **`PerceptionMemory`**: Stores `threat_table`, `entity_memory`, `terrain_memory`, and `attention_pool`.
- **`EmotionState`**: Stores `mood`, `emotional_state`, and `grudges`.
- **`NavigationState`**: Stores `cached_path`, `cached_path_target`, and `pos_history`.
- **`NarrativeMemory`**: Stores `memory_log`, `life_directive`, and `hero_familiarity`.

### 1.3 `CombatAspect` Purification
- **Remove Proxies**: Delete all properties that delegate to other aspects (e.g., `level`, `xp`, `gold`, `stamina`, `fame`, `chase_ticks`).
- **Relocate Stats**: Non-combat stats like `vision_range`, `loot_bonus`, and `interaction_speed` will be moved to a more appropriate aspect (e.g., `IdentityAspect` or a new `AttributesAspect`).

---

## 2. AI Immutability and Decision Integrity
The AI decision-making process will be isolated from state mutation paths to ensure a deterministic perception-decision-resolution flow.

### 2.1 Read-Only Sensing
- **Brain Logic**: Refactor `AIBrain.decide()` and its perception system to treat all input data as immutable. Any code that modifies an `Entity` or `MindAspect` during this phase will be removed.
- **Intent Collection**: Instead of direct mutation, any state changes that result from a decision (e.g., setting a combat target or updating a path) will be carried as `intent_metadata` in the `ActionProposal`.

### 2.2 Conversion of Handlers to Pure Proposers
- **`RECOVER_CORPSE` Action**: Replace the direct mutation logic in `CorpseRunHandler` with a formal action verb. The handler will propose the action; the `ActionSystem` will be responsible for the actual item/gold transfer only after validation.
- **Navigation Side-Effects**: Path updates will no longer be applied immediately; they will be proposals that the `ActionSystem` writes to the state only if the movement is successfully executed.

---

## 3. Action Resolution and Engine Orchestration

### 3.1 `CombatAction.apply` Decomposition
The monolithic combat logic will be extracted into discrete, testable services:
- **`DamageResolutionService`**: Calculates raw damage, defense mitigation, and elemental vulnerabilities.
- **`CombatAftermathService`**: Handles status effect triggers and threat/aggro table updates.
- **`KillRewardService`**: Handles XP distribution and loot generation upon entity death.

### 3.2 Phase-Based WorldLoop
The `WorldLoop.tick()` will be restructured into explicit, observable phases:
1. **Scheduling**: Determine who acts in this tick.
2. **Perception**: Generate immutable snapshots for all actors.
3. **Decision**: Parallelize AI handler calls to collect `ActionProposals`.
4. **Resolution**: Order and execute approved actions through their handlers.
5. **Publication**: Update external systems (API, Kafka, logging).

### 3.3 Explicit Action Priority
An `ACTION_PRIORITY_MAP` will be implemented to replace the brittle reliance on `ActionType` enum values for conflict resolution. This ensures that defensive reactions or interrupts can be intentionally prioritized over movement or standard attacks.
