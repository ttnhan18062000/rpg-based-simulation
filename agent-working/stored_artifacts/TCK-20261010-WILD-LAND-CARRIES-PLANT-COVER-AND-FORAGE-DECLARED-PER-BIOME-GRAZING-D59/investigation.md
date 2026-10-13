---
status: historical
layer: simulation
authority: P1
audience: agent
ticket_id: TCK-20261010-WILD-LAND-CARRIES-PLANT-COVER-AND-FORAGE-DECLARED-PER-BIOME-GRAZING-D59
artifact_type: investigation
phase: done
date: 2026-10-11
tags: []
---

# investigation: grazing

Read first: ResourceNodeState and the ecology (200-tick regrowth, `max(1, round(regen * density_modifier))` floor), the harvest depletion record, the world_dynamics cooldown lifecycle (a finished cooldown ADDS `max_charges`: latent, nothing starts a cooldown today), the biome and region catalog (`runtime_regions.biome`), the resolver's resource merge, the opening-steps forage way.
Findings: (a) the density floor stacks with overgrazing (named in 2.107); (b) the none-path refill overshoots (filed separately); (c) a gatherer on a patch with charges holds its task until the patch is empty (the held-action defect, reason path in 2.107); (d) cover raises the node count per region: two nodes could share a tile (fixed in the compiler, test added).
Measurement: `probes/hunting_grazing_measurement.txt` under the hunting ticket's artifacts (n=3 per world against main fc0bf4fbb, 5000 ticks).
