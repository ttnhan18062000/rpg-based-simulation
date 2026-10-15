---
status: historical
layer: engine
authority: P1
audience: agent
ticket_id: TCK-20261014-ROUTES-WEIGH-TERRAIN-COST-D75-ROUTE-STEP
phase: done
date: 2026-10-14
tags: []
---

# TCK-20261014-ROUTES-WEIGH-TERRAIN-COST-D75-ROUTE-STEP

## Title
Routes weigh terrain cost (D75, MOV-04, the route step): route choice weighs each tile by its declared terrain cost, so a road (0.5) becomes preferred.

## Status
DONE

## Tier
standard

## Type
feature

## Priority
P1

## Request Summary
Owner ruling D75 (2026-10-14), step after time (divergence 2.126): "a step costing N takes N times as long, and routes weigh the cost". Under the one-step-per-tick cap a road is no faster than plain, so its advantage has to come from route choice. Build on rpg-next 3696d0402. Measured paired after diet folds (frontier, urban, highland, seeds 42-46, 5000 ticks): road share (headline), steps and ticks per episode, pre-check refusals, deaths by kind, people deaths per seed.

## Scope
- Find the real route planner and its callers (done in Investigation: there is no weighted planner today).
- Route choice weighs each tile by `terrain_cost`.
- Divergence, parity row, Bible note, measurement.

## Out of Scope
- Fatigue. Per-body movement styles (M1). More than one step per tick. Cover and high ground, chokepoints.

## Acceptance Criteria
- A route prefers a cheaper (road) tile when the detour does not cost more than it saves; pinned by tests.
- Deterministic; bounded cost per decision; pure read of state.
- Paired measurement recorded, reported as drift.

## Related Tickets
TCK-20261014-TERRAIN-COST-BECOMES-TIME-A-STEP-COSTING-N-TAKES-N-TIMES-AS-LONG-D75; TCK-20261013-TERRAIN-COST-IS-KEYED-BY-UPPER-CASE-NAMES-SO-LOWER-CASE-TERRAIN-GETS-COST-1.

## Related Docs
docs/guidelines/intentional_divergences.md 2.124, 2.126; docs/mechanics/02_combat_laws.md section 8.

## Related Stored Artifacts
None.

## Related Code Areas
src/systems/world_systems/navigation.py (NavigationSystem.get_next_step, FlowFieldService); src/engine/movement.py (resolve_move); src/engine/movement_cache.py; src/engine/pipeline_phases/movement.py (position-swap next step).

## Assumptions / Open Questions
- (Resolved) There was no A*. `NavigationSystem.get_next_step` takes one axis-dominant step toward the target (no terrain, no obstacles); `FlowFieldService` is an anchor stub used only for a far TOWN target. The planner shape (a bounded weighted search versus a greedy two-neighbour choice) is a decision for rpg-planner and the designer.

## Implementation Notes
src/engine/route_search.py: bounded A* (node cap 3000) over declared terrain cost; the route leaves the greedy step only when cheaper; plans stored whole on AuthoritativeState.route_plans (RoutePlanStore, outside the hash, carried by apply); fallbacks counted. MovementSystem._route_step wires it. True terrain map, terrain cost only (disclosed). MovementPlanCache is never constructed in src, so the store is new rather than the dead cache. Divergence 2.128, parity COMB-349, Bible ch02 section 8.

## Test Summary
New tests/unit/engine/test_route_weighs_terrain_cost.py (9). Affected movement, pipeline, world, engine, architecture and hunting tests pass. Code-health 0 new, 0 worse; lint-imports 17 kept, 0 broken. Paired measurement under audit_mode with base-vs-base and on-vs-on determinism checks (2.128).

## Files Changed
src/engine/route_search.py (new), src/engine/movement.py, src/core/state.py, src/engine/apply.py, tests (new unit file), docs (divergence 2.128, parity COMB-349, Bible ch02).

## Completion Summary
Routes weigh terrain cost: a cheaper route than the greedy walk is taken when one exists. Fallback rate 0.004% frontier, 0 urban; detours 2.0% and 0.34% of searches. Drift, raiders flagged for the extinction watch.
