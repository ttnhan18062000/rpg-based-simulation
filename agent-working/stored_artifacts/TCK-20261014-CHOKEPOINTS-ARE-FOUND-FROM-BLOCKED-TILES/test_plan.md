---
status: historical
layer: combat
authority: P2
audience: agent
ticket_id: TCK-20261014-CHOKEPOINTS-ARE-FOUND-FROM-BLOCKED-TILES
artifact_type: test_plan
tags: []
---

# test_plan - TCK-20261014-CHOKEPOINTS-ARE-FOUND-FROM-BLOCKED-TILES

- `tests/unit/combat/test_chokepoints_from_blocked_tiles.py`: gap side by side and above/below is a chokepoint; open terrain tiles and terrain called WALL are not; a blocked tile is never one; radius bounds the search; the finder names no terrain.
- `tests/unit/combat/test_chokepoint_hold.py` (staging converted to `blocked_tiles`, assertions unchanged).

## Proof Plan
- Level: unit tests plus a paired simulation measurement and a call-count probe.
- Proof kind: behavioural tests; paired audit_mode runs with a base-vs-base self-check.
- Oracle source: owner/designer ruling D56 (code names no terrain; walls are structures' blocked tiles) and divergence 2.90 (the hold).
- Expected effect: none in the gate worlds (no chokepoint geometry there); the unit tests carry the proof.
- Selected commands: `python -m pytest tests/unit/combat -q`.
