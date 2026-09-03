---
status: historical
layer: world
authority: P2
audience: agent
ticket_id: TCK-20260902-REPRODUCTION-POPULATION-PRESSURE-CLOSURE
artifact_type: test_plan
tags: [lifecycle, world]
---

# Test Plan — TCK-20260902-REPRODUCTION-POPULATION-PRESSURE-CLOSURE

## Regression Surface

**Unit — demographics/cohort core (unchanged aggregate logic must survive untouched):**
- `tests/unit/world/test_demographics.py` (all classes: `TestComputePopulationDensity`, `TestMigrationPressure`, `TestCohortDeath`, `TestDemographicCycleServiceInterval`, `TestFindAdjacentRegions`, `TestComputeRegionalScarcity`, `TestLifecycleSystemElderWiring`)

**Unit — the three reproduction paths (their existing "does not write population_cohorts" guards will legitimately need retargeting, not deletion — see New Tests Required):**
- `tests/unit/world/test_natural_creature_reproduction.py`
- `tests/unit/world/test_calamity_magical_demonic_reproduction.py`
- `tests/unit/world/test_reproduction_humanoid_cadence.py`

**Unit — pressure model (density → demand_multiplier must still respond correctly to pre-existing seeded cohorts, independent of the new nudge):**
- `tests/unit/domains/world_emergence/test_phase8_regional_pressure_model.py`

**Unit — sibling world-dynamics services sharing `WorldDynamicsSystem.resolve_dynamics()`'s merge sequence (this ticket's fix to the `world_updates`-drop bug at `world_dynamics.py:174-182` touches shared plumbing — must not regress any of these):**
- `tests/unit/world/test_camp_lifecycle.py`
- `tests/unit/world/test_calamity_raid.py`
- `tests/unit/world/test_calamity_pressure_propagator.py`
- `tests/unit/world/test_creature_territory_lifecycle.py`
- `tests/unit/world/test_world_dynamics.py`
- `tests/unit/world/test_spawn_cadence.py`
- `tests/unit/core/test_system_cadence.py`

