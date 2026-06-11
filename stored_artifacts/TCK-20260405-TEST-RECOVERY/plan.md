---
status: historical
layer: misc
authority: P2
audience: agent
ticket_id: TCK-20260405-TEST-RECOVERY
artifact_type: plan
tags: [test, recovery]
---

# TCK-20260405-TEST-RECOVERY: Test Stabilization Plan

## Goal
Restore 100% pass rate in combat and AI test suites by resolving regressions from the AOA pivot.

## Proposed Changes
1. **AI Brain**: Harden `AIBrain._finalization_phase` by providing explicitly typed mocks in `test_action_styles.py`.
2. **Combat Systems**: 
   - Integrate `Shatter` (Frozen) effect expiration into the authoritative `ActionSystem` pipeline.
   - Synchronize `CombatTraceDetails` with simulation results.
3. **Pydantic Hardening**: Finalize `model_rebuild` for `ProgressionUpdate` to handle circular dependencies with `EffectType`.

## Verification Plan
1. Run target unit tests: `pytest tests/unit/ai/test_action_styles.py tests/unit/ai/test_combos.py`
2. Run affected API/Component tests: `pytest tests/api/test_introspection_api.py tests/component/systems/test_calamity_system.py`
3. Verify 100% pass rate.
