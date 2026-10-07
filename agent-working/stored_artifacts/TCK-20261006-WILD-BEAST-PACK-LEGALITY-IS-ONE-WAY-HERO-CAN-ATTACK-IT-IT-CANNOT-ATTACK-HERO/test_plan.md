---
status: historical
layer: world
authority: P2
audience: agent
artifact_type: test_plan
ticket_id: TCK-20261006-WILD-BEAST-PACK-LEGALITY-IS-ONE-WAY-HERO-CAN-ATTACK-IT-IT-CANNOT-ATTACK-HERO
phase: done
date: 2026-10-07
tags: [world, combat, legality]
---

# Test plan

- `tests/unit/world/test_spawn_monster_catalog_faction.py`: wolf/slime/bear/harpy/golem carry `wild_beast_pack` and `NATURAL_TERRAIN`; hero <-> spawned wolf/bear/golem legal both ways; rule 1 (wolf vs goblin, engaged), rule 2 both directions (hero vs neutral illegal both ways; hero vs undeclared monster-bucket legal both ways), rule 3 (undeclared pair, legacy fallback both ways). Positive control: with the old legality the hero/monster and wolf tests fail (4 failed).
- Unchanged and green: `tests/unit/engine/test_legality_faction_mutation.py` (a hero may not attack a defected NEUTRAL entity), `tests/unit/combat`, `tests/integration/combat`, `tests/integration/pipeline/test_combat_legality_matrix.py`, relation/species legality wiring tests.
- Measurement probes under `probes/`, results under `probes/results/`.

## Proof Plan

- **Level**: unit (legality verdicts) plus corpus measurement.
- **Proof kind**: regression pins and a before/after measurement.
- **Oracle source**: world rule CONFLICT-03 and its three-case resolution clause (memo row 18); the ratified defected-NEUTRAL pin in `test_legality_faction_mutation.py`.
- **Expected effect**: every faction pair has one verdict in both directions; spawned wolf/bear/golem and a hero may attack each other; a hero and a neutral may not.
- **Selected commands**: `pytest tests/unit/world/test_spawn_monster_catalog_faction.py tests/unit/engine/test_legality_faction_mutation.py tests/unit/combat tests/integration/combat tests/integration/pipeline/test_combat_legality_matrix.py`; probes `matrix.py`, `combat_ab.py`.
