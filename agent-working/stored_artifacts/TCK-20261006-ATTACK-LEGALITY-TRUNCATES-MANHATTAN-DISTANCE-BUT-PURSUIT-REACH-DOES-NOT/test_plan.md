---
status: active
layer: combat
authority: P1
audience: agent
ticket_id: TCK-20261006-ATTACK-LEGALITY-TRUNCATES-MANHATTAN-DISTANCE-BUT-PURSUIT-REACH-DOES-NOT
artifact_type: test_plan
tags: [combat, cognition]
---

# Test plan

New `tests/unit/engine/test_attack_reach_distance.py` (legality and pursuit reach agree on a constructed fractional pair, the ticket's `(93.34, 71.06)` / `(94.0, 70.0)`, and on integral pairs; the distance is the whole-tile distance). `tests/unit/movement/test_flow_field_navigation.py`: the old test pinned the leak (`0.7 < nx < 0.8`) and now expects the tile step `(0.0, 1.0)` for the exact tie; new tests for the dominant-axis choice and tie-break, and that a 60-step walk to a far town centre stays on whole tiles, is one tile per step and repeats exactly.

## Proof Plan
- **Level**: unit, plus a corpus before/after on both worlds.
- **Proof kind**: regression test that fails on the old code (the fractional pair disagreed there); before/after measurement.
- **Oracle source**: world rule MOV-07 as amended by Decision 25 (positions are whole tiles, one distance for every reach check).
- **Expected effect**: entities between tiles at any tick 9 / 13 to 0 / 0; reach versus legality disagreements 7 / 52 to 0 / 0.
- **Selected commands**: `pytest tests/unit/engine/test_attack_reach_distance.py tests/unit/movement tests/unit/combat/test_combat_legality_contract.py`; `probes/frac_probe.py <root> <world> 2000 42` on main `6e7ef56ec` and on this branch.