**Integration:**
- `tests/integration/scenarios/test_demographics.py` (`test_high_population_region_higher_resource_demand` is the direct pattern AC#4 mirrors)
- `tests/integration/optimization/test_component_patch_apply_parity.py` (authoritative-apply-path round trips for all three reproduction paths already live here)
- `tests/integration/optimization/test_apply_plan_parity.py`
- `tests/integration/world/test_phase9_stability.py`
- `tests/integration/pipeline/test_strategic_cadence.py`

**Parity/registry tooling (touched if `WORLD-120`/`WORLD-121`/`WORLD-122` text is rewritten or a new entry is added via `tools/parity_ledger_writer.py`):**
- `tests/tools/test_parity_index_baseline.py`
- `tests/tools/test_parity_ledger_writer.py`
- `tests/tools/test_parity_ledger_schema.py`
- `tests/tools/test_parity_updater_static.py` (hardcoded `next_available_id` baseline for `world_dynamics.yaml` will drift again, same pattern as the humanoid ticket's own documented fix)

## New Tests Required

Per AC#1 (typed `WorldUpdate` through the authoritative apply path, +1 exactly):
1. **`test_natural_creature_birth_nudges_young_cohort_by_one`** — unit — `CampService.process_camps()` with flag ON, a region seeded with `population_cohorts={"young": PopulationCohort(count=N)}`, a camp at raid maturity on the spawn cadence → assert the returned `StateUpdate.world_updates[region_id].population_cohorts_set["young"].count == N + 1` and every other bracket/field on the cohort is unchanged (`birth_rate`/`mortality_rate`/`migration_threshold` untouched). Lives in `tests/unit/world/test_natural_creature_reproduction.py`.
2. **`test_humanoid_birth_nudges_young_cohort_by_one`** — unit — same shape for `HumanoidReproductionService.process_reproduction()`, two eligible parents producing a birth. Lives in `tests/unit/world/test_reproduction_humanoid_cadence.py`.
3. **`test_magical_demonic_birth_nudge_decision`** — unit — whichever way Risk #4 (open question) is resolved: either asserts the nudge fires identically to the other two paths, or asserts it deliberately does not (with the rationale captured in a code comment/doc, matching the resolved-decision pattern the magical/demonic ticket itself used for "no population-pressure gate"). Lives in `tests/unit/world/test_calamity_magical_demonic_reproduction.py`. **Must not be silently skipped** — whichever answer Plan picks, this test must assert it explicitly.

Per AC#2 (additive-only, not a resync — the ticket's own explicit anti-drift requirement):
4. **`test_two_simultaneous_births_same_region_same_call_both_nudge`** — unit, architecture-guard shaped — two eligible camps in the *same* region, same `CampService.process_camps()` call, flag ON → assert the final count is `N + 2`, not `N + 1` (proves the within-one-call accumulation from Risk #2 doesn't silently drop the second nudge). This is the highest-value new test in this ticket — it directly targets the whole-dict-replace/last-write-wins trap identified in investigation.md Risk #2.
5. **`test_birth_nudge_does_not_recompute_other_brackets`** — unit — seed `adult`/`elder` brackets alongside `young` with arbitrary counts, trigger one birth, assert `adult`/`elder` counts are byte-for-byte unchanged (proves the nudge copies-and-increments rather than rebuilding the dict from scratch).
6. **`test_birth_in_region_missing_young_cohort`** — unit — region with `population_cohorts={}` (or missing the `young` key specifically) receives a birth → assert whichever resolution of Risk #3 was chosen (either a fresh `young` bracket materializes with `count=1`, or the nudge is a documented no-op) — must not raise.

Per AC#3 (mirrors `test_repeated_deaths_increase_danger_pressure`):
7. **`test_repeated_births_increase_population_density_signal`** — unit — `tests/unit/domains/world_emergence/test_phase8_regional_pressure_model.py`, following the death-pressure test's shape: seed a region, apply N nudge-produced `WorldUpdate`s (or simulate N births via the apply path), then call `RegionalPressureModel.evaluate()` with harvest aggregates and assert `demand_multiplier`/`res_intensity` increases measurably relative to a zero-births baseline with identical harvest activity. Use a small-`count`/small-`area` region (not `count=2000`/`100x100` like the existing AC#4-pattern test) so a handful of +1 nudges produce an assertable delta without "recomputing to a nicer number."

Per AC#4 (new integration-style test mirroring `test_high_population_region_higher_resource_demand`):
8. **`test_population_pressure_region_responds_to_real_births`** — integration — `tests/integration/scenarios/test_demographics.py`. A region under pressure (`compute_regional_scarcity` above the cohort's `migration_threshold` is *not* required here — this is about the signal responding, not eligibility) receives one or more real births driven through the actual reproduction-path service call (not a hand-built `WorldUpdate`), applied via `ApplyPath.apply_generation()`/the authoritative apply path, and the region's post-apply `population_cohorts["young"].count` and the subsequent `RegionalPressureModel.evaluate()` output both move as expected. Should exercise at least the humanoid path end-to-end (it's the only one operating on real entity pairs rather than a per-camp/per-calamity anchor) plus whichever of the other two is decided in scope.

Per AC#5 (epic gating — cross-ticket, likely not code-testable):
9. No new automated test — this AC is a process/Finalize-time confirmation (this ticket lands no later than atomically with the last birth-path ticket), not a code assertion. Note in `plan.md`/`Completion Summary` rather than pytest.

Per AC#6 (docs/parity):
10. No pytest coverage beyond the existing `done-checker` static doc-coverage check (`tools/gate_checks/done_checker_static.py::check_docs_to_update_coverage`) against this investigation's "Docs Requiring Update" bullets, and `tests/tools/test_parity_ledger_schema.py`/`test_parity_ledger_writer.py` if a new/edited entry is written via `tools/parity_ledger_writer.py`.

Architecture guard (per project CLAUDE.md's "Architecture tests" rule — read-only logic did not mutate live state, authoritative application path was used):
11. **`test_reproduction_paths_never_mutate_region_directly`** — architecture guard — `inspect.getsource()` on each of the three `process_*`/`process_camps`/`process_world_dynamics`/`process_reproduction` methods, assert no direct attribute assignment onto a `RegionState`/`region.population_cohorts` object (i.e., the only mutation path is via a returned `WorldUpdate.population_cohorts_set`, never `region.population_cohorts[...] = ...` or `dataclasses.replace(region, ...)` called locally). Mirrors the existing `test_no_marriage_contract_referenced_in_humanoid_reproduction_path`-style source-inspection guard already established in this epic's own test files.
12. **`test_world_dynamics_folds_camp_and_calamity_world_updates_into_final_update`** — regression guard for investigation.md Risk #1 — `tests/unit/world/test_world_dynamics.py`. Drives `WorldDynamicsSystem.resolve_dynamics()` with the natural-creature (and/or magical/demonic) flag ON and conditions that produce a birth, asserts the *final* returned `StateUpdate.world_updates` contains the region's `population_cohorts_set` nudge — proving the `camp_state_update.world_updates`/`calamity_update.world_updates` fold-in fix actually reaches the top-level return value, not just the inner service's own return value (a unit test on `CampService.process_camps()` alone would pass even if the world_dynamics-level drop bug were never fixed).

## Scoped Pytest Commands

```
pytest tests/unit/world/test_demographics.py \
       tests/unit/world/test_natural_creature_reproduction.py \
       tests/unit/world/test_calamity_magical_demonic_reproduction.py \
       tests/unit/world/test_reproduction_humanoid_cadence.py \
       tests/unit/world/test_camp_lifecycle.py \
       tests/unit/world/test_calamity_raid.py \
       tests/unit/world/test_calamity_pressure_propagator.py \
       tests/unit/world/test_creature_territory_lifecycle.py \
       tests/unit/world/test_world_dynamics.py \
       tests/unit/world/test_spawn_cadence.py \
       tests/unit/core/test_system_cadence.py \
       tests/unit/domains/world_emergence/test_phase8_regional_pressure_model.py \
       tests/integration/scenarios/test_demographics.py \
       tests/integration/optimization/test_component_patch_apply_parity.py \
       tests/integration/optimization/test_apply_plan_parity.py \
       tests/integration/world/test_phase9_stability.py \
       tests/integration/pipeline/test_strategic_cadence.py
```

If parity ledger entries are edited/added:
```
pytest tests/tools/test_parity_index_baseline.py \
       tests/tools/test_parity_ledger_writer.py \
       tests/tools/test_parity_ledger_schema.py \
       tests/tools/test_parity_updater_static.py
```

Never `pytest tests/`.

## Anti-Drift Test Guards

- **The three existing `test_*_does_not_write_population_cohorts` guard tests must be retargeted, not silently deleted.** A diff that just removes them without replacing their intent (asserting the *exact* new behavior — additive +1, not "anything goes now") is a scope-creep smell: it would make it impossible to later catch this ticket's own nudge silently regressing into a resync. Rename/rewrite them to assert `+1` exactly (see New Tests #1/#2/#3), keeping the same file location and near-identical setup so the diff is easy to review.
- **`test_two_simultaneous_births_same_region_same_call_both_nudge` (New Test #4) is the primary anti-drift guard against the whole-dict-replace/merge-collision risk** identified in investigation.md — this is the test most likely to catch a naive implementation that silently drops births under concurrency, and should be treated as a hard gate before this ticket can be considered done, not an optional nice-to-have.
- **`test_natural_creature_reproduction_does_not_reference_genetics`, `test_magical_demonic_reproduction_does_not_reference_genetics`, and the humanoid path's no-marriage-contract source-inspection guard must all still pass unmodified** — this ticket touches the same files but must not accidentally pull in genetics or marriage-contract references while wiring the nudge.
- **`test_flag_off_by_default_does_not_spawn_*` / `test_flag_off_produces_no_birth_regression_guard` tests in all three files must still pass unmodified** — with every reproduction flag OFF (the shipped default), no `population_cohorts` write should occur either; add an explicit assertion (`update.world_updates == {}` or equivalent) to these existing flag-off tests if not already covered, so a future accidental un-gating of the nudge is caught by the same guard that already catches un-gated spawns.
- **`DemographicCycleService.process_demographics()`'s own tests in `test_demographics.py` must show byte-for-byte identical birth/death math** — any diff to `cohort.py` itself (as opposed to the three call sites) is out of scope and should fail review even if tests happen to still pass.
- **`test_world_dynamics_folds_camp_and_calamity_world_updates_into_final_update` (New Test #12) guards against Risk #1 regressing silently** — if a future refactor of `world_dynamics.py`'s merge sequence reintroduces the drop bug, this is the test that catches it; a passing `CampService`-level unit test alone would not.
