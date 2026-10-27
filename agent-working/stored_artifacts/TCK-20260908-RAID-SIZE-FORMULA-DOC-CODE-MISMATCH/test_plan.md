---
status: active
layer: world
authority: P1
audience: agent
ticket_id: TCK-20260908-RAID-SIZE-FORMULA-DOC-CODE-MISMATCH
artifact_type: test_plan
tags: [world, content]
---

# Test Plan — TCK-20260908-RAID-SIZE-FORMULA-DOC-CODE-MISMATCH

No code change, so no new test. The retirement is pinned by an existing test:
`tests/unit/world/test_calamity_raid.py` (`not hasattr(RaidService, "spawn_raid")`), which passes on this branch's base.
