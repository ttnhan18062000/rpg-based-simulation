# Plan — TCK-20260619-E61B-PLAN-EXPORTER

## Approach

1. Extend `src/domains/campaigns/progression_plan.py` with two new classes:
   - `ProgressionPlanExporter.export(entity_id, current_plan, alive) -> Optional[ProgressionPlan]`
   - `ProgressionPlanImporter.import_plan(entity_id, plan, new_episode_index, entity_level) -> ProgressionPlan`
   (Simplified signature: pass primitives instead of AuthoritativeState to avoid circular import)

2. Wire into `src/domains/campaigns/orchestrator.py`:
   - `_advance_state()`: add `_extract_progression_plans(entity_cfs)` helper → call `self._state.progression_plans.update(...)`
   - `_build_initial_state()`: apply `ProgressionPlanImporter.import_plan()` for entities with plans; update `self._state.progression_plans`

## Key Constraints

- ProgressionPlanExporter: dead entity → None; no existing plan → None; alive + non-empty goal_queue → return plan unchanged
- ProgressionPlanImporter: for each MilestoneCheck, if entity_level >= target_level → achieved=True; returns replaced plan
- `self._state.progression_plans` is mutable (CampaignState is not frozen)

## Files Changed

1. `src/domains/campaigns/progression_plan.py` (extend — 2 new classes)
2. `src/domains/campaigns/orchestrator.py` (wire imports + 2 hooks)
3. `tests/unit/campaigns/test_progression_plan_exporter.py` (new — 3 tests)
4. `tests/unit/campaigns/test_progression_plan_importer.py` (new — 3 tests)
5. `tests/unit/campaigns/test_orchestrator_plan_wiring.py` (new — 1 integration test)
6. `docs/parity_ledger/progression.yaml` (PROG-111)
