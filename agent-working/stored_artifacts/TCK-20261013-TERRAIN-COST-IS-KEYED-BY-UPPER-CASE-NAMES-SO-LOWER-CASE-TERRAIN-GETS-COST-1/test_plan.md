---
status: historical
layer: engine
authority: P2
audience: agent
artifact_type: test_plan
ticket_id: TCK-20261013-TERRAIN-COST-IS-KEYED-BY-UPPER-CASE-NAMES-SO-LOWER-CASE-TERRAIN-GETS-COST-1
date: 2026-10-14
tags: []
---

# Test Plan: TCK-20261013-TERRAIN-COST-IS-KEYED-BY-UPPER-CASE-NAMES-SO-LOWER-CASE-TERRAIN-GETS-COST-1

Proof: tests/unit/engine/test_terrain_cost_from_content.py (ruled values by id, required field, unknown id raises, exact match, TERRAIN_COST gone, corpus worlds use catalog terrain, unknown region terrain fails compile, tile cost in frontier_living_world, configure/reset isolation). Regression: chunked non-slow suite over every test directory. Measurement: paired, seeds 42-46, 5000 ticks, urban_political and frontier_living_world.
