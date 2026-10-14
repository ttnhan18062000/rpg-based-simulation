---
status: active
layer: engine
authority: P1
audience: agent
ticket_id: TCK-20261014-ROUTES-WEIGH-TERRAIN-COST-D75-ROUTE-STEP
phase: open
date: 2026-10-14
tags: []
---

# TCK-20261014-ROUTES-WEIGH-TERRAIN-COST-D75-ROUTE-STEP

## Title
Routes weigh terrain cost (D75, MOV-04, the route step): route choice weighs each tile by its declared terrain cost, so a road (0.5) becomes preferred.

## Status
INPROGRESS

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
- There is no A* today. `NavigationSystem.get_next_step` takes one axis-dominant step toward the target (no terrain, no obstacles); `FlowFieldService` is an anchor stub used only for a far TOWN target. The planner shape (a bounded weighted search versus a greedy two-neighbour choice) is a decision for rpg-planner and the designer.

## Implementation Notes
TBD

## Test Summary
TBD

## Files Changed
TBD

## Completion Summary
TBD
