---
status: historical
layer: engine
authority: P2
audience: agent
artifact_type: plan
ticket_id: TCK-20261013-TERRAIN-COST-IS-KEYED-BY-UPPER-CASE-NAMES-SO-LOWER-CASE-TERRAIN-GETS-COST-1
date: 2026-10-14
tags: []
---

# Plan: TCK-20261013-TERRAIN-COST-IS-KEYED-BY-UPPER-CASE-NAMES-SO-LOWER-CASE-TERRAIN-GETS-COST-1

Written at close. Dispatched as D72 by rpg-planner (owner ruling 2026-10-14). Steps: make `move_cost_multiplier` required on `TerrainDefinition`; set the ruled values in `terrain.yaml`; add `src/engine/terrain_cost.py` (exact-id lookup, raises on unknown); point `TerrainCostService` at it; retire `TERRAIN_COST`; validate terrain ids in `WorldCompiler`; fix test worlds; docs (divergence 2.122, COMB-347, Bible ch02 section 8); paired measurement. Route choice and per-body styles are out of scope (consumer pending a designer decision).
