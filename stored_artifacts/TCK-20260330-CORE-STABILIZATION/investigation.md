# Investigation: Core AOA Stabilization State (Updated)

## Current Progress Assessment

Based on the audit of the codebase:

### 1. Entity & Aspects [COMPLETED]
- [x] `src/core/entities/entity.py`: Refactored to explicit typed field composition. `aspects` dict is removed.
- [x] `src/core/aspects/mind.py`: Decomposed into `DecisionState`, `PerceptionMemory`, `EmotionState`, `NavigationState`, and `NarrativeMemory`.
- [x] `src/core/aspects/combat.py`: Stripped of cross-aspect proxies.
- [x] `src/core/aspects/interaction.py`: Exists and holds interaction-specific fields.

### 2. AI Cognitive Pipeline [PARTIAL]
- [x] `src/ai/brain.py`: Structure for 4-phase cognitive pipeline exists.
- [x] `_sensory_perception_phase`: Implements saliency-based attention and position history tracking.
- [/] `_memory_appraisal_phase`: Updates `entity_memory` but lacks decay logic and "gone" entity handling via metadata.
- [x] `src/ai/states/navigation.py`: Updated to aspect-oriented paths. Direct mutations (like healing in camp) have been moved to `intent_metadata`.
- [x] `src/systems/gameplay/action_system.py`: Properly applies `intent_metadata` including pathing, memory, and resource recovery.

### 3. Combat Resolution [COMPLETED]
- [x] `src/actions/combat.py`: Decomposed into services. `CombatAction.apply` is now a coordinator.
- [x] `src/engine/conflict_resolver.py`: `PRIORITY_MAP` implemented and used in `_sort`.

### 4. Engine Orchestration [PENDING]
- [ ] `src/engine/world_loop.py`: Still a god-object. Comments denote phases, but logic is inline.
- [ ] **Next Step**: Create `src/engine/phases/` and extract `Scheduling`, `Collection`, `Resolution`, `Cleanup`, and `Persistence`.

### 5. Determinism [PENDING]
- [ ] `WorldState.compute_hash()` is missing.
- [ ] Deterministic replay needs verification.

## Significant Findings
- The "Burn" phase is largely successful. The core models are clean.
- The `ActionSystem` already has a robust `_apply_intent_metadata` method, which is the key to Pillar 1 (Read-only AI decisions).
- `WorldLoop` contains significant Kafka integration that should be isolated in a `PersistencePhase`.

## Risks
- **Phase Extraction Complexity**: Moving things like `_emit` and `SystemManager` access into standalone phases might require careful context passing to avoid circular dependencies or "prop-drilling".
- **Hash Stability**: `compute_hash` must be extremely careful with dictionary ordering and floating point precision to be useful in tests.
