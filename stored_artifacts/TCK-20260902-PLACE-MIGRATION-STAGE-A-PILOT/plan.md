---
status: historical
layer: world
authority: P1
audience: agent
ticket_id: TCK-20260902-PLACE-MIGRATION-STAGE-A-PILOT
artifact_type: plan
tags: [content, determinism]
---

# Plan — TCK-20260902-PLACE-MIGRATION-STAGE-A-PILOT

1. Add one `places:` declaration to `frontier_village_core.yaml`'s `hometown` region
   (`{id: hometown_city, kind: city, position: [25, 25]}`, centroid of `grid_bounds`).
2. Re-resolve and recompile `unit_information_source` with the correct committed seed (42).
3. Verify via `CanonicalStateHasher` (not `state_hash` alone, found blind to Place data) that the only
   diff between with/without-Place compiled states is `regions`/`places` — nothing else.
4. Add `canonical_state_hash`/`place_count` to `WorldCompiler.compile()`'s report output, so this
   verification is a first-class, reusable check (not a one-off script) for Recalibration's own future
   needs.
5. Regenerate the real committed `world_compile_report.json`/`resolved/` assets for
   `unit_information_source`.
6. Write regression tests locking in both the new report fields and the exact regression this ticket
   found (`state_hash` blind, `canonical_state_hash` not).
7. File a follow-up ticket for the repo-wide baseline staleness found along the way — genuinely out of
   scope for idea 66, root-caused (not a determinism bug) but not fixed here.
