---
status: active
layer: strategy
authority: P1
audience: agent
ticket_id: TCK-20260811-MULTI-STEP-PLANNING-DESIGN
phase: open
date: 2026-08-11
tags: [cognition]
---

# TCK-20260811-MULTI-STEP-PLANNING-DESIGN

## Title
Design-scoping: multi-step/persistent planning for adventure-eligible entities

## Status
OPEN

## Tier
standard

## Type
feature

## Priority
P3

## Request Summary
Explore letting an entity commit to a short sequence of future intentions (train -> craft -> quest) rather than re-deciding the single next action every eligible tick. The original author explicitly stated this needs its own separate design conversation, not a scorer tweak -- investigation confirms no implementation ACs can be honestly derived, so this ticket is scoped as design-scoping work that produces a design doc and a go/no-go decision, not code.

## Scope
- A design doc (e.g. docs/architecture/<date>-multi-step-persistent-planning-design.md) proposing a durable typed model for committing to a short sequence of future intentions, explicitly reviewed against the Strategic/Tactical Rule
- Design doc explicitly resolves how a committed-but-not-yet-executed intention interacts with the existing single-slot current_project_id/current_objective_id model and the detour/lock-bypass arbiter in evaluate_strategic_intent()
- Design doc explicitly states its relationship to the existing ProgressionPlan.goal_queue and its documented 'multi-goal lookahead deferred' boundary (docs/simulation/domains/progression_planner_contract.md) -- supersede/extend/coexist, or explicit rationale for a separate tick-level concept
- Ticket closes when the design doc is written and reviewed, with either an accepted follow-up implementation ticket opened or an explicit reject/defer decision recorded with rationale

## Out of Scope
- No production code merged under this ticket -- this is design-scoping work only, not an implementation ticket
- Any code-behavior AC is explicitly excluded per the source proposal's own scoping statement

## Acceptance Criteria
- [ ] A design doc exists (e.g. docs/architecture/<date>-multi-step-persistent-planning-design.md) proposing a durable typed model for committing to a short sequence of future intentions, explicitly reviewed against the Strategic/Tactical Rule
- [ ] Design doc explicitly resolves how a committed-but-not-yet-executed intention interacts with the existing single-slot current_project_id/current_objective_id model and the detour/lock-bypass arbiter in evaluate_strategic_intent()
- [ ] Design doc explicitly states its relationship to the existing ProgressionPlan.goal_queue and its documented 'multi-goal lookahead deferred' boundary -- supersede/extend/coexist, or explicit rationale why a separate tick-level concept is needed alongside it
- [ ] No production code is merged under this ticket; the ticket closes when the design doc is written and reviewed, with either an accepted follow-up implementation ticket opened or an explicit reject/defer decision recorded with rationale

## Related Tickets
- TCK-20260619-E61-PROGRESSION

## Related Docs
- docs/simulation/domains/progression_planner_contract.md

## Related Stored Artifacts
None.

## Related Code Areas
- src/domains/campaigns/progression_plan.py
- src/domains/campaigns/plan_revision.py
- src/domains/campaigns/orchestrator.py
- src/domains/adventure/scoring.py
- src/systems/strategic_systems/intelligence.py

## Assumptions / Open Questions
- The single-slot current_project_id model and lock-bypass arbiter are actively in flux right now (this batch's own TCK-20260811-ADVENTURE-GOAL-SCORER and TCK-20260811-THREAT-RESOLVED-ARBITER-RELOCATION) -- this design-scoping work should probably explicitly wait for those to land and stabilize first
- Two structurally distinct planning concepts already coexist (episode-level ProgressionPlan vs. tick-level single-step GoalScorer re-decision) -- the new design risks creating a third overlapping concept if not explicitly scoped against both
- Forcing implementation-level ACs here would violate the source doc's own explicit scoping and this repo's Uncertainty Rule
- Related design doc: docs/architecture/2026-08-11-adventure-as-cognition-strategy-subcomponent-design.md (Future Extension Patterns)

## Implementation Notes

## Test Summary

## Files Changed

## Completion Summary
