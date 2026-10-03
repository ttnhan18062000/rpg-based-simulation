---
status: active
layer: strategy
authority: P2
audience: agent
ticket_id: TCK-20260807-TOWN-RETURN-TARGET-RESOLUTION-BUG
artifact_type: test_plan
tags: [strategy, simulation-quality]
---

# Test Plan: TCK-20260807-TOWN-RETURN-TARGET-RESOLUTION-BUG

## New/updated tests

**`tests/unit/tactical/test_objective_pursuit_coverage.py`**

| Test | Behavior verified |
|---|---|
| `test_reach_location_with_unparseable_target_id_falls_back_to_target_position` | `target="town_center"` (unparseable), `target_position=(0.0, 0.0)` set → entity navigates toward `(0.0, 0.0)` |
| `test_reach_location_with_unparseable_target_id_and_no_target_position_stays_unresolved` | `target="nowhere"`, `target_position=None` → no navigation (same as pre-fix behavior — not silently different) |
| `test_reach_location_target_position_fallback_does_not_override_resolvable_node_id` | A real resolvable resource-node `target` PLUS a deliberately wrong `target_position` → the resolvable ID's real position wins; `node_id` still populated, `interaction` update still fires at arrival |

**`tests/unit/strategic/test_expanded_goals.py`**

| Test | Behavior verified |
|---|---|
| `test_town_return_project_now_produces_real_navigation` | End-to-end: real `evaluate_strategic_intent()` (TownScorer wins under high hunger/sleep_debt) → real `evaluate_entity_intent()` → a real `NavigationUpdate` toward `town_center` results |

## Regression coverage
- Full `tests/unit/tactical/test_objective_pursuit_coverage.py` (7 tests total, including the
  pre-existing `test_reach_location_arrival_behavior_unchanged` anti-drift pin) re-run to confirm
  the resource-node/tavern/inn INTERACT/EAT/REST arrival-dispatch paths are byte-identical.
- `tests/unit/strategic/test_expanded_goals.py` full suite (8 tests, including the pre-existing
  `test_recover_scorer`/`test_resolve_blocker_scorer` scorer-level tests) re-run.
- Wider regression sweep: `tests/unit/tactical/`, `tests/unit/strategic/`, `tests/unit/movement/`,
  `tests/unit/combat/test_tactical_hardening.py`, `tests/unit/combat/test_tactical_legality.py`.

## Results
`tests/unit/tactical/` + `tests/unit/strategic/` + `tests/unit/movement/` +
`test_tactical_hardening.py` + `test_tactical_legality.py`: 247/248 passed. The 1 failure
(`tests/unit/movement/test_movement_spatial_regression.py::test_normal_move_triggers_oa`) is
pre-existing and unrelated — confirmed via `git stash` on this ticket's changed files: fails
identically on the clean baseline. It concerns an opportunity-attack combat mechanic in
`MovementSystem`, no intersection with `TacticalDecisionSystem._resolve_target_position` or any
file this ticket touches.

## Out of scope for this test plan
- Arrival-dispatch behavior for `TOWN_RETURN`/`RECOVER`/`RESOLVE_BLOCKER` once they DO arrive —
  not implemented in this pass (see investigation.md's "Confirmed open question" section);
  nothing to test here since the ticket's own scope stops at "does it navigate there."
