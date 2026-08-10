---
status: active
layer: combat
authority: P2
audience: agent
ticket_id: TCK-20260810-NAVIGATION-SINGLE-AXIS-STEPPING-DIAGONAL-PURSUIT-DEADLOCK
artifact_type: test_plan
tags: [combat, engine]
---

# Test Plan: TCK-20260810-NAVIGATION-SINGLE-AXIS-STEPPING-DIAGONAL-PURSUIT-DEADLOCK

## New Tests
`tests/unit/movement/test_navigation_get_next_step.py` (new file, first direct coverage for
`get_next_step()`):
- `test_get_next_step_moves_x_when_dx_strictly_greater`
- `test_get_next_step_moves_y_when_dy_strictly_greater`
- `test_get_next_step_favors_y_on_exact_diagonal_tie`
- `test_get_next_step_single_sided_pursuit_of_static_target_converges` — regression guard
  confirming the deadlock is genuinely mutual-pursuit-specific, not a general diagonal-approach
  issue
- `test_get_next_step_mutual_diagonal_pursuit_deadlocks` — characterization test locking in the
  current, real, confirmed deadlock behavior (not a "should never happen" assertion)

## Fixed Test (unrelated regression found during sweep)
`tests/unit/world/test_terrain_weighting.py::test_terrain_readiness_success` — updated a stale
assertion left behind by an earlier same-session ticket
(`TCK-20260809-COMBAT-PACING-READINESS-MOVEMENT-DECOUPLE`) whose own scoped test sweep never
included `tests/unit/world/`.

## Regression Scope
`tests/unit/movement/`, `tests/unit/world/`, `tests/unit/combat/`, `tests/unit/tactical/`,
`tests/unit/kernel/`, `tests/unit/core/`, `tests/unit/engine/`.

## Prevalence Measurement (the primary deliverable)
A live, non-mocked `Kernel.tick_once()` loop, 3 seeds (42/123/456) × up to 8 corpus worlds
(`dungeon_crawl`, `urban_political` at all 3 seeds; `wilderness_survival`, `crowded_frontier`,
`swamp_border_world`, `hero_guild_routing` at seed 42), 2000 ticks each, tracking mutual-pursuit
pairs and their Manhattan-distance streak length.
