---
status: open
layer: simulation
authority: P1
audience: agent
ticket_id: TCK-20260619-E61-PROGRESSION
phase: open
date: 2026-06-19
tags: [progression-planner, multi-episode, build-goal, skill-planning, epic, phase-6]
---

# TCK-20260619-E61-PROGRESSION

## Title
Epic 6.1 · Progression Planner (Long Horizon — 18+ months)

## Status
OPEN

## Tier
epic

## Type
feature

## Priority
P2

## Request Summary
XP/leveling/evolution-points are fully implemented. No multi-episode skill/equipment/build-goal planning. Progression is currently tick-local only. A HERO that wants to become a legendary swordsmith should start planning in episode 1 for episode 3.

Score: 6/10 · Effort: M · Source: `docs/plans/engine_future_epics_roadmap.md` § C (Progression Planner)

**Note: Phase 6 epics are speculative at planning time. Scope and sequencing must be re-evaluated after Phase 5 is complete.**

## Scope
- **Prerequisite:** TCK-20260619-E32-CAMPAIGN-RUNTIME (CampaignState for plan persistence)
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
- TCK-20260619-E32-CAMPAIGN-RUNTIME (prerequisite)
- TCK-20260619-E43-SOCIAL-MEMORY (prerequisite: SocialMemoryRecord for plan integration)

## Related Docs
- `docs/plans/engine_future_epics_roadmap.md` § C
- `docs/plans/long_term_development_roadmap.md` § Epic 6.1

## Related Code Areas
- `src/core/strategic.py` (goal model — extension point for progression plan)
- `src/domains/campaigns/` (CampaignState — plan persistence)
- `src/domains/adventure/scoring.py` (scoring bonus for plan-advancing routes)

## Assumptions / Open Questions
- Re-evaluate full scope after Phase 5 is complete

## Implementation Notes
Scope this epic fresh at Phase 5 completion time. This ticket is a planning placeholder.

When implementing: update `docs/parity_ledger/progression.yaml` with multi-episode planning entries. Create `docs/simulation/domains/progression_planner_contract.md`. Run `make knowledge-index-update` after docs/ changes.

## Test Summary
To be defined at Phase 5 completion.

## Files Changed
_To be filled on completion._

## Completion Summary
_To be filled on completion._
