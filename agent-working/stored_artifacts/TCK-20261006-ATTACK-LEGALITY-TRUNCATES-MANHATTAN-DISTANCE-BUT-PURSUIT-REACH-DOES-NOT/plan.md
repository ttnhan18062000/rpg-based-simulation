---
status: active
layer: combat
authority: P1
audience: agent
ticket_id: TCK-20261006-ATTACK-LEGALITY-TRUNCATES-MANHATTAN-DISTANCE-BUT-PURSUIT-REACH-DOES-NOT
artifact_type: plan
tags: [combat, cognition]
---

# Plan

1. First commit: the designer's ruling patch (memo row 25, MOV-07 amendment), `docs/REGISTRY.yaml` regenerated.
2. `navigation.py`: the flow step becomes a one-tile step along the flow vector's dominant axis; a tie takes the y axis, exactly as the local step does.
3. `legality.py`: `get_manhattan_dist` measures the distance between the tiles the positions stand on (`int(coord)` per coordinate, as every whole-tile lookup reads a position), no truncated sum. `candidate_selector._target_in_attack_reach` calls it, so legality and pursuit share one distance.
4. Parity: Bible 02 section 7 bullet, ledger COMB-337 (and COMB-333's support boundary), divergence 2.83 (Bug Fix).
5. Re-measure both worlds before and after; disclose the re-baseline.

Out of scope: MOV-07's evidence line (stays CONFLICTING; its flip rides a later designer batch), any change to melee adjacency, ranged reach, or the yield push.
