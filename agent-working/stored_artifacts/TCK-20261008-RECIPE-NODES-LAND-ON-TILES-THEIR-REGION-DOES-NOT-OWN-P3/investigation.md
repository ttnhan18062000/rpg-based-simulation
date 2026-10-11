---
status: historical
layer: world
authority: P2
audience: agent
ticket_id: TCK-20261008-RECIPE-NODES-LAND-ON-TILES-THEIR-REGION-DOES-NOT-OWN-P3
artifact_type: investigation
tags: [world, content, economy]
---

# investigation — TCK-20261008-RECIPE-NODES-LAND-ON-TILES-THEIR-REGION-DOES-NOT-OWN-P3

## Findings
Recipe nodes were placed on tiles outside the owning region, so a compiled world had producers no resident could reach by its own region's law. Placement now defaults to owned tiles; `crowded_frontier` gets the forest-edge module (Decision 35).

## Code areas
`src/worldassembly/resolver.py`, `src/worldbuilding/compiler.py`, `data/content/world_modules/wild_edge_forage.yaml`

## Evidence
Paired pinned measurements (5 seeds x 3 worlds, 5000 ticks, kind groups) are in the PR; the earlier 4-arm table is in the removal-evidence probes directory.
