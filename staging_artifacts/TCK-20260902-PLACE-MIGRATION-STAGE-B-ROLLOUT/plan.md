---
status: active
layer: world
authority: P1
audience: agent
ticket_id: TCK-20260902-PLACE-MIGRATION-STAGE-B-ROLLOUT
artifact_type: plan
tags: [content, determinism]
---

# Plan — TCK-20260902-PLACE-MIGRATION-STAGE-B-ROLLOUT

1. Migrate `hero_guild_routing`'s 4 regions to Place-shaped content.
2. Compile and verify by direct inspection that each region produces the expected `Place.kind`
   (City/CAMP/RUIN/no-Place-wilderness as applicable to `mountain_pass`).
3. Only once verified: migrate the remaining 19 worlds' content, one at a time, recompiling each.
4. Hand off each world's compiled result to `TCK-20260902-PLACE-MIGRATION-RECALIBRATION` for
   `state_hash`/grade triage — do not triage within this ticket.
5. Reassess mid-way (per this ticket's own Assumptions note) whether the remaining-19 batch should split
   into smaller PRs.
