---
status: historical
layer: combat
authority: P2
audience: agent
ticket_id: TCK-20261017-FORCED-SCENARIOS-FOR-COVER-CHOKEPOINTS-AND-HIGH-GROUND
artifact_type: investigation
tags: []
---

# investigation - TCK-20261017-FORCED-SCENARIOS-FOR-COVER-CHOKEPOINTS-AND-HIGH-GROUND

- Path probe (a1e4b6f3a, seed 42, 5000t): 1081 resolved attacks (878 resolve_attack, 203 multi_attack calls), 1094 multiplier calls, 0 skill and 0 AoE; highland_traverse has no fights. Probe: /mnt/data/scratch-rpg-implementer/path_probe.py.
- check_cover reads the tile on the attacker's side of the defender (x - sign(dx)), contrary to the Bible/docstring wording; pinned by tests/unit/engine/test_terrain_declares_cover_and_high_ground.py. Search tools were unavailable (index not found, no graph in worktree); grep used.
