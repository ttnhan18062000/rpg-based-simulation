---
status: historical
layer: combat
authority: P2
audience: agent
ticket_id: TCK-20261014-CHOKEPOINTS-ARE-FOUND-FROM-BLOCKED-TILES
artifact_type: investigation
tags: []
---

# investigation - TCK-20261014-CHOKEPOINTS-ARE-FOUND-FROM-BLOCKED-TILES

- Before the change no catalog terrain is `WALL`, so the finder never returned a tile and `HOLD_CHOKEPOINT` was never decided from a run (divergence 2.90 recorded 0 decisions in 30 runs).
- Consumers: one, `tactical.py` VANGUARD branch (target within 5 tiles; standing on a chokepoint with the target out of reach decides ENTITY_ACT HOLD). `action_router.py` HOLD is a no-op success.
- Paired measurement (40 runs, 4 worlds, seeds 42-46, 5000t): identical to base in every counter; people deaths 132/58/166/53; self-check byte-identical.
- Probe (seed 42): worlds hold 5-8 blocked tiles; finder reached in frontier (365), urban (116), crowded (217) and found 0 chokepoint tiles; 0 HOLD_CHOKEPOINT actions; highland never reached the finder (0 calls). Cause is geometry; the mechanic is dormant in the gate worlds and proved by unit tests.
- Knowledge index and graph were missing in this worktree; consumers were found by grep.
