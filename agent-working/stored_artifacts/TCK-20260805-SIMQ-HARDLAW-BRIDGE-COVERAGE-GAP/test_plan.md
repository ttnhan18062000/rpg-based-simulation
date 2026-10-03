---
status: active
layer: simulation
authority: P2
audience: agent
ticket_id: TCK-20260805-SIMQ-HARDLAW-BRIDGE-COVERAGE-GAP
artifact_type: test_plan
tags: [simulation-quality, observability, world]
---

# test_plan.md — TCK-20260805-SIMQ-HARDLAW-BRIDGE-COVERAGE-GAP

## Regression Surface (existing tests that must pass)

- `tests/simulation_quality/test_quality_hub_event_translation.py` — dispatcher-level tests
- `tests/simulation_quality/test_quality_hub_integration.py`
- `tests/simulation_quality/test_world_dynamics_scorer.py` — WorldDynamicsScorer-level tests
- `tests/simulation_quality/test_grade_regression.py -m "not slow"` — corpus anchors must be
  unaffected (no real corpus scenario currently triggers any of these 6 laws, confirmed by 0
  score-delta across the full suite run)

## New Tests Required (per AC)

- `test_invariant_hp_nonnegative_routes_to_combat_hard_law`
- `test_invariant_readiness_nonnegative_routes_to_combat_hard_law`
- `test_invariant_gold_nonnegative_routes_to_conservation_violated`
- `test_invariant_stamina_position_occupancy_route_to_world_hard_law`
- `TestWorldHardLawViolation` class in `test_world_dynamics_scorer.py` (3 tests: EVENT_TYPES
  membership, scoring, weights file key)
- Corrected `test_invariant_spawn_occupancy_no_violation_no_translation` (renamed
  `test_invariant_unknown_law_id_no_translation`), which previously encoded the exact gap this
  ticket closes

## Scoped Pytest Commands

```
pytest tests/simulation_quality/ -m "not slow" -q
```

## Anti-Drift Test Guards

The corrected/renamed test (`test_invariant_unknown_law_id_no_translation`) now uses a genuinely
nonexistent law_id (`LAW-DOES-NOT-EXIST`) rather than a real one — guards against a future law_id
being silently added without a corresponding translation decision being made.
