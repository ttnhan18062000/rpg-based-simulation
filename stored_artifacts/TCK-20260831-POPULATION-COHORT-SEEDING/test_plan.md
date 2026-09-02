---
status: historical
layer: world
authority: P2
audience: agent
ticket_id: TCK-20260831-POPULATION-COHORT-SEEDING
artifact_type: test_plan
tags: [world]
---

# Test Plan — TCK-20260831-POPULATION-COHORT-SEEDING

## Regression Surface

**unit — worldbuilding/compiler:**
- `tests/unit/worldbuilding/test_world_compiler.py` — full file (58+ tests as of investigation). In particular: `test_compiler_minimal_world`, `test_compiler_placement_bounds`, `test_compiler_entity_mappings`, `test_compile_sets_real_town_center_from_town_region`, `test_compiler_terrain_variants_deterministic_same_seed`, `test_compiler_no_terrain_variants_declared_produces_byte_identical_terrain_dict` (determinism-style precedent this ticket's own determinism test should mirror), `test_compiler_faction_bravery_bias_produces_real_population_skew` (existing precedent for population-derived assertions). None of these currently assert anything about `population_cohorts` — confirmed via grep of the file for `population`/`cohort`/`PopulationSpec` (only unrelated `target_population_id` matches found). Must all keep passing unmodified — this ticket adds a new constructor kwarg to `RegionState(...)` at `compiler.py:245-254`, which risks breaking any test asserting on `RegionState` field equality/repr if one exists (spot-check during implementation).

**unit — demographics:**
- `tests/unit/world/test_demographics.py` — full file (57 tests). All hand-construct `RegionState`/`AuthoritativeState` directly (confirmed: `RegionState` imported and instantiated at `tests/unit/world/test_demographics.py:26`, inside test bodies, never via `WorldCompiler.compile()`). This ticket does not change any of `cohort.py`'s logic, so these must keep passing byte-for-byte unmodified. Includes `TestPopulationCohortModel` (dataclass shape/defaults/frozen), `TestDemographicCycleServiceInterval`, `TestCohortBirth`, `TestCohortDeath`, `TestCohortZeroNet` (incl. `test_region_without_cohorts_skipped` — the existing hand-built-fixture analog of this ticket's new guard-passes test), `TestCohortMultiple`, `TestRegionStateBackwardCompatibility`, `TestWorldUpdateCohorts`, `TestComputeRegionalScarcity`, `TestFindAdjacentRegions`, `TestMigrationPressure`, `TestComputePopulationDensity`, `TestLifecycleSystemElderWiring`.

**integration — scenarios:**
- `tests/integration/scenarios/test_demographics.py` — covers `WORLD-DEMO-002` (`test_cohort_migrates_on_scarcity`) and `WORLD-DEMO-005` (`test_high_population_region_higher_resource_demand`), both P1 parity entries. Must keep passing; also the natural home for this ticket's own compiler-driven integration test (see below) since it already exercises multi-tick, non-hand-built-state scenarios in this subsystem.

**architecture-guard adjacent:**
- Any existing frozen/slots-dataclass or determinism architecture-guard tests that scan `src/core/state.py`/`src/worldbuilding/compiler.py` for constructor-arg completeness (spot-check for these during implementation; none identified by name in this investigation pass — flag as a gap if found missing).

## New Tests Required

- **Test name:** `test_compiler_seeds_population_cohorts_from_spec`
  **Category:** unit (compiler)
  **Verifies:** A `WorldSpec` with a region and one or more `PopulationSpec` entries whose `spawn_region` matches that region produces a `RegionState.population_cohorts` dict with `"young"`/`"adult"`/`"elder"` keys, each a `PopulationCohort` instance, whose `count` values sum exactly to the region's declared population (`sum(p.count for p in spec.entities if p.spawn_region == region.id)`). Must include a fixture with **2+ `PopulationSpec` entries sharing the same `spawn_region`** (per investigation's anti-drift note — proves real aggregation, not 1:1 pass-through).
  **Where:** `tests/unit/worldbuilding/test_world_compiler.py`

- **Test name:** `test_compiler_population_cohorts_sum_exact_at_small_totals`
  **Category:** unit (compiler) — edge case / rounding correctness
  **Verifies:** Declared populations that don't divide evenly by the chosen ratio (e.g. `count=1`, `count=2`, `count=7`) still produce bracket counts summing to exactly the declared total — no silent 1-2 unit loss from per-bracket truncation. This directly targets the rounding-remainder risk flagged in investigation.md.
  **Where:** `tests/unit/worldbuilding/test_world_compiler.py`

- **Test name:** `test_compiler_population_cohorts_deterministic_same_seed`
  **Category:** unit (compiler) — determinism (AC 3)
  **Verifies:** Calling `WorldCompiler.compile(spec, seed=N)` twice with the same `spec`/`seed` produces byte-identical `population_cohorts` dicts across both resulting `AuthoritativeState`s (compare via `RegionState.to_canonical_dict()` or direct dict equality on `population_cohorts`, following the existing pattern of `test_compiler_terrain_variants_deterministic_same_seed`).
  **Where:** `tests/unit/worldbuilding/test_world_compiler.py`

