---
status: historical
layer: world
authority: P2
audience: agent
ticket_id: TCK-20260902-REPRODUCTION-MAGICAL-DEMONIC-PATH
artifact_type: test_plan
tags: [lifecycle, world]
---

# Test Plan — TCK-20260902-REPRODUCTION-MAGICAL-DEMONIC-PATH

## Regression Surface

**Unit:**
- `tests/unit/world/test_calamity_raid.py` — `test_calamity_raid_maturity_advancement`, `test_calamity_raid_spawning`, `test_calamity_intensity_shift` — must pass byte-for-byte unchanged; these exercise the exact `process_world_dynamics`/`apply_calamity_consequences` code the new branch sits beside.
- `tests/unit/world/test_calamity_pressure_propagator.py` — `CalamityPressurePropagator.propagate_seasonal`, unrelated but same file.
- `tests/unit/world/test_camp_lifecycle.py` — sibling flag-off regression precedent (natural-creature path); confirms the pattern of "new flag-gated branch does not perturb existing behavior when OFF" holds project-wide.
- `tests/unit/world/test_natural_creature_reproduction.py` — sibling ticket's own suite; must remain unaffected since this ticket touches a different file/function.
- `tests/unit/progression/test_lifecycle.py` — birth-record schema regression (`LifecycleComponent`/`LifecycleUpdate`/`LifecyclePatch`/`V2EntityBuilder.birth_record()`), reused verbatim by this ticket.
- `tests/unit/world/test_world_dynamics.py` — exercises `WorldDynamicsSystem.resolve_dynamics()`, the call site this ticket's new branch (wherever Plan wires it) will run through.

**Integration:**
- `tests/integration/optimization/test_component_patch_apply_parity.py` — round-trip apply-path parity; this ticket's spawn must pass through the same authoritative apply mechanism verified here.
- `tests/integration/optimization/test_apply_plan_parity.py` — apply-plan builder parity.
- `tests/integration/world/test_phase9_stability.py` — exercises `EntityGenerator.spawn_monster` indirectly through world dynamics; confirms the existing boss-spawn path (which this ticket sits beside, and must not regress) stays stable.
- `tests/integration/scenarios/test_demographics.py` — only relevant if Plan resolves the population-pressure-gate question in favor of reading `compute_regional_scarcity()`/`migration_threshold`.

## New Tests Required

Per acceptance criteria (exact test names are Plan/Implement's call; these are the required coverage points):

1. **Calamity trigger spawns the magical/demonic entity**
   - Category: unit
   - Verifies: AC1 — a calamity/pressure event at or above `CalamityService`'s existing trigger threshold (reusing `CALAMITY_MIN_INTERVAL`/`CALAMITY_FORCE_INTERVAL`/the `calamity_intensity > 0.3` region filter, per Plan's trigger decision) produces a new entity, following `test_calamity_raid_maturity_advancement`'s state-construction style (`AuthoritativeState(tick=..., seed=42, ...)`, `CalamityService.process_world_dynamics(state, generator)`).
   - Location: new file `tests/unit/world/test_calamity_magical_demonic_reproduction.py`.

2. **No CHILD→ADULT transition or maturation clock applied**
   - Category: unit
   - Verifies: AC2 — the spawned entity's `life_stage == LifeStage.ADULT` and `age_ticks` is *not* pre-seeded near the CHILD→ADULT boundary (i.e., does not mirror the natural-creature path's `age_ticks=2970` trick). Explicitly assert the entity is NOT built with `life_stage=LifeStage.CHILD`.
   - Location: same new file.

3. **Parentless birth-record fields populated correctly**
   - Category: unit
   - Verifies: AC3 — `parent_a_entity_id is None`, `parent_b_entity_id is None`, `birth_tick` equals the spawn tick, and `birth_city_id`/region: either `birth_city_id is None` with the entity's `position` falling inside the calamity's origin region's `bounds` (matching the natural-creature path's own resolution of this same ambiguity), or a Plan-decided alternative — whichever Plan settles on must have a dedicated assertion.
   - Location: same new file.

4. **Spawn commits through the authoritative apply path**
   - Category: integration
   - Verifies: AC4 — the `StateUpdate`/`EntityUpdate` round-trips through `ApplyPath.apply_generation()` with all birth-record fields surviving, mirroring `test_lifecycle_patch_apply_writes_birth_fields_through_authoritative_path` (birth-record-schema ticket) and `test_natural_creature_spawn_commits_through_authoritative_apply_path` (natural-creature ticket).
   - Location: `tests/integration/optimization/test_component_patch_apply_parity.py` (append, following the existing round-trip pattern in that file).

