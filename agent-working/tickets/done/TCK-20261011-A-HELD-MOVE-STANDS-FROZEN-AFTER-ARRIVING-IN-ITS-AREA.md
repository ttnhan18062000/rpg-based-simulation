---
status: historical
layer: strategy
authority: P1
audience: agent
ticket_id: TCK-20261011-A-HELD-MOVE-STANDS-FROZEN-AFTER-ARRIVING-IN-ITS-AREA
phase: done
date: 2026-10-11
tags: []
---

# TCK-20261011-A-HELD-MOVE-STANDS-FROZEN-AFTER-ARRIVING-IN-ITS-AREA

## Title
A held move stands frozen after arriving in its area: LEASH_RETURN, REGROUP and AVOID_HOSTILE end only on an exact tile the entity never stands on.

## Status
DONE

## Tier
hotfix

## Type
bug

## Priority
P1

## Request Summary
rpg-planner dispatch (2026-10-11): "a move completes on arriving in its area". A held ENTITY_MOVE runs no brain, so a move that reached its area but not its exact tile held its owner for hundreds of ticks (probe, seed 42, 1500 ticks: REGROUP mean run 97 to 239, max 1109; AVOID_HOSTILE mean 217 to 393; frontier LEASH_RETURN mean 183, max 788).

## Scope
MovementCandidateSelector.arrived_in_area and ARRIVAL_ENDS_MOVE_REASONS; LeashService.in_home_area; the REGROUP payload's arrival_radius; tile_distance (Lane A's helper, verbatim).

## Out of Scope
A dead band inside the leash edge (a designer knob not taken); the never-ate non-holder diagnosis; apply.py.

## Acceptance Criteria
Frozen-after-arrival ticks fall on all three reasons; no death count moves beyond 2 SE; both dispatchers end the move by the same rule; a move without an area is unchanged.

## Related Tickets
TCK-20261009-HEROES-ON-A-LEASH-NEVER-SEEK-FOOD-AND-STARVE-WITHOUT-ONE-EAT-ATTEMPT

## Related Docs
docs/mechanics/04_strategic_cognition.md; docs/guidelines/intentional_divergences.md Section 2.113; docs/parity_ledger/combat_movement.yaml COMB-345.

## Related Stored Artifacts
None.

## Related Code Areas
src/engine/candidate_selector.py, src/engine/rpg_depth.py, src/engine/tactical.py, src/engine/tile_distance.py.

## Assumptions / Open Questions
LEASH_RETURN ends at the leash edge (rpg-planner, option a); the edge-hover churn is disclosed in 2.113.

## Implementation Notes
Measured pinned NORMAL, seeds 42 to 46, 5000 ticks, urban_political and frontier_living_world: frozen REGROUP 10119 to 61 and 4235 to 45, AVOID_HOSTILE 1923 to 8 and 2720 to 30, LEASH_RETURN frontier 5825 to 1664. Frontier LEASH_RETURN re-issues within 20 ticks of a completion 12 to 1644 (SE 358).

## Test Summary
tests/unit/engine/test_move_completes_on_arriving_in_its_area.py (14); scoped unit run engine, combat, ai, worldbuilding: 1139 passed.

## Files Changed
See the branch diff.

## Completion Summary
A held move ends on arriving in its area on both dispatchers; divergence 2.113, parity COMB-345.
