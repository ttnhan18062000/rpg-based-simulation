---
status: historical
layer: simulation
authority: P2
audience: agent
ticket_id: TCK-20260928-MECHANISM-REACHABILITY-CALAMITY-TRAUMA-AGING
artifact_type: test_plan
tags: [simulation-quality, world, root-cause]
---

# Test Plan — TCK-20260928-MECHANISM-REACHABILITY-CALAMITY-TRAUMA-AGING

This ticket is an assessment/classification, not a fix. No new mechanic behavior is introduced, so
there are no fix-verification tests. The "New Tests Required" below are **regression-pinning
tests** — they lock in today's classified state (defect / condition / mislabel, per mechanism) so a
future change to any of these three mechanisms cannot silently drift the classification this
investigation just recorded without a visible test failure.

## Regression Surface

Existing tests that must keep passing (none of them are modified by this ticket):

**Unit — calamity/trauma:**
- `tests/unit/world/test_calamity_pressure_propagator.py` (`WORLD-105`)
- `tests/unit/world/test_regional_consequences.py` (`WORLD-029`)
- `tests/unit/world/test_calamity_magical_demonic_reproduction.py` (`WORLD-121`)
- `tests/unit/world/test_creature_territory_lifecycle.py` (`WORLD-118`)
- `tests/unit/world/test_world_dynamics.py`
- `tests/unit/domains/world_emergence/test_phase8_trauma_concern_bridge.py` (`WORLD-106`)
- `tests/unit/domains/world_emergence/test_phase8_regional_pressure_model.py` (`WORLD-123`)

**Unit — lifecycle/aging:**
- `tests/unit/engine/test_apply.py` (the dual-writer-race fix's own architecture guard)
- `tests/unit/entities/test_archetype_entity_factory.py`
- `tests/mechanic_scenarios/test_aging_death_value_differential.py`
- `tests/mechanic_scenarios/test_succession_heir_selection_value_differential.py`
- `tests/mechanic_scenarios/test_natural_aging_old_age_dispatch.py`

**Integration:**
- `tests/integration/economy/test_economic_vacancy_signal.py`
- `tests/integration/campaigns/test_lineage_dispatch_deterministic_kernel_tick.py`
- `tests/integration/scenarios/test_demographics.py` (`WORLD-123`)
- `tests/unit/observability/test_event_extractor_world_dynamics.py`

**Registry/tooling (mechanism-registry integrity, not domain behavior — run if any registry label is
touched during Finalize):**
- `tests/unit/tools/test_mechanism_registry.py`

**Arena-combat:** none of the three mechanisms is combat-resolution-adjacent; no arena-combat tests
are in scope.

## New Tests Required

Per this ticket's Acceptance Criteria, one regression-pinning test per confirmed exit claim:

1. **`test_calamity_producer_has_zero_real_callers`**
   - Category: architecture guard
   - Verifies: `CalamityService.apply_calamity_consequences` is not referenced by any real (non-
     docstring, non-comment) call site under `src/`. Pins J1's Level-1 DEFECT finding
     (zero callers) so a future accidental wiring change — or, conversely, an accidental removal of
     an existing real caller — is caught by a failing test rather than silently drifting the
     registry's own claim further out of date.
   - Where: `tests/architecture/test_calamity_intensity_producer_unwired.py` (new file, mirrors the
     shape of `tests/architecture/test_displacement_write_paths.py`).

2. **`test_moon_cave_region_records_zero_trauma_across_full_corpus_run`**
   - Category: integration (corpus_run instrument, matching the registry's own `verified.instrument`
     for `regional_trauma`)
   - Verifies: a real `Kernel.tick_once()` run against `generated_frontier_3_42` for the same run
     length already cited (5000 ticks) still shows `moon_cave.trauma_score == 0.0` at the end. Pins
     J2's CONDITION finding — a future world-composition change that adds a hostile faction near
     `moon_cave` should make this test fail loudly (a welcome failure, signalling the condition was
     resolved and the exit claim needs updating), not pass silently while nobody notices the
     underlying mechanism started working.
   - Where: `tests/integration/world/test_lair_region_trauma_reachability.py` (new file).

3. **`test_natural_aging_death_reachable_via_ordinary_progression`**
   - Category: unit / mechanic-scenario (already exists — no new test needed)
   - Verifies: this is already covered by
     `tests/mechanic_scenarios/test_natural_aging_old_age_dispatch.py::
     test_natural_aging_death_is_recorded_as_old_age_and_dispatches_succession`, landed by the
     already-merged `TCK-20260928-NATURAL-AGING-DEATH-DUAL-WRITER-RACE`. Listed here to make explicit
     that this investigation relies on it for J3's Level-1/Level-3 exit-claim evidence rather than
     re-deriving it; no duplicate test is added.

4. **`test_default_lifespan_exceeds_corpus_run_horizon`**
   - Category: unit (architecture/constant guard)
   - Verifies: `LifecycleComponent().max_age_ticks == 70 * TICKS_PER_FANTASY_YEAR ==
     20_160_000`, and that this exceeds a stated corpus-run-length reference constant (e.g. `5000`)
     by at least three orders of magnitude. Pins J3's Level-2 horizon arithmetic as a literal,
     checkable fact rather than prose alone — if the default lifespan or the fantasy-year constant is
     ever changed, this test forces the horizon claim in this investigation to be re-examined rather
     than silently going stale.
   - Where: `tests/unit/entities/test_lifecycle_horizon_constants.py` (new file) or as an added case
     in the existing `tests/unit/entities/test_archetype_entity_factory.py` if a narrower addition is
     preferred at implementation time.

5. **`test_old_age_death_excluded_from_combat_kill_event_but_emits_vacancy_signal`**
   - Category: integration (observability)
   - Verifies: an entity that dies with `death_reason == "OLD_AGE"` does not produce a
     `CombatKillEvent`, and — when the entity holds a `SHOPKEEPER`/`WORKER` role and was the region's
     last holder of that role — does produce a `WorldEvent(category=PRODUCTION_ROLE_VACATED)`. Pins
     J3's Level-4 observer-evidence finding (recorded, not required). Largely already covered by
     `tests/integration/economy/test_economic_vacancy_signal.py`'s new tick-shift test (added by the
     dual-writer-race ticket) plus `tests/unit/observability/test_event_extractor_world_dynamics.py`;
     add only if neither already asserts the `CombatKillEvent`-exclusion half explicitly.
   - Where: extend `tests/integration/economy/test_economic_vacancy_signal.py` or
     `tests/unit/observability/test_event_extractor_world_dynamics.py`, whichever does not already
     cover the exclusion assertion — confirm before adding a duplicate.

