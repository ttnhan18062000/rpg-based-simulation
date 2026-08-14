---
status: active
layer: combat
authority: P1
audience: agent
ticket_id: TCK-20260810-COMBAT-PURSUIT-STALE-TARGET-SNAPSHOT-NEVER-RETARGETS
artifact_type: test_plan
tags: [combat, engine]
---

# Test Plan: TCK-20260810-COMBAT-PURSUIT-STALE-TARGET-SNAPSHOT-NEVER-RETARGETS

## New Tests
`tests/unit/optimization/test_movement_candidate_selector.py`:
- `test_resolve_live_tracking_target_returns_live_position_when_target_alive`
- `test_resolve_live_tracking_target_falls_back_when_target_dead`
- `test_resolve_live_tracking_target_falls_back_when_no_target_id`
- `test_movement_selector_includes_pursuer_arrived_at_stale_snapshot_but_target_moved` — the exact
  bug reproduction: a pursuer whose persisted `navigation.target` equals its own current position
  must still be selected if `task.payload["target_id"]` names a still-alive entity elsewhere.

All 4 confirmed via `git stash` bisection to genuinely fail against pre-fix code.

## Updated Tests
`tests/integration/pipeline/test_combat_legality_matrix.py`:
- `test_pipeline_simultaneous_attack_atomicity`, `test_aoe_sliding_state_awareness` — updated to
  check the correct, already-established `payload_set == {}` reset behavior (previously checked a
  stale `outcome=="FAILURE"` expectation that predates `TCK-20260809-COMBAT-STUCK-ATTACK-TASK-
  DEAD-TARGET`'s own reset fix).

## Regression Scope
`tests/unit/optimization/`, `tests/unit/movement/`, `tests/unit/combat/`, `tests/unit/tactical/`,
`tests/unit/kernel/`, `tests/unit/core/`, `tests/unit/engine/`, `tests/unit/actions/`,
`tests/unit/strategic/`, `tests/unit/observability/`, `tests/unit/entities/`,
`tests/integration/combat/`, `tests/integration/pipeline/`,
`tests/integration/kernel/test_determinism_suite.py`, `test_seed_stability.py`,
`test_authoritative_outcome_truth.py` — full sweep, since the changed files are shared, core
engine dispatch paths (movement candidacy, ENTITY_MOVE work-item execution) touched by many
domains' own tests.

## Real Corpus Verification
Direct `Kernel.tick_once()` loop (2000 ticks, `dungeon_crawl_seed42` and `urban_political_seed42`,
corpus-default flags), comparing `combat_resolved`/`entity_killed`/`combat_damage`/
`combat_initiated`/`combat_engagement_started` event counts before and after the fix, plus a
`tools/calibrate_simq.py` run confirming the COMBAT pillar norm score change.