5. **Flag defaults OFF / flag-off regression guard**
   - Category: unit
   - Verifies: the new `ENABLE_REPRODUCTION_MAGICAL_DEMONIC_PATH` flag defaults to `FeatureMode.OFF`, and with the flag OFF the new branch produces no behavior change to `process_world_dynamics`'s existing output (mirrors natural-creature's flag-off guard).
   - Location: same new file, plus a flag-sanity check (`FeatureFlagManager().get_flag_mode('ENABLE_REPRODUCTION_MAGICAL_DEMONIC_PATH') == FeatureMode.OFF`).

6. **No genetics dependency (architecture guard)**
   - Category: architecture guard (behavioral-form, matching the birth-record-schema and natural-creature tickets' precedent)
   - Verifies: no `GeneticsSystem`/`GeneticProfile` import or reference anywhere in the new spawn code path — this ticket's Out of Scope.
   - Location: same new file.

7. **Existing boss-spawn/maturity behavior unregressed**
   - Category: unit
   - Verifies: `test_calamity_raid_maturity_advancement` and `test_calamity_raid_spawning`'s existing assertions (`update.maturity_set == 1`; world-boss spawn count/kind/target) still hold identically once the new branch is added — either reuse those exact existing tests as regression gates, or add an explicit "new branch does not alter existing boss-spawn output" assertion if Plan decides the two branches share trigger evaluation.
   - Location: `tests/unit/world/test_calamity_raid.py` (existing, unmodified) plus a new explicit assertion in the new file if Plan's trigger-sharing decision warrants it.

8. **Population-pressure gate (conditional on Plan's resolution)**
   - Category: unit
   - Verifies: if Plan resolves the open population-pressure-gate question in favor of applying it — both the suppressed and allowed cases, mirroring `test_spawn_eligibility_suppressed_when_regional_scarcity_exceeds_migration_threshold`/`test_spawn_eligibility_allowed_when_regional_scarcity_below_migration_threshold` from the natural-creature ticket. If Plan resolves it as inapplicable (calamity-intensity-driven only, no population gate), this test is not required — but the decision itself, and its rationale, must be recorded in plan.md, not silently omitted.
   - Location: same new file, if applicable.

## Scoped Pytest Commands

```
pytest tests/unit/world/test_calamity_raid.py tests/unit/world/test_calamity_pressure_propagator.py \
  tests/unit/world/test_camp_lifecycle.py tests/unit/world/test_natural_creature_reproduction.py \
  tests/unit/progression/test_lifecycle.py tests/unit/world/test_world_dynamics.py \
  tests/unit/world/test_calamity_magical_demonic_reproduction.py \
  tests/integration/optimization/test_component_patch_apply_parity.py \
  tests/integration/optimization/test_apply_plan_parity.py \
  tests/integration/world/test_phase9_stability.py -v
```

If Plan adopts the population-pressure gate, add:
```
tests/integration/scenarios/test_demographics.py
```

Never: `pytest tests/` (unscoped).

## Anti-Drift Test Guards

- **Boss-spawn non-regression**: `test_calamity_raid_maturity_advancement`/`test_calamity_raid_spawning` must pass with their exact pre-existing assertions unchanged — guards against the new branch accidentally altering `should_spawn`, `high_intensity_regions` selection, or the existing `world_boss` entity's shape.
- **No-childhood guard**: an explicit test asserting the spawned entity is built WITHOUT `life_stage=LifeStage.CHILD` and WITHOUT a reduced `age_ticks` — this directly guards against copy-pasting the sibling natural-creature path's maturation-clock code, which would silently violate this ticket's core "no childhood" design decision.
- **Flag-off guard**: with `ENABLE_REPRODUCTION_MAGICAL_DEMONIC_PATH` OFF (the default), `process_world_dynamics`'s output must be byte-identical to today's — guards against the new branch being wired unconditionally.
- **No-genetics guard**: guards against silent scope creep pulling in `GeneticsSystem`/`GeneticProfile`, matching the two prior sibling tickets' established precedent.
- **No-population-cohorts-write guard**: even if Plan adopts the population-pressure gate as a read, assert `StateUpdate.world_updates` contains no `population_cohorts_set` entry from this new branch — guards against accidentally closing the population-pressure feedback loop, which is explicitly `TCK-20260902-REPRODUCTION-POPULATION-PRESSURE-CLOSURE`'s separate scope, not this ticket's.
- **Flag-name uniqueness guard**: confirm `ENABLE_REPRODUCTION_MAGICAL_DEMONIC_PATH` is registered as its own distinct flag (not aliased to or reusing `ENABLE_REPRODUCTION_NATURAL_CREATURE_PATH`) — guards against a shared-flag regression that would let a rollback of one path inadvertently disable the other.
