---
status: historical
layer: engine
authority: P1
audience: agent
ticket_id: TCK-20261014-TERRAIN-COST-BECOMES-TIME-A-STEP-COSTING-N-TAKES-N-TIMES-AS-LONG-D75
phase: done
date: 2026-10-14
tags: []
---

# TCK-20261014-TERRAIN-COST-BECOMES-TIME-A-STEP-COSTING-N-TAKES-N-TIMES-AS-LONG-D75

## Title
Terrain cost becomes TIME: a step onto a tile of cost N takes N times as long (D75, MOV-04). The terrain multiplier leaves the readiness pre-check in the same change.

## Status
DONE

## Tier
standard

## Type
feature

## Priority
P1

## Request Summary
Owner ruling D75 (2026-10-14), memo row 75, roadmap 75, via rpg-designer and rpg-planner:
- Terrain cost: a step costing N takes N times as long (road 0.5 takes half as long, mountain 4.0 four times). Route choice weighted by cost is the NEXT step, not this one. No fatigue now.
- D72 shipped the cost in content (divergence 2.124); its only reader was the readiness pre-check at `legality.py:190`, which refused steps and charged nothing, and moved frontier seeds both ways.
- In this same change the terrain multiplier LEAVES that pre-check. The plain `move_cost` readiness check stays.
- Measure alone, paired, seeds 42-46 at 5000 ticks, on `frontier_living_world` and `urban_political`, plus at least one mountain/river world (for example `highland_traverse`). Report drift with the per-terrain refusal counts of the pre-check (they should fall back to the old values).

## Scope
- Make a step's duration depend on the declared terrain cost of the tile entered, through a typed durable field, with a lifecycle and a test.
- Remove the terrain factor from `LegalityServiceV2.verify_movement_legality`; keep `move_cost / move_speed_mult`.
- Divergence, parity row, Bible note, measurement.

## Out of Scope
- Route choice weighted by cost (next step). Fatigue. Per-body movement styles (M1).
- The line-of-sight / wall checks (own ticket; rpg-planner drafting).

## Acceptance Criteria
- A step onto a tile of cost N takes N times as long as a step onto cost 1.0, pinned by a test per terrain value.
- The pre-check no longer reads terrain cost; pre-check refusals per terrain return to the pre-D72 values.
- Paired measurement recorded with drift reported, no direction claimed from five seeds.

## Related Tickets
TCK-20261013-TERRAIN-COST-IS-KEYED-BY-UPPER-CASE-NAMES-SO-LOWER-CASE-TERRAIN-GETS-COST-1 (D72).

## Related Docs
docs/guidelines/intentional_divergences.md 2.124; docs/mechanics/02_combat_laws.md section 8.

## Related Stored Artifacts
None.

## Related Code Areas
src/engine/movement.py; src/engine/legality.py (verify_movement_legality); src/engine/terrain_cost.py; src/engine/rpg_depth.py (TerrainCostService); src/core/state.py (NavigationComponent).

## Assumptions / Open Questions
- Cost below 1.0 (road 0.5) would mean more than one step per tick; the engine allows one. Designer ruled option A: keep the cap, road takes 1 tick, its edge comes with route weighting.

## Implementation Notes
NavigationComponent.step_ready_tick (typed, durable; canonical form only once non-zero), NavigationUpdate.step_ready_tick_set, patches/apply copy; resolve_move holds while tick < step_ready_tick and sets base + cost on a step (base = previous value if later than tick - 1, else tick); the terrain factor leaves verify_movement_legality. Two tests changed for stated reasons (divergence 2.126). Divergence 2.126, parity COMB-348, Bible ch02 section 8.

## Test Summary
New tests/unit/engine/test_terrain_cost_is_time.py (9). Chunked non-slow suite over every test directory, failing areas fixed and re-run. Paired measurement seeds 42-46, 5000 ticks: urban_political identical; frontier_living_world and highland_traverse differ (drift, see 2.126).

## Files Changed
src/core/state.py, src/core/updates.py, src/engine/{movement,legality,patches,apply}.py, tests (new unit file, terrain weighting, hunting scenario), docs (Bible ch02, parity COMB-348, divergence 2.126).

## Completion Summary
Terrain cost is time. One step per tick cap: road equals plain. Route weighting is the next step.
