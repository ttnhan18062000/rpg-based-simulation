---
status: historical
layer: combat
authority: P1
audience: agent
ticket_id: TCK-20261014-CHOKEPOINTS-ARE-FOUND-FROM-BLOCKED-TILES
phase: done
date: 2026-10-14
tags: []
---

# TCK-20261014-CHOKEPOINTS-ARE-FOUND-FROM-BLOCKED-TILES

## Title
Chokepoints are found from blocked_tiles, so the chokepoint mechanic can run (designer application of D56).

## Status
DONE

## Tier
standard

## Type
repair

## Priority
P1

## Request Summary
`positioning.py` found a chokepoint as a one-tile gap between two "WALL" terrain tiles; no terrain is "WALL", so none was ever found. Read `state.blocked_tiles` (structures) instead.

## Scope
- Chokepoint detection reads `state.blocked_tiles`; report the consumers; measure alone; divergence 2.130.

## Out of Scope
- The walk check, cover and high ground (their own tickets).

## Acceptance Criteria
- A one-tile gap between two blocked tiles is a chokepoint; a gap between open terrain tiles is not (test).
- No "WALL" literal in positioning.py.
- Divergence entry with the measurement and the consumer list.

## Related Tickets
- TCK-20261014-TERRAIN-DECLARES-COVER-AND-HIGH-GROUND-IN-CONTENT, TCK-20261008-CHOKEPOINT-HOLD-HAS-NO-ROUTER-HANDLER-AND-ENDS-AS-UNSUPPORTED-ACTION

## Related Docs
- docs/guidelines/intentional_divergences.md (2.130, 2.90), docs/parity_ledger/combat_movement.yaml (COMB-015)

## Related Stored Artifacts
- agent-working/stored_artifacts/TCK-20261014-CHOKEPOINTS-ARE-FOUND-FROM-BLOCKED-TILES/

## Related Code Areas
- src/engine/positioning.py, src/engine/tactical.py (VANGUARD hold), src/engine/domain/action_router.py

## Assumptions / Open Questions
- Behaviour fold is held by the owner until the 10-seed cumulative D76 ruling (rpg-planner); the branch is pushed, not folded.

## Implementation Notes
See plan.md and divergence 2.130.

## Test Summary
tests/unit/combat: 164 passed (incl. 8 new). Paired run: 40 runs, no drift; probe: finder reached, 0 chokepoints found, 0 holds.

## Files Changed
src/engine/positioning.py, tests/unit/combat (1 new, 1 converted), divergence log (2.130, 2.129 highland note), parity row COMB-015.

## Completion Summary
Done; divergence 2.130. Dormant in the gate worlds (no chokepoint geometry), proved by unit tests.
