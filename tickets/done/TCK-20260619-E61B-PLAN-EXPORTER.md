---
status: open
layer: simulation
authority: P1
audience: agent
ticket_id: TCK-20260619-E61B-PLAN-EXPORTER
phase: open
date: 2026-06-22
tags: [progression-planner, campaign-orchestrator, episode-boundary, export-import]
---

# TCK-20260619-E61B-PLAN-EXPORTER

## Title
Epic 6.1B · ProgressionPlanExporter + Importer (Episode Boundary Wiring)

## Status
DONE

## Tier
standard

## Type
feature

## Priority
P2

## Request Summary
Implement `ProgressionPlanExporter` (episode-end) and `ProgressionPlanImporter`
(episode-start) for cross-episode progression plan carry-forward. Wire both into
`CampaignOrchestrator` following the `SocialMemoryExporter` / `SocialMemoryImporter`
pattern established by E43B.

## Scope
- `src/domains/campaigns/progression_plan.py` (extend file from E61A):
  - `ProgressionPlanExporter`:
    - `export(entity_id: int, current_plan: Optional[ProgressionPlan], auth_state: AuthoritativeState, episode_index: int) -> Optional[ProgressionPlan]`
    - If entity is alive (`EntityCarryForward.alive == True`) and has a non-empty `goal_queue`, return plan unchanged (carry forward)
    - If entity is dead, return None (plan is dropped — dead entities do not carry plans)
    - If no current plan exists for entity, return None
  - `ProgressionPlanImporter`:
    - `import_plan(entity_id: int, plan: ProgressionPlan, new_episode_index: int) -> ProgressionPlan`
    - Advances `MilestoneCheck.achieved = True` for any milestone whose `target_level` is
      now met by the entity's carried `EntityCarryForward.level`
    - Returns a new (replaced) `ProgressionPlan` with updated milestones
- `src/domains/campaigns/orchestrator.py`:
  - Import `ProgressionPlanExporter`, `ProgressionPlanImporter`
  - In `_advance_state()` (episode-end): call exporter for each entity in `persistent_entities`;
    populate `campaign_state.progression_plans`
  - In `_prepare_next_episode()` (episode-start): call importer for each entity that has
    a plan in `campaign_state.progression_plans`; update plans in-place
- Parity ledger: add PROG-111 to `docs/parity_ledger/progression.yaml`
  - text: "ProgressionPlan is exported at episode end and imported at episode start; dead entity plans are dropped"
  - status: verified, priority: P1

## Out of Scope
- Scoring integration (E61C)
- Plan revision on blockers (E61D)
- Generating new plans for entities that have none (E61D)

## Acceptance Criteria
1. After episode 1 ends, a live HERO entity's `ProgressionPlan` appears in `CampaignState.progression_plans`
2. After episode 1 ends, a dead HERO entity's plan is absent from `CampaignState.progression_plans`
3. At the start of episode 2, `MilestoneCheck.achieved` is set to True for milestones whose `target_level` the entity has already met
4. The orchestrator unit test for `_advance_state` passes with plans in the fixture

## Related Tickets
- TCK-20260619-E61A-PLAN-MODEL (prerequisite)
- TCK-20260619-E43-SOCIAL-MEMORY (reference pattern — DONE)
- TCK-20260619-E61-PROGRESSION (parent epic)
- TCK-20260619-E61C-PLAN-SCORER (next — depends on this)

## Related Docs
- `stored_artifacts/TCK-20260619-E61-PROGRESSION/investigation.md`
- `docs/parity_ledger/progression.yaml`

## Related Stored Artifacts
- `stored_artifacts/TCK-20260619-E61-PROGRESSION/`

## Related Code Areas
- `src/domains/campaigns/orchestrator.py` (CampaignOrchestrator._advance_state / _prepare_next_episode)
- `src/domains/campaigns/progression_plan.py` (ProgressionPlanExporter, ProgressionPlanImporter)
- `src/domains/campaigns/social_memory.py` (reference pattern)

## Assumptions / Open Questions
- `_advance_state()` and `_prepare_next_episode()` already exist in orchestrator from E32C;
  locate exact method names before implementing (read the file)
- `AuthoritativeState` is available as a parameter in the episode-end hook — confirm via
  read of orchestrator before implementing
- Importer only updates milestones; it does not re-score or re-route (that is E61D)

## Implementation Notes
- Follow `SocialMemoryExporter` / `SocialMemoryImporter` in `social_memory.py` as the model
- Exporter must handle the case where `campaign_state.progression_plans` is empty on first run
- Importer must handle plans with empty `milestone_checks` gracefully (no-op)
- Both classes should be pure functions (no side effects beyond returning new dataclasses)

## Test Summary
- `tests/unit/campaigns/test_progression_plan_exporter.py`:
  - `test_exporter_carries_live_entity_plan`: alive entity's plan is returned unchanged
  - `test_exporter_drops_dead_entity_plan`: dead entity's plan returns None
  - `test_exporter_no_plan_returns_none`: entity with no existing plan returns None
- `tests/unit/campaigns/test_progression_plan_importer.py`:
  - `test_importer_achieves_met_milestone`: milestone target_level <= entity level → achieved=True
  - `test_importer_skips_unmet_milestone`: milestone target_level > entity level → achieved=False unchanged
  - `test_importer_empty_milestones_no_op`: empty milestone_checks returns plan unchanged
- `tests/unit/campaigns/test_orchestrator_plan_wiring.py`:
  - `test_orchestrator_exports_plan_at_episode_end`: integration test verifying CampaignState.progression_plans populated after advance

## Files Changed
- `src/domains/campaigns/progression_plan.py` (extended — ProgressionPlanExporter + ProgressionPlanImporter)
- `src/domains/campaigns/orchestrator.py` (wired — imports, _export_progression_plans helper, _advance_state + _build_initial_state hooks)
- `tests/unit/campaigns/test_progression_plan_exporter.py` (new — 3 tests)
- `tests/unit/campaigns/test_progression_plan_importer.py` (new — 3 tests)
- `tests/unit/campaigns/test_orchestrator_plan_wiring.py` (new — 1 integration test)
- `docs/parity_ledger/progression.yaml` (PROG-111)

## Completion Summary
ProgressionPlanExporter and ProgressionPlanImporter added to progression_plan.py.
Wired into CampaignOrchestrator: _advance_state() exports plans (alive entities kept, dead dropped);
_build_initial_state() imports plans (milestone achieved flags updated from entity level).
7 new tests all pass. PROG-111 added to progression parity ledger.