## Scoped Pytest Commands

```
pytest tests/unit/world/test_calamity_pressure_propagator.py tests/unit/world/test_regional_consequences.py tests/unit/world/test_calamity_magical_demonic_reproduction.py tests/unit/world/test_creature_territory_lifecycle.py tests/unit/world/test_world_dynamics.py tests/unit/domains/world_emergence/test_phase8_trauma_concern_bridge.py tests/unit/domains/world_emergence/test_phase8_regional_pressure_model.py -m "not slow"

pytest tests/unit/engine/test_apply.py tests/unit/entities/test_archetype_entity_factory.py tests/mechanic_scenarios/test_aging_death_value_differential.py tests/mechanic_scenarios/test_succession_heir_selection_value_differential.py tests/mechanic_scenarios/test_natural_aging_old_age_dispatch.py -m "not slow"

pytest tests/integration/economy/test_economic_vacancy_signal.py tests/integration/campaigns/test_lineage_dispatch_deterministic_kernel_tick.py tests/integration/scenarios/test_demographics.py tests/unit/observability/test_event_extractor_world_dynamics.py -m "not slow"

pytest tests/architecture/test_calamity_intensity_producer_unwired.py tests/integration/world/test_lair_region_trauma_reachability.py tests/unit/entities/test_lifecycle_horizon_constants.py -m "not slow"
```

(Fourth group covers the new regression-pinning tests once added; the first three groups are the
existing regression surface and can be run before any new test is written.)

Never: `pytest tests/`.

## Anti-Drift Test Guards

- `test_calamity_producer_has_zero_real_callers` fails loudly (in a good way) if someone wires
  `apply_calamity_consequences()` to a real caller without also updating the registry's `state`/
  `verified` block for `calamity_intensity` — catching exactly the kind of stale-registry drift this
  epic has repeatedly found (`motivation_doctrine`'s "confirmed live... eight days after its code was
  deleted" cautionary precedent cited in `docs/plans/mechanism_identity_and_change_taxonomy.md`).
- `test_moon_cave_region_records_zero_trauma_across_full_corpus_run` guards against silently
  "fixing" J2 via an unrelated world-composition edit (e.g. a future content-authoring pass that
  happens to place a hostile faction near `moon_cave`) without anyone noticing the classification
  needs to move from CONDITION to something else.
- `test_default_lifespan_exceeds_corpus_run_horizon` guards against a future lifespan-tuning or
  calendar-constant change silently invalidating this investigation's Level-2 arithmetic without a
  visible signal.
- The existing `tests/unit/engine/test_apply.py` architecture guard (already landed by the merged
  dual-writer-race fix) already protects J3's Level-1 finding — a regression to the pre-fix formula at
  `apply.py:109` would fail it; this investigation does not duplicate that guard, only relies on it.
- Do not add a new mechanism-registry structured field for runtime reach — `docs/plans/
  status_axis_model.md` §4 already decided against this (Axis C stays prose-only); any new test here
  must assert against existing `state`/`verified` fields and real code paths, not a new schema field.
