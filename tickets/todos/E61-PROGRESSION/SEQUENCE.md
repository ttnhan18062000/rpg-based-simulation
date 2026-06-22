# E61 — Long-Term Progression Planner

**Parent epic:** TCK-20260619-E61-PROGRESSION (EPIC_SCOPED)
**Inter-epic prerequisite:** None (E61 is independent of E53)
**Inter-epic unlocks:** E62-CULTURE-DRIFT (E61 must be complete before E62 starts — Phase 6 sequencing)

## Sequence (linear)

1. **TCK-20260619-E61A-PLAN-MODEL** — `ProgressionPlan` frozen dataclass (entity_id, goal_queue: List[GoalKind], derived_episode, plan_id) + `CampaignState.progression_plans: Dict[int, ProgressionPlan]` field + serialization (to_dict/from_dict)
2. **TCK-20260619-E61B-PLAN-EXPORTER** — `ProgressionPlanExporter` + `ProgressionPlanImporter`; wired into `CampaignOrchestrator._advance_state()` after social_memories (same pattern as E43B)
3. **TCK-20260619-E61C-PLAN-SCORER** — `AdventureRouteScorer` extension: +1.5 bonus when route matches `goal_queue[0].target_route_family`; `docs/simulation/domains/progression_planner_contract.md`
   - **Circular import risk:** `scoring.py` must NOT import from `src/domains/campaigns/` — accept `plan: Optional[ProgressionPlan]` as a plain parameter
4. **TCK-20260619-E61D-PLAN-REVISION** — `PlanRevisionService`: initial plan generation for HERO entities at episode start; mentor-dead / item-unavailable blocker detection using `BlockerState`; `goal_queue` rotation; emits `plan_revision` NarrativeLedgerEntry

## Key Notes

- `CampaignState.progression_plans` mirrors `CampaignState.social_memories` exactly — reuse that serialization pattern.
- `ProgressionPlan.goal_queue` uses existing `GoalKind` entries — no new GoalKind values needed.
- Plan revision runs at episode boundary (not per-tick) via `CampaignOrchestrator`, not the tick loop.
