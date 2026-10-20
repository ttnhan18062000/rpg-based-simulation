---
status: historical
layer: world
authority: P2
audience: agent
ticket_id: TCK-20261014-A-CONQUEST-NO-LONGER-SPAWNS-A-STRONGHOLD-BODY-D71
artifact_type: test_plan
tags: []
---

# test_plan — TCK-20261014-A-CONQUEST-NO-LONGER-SPAWNS-A-STRONGHOLD-BODY-D71

- Flip at -50 adds no entity and leaves `next_entity_id` alone (9 hero deaths leave -45 and unowned; the 10th flips).
- Liberation at +50 for an invader-owned region (19 invader deaths leave +45; the 20th frees it).
- Round trip changes no entity.
- The conquest entry point and the stronghold spawner no longer exist.
- A town in a conquered region pays its tax to the MONSTER_HORDE treasury with no stronghold in the world.
- Determinism.
