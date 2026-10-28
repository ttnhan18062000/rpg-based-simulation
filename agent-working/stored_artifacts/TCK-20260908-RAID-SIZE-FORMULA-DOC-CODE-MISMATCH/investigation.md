---
status: active
layer: world
authority: P1
audience: agent
ticket_id: TCK-20260908-RAID-SIZE-FORMULA-DOC-CODE-MISMATCH
artifact_type: investigation
tags: [world, content]
---

# Investigation — TCK-20260908-RAID-SIZE-FORMULA-DOC-CODE-MISMATCH

Checked at main 3533fde71 (2026-10-26):

- `python3 -c "from src.world.raid import RaidService; ..."`: `hasattr(RaidService, "check_for_raid")` is False and `hasattr(RaidService, "spawn_raid")` is False. The class keeps only `RAID_BASE_SIZE`, `RAID_INTERVAL_DAYS`, `SANCTUARY_RADIUS` and `TICKS_PER_DAY`. `src/world/raid.py` is 33 lines.
- Global raid: `src/engine/world_dynamics.py` section 3.5 builds an empty `StateUpdate` ("RETIRED", owner decision 9, 2026-10-03, TCK-20261003-GLOBAL-RAID-SPAWNS-AT-HARDCODED-ORIGIN-OUTSIDE-EVERY-REGION).
- Camp raid: `src/world/camp.py` no longer raids ("A camp no longer raids", owner ruling D70, 2026-10-14, divergence 2.125, TCK-20261014-CAMPS-STOP-SPAWNING-MONSTERS-FROM-NOTHING-D70). `tests/unit/world/test_calamity_raid.py` asserts `not hasattr(RaidService, "spawn_raid")`.
- Conclusion: nothing computes a raid size, so the doc-versus-code mismatch has no code side.
- Finding: `docs/world/raid_boss_camp_contract.md` (`last_verified: 2026-09-04`) still describes both paths as live (the "Resolved" paragraph for CAMP-RAID-ORIGIN-SPAWN-FIX, the "Raid composition" block, the extension rule citing `spawn_raid`). Reported, not edited.
