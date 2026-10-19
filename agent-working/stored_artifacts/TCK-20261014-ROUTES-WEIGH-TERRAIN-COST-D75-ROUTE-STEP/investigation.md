---
status: historical
layer: engine
authority: P2
audience: agent
artifact_type: investigation
ticket_id: TCK-20261014-ROUTES-WEIGH-TERRAIN-COST-D75-ROUTE-STEP
date: 2026-10-15
tags: []
---

# Investigation: TCK-20261014-ROUTES-WEIGH-TERRAIN-COST-D75-ROUTE-STEP

The only route chooser was NavigationSystem.get_next_step (greedy axis-dominant, terrain-blind); FlowFieldService is an anchor stub for a far town target; the swap phase has its own greedy step. MovementPlanCache is never constructed in src, so its next-step cache never ran.
