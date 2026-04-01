# Implementation Plan: TCK-20260401-FINAL-NON-PARTIAL-TASKS

## Goal
Stabilizing AOA Combat Engine by purging legacy `intent_metadata` shims, enforcing Mind aspect type safety, and ensuring total simulation determinism through deep-frozen snapshots.

## Proposed Changes

### Core Models
- `src/core/models/base.py`: Introduce `SimulationModel` with `.freeze()` and `__setattr__` guard.
- `src/core/entities/entity.py`: Update `Entity` to inherit from `SimulationModel` and recursively freeze aspects.
- `src/core/models/snapshot.py`: Integrate `freeze()` into `Snapshot.from_world`.

### AI Brain & States
- `src/core/aspects/mind.py`: Introduce `GoalType` and `EmotionType` enums.
- `src/ai/brain.py`: Consolidate `MindUpdate` and remove `intent_metadata` generation.
- `src/ai/states/navigation.py`: Fix `is_at_camp` -> `is_in_camp` and heal rate calculations.

### Action System
- `src/systems/gameplay/action_system.py`: Remove `_apply_intent_metadata` shim and enforce typed updates.

### Test Suite Migration
- Refactor `tests/unit/ai/test_mob_leash.py`
- Refactor `tests/unit/ai/test_ai_heuristics.py`
- Refactor `tests/api/test_introspection_api.py`
- Refactor `tests/unit/ai/test_inventory_goals.py`

## Verification
- Run all migrated AI and API tests.
- Verify 100% pass rate.
