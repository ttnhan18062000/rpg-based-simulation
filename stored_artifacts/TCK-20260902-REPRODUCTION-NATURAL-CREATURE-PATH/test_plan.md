---
status: historical
layer: world
authority: P2
audience: agent
ticket_id: TCK-20260902-REPRODUCTION-NATURAL-CREATURE-PATH
artifact_type: test_plan
tags: [lifecycle, world]
---

# Test Plan — TCK-20260902-REPRODUCTION-NATURAL-CREATURE-PATH

## Regression Surface

**Unit:**
- `tests/unit/world/test_camp_lifecycle.py` — `test_camp_maturity_and_spawn`,
  `test_camp_clearing_reward`, `test_camp_raid_trigger`. Must keep passing byte-for-byte: this
  ticket's new logic is additive inside/alongside `CampService`, and the existing maturity-delta
  (`0.075` at trauma>50), garrison-spawn-cap, and raid-trigger (`-20.0` maturity, `last_raid_tick_set`)
  assertions must not shift.
- `tests/unit/world/test_creature_territory_lifecycle.py` — full suite (13 tests). Confirms this
  ticket does not collide with the structurally similar but separate `territory_maturity` mechanic
  or its `ApplyPath._fast_replace_identity` fix.
- `tests/unit/world/test_demographics.py` — in particular
  `TestMigrationPressure::test_migration_pressure_triggers_on_scarcity_threshold` and any
  `compute_regional_scarcity`/`migration_threshold` coverage. Confirms this ticket's reuse of the
  scarcity/migration-threshold law does not perturb the existing migration mechanic itself (this
  ticket only reads these functions, never writes `population_cohorts`).
- `tests/unit/progression/test_lifecycle.py` — full suite (24 tests as of the birth-record schema
  ticket). Confirms `.birth_record()`, `LifecycleComponent`/`LifecycleUpdate` merge/`is_noop()`, and
  the no-marriage-precondition guard remain correct; this ticket is a new consumer of that surface,
  not a modifier of it.
- `tests/unit/world/test_spawn_cadence.py` — confirms `EntityGenerator`/`SpawnService` cadence
  behavior is unaffected if `spawn_monster()` (or a new generator method) is touched.

**Integration:**
- `tests/integration/optimization/test_component_patch_apply_parity.py`,
  `tests/integration/optimization/test_apply_plan_parity.py` — confirm any new/reused `EntityUpdate`/
  `StateUpdate` round-trips correctly through `ApplyPath.apply_generation()`, and (if the "short
  clock" design ends up needing an `EntityUpdate` write, not just a fresh `entities_add` construction)
  that no silent-drop point was missed, per the `CreatureTerritoryService` precedent bug.
- `tests/integration/scenarios/test_demographics.py::test_cohort_migrates_on_scarcity` — confirms the
  migration law this ticket's suppression gate reuses stays intact end-to-end.

## New Tests Required

Per acceptance criteria, following the pattern of
`tests/unit/world/test_camp_lifecycle.py::test_camp_maturity_and_spawn` /
`::test_camp_raid_trigger`:

- **`test_camp_maturity_threshold_spawns_natural_creature_offspring`**
  Category: unit. Verifies: a camp at/above its maturity threshold produces a new same-kind entity
  in `entities_add`, using `CampService`'s existing maturity/spawn constants (deterministic state
  construction analogous to `test_camp_maturity_and_spawn`'s `tick=30`/`maturity=10.0` setup, adapted
  to whatever specific threshold Plan wires the reproduction trigger to). Location:
  `tests/unit/world/test_camp_lifecycle.py` (extends the existing file, following its established
  fixture style) or a new `tests/unit/world/test_natural_creature_reproduction.py` if Plan implements
  this as a distinct method/service rather than inline in `process_camps()`.

- **`test_natural_creature_offspring_has_no_tracked_parents`**
  Category: unit. Verifies: the spawned entity's `LifecycleComponent.parent_a_entity_id` and
  `parent_b_entity_id` are both `None`, `birth_tick` equals the spawn tick, and `birth_city_id`
  matches the camp's region/city — i.e. `V2EntityBuilder.birth_record()` was called with parent ids
  left at their `None` defaults. Same file as above.

