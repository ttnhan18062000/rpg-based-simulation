---
status: historical
layer: world
authority: P2
audience: agent
ticket_id: TCK-20261014-CAMPS-STOP-SPAWNING-MONSTERS-FROM-NOTHING-D70
artifact_type: investigation
tags: []
---

# investigation — TCK-20261014-CAMPS-STOP-SPAWNING-MONSTERS-FROM-NOTHING-D70

- The camp spawn added a monster every CAMP_SPAWN_INTERVAL ticks below max(2, maturity/10) members, with no parent and no cost; the raid added 3 + maturity raiders for a 20-maturity cost. Both are V1 violations (D67, D70).
- The nest-spread branch and the natural-creature path are flag-OFF; kept.
- No remaining camp logic reads `EntityRole.MONSTER`; the imports were removed with the block.
- `RaidService` callers: only camp.py's trigger; `spawn_raid` had tests only.
- The camp mechanism still binds `EntityGenerator` because `process_camps` calls it for the flag-OFF nest-spread offspring.
