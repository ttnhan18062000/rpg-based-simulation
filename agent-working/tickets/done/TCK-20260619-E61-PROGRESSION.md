---
status: historical
layer: simulation
authority: P1
audience: agent
ticket_id: TCK-20260619-E61-PROGRESSION
phase: done
date: 2026-06-19
tags: [progression-planner, multi-episode, build-goal, skill-planning, epic, phase-6]
---

# TCK-20260619-E61-PROGRESSION

## Title
Epic 6.1 · Progression Planner (Long Horizon — 18+ months)

## Status
EPIC_SCOPED

## Tier
epic

## Type
feature

## Priority
P2

## Request Summary
XP/leveling/evolution-points are fully implemented. No multi-episode skill/equipment/build-goal planning. Progression is currently tick-local only. A HERO that wants to become a legendary swordsmith should start planning in episode 1 for episode 3.

Score: 6/10 · Effort: M · Source: `docs/plans/engine_future_epics_roadmap.md` § C (Progression Planner)

**Note: Phase 6 epics are speculative at planning time. Scope and sequencing must be re-evaluated after Phase 5 is complete. Re-evaluated 2026-06-22 at Phase 5 completion — scoped into 4 child tickets.**

## Scope
- **Prerequisite:** TCK-20260619-E32-CAMPAIGN-RUNTIME (CampaignState for plan persistence) — DONE
- **Prerequisite:** TCK-20260619-E43-SOCIAL-MEMORY (SocialMemoryRecord) — DONE
- Multi-episode goal queue integrated with `SocialMemoryRecord` (Epic 4.3)
- Plan persistence in `CampaignState`: `ProgressionPlan` model with goal_queue[], milestone_checks[], revision_triggers[]
- Plan revision: when intermediate goal becomes blocked (mentor died, item unavailable), entity generates plan_revision event and re-routes
- Scoring integration: entities with an active progression plan score routes that advance the plan higher than neutral-utility routes of equal score

## Out of Scope
- Player-controlled build planning
- Class prestige/ascension system

## Acceptance Criteria
- A HERO entity that identifies a target equipment tier in episode 1 pursues a coherent upgrade chain across 3 episodes, revising the plan when an intermediate goal is blocked

## Related Tickets
- TCK-20260619-E32-CAMPAIGN-RUNTIME (prerequisite — DONE)
- TCK-20260619-E43-SOCIAL-MEMORY (prerequisite — DONE)
- TCK-20260619-E61A-PLAN-MODEL (child — open)
- TCK-20260619-E61B-PLAN-EXPORTER (child — open)
- TCK-20260619-E61C-PLAN-SCORER (child — open)
- TCK-20260619-E61D-PLAN-REVISION (child — open)

## Related Docs
- `docs/plans/engine_future_epics_roadmap.md` § C
- `docs/plans/long_term_development_roadmap.md` § Epic 6.1
- `docs/audits/D01_rpg_feature_impact.md` § Progression Planner [MISSING]
- `docs/simulation/domains/progression_planner_contract.md` (created by E61C/E61D)

## Related Stored Artifacts
- `stored_artifacts/TCK-20260619-E61-PROGRESSION/`

## Related Code Areas
- `src/core/strategic.py` (goal model — extension point for progression plan)
- `src/domains/campaigns/state.py` (CampaignState — plan persistence field)
- `src/domains/campaigns/progression_plan.py` (new — created by E61A)
- `src/domains/campaigns/plan_revision.py` (new — created by E61D)
- `src/domains/campaigns/orchestrator.py` (episode boundary wiring — E61B/E61D)
- `src/domains/adventure/scoring.py` (plan-advance bonus — E61C)
- `docs/parity_ledger/progression.yaml` (PROG-110 through PROG-113)

## Assumptions / Open Questions
- Phase 5 (E51–E53) now complete; scope re-evaluated 2026-06-22
- ProgressionPlan is a frozen dataclass keyed per entity_id in CampaignState, parallel to social_memories
- Plan revision uses BlockerState mechanism already in strategic.py — no new strategic type needed
- SocialMemoryRecord integration point: plan_revision events read interaction_history to detect mentor-death blockers

## Implementation Notes
Scoped 2026-06-22 at Phase 5 completion into 4 child standard tickets:
- **E61A**: `ProgressionPlan` frozen dataclass + `CampaignState.progression_plans` field + serialization
- **E61B**: `ProgressionPlanExporter` (episode-end) + `ProgressionPlanImporter` (episode-start) wired into `CampaignOrchestrator`
- **E61C**: `AdventureRouteScorer` plan-advance bonus (+1.5 when route matches active `goal_queue` head); `progression_planner_contract.md` created
- **E61D**: `PlanRevisionService` — generates initial plans for HERO entities; detects mentor-dead/item-unavailable blockers; rotates `goal_queue`; emits `plan_revision` NarrativeLedgerEntry

Dependency order: E61A → E61B → E61C → E61D (strictly linear).

## Test Summary
Each child ticket carries its own test plan. Integration test lives in E61D:
`tests/integration/campaigns/test_progression_planner_three_episode.py` — 3-episode scenario
covering plan generation, carry-forward, and revision on mentor death.

## Files Changed
Scoping only — no code changes. Child tickets implement code.

## Completion Summary
Scoped 2026-06-22 into 4 child tickets (E61A through E61D). Prerequisites E32 and E43 confirmed DONE. Investigation stored at `stored_artifacts/TCK-20260619-E61-PROGRESSION/`. Dependency order is strictly linear. Phase 6 note preserved; epic is EPIC_SCOPED.