- **Test name:** `test_compiler_zero_population_spec_region_no_crash_and_cohorts_empty`
  **Category:** unit (compiler) — edge case (AC 4)
  **Verifies:** A `WorldSpec` region with **zero** `PopulationSpec` entries targeting it (either `spec.entities == []` entirely, or entries present but none with a matching `spawn_region`) compiles without raising, and the resulting `RegionState.population_cohorts` is falsy (`{}` or all-zero-count depending on implementation choice — assert whichever representation Implementation Notes records) such that `DemographicCycleService`'s guard at `cohort.py:349` genuinely no-ops on it (see integration test below for the guard-no-op proof itself; this test only proves compile-time non-crash + correct empty/zero representation).
  **Where:** `tests/unit/worldbuilding/test_world_compiler.py`

- **Test name:** `test_demographic_cycle_proceeds_past_guard_on_compiler_produced_state_at_tick_200`
  **Category:** integration (AC 2 — the ticket's own headline claim: "the guard has never fired against real data")
  **Verifies:** Build a real `WorldSpec` with a populated region, run it through `WorldCompiler.compile()` (not a hand-built `RegionState`/`AuthoritativeState` fixture), then call `DemographicCycleService.process_demographics(compiled_state, tick=200)` directly and assert: (a) the guard at `cohort.py:349` is passed (not hit) — provable via a non-empty returned `StateUpdate`, i.e. `result.world_updates` and/or `result.world_events_add` non-empty for at least one region with non-zero-count cohorts; (b) the returned `StateUpdate` is a real, non-trivial value distinct from the `StateUpdate()` empty-sentinel returned by the off-cycle/empty-cohort short-circuits. This is the AC's explicit "not hand-built" requirement — using a hand-constructed `RegionState` here would not satisfy AC 2 even if it passes.
  **Where:** `tests/integration/scenarios/test_demographics.py` (co-located with the other compile-adjacent demographic scenario tests, `WORLD-DEMO-002`/`WORLD-DEMO-005`)

- **Test name:** `test_compiler_zero_population_region_guard_noop_via_full_tick_pipeline` (optional strengthening of the above, if Plan wants belt-and-suspenders coverage)
  **Category:** integration — anti-drift
  **Verifies:** The zero-`PopulationSpec` region from the unit-level edge case above, run through the real `DemographicCycleService.process_demographics` at tick 200, produces no `WorldUpdate`/`WorldEvent` for that region (confirms the guard's no-op is real end-to-end, not just a compile-time data-shape assertion).
  **Where:** `tests/integration/scenarios/test_demographics.py`

## Scoped Pytest Commands

```
pytest tests/unit/worldbuilding/test_world_compiler.py -v
pytest tests/unit/world/test_demographics.py -v
pytest tests/integration/scenarios/test_demographics.py -v
```

Combined regression + new-test run for this ticket (scoped to the demographics/worldbuilding domain, never the full suite):
```
pytest tests/unit/worldbuilding/test_world_compiler.py tests/unit/world/test_demographics.py tests/integration/scenarios/test_demographics.py -v
```

If implementation touches `src/engine/apply_plan.py` or `src/engine/world_dynamics.py` incidentally (it should not — this ticket is scoped to `compile()` only), also scope in:
```
pytest tests/unit/world/test_demographics.py -k "Cycle or Migration" -v
```

## Anti-Drift Test Guards

- **Bracket-key guard:** assert `set(region.population_cohorts.keys()) <= {"young", "adult", "elder"}` in every new compiler test — catches any accidental drift toward keying by `PopulationSpec.id` or population-group name instead of age bracket (would silently break `compute_population_density`, `_check_migration`, and `DemographicCycleService` for any real population, not just this ticket's fixtures).
- **Type guard:** assert every value in `region.population_cohorts` is a `PopulationCohort` instance (not a bare `int` or dict) — catches the `AttributeError`-on-`.count`/`.birth_rate` failure mode described in investigation.md if a future refactor "simplifies" the seeded structure.
- **Non-interference guard:** run `test_compiler_entity_mappings` and `test_compiler_placement_bounds` (existing, unmodified) alongside the new cohort tests in the same file to confirm the new pre-aggregation pass over `spec.entities` does not perturb step 6's actual `EntityState` spawning (tile placement, entity count, entity IDs) — the two must derive from the same underlying `spec.entities` data without one path affecting the other's RNG draw sequence (step 6's `rng.get_int(...)` calls are keyed by `next_entity_id`/`sub_id`, not draw order, so a correctly-scoped pure-arithmetic pre-pass should be provably RNG-silent; a regression here would mean the new code accidentally consumed RNG state).
- **Rate-default guard:** assert seeded `PopulationCohort.birth_rate`/`mortality_rate` match whatever Implementation Notes states was intended (either literally `0.02`/`0.01` untouched, or the specific new values chosen) — prevents silent drift between what Implementation Notes claims and what the code actually seeds, which the "Cadence-coupled rate finding" in the ticket explicitly warns against leaving implicit.
- **Parity-ledger guard (manual, not a pytest test):** confirm the new `WORLD-DEMO-006` parity entry's `test_path` (once Plan/Implementer assign it) points at one of the new tests above and that test actually exists and passes before Finalize — do not let the parity entry cite a test path that doesn't exist (per investigation.md's cross-reference finding that some sibling entries were checked for exactly this).