- **`test_natural_creature_offspring_short_maturation_clock`**
  Category: unit. Verifies: the spawned entity starts at (or is driven to) `LifeStage.CHILD` and
  reaches `LifeStage.ADULT` after advancing tick state by the short interval Plan defines — NOT the
  global 3000-tick `LifeStageService` threshold. Must exercise the real transition path
  (`LifecycleSystem.resolve_lifecycle()` + `src/engine/apply.py`'s per-tick `age_ticks` increment),
  not just assert a static field value, since the mechanism depends on the *global* aging pipeline
  applying to this entity correctly (per investigation.md's Risk #1 — this design choice is not yet
  settled at investigation time; write this test against whatever concrete mechanism Plan selects).
  Same file as above.

- **`test_spawn_eligibility_suppressed_when_regional_scarcity_exceeds_migration_threshold`** and
  **`test_spawn_eligibility_allowed_when_regional_scarcity_below_migration_threshold`**
  Category: unit (paired allowed/suppressed cases, per the AC's explicit "a test proves both the
  allowed and suppressed cases"). Verifies: constructing a region with resource-node
  `remaining_charges`/`max_charges` ratios that push `compute_regional_scarcity()` above vs. below
  the region's `migration_threshold` (or the `0.7` default fallback, per whichever resolution Plan
  picks for investigation.md's Risk #2) toggles whether the camp spawns a natural-creature offspring
  that tick, with maturity/tick otherwise held constant across the two cases (isolate the scarcity
  variable). Same file as above.

- **`test_natural_creature_spawn_commits_through_authoritative_apply_path`**
  Category: integration / architecture guard. Verifies: the new entity and its birth-record fields
  survive a full `ApplyPath.apply_generation()` round-trip (not just a raw `StateUpdate` inspection),
  and that no direct/`object.__setattr__`-style mutation of live state occurs — mirrors
  `test_component_patch_apply_parity.py`'s existing round-trip pattern and the birth-record schema
  ticket's own `test_lifecycle_patch_apply_writes_birth_fields_through_authoritative_path`. Location:
  `tests/integration/optimization/test_component_patch_apply_parity.py` (extend existing file,
  matching the `CreatureTerritoryService` precedent's placement of its own round-trip test there).

- **`test_natural_creature_reproduction_does_not_write_population_cohorts`**
  Category: architecture guard / anti-drift. Verifies the `StateUpdate` returned by the new spawn
  logic never populates `world_updates[...].population_cohorts_set` — the population-pressure
  feedback-loop closure is explicitly out of scope for this ticket
  (`TCK-20260902-REPRODUCTION-POPULATION-PRESSURE-CLOSURE`). Same file as the primary new tests.

- **`test_natural_creature_reproduction_does_not_reference_genetics`**
  Category: architecture guard. Verifies (by construction/grep-style assertion, following the
  no-marriage-precondition guard's "behavioral form" precedent in the birth-record schema ticket)
  that no `GeneticsSystem`/`GeneticProfile` import or call appears in the new code path, since
  genetics wiring is explicitly scoped to the human/humanoid path only. Same file.

## Scoped Pytest Commands

```
pytest tests/unit/world/test_camp_lifecycle.py tests/unit/world/test_creature_territory_lifecycle.py tests/unit/world/test_demographics.py -v

pytest tests/unit/progression/test_lifecycle.py -v

pytest tests/integration/optimization/test_component_patch_apply_parity.py tests/integration/optimization/test_apply_plan_parity.py -v

pytest tests/integration/scenarios/test_demographics.py -v

pytest tests/unit/world/test_spawn_cadence.py -v
```

Never `pytest tests/` — scoped to `src/world/camp.py`, `src/domains/demographics/cohort.py`,
`src/core/updates.py`/`src/core/builder.py` consumers, and the lifecycle/apply-parity domains this
ticket touches or reads from.

## Anti-Drift Test Guards

- `test_camp_maturity_and_spawn`/`test_camp_raid_trigger` (existing, unmodified) — pin
  `CampService`'s pre-existing numeric constants (`0.075` maturity delta at trauma>50, `-20.0` raid
  cost) so a change accidentally made while adding the reproduction branch is caught immediately.
- `test_natural_creature_reproduction_does_not_write_population_cohorts` — catches scope creep into
  the population-pressure closure ticket's territory.
- `test_natural_creature_reproduction_does_not_reference_genetics` — catches scope creep into the
  genetics-inheritance ticket's territory.
- Full `test_creature_territory_lifecycle.py` suite as regression — catches accidental collision
  between this ticket's camp-maturity-anchored spawn and the structurally similar but distinct
  `territory_maturity` per-entity mechanic (different maturity field, different threshold, different
  service).
- `test_migration_pressure_triggers_on_scarcity_threshold` (existing, unmodified) — catches any
  accidental mutation of `compute_regional_scarcity()`/`migration_threshold` behavior itself, since
  this ticket must only *read* that law, never alter it.
- The paired allowed/suppressed scarcity tests directly guard against the AC's explicit dual-case
  requirement being satisfied by only one branch (a common shallow-coverage failure mode for gate
  logic).
