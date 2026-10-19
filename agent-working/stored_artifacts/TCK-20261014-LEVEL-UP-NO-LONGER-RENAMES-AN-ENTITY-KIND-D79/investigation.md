---
status: historical
layer: simulation
authority: P2
audience: agent
ticket_id: TCK-20261014-LEVEL-UP-NO-LONGER-RENAMES-AN-ENTITY-KIND-D79
artifact_type: investigation
tags: []
---

# investigation - TCK-20261014-LEVEL-UP-NO-LONGER-RENAMES-AN-ENTITY-KIND-D79

- `evolution.py` ran every tick (no flag) and wrote `kind_set` unconditionally; on a crossing of 10/25/50 `_get_evolved_kind` renamed by name. No body, `species_id` unchanged.
- Consumers of the renamed kind: `calamity.py:99` (`kind == "hero"`; an evolved hero stopped matching), `ProgressionShaper` `entity_evolved` (diffs `kind_set` against the prior kind; dormant now).
- The goblin gear branch tests `"1"`/`"2"` in the kind; no shipped kind has a digit, so it never fired (dead before and after).
- Measured: nobody leaves level 0 in the three gate worlds in 5000 ticks, so the rename path was never live there; deaths, alive, levels and calamity are identical in all 15 pairs. Final digests differ in frontier and urban only through the removed `previous_kind` entity property (confirmed on frontier 42: first divergence tick 100, one entity, field `properties.previous_kind`). See divergence 2.133.
- Knowledge index was missing during this work (`search_docs` returned "index not found"), so docs were found by targeted grep after the handover note.
