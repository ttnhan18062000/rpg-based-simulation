---
status: historical
layer: world
authority: P2
audience: agent
ticket_id: TCK-20261008-RECIPE-NODES-LAND-ON-TILES-THEIR-REGION-DOES-NOT-OWN-P3
artifact_type: plan
tags: [world, content, economy]
---

# plan — TCK-20261008-RECIPE-NODES-LAND-ON-TILES-THEIR-REGION-DOES-NOT-OWN-P3

## Approach
- Placement default for recipe nodes: owned tiles of the declaring region.
- `wild_edge_forage` world module and its wiring into `crowded_frontier` (Decision 35).
- Divergences 2.96 (placement) and 2.99 (crowded edge).

## Scope guards
- Changing node yields or counts.
- Any other world's layout.
