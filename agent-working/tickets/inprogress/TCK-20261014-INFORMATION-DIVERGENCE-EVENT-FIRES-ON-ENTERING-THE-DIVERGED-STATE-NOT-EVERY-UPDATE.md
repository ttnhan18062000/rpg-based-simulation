---
status: active
layer: simulation
authority: P1
audience: agent
ticket_id: TCK-20261014-INFORMATION-DIVERGENCE-EVENT-FIRES-ON-ENTERING-THE-DIVERGED-STATE-NOT-EVERY-UPDATE
phase: open
date: 2026-10-14
tags: []
---

# TCK-20261014-INFORMATION-DIVERGENCE-EVENT-FIRES-ON-ENTERING-THE-DIVERGED-STATE-NOT-EVERY-UPDATE

## Title
`decision_diverged_by_belief` fires once per divergence episode (on the update that moves an entity into the diverged state), not on every update the entity stays diverged.

## Status
INPROGRESS

## Tier
hotfix

## Type
bug

## Priority
P1

## Request Summary
The INFORMATION pillar is almost entirely `decision_diverged_by_belief` at +30 each. The producer (`event_shapers.py` live path and `event_extractor.py` rollback path) emitted it on every strategic update of an entity holding a VAGUE/EXHAUSTED lead under a non-information project, so the pillar measured entity-updates held, not divergences. Measured (audit_mode, 200t): generated_frontier_3_42 s123 INFORMATION 2.30 before #536, 41.78 after (279 of 296 events), frontier_extended s123 14.95 -> 1.13. Ruled by rpg-planner 2026-10-14: fire on the transition into the diverged state, per entity.

## Scope
- New `src/observability/divergence_episode.py`: `DivergenceEpisodes.project_kind(...)` (the diverged project kind, or "" when not diverged) and `started(entity_id, project_kind)` (True only on the update entering the diverged state), run-scoped per-entity state cleared by `EventExtractor.reset_run_state`.
- Both producers call it, so the live shaper and the extractor rollback path agree.

## Out of Scope
Re-anchoring the affected anchors (testing's process); the PROGRESSION no-data contract (its own ticket, held for testing's harness).

## Acceptance Criteria
- One event per episode: a diverged entity held over N updates emits once; after it stops diverging a new episode emits again; episodes are per entity and cleared at run start. Both paths.
- Measured: generated_frontier_3_42 s123 200t INFORMATION returns near its pre-#536 value (3.43 against 2.30), frontier_extended s123 unchanged (1.13).

## Related Tickets
TCK-20261014-POST-536-PROGRESSION-FLOOR-AND-INFORMATION-SPIKE-IN-200T-GRADE-ANCHORS; TCK-20261011-SIMQ-GRADE-ANCHORS-RUN-UNDER-AUDIT-MODE (#531).

## Related Docs
None.

## Related Stored Artifacts
None (hotfix).

## Related Code Areas
src/observability/divergence_episode.py, event_shapers.py (StrategyShaper), event_extractor.py (EventExtractor), src/simulation_quality/scorers/information.py (unchanged).

## Assumptions / Open Questions
The per-entity state is run-scoped observer state, like the extractor's other emitted sets, not durable simulation state.

## Implementation Notes
Pre-#536 tree c35ebf475, post-#536 b396080cc, this branch; calibrate_simq --audit-mode, 200t. generated_frontier_3_42 s123: INFORMATION 2.3021 / 41.7800 / 3.4315 (events 28 / 296 / 40; divergence events 15 / 279 / 23). frontier_extended s123: 14.945 / 1.13 / 1.13. crowded_frontier s123: 2.39 after.

Disclosure for the divergence entry (rpg-planner, 2026-10-14): INFORMATION moves on EVERY anchored key (the divergence event count falls wherever entities held a vague lead across updates), so the committed anchors go stale until the single re-anchor that follows this fix, the PROGRESSION no-data ticket and testing's harness ticket (TCK-20261013-SIMQ-NO-DATA-PILLAR-IN-GRADE-REGRESSION), all on main. Rationale class: Bug Fix (the pillar counted entity-updates held, not divergences). Divergence id assigned by rpg-planner at the fold.

## Test Summary
tests/unit/observability (1116 passed, 1 skipped, non-slow) incl. 3 new shaper tests and 1 extractor-path test; tests/simulation_quality/test_information_scorer.py green.

## Files Changed
src/observability/{divergence_episode,event_extractor,event_shapers}.py; tests/unit/observability/{test_event_shapers_strategy,test_event_extractor_information2}.py

## Completion Summary
Pending PR.
