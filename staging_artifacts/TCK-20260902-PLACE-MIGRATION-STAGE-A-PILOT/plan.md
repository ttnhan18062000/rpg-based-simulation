---
status: active
layer: world
authority: P1
audience: agent
ticket_id: TCK-20260902-PLACE-MIGRATION-STAGE-A-PILOT
artifact_type: plan
tags: [content, determinism]
---

# Plan — TCK-20260902-PLACE-MIGRATION-STAGE-A-PILOT

1. Migrate `unit_information_source`'s content to Place-shaped form (1 Region, 1 `Place(kind=CITY)`).
2. Compile under the new schema.
3. Diff `state_hash` against the committed baseline in its `world_compile_report.json`.
4. If byte-identical: done, proceed to Stage B. If not: hand-verify the diff, explain it, and record
   explicit acceptance (or reject and fix) before Stage B starts — never silently proceed on a changed
   hash.
