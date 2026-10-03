---
status: historical
layer: strategy
authority: P2
audience: agent
ticket_id: TCK-20260409-PH1-STG1-STRATEGIC-STATE
artifact_type: investigation
tags: [ph1, stg1, strategic, state]
---

# Investigation: Strategic State Foundation (Phase 1)

## Findings from Codebase Scan
- **Model Patterns**: `src/core/models/base.py` defines `SimulationModel` with a `freeze`/`copy` mechanism. All new strategic records must inherit from `SimulationModel` and use Pydantic for validation.
- **Mind Integration**: `src/core/aspects/mind.py` contains `MindAspect`. It already has several domains (decision, perception, emotion, etc.). Adding `strategic` as a new field fits the existing pattern.
- **Action System**: `src/actions/base.py` defines `IntentUpdate`. I need to create `StrategicUpdate` inheriting from it.
- **Authoritative Application**: `src/systems/gameplay/action_system.py` contains `_apply_updates`. I need to add a branch for `StrategicUpdate` that delegages to `StrategicState` mutation.
- **Conflict Scan**: 
    - No existing `src/core/models/strategy.py`.
    - Found `TCK-20260409-PH4-STG1-CORE-MODELS` in `done/`, which implements "Inheritance and Succession" (Phase 4 in its context). 
    - The new request "Phase 1" refers to "Strategic State Foundation" from `thinking_high_level_implementation.md`. 
    - Result: No functional conflict, but naming prefix `PH4` was used for a different feature. I will stick to `TCK-20260409-PH1-STG1-STRATEGIC-STATE` for clarity.

## Reused Patterns
- `SimulationModel` for typed records.
- `IntentUpdate` for authoritative state changes.
- `ActionSystem._apply_updates` for enforcement.
- `model_rebuild` for resolving circular dependencies.

## Assumptions
- Each strategic record (Directive, Project, etc.) needs a unique ID for deterministic merging in `ActionSystem`.
- `StrategicUpdate` will carry lists of records to add/update or IDs to remove.

## Known Risks
- **Mutable Aliasing**: Nested models in `StrategicState` must be deep-copied or frozen correctly to avoid leakage into snapshots.
- **Circular Dependencies**: `ActionProposal` and `MindAspect` are heavily interconnected. I must ensure correct `model_rebuild` calls.
