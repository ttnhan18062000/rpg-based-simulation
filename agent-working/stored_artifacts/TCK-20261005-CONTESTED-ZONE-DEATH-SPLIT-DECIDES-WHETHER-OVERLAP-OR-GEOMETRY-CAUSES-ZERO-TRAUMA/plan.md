---
status: historical
layer: world
authority: P2
audience: agent
artifact_type: plan
ticket_id: TCK-20261005-CONTESTED-ZONE-DEATH-SPLIT-DECIDES-WHETHER-OVERLAP-OR-GEOMETRY-CAUSES-ZERO-TRAUMA
phase: done
date: 2026-10-05
tags: [world]
---

# plan — TCK-20261005-CONTESTED-ZONE-DEATH-SPLIT-DECIDES-WHETHER-OVERLAP-OR-GEOMETRY-CAUSES-ZERO-TRAUMA

Measurement only; no `src/` change, no precedence rule chosen (owner decision 13).
1. Static geometry for every corpus world (`probes/geometry.py`): overlap tiles per pair and owned-tile share under the rule in force.
2. Death split (`probes/zones.py`, extending the earlier overlap probes): tick-start position, containing-region set, credited region, victim and killer faction/species/role, outcome, hazard damage. Every run under `audit_mode` with `max_tick_budget_ms=1e9`.
3. Worlds: `frontier_living_world` (required), plus one world per author-call pair: `frontier_extended` and `simq_scale_stress_seed42` (`goblin_camp`/`haunted_battlefield`, `old_mine`/`sacred_grove`+`deep_forest`, `haunted_battlefield`/`river_ford` in the second), `hero_guild_routing` and `lifecycle_full_coverage_world` (`mountain_pass_zone`/`haunted_battlefield`). `quest_dense_frontier` was tried and failed at kernel construction (artifact manifest JSON decode error), so two worlds cover that pair instead.
