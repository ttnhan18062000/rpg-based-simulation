---
status: historical
layer: misc
authority: P2
audience: agent
ticket_id: TCK-20260517-FULL-SCAN-COMPLIANCE
artifact_type: plan
tags: [full, scan, compliance]
---

# Milestone 2: Full-Scan Phase Compliance Plan

## 1. Goal

Implement `tests/integration/optimization/test_force_full_scan_phase_compliance.py` containing the 5 integration test cases specified in `perf_test_plan.md` to guarantee that an empty `DirtySet` cannot suppress evaluation when `force_full_scan=True`.

## 2. Test Cases to Implement

1. `test_interaction_phase_force_full_scan_processes_entity_with_empty_dirty_set`
   - Setup entity with `navigation.target` pointing to a resource node.
   - Run `InteractionPhase.route_interaction_intent` with `force_full_scan=True` and `dirty_set=DirtySet()`.
   - Assert `refined.entity_updates[entity_id].interaction` is not None.

2. `test_movement_phase_force_full_scan_processes_entity_with_target_and_empty_dirty_set`
   - Setup entity with `navigation.target`.
   - Run `MovementPhase.route_movement_intent` with `force_full_scan=True` and empty `dirty_set`.
   - Assert `refined.entity_updates[entity_id].new_position` is not None.

3. `test_strategic_phase_force_full_scan_processes_active_project_entity_with_empty_dirty_set`
   - Setup entity with an active strategic project and objective.
   - Run `StrategicIntelligenceSystem.fused_strategic_pass` with `force_full_scan=True` and empty `dirty_set`.
   - Verify strategic evaluation runs.

4. `test_shop_phase_force_full_scan_processes_inventory_entity_with_empty_dirty_set`
   - Setup entity at a shop building tile with sellable materials.
   - Run `ShopSystem.enforce` with `force_full_scan=True` and empty `dirty_set`.
   - Assert auto-sell transfer intent is created.

5. `test_capacity_phase_force_full_scan_processes_all_inventory_entities`
   - Setup entity with strategic leads/concerns/projects exceeding cognitive profile limits.
   - Run `CapacityEnforcementPhase.enforce` with `force_full_scan=True` and empty `dirty_set`.
   - Assert capacity trimming is executed.

## 3. Verification

Run `pytest tests/integration/optimization/test_force_full_scan_phase_compliance.py -v`.
Ensure 5/5 tests pass deterministically.
