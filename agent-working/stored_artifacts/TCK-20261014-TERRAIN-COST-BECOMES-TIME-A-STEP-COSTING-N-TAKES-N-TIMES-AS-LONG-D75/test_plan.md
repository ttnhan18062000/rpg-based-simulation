---
status: historical
layer: engine
authority: P2
audience: agent
artifact_type: test_plan
ticket_id: TCK-20261014-TERRAIN-COST-BECOMES-TIME-A-STEP-COSTING-N-TAKES-N-TIMES-AS-LONG-D75
date: 2026-10-14
tags: []
---

# Test Plan: TCK-20261014-TERRAIN-COST-BECOMES-TIME-A-STEP-COSTING-N-TAKES-N-TIMES-AS-LONG-D75

Proof: tests/unit/engine/test_terrain_cost_is_time.py (steps per tick by terrain, the cap, held tick is not a failure, the pre-check ignores terrain, canonical form). Regression: chunked non-slow suite. Measurement: paired seeds 42-46 at 5000 ticks on frontier_living_world, urban_political and highland_traverse, with per-terrain pre-check refusals.
