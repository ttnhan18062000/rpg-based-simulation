---
status: historical
layer: strategy
authority: P1
audience: agent
ticket_id: TCK-20261009-HEROES-ON-A-LEASH-NEVER-SEEK-FOOD-AND-STARVE-WITHOUT-ONE-EAT-ATTEMPT
phase: done
date: 2026-10-09
tags: []
---

# TCK-20261009-HEROES-ON-A-LEASH-NEVER-SEEK-FOOD-AND-STARVE-WITHOUT-ONE-EAT-ATTEMPT

## Title
Living-world heroes starve without a single eat attempt: they hold LEASH and INTERCEPT moves 12-60 tiles from an inn while hunger rises, on main as on batch 2.

## Status
DONE

## Tier
standard

## Type
bug

## Priority
P1

## Request Summary
Lane B's batch-2 trace (2026-10-09; frontier_living_world, seeds 42-46, 5000 ticks, main edda25490 and batch 2 with and without profiles): heroes_other starvation is the leading cause of death on MAIN already (26 of 40 deaths; 33-35 on batch 2). Every starvation victim (36/39/36) has ZERO EAT, TOWN_SERVICE, CARRIED_FOOD or FORAGE events, accepted or rejected. Their last 10 decisions are mostly ENTITY_ACT with an empty payload, LEASH moves and INTERCEPT/attack moves. They die 12-60 tiles from the nearest inn at ticks 1900-4400. Free meals are on, so a reachable free way exists and is never tried. That is exactly what the M0 gate's H6 forbids, so the gate can't pass while this stands. Decision 36 (staged starvation) and SURV-07 (a need with no open way pulls toward the step that opens one) should already escalate hunger above the leash.

## Scope
- Find why rising hunger never wins over the leash/intercept behaviour for these heroes: the goal arbitration (SURV-07 escalation above ordinary goals, #414), the leash anchor, the interruption resistance (Bible 04), or a guard role that suppresses the need pull.
- Fix at the strategic/goal layer, not by stacking tactical scores (CLAUDE.md Strategic/Tactical rule).
- A mechanic scenario: a leashed hero with an inn in reach and rising hunger attempts a meal before the consequence line.

## Out of Scope
- The off-map pursuit runaway (its own ticket).
- Food supply amounts.

## Acceptance Criteria
- In the scenario, the hero attempts a meal before SURV-07's consequence line.
- Re-measure living heroes_other, main vs fix, 5 seeds: starvation victims with zero eat attempts falls to 0 (report it; no number targeted for starvation itself).

## Related Tickets
Batch 2 (EXCH-02 tickets; the trace is in its PR). M0 gate (designer memo rows 52-54: H6, R1). TCK-20261009-A-STARVATION-DEATH-RECORDS-THE-WAYS-IN-REACH-AND-THE-WAYS-TRIED-M0-GATE-H6.

## Related Docs
docs/mechanics/04_strategic_cognition.md; docs/world_rules (SURV-06, SURV-07).

## Related Stored Artifacts
Lane B's trace probe: /tmp/claude-1000/scratch27/trace2.py and an2.py (to be copied into batch 2's stored artifacts probes).

## Related Code Areas
src/ai/goals (need pull, opening steps), the leash logic, src/engine/tactical.py.

## Assumptions / Open Questions
- Code trace of origin/main (2026-10-09): there is NO LEASH movement mode. The leash is tactical.py:189-206 (LEASH_RETURN, RETREAT toward home_position past leash_radius, checked BEFORE objective pursuit, so an inn outside the radius is overridden every tick). Leashes are set only for monster spawns (generator.py). Check whether heroes_other entities carry a home_position/leash_radius from another path; if they do, that's the mechanism. Also: EatScorer is reached only on strategic cadence ticks and after several early returns in evaluate_strategic_intent (intelligence.py:1260-1541: an active objective, an active project, detours), so a held project/objective may never return to goal scoring. Check which of these the victims hit.
- Which archetypes in heroes_other (adventurer, mage-type, ranger-type) are affected. Rangers carry travel_ration 2; check whether they eat it.
- Lane: Lane A after the hunting batch, or the next free lane. If it touches scheduler.py or policy.py it waits for Phase B.

## Implementation Notes
- Designer's fiction lens (2026-10-09): a hungry subject's need re-decides a held chase. D32 notice-and-decide applies to hunger too.
- PARKED P3 CONTENT NOTE (designer, D33): adventurer_hero's hero_pocket (100 coin, small_potion 1, no food) is implausible; an adventurer sets out with a few days' provisions, so give it a couple of travel rations, in the ranger band. Sequence it AFTER this fix lands and H6 is measured on the logic alone, because adding rations first would hide this defect. It lands as its own content change with before/after figures, never sized to a starvation count. Check the mage-type archetypes too: if their content has them wandering the wild, they get the same treatment.

## Test Summary
tests/unit/engine/test_pressing_need_wakes_a_held_move.py (7), tests/unit/ai/test_way_in_range.py (5), tests/unit/worldbuilding/test_camp_has_wild_food_in_range.py (26, one per composed world plus the supplying-land report); updated pins: test_first_coin_is_declared_content, test_wild_food_node, test_assembly module count, the forage-loop scenario. Paired measurement (seeds 42-46, 5000 ticks, three camp worlds): see divergence 2.106.

## Files Changed
src/engine/need_pull.py, src/engine/scheduler.py, src/engine/rpg_depth.py, src/ai/goals/scorers.py, src/ai/goals/opening_steps.py, src/worldbuilding/camp_food.py, data/content/world_modules/goblin_camp_forage.yaml, data/content/world_modules/camp_maturity_calibration_pilot.yaml, data/content/world/runtime_regions.yaml, nine data/worlds/*/world.yaml and their resolved/ artifacts, the tests above, docs/mechanics/04_strategic_cognition.md, docs/parity_ledger/strategic_cognition.yaml, docs/guidelines/intentional_divergences.md.

## Completion Summary
A pressing need wakes the brain of an entity holding a move; a range-bound subject targets only ways inside its range; each goblin camp has berries inside its range (camp monsters eat them, 0 meals outside range, 0 inn meals). The ticket's frontier "heroes" were leashed camp monsters, misgrouped. Victims who never ate do not fall to 0; the rest are not this mechanism. The held-move completion rule, the passive-death cause label and the never-ate diagnosis are the next tickets.
