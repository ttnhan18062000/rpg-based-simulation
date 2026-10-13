---
status: historical
layer: strategy
authority: P1
audience: agent
ticket_id: TCK-20261011-A-PANIC-RETREAT-TO-ITS-OWN-TILE-IS-HELD-WITH-NO-THREAT-IN-SIGHT
phase: done
date: 2026-10-11
tags: []
---

# TCK-20261011-A-PANIC-RETREAT-TO-ITS-OWN-TILE-IS-HELD-WITH-NO-THREAT-IN-SIGHT

## Title
A wounded subject with no threat in sight flees to its own tile and stands in a held PANIC_RETREAT above hunger.

## Status
DONE

## Tier
hotfix

## Type
bug

## Priority
P1

## Request Summary
rpg-planner dispatch after the never-ate diagnosis (pattern 2): merchants #19 and #28 held PANIC_RETREAT to their own tile for 380 to 500+ ticks, no hostile within 12 tiles, hp 7/85, then slept through starvation.

## Scope
The first tactical panic gate (tactical.py) flees only with a perceived threat; PANIC_RETREAT ends within a tile of its point (arrived_in_area).

## Out of Scope
Natural hit-point regeneration (a disclosed gap, designer asked separately); a starving sleeper never woken by hunger; coin-less hunger (earn path); the 15% pure retreat (already hostile-gated).

## Acceptance Criteria
No PANIC_RETREAT without a perceived threat; a cornered subject with a threat still holds (MOV-03); held own-tile flights fall; no death count worsens beyond 2 SE.

## Related Tickets
TCK-20261011-A-HELD-MOVE-STANDS-FROZEN-AFTER-ARRIVING-IN-ITS-AREA

## Related Docs
docs/mechanics/04_strategic_cognition.md; docs/guidelines/intentional_divergences.md Section 2.114; docs/parity_ledger/combat_movement.yaml COMB-346.

## Related Stored Artifacts
None.

## Related Code Areas
src/engine/tactical.py, src/engine/candidate_selector.py, src/engine/cognition.py (unchanged).

## Assumptions / Open Questions
HP regeneration outside a town tile is absent (disclosed). Regional dread or a grudge alone never flees (rpg-planner, yes).

## Implementation Notes
Measured vs rpg-lanec-arrival 4815cb85f, seeds 42 to 46, 5000 ticks: own-tile PANIC_RETREAT hold ticks urban 1357 to 1, frontier 2181 to 115; never-ate urban 0.4 to 0.

## Test Summary
tests/unit/combat/test_panic_flight_needs_a_present_threat.py (5); arrival tests updated; engine and combat unit groups pass (670).

## Files Changed
See the branch diff.

## Completion Summary
The panic flight needs a present threat; divergence 2.114, COMB-346.
