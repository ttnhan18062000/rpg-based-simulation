# Test Plan — TCK-20260619-E61B-PLAN-EXPORTER

## tests/unit/campaigns/test_progression_plan_exporter.py

1. `test_exporter_carries_live_entity_plan` — alive=True, non-empty goal_queue → plan returned unchanged
2. `test_exporter_drops_dead_entity_plan` — alive=False → None
3. `test_exporter_no_plan_returns_none` — current_plan=None → None

## tests/unit/campaigns/test_progression_plan_importer.py

4. `test_importer_achieves_met_milestone` — target_level=3, entity_level=5 → achieved=True
5. `test_importer_skips_unmet_milestone` — target_level=10, entity_level=5 → achieved unchanged=False
6. `test_importer_empty_milestones_no_op` — milestone_checks=() → plan returned structurally equal

## tests/unit/campaigns/test_orchestrator_plan_wiring.py

7. `test_orchestrator_exports_plan_at_episode_end` — CampaignOrchestrator with pre-seeded progression_plans; after _advance_state(), plans updated (alive entity kept, dead entity dropped)
