---
status: historical
layer: combat
authority: P2
audience: agent
ticket_id: TCK-20261014-CHOKEPOINTS-ARE-FOUND-FROM-BLOCKED-TILES
artifact_type: plan
tags: []
---

# plan - TCK-20261014-CHOKEPOINTS-ARE-FOUND-FROM-BLOCKED-TILES

1. `PositioningService.identify_chokepoints` reads `state.blocked_tiles` (structures' tiles) for both the walkable check and the two opposite-side checks; it reads no terrain.
2. Report the consumers of the finder (one: the VANGUARD hold in `tactical.py`, routed as a typed no-op success by `action_router.py`).
3. New tests in `test_chokepoints_from_blocked_tiles.py`; convert the staging in `test_chokepoint_hold.py` from `WALL` terrain to `blocked_tiles`; point parity row COMB-015 at divergence 2.130.
4. Measure with the standard paired command (`--terrain`, 4 worlds) and a finder/hold call-count probe; write divergence 2.130; close.
