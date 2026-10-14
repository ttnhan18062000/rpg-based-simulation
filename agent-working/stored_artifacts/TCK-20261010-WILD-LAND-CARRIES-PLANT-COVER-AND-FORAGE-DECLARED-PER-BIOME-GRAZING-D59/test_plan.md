---
status: historical
layer: simulation
authority: P1
audience: agent
ticket_id: TCK-20261010-WILD-LAND-CARRIES-PLANT-COVER-AND-FORAGE-DECLARED-PER-BIOME-GRAZING-D59
artifact_type: test_plan
phase: done
date: 2026-10-11
tags: []
---

# test plan: grazing

- LB-S22 `tests/mechanic_scenarios/test_grazing_on_plant_cover.py`: compile counts and declared charges; a hungry grazer eats cover and a person takes none; an emptied patch waits bare then regrows from zero.
- `tests/unit/world/test_resource_ecology.py` group D: the wait starts only for `regrow`, ends with no charges, ecology resumes from zero, the canonical form carries the mode only when declared.
- `tests/unit/worldbuilding/test_resource_nodes_never_share_a_tile.py`: six worlds x four seeds.
- Re-scoped to a person's food: wild-food node, first-coin, forage-loop, camp food, need-path tests.
- Gates: code-health ratchet, mypy baseline, import-linter, mechanism pin 333/246.
