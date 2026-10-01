---
status: historical
layer: world
authority: P2
audience: agent
ticket_id: TCK-20260930-RESOURCE-NODE-YIELDS-ITEM-COLLIDES-WITH-RESOURCE-KIND
artifact_type: test_plan
tags: [world]
---

# Test Plan — TCK-20260930-RESOURCE-NODE-YIELDS-ITEM-COLLIDES-WITH-RESOURCE-KIND

- Unit: context-resolved yield item for herb_patch/wood_node/iron_vein; no-context fallback via `ResourceRegistry`;
  unknown kind keeps declared string (unchanged behaviour).
- Corpus: for each world under `data/worlds`, compile with real context; every node yields an id `ItemRegistry`
  knows, and known kinds map to herb/wood/iron_ore.
- Runtime: probe before/after (see investigation.md) - misses and harvested-item presence.
- Scoped suite: worldbuilding, worldassembly, resource, engine, core, docs, world, integrity with
  `-m "not slow and not extra_slow"`.
- Slow tier: `test_corpus_diversity.py` vs untouched origin/main control; classified in investigation.md.
