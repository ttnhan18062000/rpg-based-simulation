# Implementation Plan: Phase 7/8 Recovery Gaps

## 1. Core State Expansion
- [MODIFY] `src_v2/core/state.py`: Add `RegionState`, `BuildingState`, and update `IdentityComponent`.
- [MODIFY] `src_v2/core/updates.py`: Add `WorldUpdate`, `BuildingUpdate`, and `kind_set` to `EntityUpdate`.

## 2. Authoritative System Recovery
- [NEW] `src_v2/engine/world_dynamics.py`: Implement hazard HP/Readiness drains and calamity scaling.
- [NEW] `src_v2/engine/evolution.py`: Implement milestone-driven role transformation.
- [NEW] `src_v2/engine/sabotage.py`: Implement building damage and service disabling.
- [MODIFY] `src_v2/engine/apply.py`: Implement applicators for the new update domains.

## 3. Pipeline Integration
- [MODIFY] `src_v2/engine/pipeline.py`: Inject `WorldDynamicsSystem`, `EvolutionSystem`, and `BuildingSabotageSystem` into the `refine` method.

## 4. Integrity Restoration
- [MODIFY] `src_v2/certification/scenarios.py`: Remove `navigation_target` from `IdentityComponent` and move to `NavigationComponent`.
- [MODIFY] `tests_v2/integrity/test_logic_guards.py`: Update attribute access to match the new state model.

## 5. Certification Update
- [MODIFY] `docs/engine/legacy_replacement_ledger.md`: Update status to SUPPORTED for recovery rows.
- [MODIFY] `legacy_checklist_part3.md`, `legacy_checklist_part4.md`: Mark items as completed.
