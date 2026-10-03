---
status: historical
layer: engine
authority: P2
audience: agent
ticket_id: TCK-20260504-V2-ENGINE-REGRESSION-FIX
artifact_type: plan
tags: [v2, engine, regression, fix]
---

# Implementation Plan - V2 Engine Regression Fix

Fixing 39 failed tests by completing the migration to `V2EntityBuilder`.

## User Review Required

> [!IMPORTANT]
> The `EntityGenerator` is a core utility used by many subsystems. Changing it to use `V2EntityBuilder` is the most efficient way to fix the majority of test failures, but it enforces the V2 engine's strict state contract on all spawned entities.

## Proposed Changes

### Core Subsystems

#### [MODIFY] [builder.py](file:///home/vboxuser/Work/rpg-based-simulation/src/core/builder.py)
- Add `.leash(radius, home_pos=None)` to `V2EntityBuilder`.
- Add `.with_stamina(current, max_stamina=None)` to `V2EntityBuilder`.

#### [MODIFY] [generator.py](file:///home/vboxuser/Work/rpg-based-simulation/src/systems/generator.py)
- Replace all direct `EntityState(...)` instantiations with `V2EntityBuilder` chains.
- Ensure `spawn_hero`, `spawn_monster`, `spawn_goblin`, `spawn_calamity`, and `spawn_stronghold` all use the builder.

### Test Infrastructure

#### [MODIFY] [tests/engine/](file:///home/vboxuser/Work/rpg-based-simulation/tests/engine/)
- Audit and refactor remaining failed tests:
  - `test_phase9_stability.py`
  - `test_race_conditions_v2.py`
  - `test_reputation_learning.py`
  - `test_routine_biasing.py`
  - `test_runtime_state_contract.py`
  - `test_signal_hardening.py`
  - (and others as identified during execution)

## Verification Plan

### Automated Tests
- Run `pytest tests/engine/` and verify 0 failures.
- Run `pytest tests/rpg/` to ensure no regressions in RPG logic.

### Manual Verification
- None required.
