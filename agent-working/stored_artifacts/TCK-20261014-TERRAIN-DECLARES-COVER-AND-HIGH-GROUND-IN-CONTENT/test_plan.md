---
status: historical
layer: combat
authority: P2
audience: agent
ticket_id: TCK-20261014-TERRAIN-DECLARES-COVER-AND-HIGH-GROUND-IN-CONTENT
artifact_type: test_plan
tags: []
---

# test_plan - TCK-20261014-TERRAIN-DECLARES-COVER-AND-HIGH-GROUND-IN-CONTENT

- `tests/unit/engine/test_terrain_declares_cover_and_high_ground.py`: ruled flags per catalog id, whole catalog covered, a missing flag fails to load, unknown id raises, cover on both axes, no cover from no tile or an adjacent attacker, high ground against a defender on mountain, no terrain name in either check.
- `tests/unit/world/test_local_environment_semantics.py::test_high_ground_bonus`, `tests/unit/engine/test_terrain_cost_from_content.py`, `tests/unit/engine/test_kernel_tick_reads_terrain_without_a_compile.py`.

## Proof Plan
- Level: unit tests plus a paired simulation measurement and a call-count probe.
- Proof kind: behavioural tests; paired audit_mode runs with a base-vs-base self-check.
- Oracle source: owner rulings D33, D56, D72 (terrain declares its properties; code names no terrain) and Bible 02 section 2.
- Expected effect: none in the gate worlds (the modifiers are dormant there); the unit tests carry the proof.
- Selected commands: `python -m pytest tests/unit/engine tests/unit/combat tests/unit/world -q`.
