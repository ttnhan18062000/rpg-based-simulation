---
status: historical
layer: observability
authority: P2
audience: agent
ticket_id: TCK-20260914-BOSS-KINDS-OBSERVABILITY-CONSTANT-DRIFT
artifact_type: test_plan
tags: [observability, world]
---

# Test Plan — TCK-20260914-BOSS-KINDS-OBSERVABILITY-CONSTANT-DRIFT

## Regression Surface
Unit (must keep passing):
- `tests/unit/observability/test_event_shapers_world_dynamics.py`
- `tests/unit/observability/test_event_extractor_world_dynamics.py` (dragonkin cases at ~:172 and ~:330, `TestSpawnCadrenceFired`, the WORLD-109 test_path)
- `tests/unit/observability/test_event_extractor_world.py`, `test_event_extractor_narrative.py`, `test_event_shapers.py`, `test_event_shapers_narrative.py`
- `tests/unit/world/test_boss_gate_reachability.py`, `tests/unit/world/test_world_dynamics.py`
- `tests/simulation_quality/test_world_dynamics_scorer.py`, `tests/simulation_quality/test_scenario_coverage.py`, `tests/simulation_quality/test_grade_regression.py`

Integration: `tests/integration/observability/test_kernel_event_recording.py`

Architecture: `tests/architecture/test_phase19_observability_boundaries.py`, `tests/architecture/test_phase18_import_boundaries.py`

Arena-combat: none affected.

## New Tests Required
1. `test_boss_kind_set_is_one_shared_constant` — architecture guard/unit. Asserts the shaper's boss set `is` the new module's boss constant and the extractor uses the same object; membership == {world_boss, ancient_sentinel, dragonkin}. Fails on the pre-fix shapers. Location: `tests/unit/observability/test_entity_kind_constants.py`.
2. `test_spawn_exclusion_tuple_shared_and_membership` — same file; identity across both modules; membership {None, world_boss, ancient_sentinel, goblin_raider, dragonkin}.
3. `test_goblin_raider_in_exclusion_not_in_boss_set` — same file; concept separation, and dragonkin in both.
4. `test_shaper_emits_boss_spawned_and_milestone_for_dragonkin` — unit behaviour; dragonkin `entities_add` emits `boss_spawned` and `narrative_milestone` (`first_boss_spawned`), no `raid_party_spawned`. Location: `tests/unit/observability/test_event_shapers_world_dynamics.py`.
5. `test_shaper_spawn_cadence_excludes_dragonkin` — at tick 50, dragonkin-only `entities_add` yields no `spawn_cadence_fired`; dragonkin + villager yields `spawned_count == 1`. Same file.
6. Rollback path: existing extractor dragonkin tests must pass unchanged (no new test).

## Proof Plan
### AC1 identical membership
- level: unit
- proof kind: invariant + differential (shaper vs extractor constants)
- oracle source: `docs/parity_ledger/world_dynamics.yaml` WORLD-109 / WORLD-115 and the `src/world/boss.py` producer set; no Bible chapter defines the telemetry set (`docs/mechanics/05_world_evolution.md` Lair note only)
- expected effect: both modules reference sets with the stated membership
- selected commands: `pytest tests/unit/observability/test_entity_kind_constants.py -q`
### AC2 goblin_raider excluded from boss sets
- level: unit
- proof kind: negative invariant
- oracle source: WORLD-109; the raid_party branch in both modules
- expected effect: `goblin_raider` not in boss constant, in exclusion tuple
- negative cases: a merged-constant regression fails
- selected commands: same as AC1
### AC3 drift-proof test
- level: unit / architecture guard
- proof kind: regression (must fail pre-fix)
- oracle source: ticket Scope decision 2026-10-02; WORLD-109
- expected effect: identity (`is`) and membership assertions, no source parsing; red before the shaper edit, green after
- selected commands: same as AC1, plus tests 4-5 in `test_event_shapers_world_dynamics.py`
### AC4 fixtures/hashes/scorers named
- level: process / regression
- proof kind: regression report
- oracle source: `docs/testing/regression_policy.md` §13; WORLD-115
- expected effect: plan lists scorer `src/simulation_quality/scorers/world_dynamics.py` and the tests above; the run states that no recorded expectation moved (none found in this investigation)
- selected commands: scorer/regression command below
- non-functional risk: default-path emitted-output change for dragonkin (tests 4-5)

## Scoped Pytest Commands
```
pytest tests/unit/observability/test_entity_kind_constants.py tests/unit/observability/test_event_shapers_world_dynamics.py tests/unit/observability/test_event_extractor_world_dynamics.py tests/unit/observability/test_event_extractor_world.py tests/unit/observability/test_event_extractor_narrative.py tests/unit/observability/test_event_shapers.py -q
pytest tests/simulation_quality/test_world_dynamics_scorer.py tests/simulation_quality/test_scenario_coverage.py tests/simulation_quality/test_grade_regression.py -q
pytest tests/architecture/test_phase19_observability_boundaries.py tests/architecture/test_phase18_import_boundaries.py tests/integration/observability/test_kernel_event_recording.py -q
```

## Anti-Drift Test Guards
- Test 3 guards merging of the two concepts.
- Tests 1-2 identity assertions catch reintroduced inline literals in either module.
- Existing extractor dragonkin tests guard the rollback path's membership staying byte-identical.
- The architecture hot-path import test guards the new leaf module's dependencies.
