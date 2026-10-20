---
status: active
layer: ai
authority: P1
audience: agent
ticket_id: TCK-20261020-A-DEAD-BODY-IS-NOT-A-PERCEIVED-THREAT
phase: open
date: 2026-10-20
tags: []
---

# TCK-20261020-A-DEAD-BODY-IS-NOT-A-PERCEIVED-THREAT

## Title
A dead body in the neighbour view is not a perceived threat: the panic gate, the emotional appraisal and the saliency ranking skip the dead

## Status
INPROGRESS

## Tier
standard

## Type
bug

## Priority
P1

## Request Summary
Raider 27 of crowded_frontier seed 45 (the v1 gate's V3 death, t1091) shuttled on y=40 between the corpses of workers 2, 3 and guard 11 and the inn until it starved. The neighbour view lists dead entities; the tactical panic gate (`_perceived_threats`) had no alive test, so a hp-2 raider fled from corpses every ~10 ticks while the brain tick (which filters the dead) saw nothing to avoid. Designer ruling (via rpg-planner): option B alone, before v1; one defect, so appraisal and saliency stay in the same step.

## Scope
- `TacticalDecisionSystem._perceived_threats` skips non-alive entities.
- `AppraisalSystem.evaluate_emotional_state` ignores dead neighbours (hostile ratio, allies, nemesis, grudge).
- `SensoryFilter.filter_saliency` gives a dead body no hostility bonus.
- Audit of every neighbour-view and hostile reader (list under Implementation Notes).

## Out of Scope
- The hunger re-choice (parked: TCK-20261020-PARKED-HUNGER-SAFE-ROUTE-STEP-AFTER-V1).
- Blacksmith 13's hunger-100/no-project state on crowded s45 (its own trace).

## Acceptance Criteria
- A corpse in view gives no PANIC_RETREAT; a live hostile in view still does; a hungry hp-2 raider with the three townsfolk dead on its walk reaches a meal and eats.
- V3 crowded 45 is 0 (gate harness).

## Related Tickets
- TCK-20261020-A-HUNGER-PULL-AIMS-AT-A-WAY-WHOSE-ROUTE-IS-NOT-THREATENED (parked), TCK-20261020-PARKED-HUNGER-SAFE-ROUTE-STEP-AFTER-V1

## Related Docs
- docs/mechanics/04_strategic_cognition.md, docs/guidelines/intentional_divergences.md (2.114)

## Related Stored Artifacts
- None yet (standard tier: plan/investigation/test_plan are written at close).

## Related Code Areas
- src/engine/tactical.py, src/engine/cognition.py

## Assumptions / Open Questions
- Grief, mourning and vengeance do not read appraisal's ally/nemesis lists: grief reads the death record and `trust_history` (src/core/grief_triggers.py), the heir's nemesis comes from strategic blockers (lifecycle.py), campaign nemesis from campaign state.

## Implementation Notes
Audit (get_neighbor_view and every are_entities_hostile reader). Already filtered on alive: intelligence.py 152 and 444, intake.py 35, scorers.py 180, scorers_support perceived_hostiles, cooperation/providers 53, combat.py 496, legality get_engaged_hostiles_at_pos, classify_neighbours (via perceives). Fixed here: tactical._perceived_threats, appraisal (and its callers domain/cognition 57, CombatRetreatScorer, intelligence 1020), saliency. Not hostile reads: intelligence 592/914 salience (dead-ally grief branch wants corpses), worker_logic/actions/kernel neighbour views feeding action execution, spatial_query, combat_engagement phase (filters alive). Occupancy maps are alive-only.

## Test Summary
tests/integration/observability/test_a_dead_body_is_not_a_perceived_threat_through_the_real_kernel.py (3): (a) and (c) fail without the fix, (b) passes both ways.

## Files Changed
src/engine/tactical.py, src/engine/cognition.py, the test file above.

## Completion Summary
Open.
