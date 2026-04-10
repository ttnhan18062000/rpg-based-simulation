# Implementation Plan: Strategic State Foundation (Phase 1)

## Affected Files
- [NEW] `src/core/models/strategy.py`
- [MODIFY] `src/core/models/__init__.py`
- [MODIFY] `src/core/aspects/mind.py`
- [MODIFY] `src/actions/base.py`
- [MODIFY] `src/systems/gameplay/action_system.py`
- [MODIFY] `src/ui/cli/inspector.py`
- [MODIFY] `src/core/entities/entity_builder.py`

## Implementation Steps

### 1. Strategic Domain Schema
- Define the following in `src/core/models/strategy.py`:
    - `DirectiveRecord`
    - `ProjectRecord`
    - `ObjectiveRecord`
    - `ConcernRecord`
    - `LeadRecord`
    - `BlockerRecord`
    - `ObligationRecord`
    - `SocialContractRecord`
    - `StrategicState` (Aggregate)

### 2. Mind Integration
- Add `strategic: StrategicState` to `MindAspect` in `src/core/aspects/mind.py`.
- Handle circular imports with `model_rebuild`.

### 3. Action Update Intents
- Define `StrategicUpdate(IntentUpdate)` in `src/actions/base.py`.
- Support add/update/remove collections for each strategic record type.

### 4. Authoritative Application
- In `ActionSystem._apply_updates`, add handling for `StrategicUpdate`.
- Deterministically merge updates into `entity.mind.strategic`.

### 5. Snapshot & Serialization
- Verify `MindAspect.copy()` and `freeze()` correctly handle the new `strategic` domain.
- Verify JSON serialization via `SimulationModel`.

### 6. Bootstrapping
- Update `EntityBuilder` and `WorldGenerator` to seed minimal strategic state (empty collections + archetype-based directives).

### 7. Observability
- Update `src/ui/cli/inspector.py` to render the strategic state.

### 8. Verification
- Implement and run tests defined in `test_plan.md`.
