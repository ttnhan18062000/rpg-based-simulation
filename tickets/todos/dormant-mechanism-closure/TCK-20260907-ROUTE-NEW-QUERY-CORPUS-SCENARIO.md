---
status: active
layer: testing
authority: P1
audience: agent
ticket_id: TCK-20260907-ROUTE-NEW-QUERY-CORPUS-SCENARIO
phase: open
date: 2026-09-07
tags: [testing, simulation-quality, corpus]
---

# TCK-20260907-ROUTE-NEW-QUERY-CORPUS-SCENARIO

## Title
Author a real corpus scenario exercising route_new_query's Branch 3 information-routing trigger

## Status
OPEN

## Tier
standard

## Type
feature

## Priority
P2

## Request Summary
Dormant Mechanism Closure epic (`TCK-20260907-EPIC-RPG-DORMANT-MECHANISM-CLOSURE`) child 3 of 6.
`route_new_query`'s SimQ signal rule (added during M7's pillar-integration pass,
`src/simulation_quality/scorers/information.py`) has never fired in any shipped calibration corpus,
confirmed still true 2026-09-07 (M9's own `route_new_query_isolated_calibration.py` proved the rule
correctly produces a 0.0→10.0 score delta via an isolated `QualityHub` replay, but no real corpus
world exercises it end-to-end). The real trigger (`src/domains/information/phase.py:86-104`, "Branch
3" of `InformationPhase.apply()`) fires when an entity has unresolved informational "unknowns" with
no higher-priority branch (1/2) already satisfied — this rule postdates M9's own scoping pass, so
it's a genuinely new gap M9 could not have caught, not something it missed.

## Scope
- Confirm the exact real conditions for Branch 1/2 to NOT already satisfy an entity (so Branch 3
  genuinely fires) during Investigate — read `InformationPhase.apply()`'s full branch logic, not just
  the Branch 3 comment.
- Author or extend a real corpus world/profile with at least one entity carrying a genuine unresolved
  "unknown" and no competing higher-priority route active, so `route_new_query` fires naturally during
  a real calibration run (not an isolated replay).
- Confirm the INFORMATION pillar produces a real, non-flat, attributable score change from this real
  corpus run, following the same evidentiary bar M9's own isolated-replay proof already established.

## Out of Scope
- Redesigning `InformationPhase`'s branch logic — confirm it's correct as-is, this ticket only proves
  a real scenario can reach Branch 3.
- Any other item from the Dormant Mechanism Closure epic's scope.

## Acceptance Criteria
- [ ] A real corpus world/profile exercises `route_new_query` naturally during a normal calibration
      run (not an isolated replay).
- [ ] The INFORMATION pillar shows a real, non-flat score contribution from this run, confirmed and
      recorded.

## Related Tickets
- `TCK-20260907-EPIC-RPG-DORMANT-MECHANISM-CLOSURE` (parent epic)
- `TCK-20260906-SIMQ-PILLAR-MAPPING-AND-RULES` (the ticket that added this rule)
- `TCK-20260906-SIMQ-CALIBRATION-AND-COMPLETENESS` (the ticket that proved it via isolated replay)

## Related Docs
- `docs/plans/rpg_design_roadmap/rpg_dormant_mechanism_closure_plan.md`
- `docs/simulation_quality/event_type_coverage.md`

## Related Stored Artifacts
None yet — created by this ticket's own Investigate/Plan phases once picked up for implementation.

## Related Code Areas
- `src/domains/information/phase.py`
- `src/observability/event_shapers.py`
- `config/simulation_quality/corpus_registry.yaml`

## Assumptions / Open Questions
- Whether an existing corpus world can be extended, or a new one is genuinely needed, is not decided
  here — real design work for this ticket's own Investigate/Plan phases.

## Implementation Notes

## Test Summary

## Files Changed

## Completion Summary
