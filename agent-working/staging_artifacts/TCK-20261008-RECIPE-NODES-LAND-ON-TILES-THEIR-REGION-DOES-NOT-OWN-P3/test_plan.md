---
status: active
layer: world
authority: P2
audience: agent
ticket_id: TCK-20261008-RECIPE-NODES-LAND-ON-TILES-THEIR-REGION-DOES-NOT-OWN-P3
artifact_type: test_plan
tags: [world, content, economy]
---

# test_plan — TCK-20261008-RECIPE-NODES-LAND-ON-TILES-THEIR-REGION-DOES-NOT-OWN-P3

## Tests
tests/unit/worldbuilding/test_wild_food_node.py

## Acceptance map
- [ ] Recipe nodes in a compiled world sit on tiles their region owns (tests/unit/worldbuilding/test_wild_food_node.py).
- [ ] Resolved world artifacts regenerated and consistent.
- [ ] Divergences 2.96 and 2.99 recorded with a test path.

## Gates
mypy, ratchet, import-linter (17 kept), mechanism completeness pin, scoped unit sweeps, CI matrix sweep.
