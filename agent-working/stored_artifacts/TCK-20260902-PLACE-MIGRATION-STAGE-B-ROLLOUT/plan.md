---
status: historical
layer: world
authority: P1
audience: agent
ticket_id: TCK-20260902-PLACE-MIGRATION-STAGE-B-ROLLOUT
artifact_type: plan
tags: [content, determinism]
---

# Plan — TCK-20260902-PLACE-MIGRATION-STAGE-B-ROLLOUT

1. Add `places:` to `ruins_mystery_quest.yaml`'s `haunted_battlefield` (RUIN, `hazard_level: 3.5`) and
   `goblin_camp_conflict.yaml`'s `goblin_camp` (CAMP). Leave `mountain_pass.yaml` untouched (empty
   wilderness case).
2. Resolve + compile `hero_guild_routing`, verify by direct inspection all 4 region kinds produce the
   expected `Place.kind` (or none, for `mountain_pass_zone`).
3. Verify isolation (canonical-dict diff, only `regions`/`places` change) — same rigor as Stage A.
4. Compute the real union of affected worlds; investigate and cover the 2 that use none of the 3 edited
   modules (`highland_traverse` via `settled_quarter`, `wilderness_survival` via
   `survivor_camp_shelter`/`undead_battlefield`) rather than leaving them uncovered.
5. Run a batch resolve+compile pass across all 21 worlds, regenerating their committed
   `world_compile_report.json`/`resolved/` assets.
6. Verify isolation holds at multiple scales (not just the smallest pilot world).
7. Write a regression test locking in `hero_guild_routing`'s real 4-region-kind acceptance criterion.
