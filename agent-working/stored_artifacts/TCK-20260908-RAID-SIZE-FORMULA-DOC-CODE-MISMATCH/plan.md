---
status: active
layer: world
authority: P1
audience: agent
ticket_id: TCK-20260908-RAID-SIZE-FORMULA-DOC-CODE-MISMATCH
artifact_type: plan
tags: [world, content]
---

# Plan — TCK-20260908-RAID-SIZE-FORMULA-DOC-CODE-MISMATCH

Disposition close, no code change. The ticket asks which `raid_size` formula is right; the plan is to verify that
the question still has an object, and close it if it does not.

1. Check each raid path named in the ticket against main 3533fde71: the global `RaidService.check_for_raid` and the
   camp-triggered `RaidService.spawn_raid`.
2. If both are gone, record the verification and close with a Completion Summary stating no code changed.
3. Report (do not edit) the contract doc that still describes both paths as live.
