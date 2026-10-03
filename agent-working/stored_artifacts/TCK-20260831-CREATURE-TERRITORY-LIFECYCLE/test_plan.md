---
status: historical
layer: world
authority: P2
audience: agent
ticket_id: TCK-20260831-CREATURE-TERRITORY-LIFECYCLE
artifact_type: test_plan
tags: [world, ecology]
---

# Test Plan — TCK-20260831-CREATURE-TERRITORY-LIFECYCLE

## Regression Surface

**Unit — world/camp/lifecycle:**
- `tests/unit/world/test_camp_lifecycle.py` — `test_camp_maturity_and_spawn`,
  `test_camp_clearing_reward`, `test_camp_raid_trigger`. Must keep passing unchanged: the new
  creature-territory service must not alter `CampService.process_camps`'s own maturity_delta
  (0.05 base, 0.075 with trauma>50.0) or spawn/raid outputs.
- `tests/unit/world/test_world_lifecycle_regression.py`
- `tests/unit/world/test_regional_consequences.py` (hazard drain — must stay unaffected by any
  new per-entity field added to `IdentityComponent`/`EntityState`)
- `tests/unit/world/test_demographics.py` (age-bracket / cohort tests — must confirm no accidental
  coupling between the new per-species maturity and `get_age_bracket()`/`LifeStageService`)

**Unit — core/apply/updates (durable-state plumbing, if a new typed field is added):**
- `tests/unit/core/test_biological.py` (exercises the dead-but-still-tested `BiologicalSystem`
  class directly — must keep passing unchanged; confirms this ticket does not delete/alter that
  class, only bypasses it as already-inert)
- `tests/integration/optimization/test_component_patch_apply_parity.py` — the established
  end-to-end pattern for a new `IdentityUpdate` field reaching `AuthoritativeState` through
  `apply_generation` (silent-drop-trap regression coverage, per `TCK-20260824-LIFE-STAGE-
  TRANSITIONS` precedent)
- `tests/unit/strategic/test_life_stage_transitions.py` — must keep passing unchanged; confirms
  the new mechanic did not repurpose `LifeStageService`/`identity.life_stage`

**Unit — feature flags:**
- `tests/unit/ai/test_guild_need_scorer.py` (reference pattern for `state.feature_flags` direct-
  read gating — not itself expected to change, but the new flag's test should mirror its shape)

**Integration — world dynamics tick:**
- `tests/integration/domains/test_fused_loop.py` (SHADOW-mode / feature-flag skip-preserves-hash
  coverage — relevant if the new service is wired into `WorldDynamicsSystem.resolve_dynamics`)

## New Tests Required

Per acceptance criteria:

1. **Trauma-scaled maturity delta (AC #1)**
   - Test name: `test_creature_maturity_delta_scales_with_region_trauma`
   - Category: unit
   - Verifies: two otherwise-identical monster-kind entities anchored to camps in regions with
     `trauma_score <= 50.0` vs `trauma_score > 50.0` receive different per-tick maturity deltas,
     with the higher-trauma region's delta equal to the base delta × 1.5 (reusing
     `CampService.MATURITY_PER_TICK`'s shape, per-species base rate substituted). Deterministic:
     construct both states explicitly, call the new service directly, assert on the returned
     `StateUpdate`'s typed delta field — no RNG, no multi-tick simulation needed.
   - Location: `tests/unit/world/test_creature_territory_lifecycle.py` (new file, mirrors
     `test_camp_lifecycle.py`'s naming/shape)

2. **Life-stage transition / new-occupant spawn at maturity threshold (AC #2)**
   - Test name: `test_creature_reaches_maturity_threshold_spawns_or_transitions`
   - Category: unit
   - Verifies: construct a monster-kind entity/territory state just below the defined maturity/age
     threshold, advance one tick (or call the service directly with `maturity` already at/above
     threshold), and assert either a life-stage-transition typed update fires or a new territory-
     occupant entity appears in `entities_add` — whichever the implementation chooses. Must also
     assert the threshold is **not** crossed prematurely one tick before (boundary test, mirroring
     `TCK-20260824-LIFE-STAGE-TRANSITIONS`'s "monotonic forward-only" and boundary-exactness
     discipline).
   - Location: `tests/unit/world/test_creature_territory_lifecycle.py`

3. **HERO/VILLAGER-only biological gate is respected (AC #3)**
   - Test name: `test_monster_kind_entities_remain_outside_generic_biological_needs`
   - Category: unit / architecture guard
   - Verifies: after processing the new creature-territory system (flag ON) for N ticks, a
     monster-kind entity's `biological.hunger`/`biological.sleep_debt` are **not** driven by the new
     system's own logic (i.e. the new service never emits a `BiologicalUpdate` for a MONSTER-role
     entity) — distinguishing this from the pre-existing, unrelated `ApplyPath._compute_entity_
     changes` passive hunger/sleep accrual (Investigation finding #3), which this ticket does not
     touch and this test must not conflate with. If AC #3 is instead resolved as "superseded" during
     implementation, this test must be rewritten to assert the opposite and the
     `intentional_divergences.md` entry (conditional bullet in investigation.md) must be added in
     the same commit.
   - Location: `tests/unit/world/test_creature_territory_lifecycle.py`

4. **Per-species pacing constants exist as real content + metamorphic directional check (AC #4)**
   - Test name: `test_per_species_pacing_constants_are_inspectable`
   - Category: unit
   - Verifies: at least two distinct monster species/kinds have distinct, named, non-hardcoded-
     inline pacing constants (e.g. a small dict/table, not magic numbers scattered in the service
     body) — asserts the table exists and has >= 2 entries with different values.
   - Location: `tests/unit/world/test_creature_territory_lifecycle.py`
   - Test name: `test_region_trauma_increase_never_decreases_maturity_growth_rate`
   - Category: unit (directional/metamorphic-style assertion — plain pytest, not wired into the
     `src/simulation_quality`/lab metamorphic tooling; per investigation.md, that tooling wiring is
     explicitly deferred to "once proven working by the pilot ticket," i.e. not required here)
   - Verifies: for a fixed species and fixed base state, computing the maturity delta at
     `trauma_score = T1` and `trauma_score = T2` where `T2 > T1` never yields
     `delta(T2) < delta(T1)` — sampled across a small set of trauma values spanning the 50.0
     threshold (e.g. 0, 40, 50, 51, 80, 100).
   - Location: `tests/unit/world/test_creature_territory_lifecycle.py`

5. **FeatureMode flag gates the new system, default OFF (AC #5)**
   - Test name: `test_creature_territory_lifecycle_flag_default_off_no_behavior_change`
   - Category: unit
   - Verifies: `FeatureFlagManager().get_flag_mode("ENABLE_CREATURE_TERRITORY_LIFECYCLE") ==
     FeatureMode.OFF` (registry default), and that processing world dynamics with the flag absent/
     OFF on `state.feature_flags` produces byte-identical `StateUpdate` output (no camp_updates
     changes beyond existing `CampService` output, no new entities_add, no new entity_updates)
     compared to running with the new service entirely uncalled.
   - Location: `tests/unit/world/test_creature_territory_lifecycle.py`
   - Test name: `test_creature_territory_lifecycle_flag_on_activates_maturity_processing`
   - Category: unit
   - Verifies: same setup with `state.feature_flags={"ENABLE_CREATURE_TERRITORY_LIFECYCLE": "ON"}`
     produces non-noop output for a qualifying monster-kind entity.
   - Location: `tests/unit/world/test_creature_territory_lifecycle.py`

6. **Silent-drop-trap guard, if a new `IdentityComponent`/`IdentityUpdate` field is added**
   - Test name: `test_new_maturity_field_survives_apply_generation_round_trip`
   - Category: integration (architecture guard)
   - Verifies: an `EntityUpdate` carrying the new field's `_set`/`_delta` reaches the resulting
     `AuthoritativeState` after a full `apply_generation()` call — not just after calling the
     patch's `.apply()` in isolation. Mirrors
     `tests/integration/optimization/test_component_patch_apply_parity.py`'s existing
     `IdentityUpdate(role_set=...)` round-trip pattern exactly, substituting the new field. This
     directly guards against the two silent-drop traps `TCK-20260824-LIFE-STAGE-TRANSITIONS`
     documented (`IdentityUpdate.is_noop()`/`.merge()` omission, `IdentityPatch.apply()`'s
     `replace()` kwarg omission).
   - Location: `tests/integration/optimization/test_component_patch_apply_parity.py` (extend
     existing file) or a new test in `tests/unit/world/test_creature_territory_lifecycle.py` if the
     field lives outside `IdentityComponent`.

## Scoped Pytest Commands

```bash
# New + directly modified test file(s)
python3 -m pytest tests/unit/world/test_creature_territory_lifecycle.py -v

# Camp/world-dynamics regression surface (must stay green, unmodified)
python3 -m pytest tests/unit/world/test_camp_lifecycle.py tests/unit/world/test_world_lifecycle_regression.py tests/unit/world/test_regional_consequences.py tests/unit/world/test_demographics.py -v

# Biological/lifecycle regression surface
python3 -m pytest tests/unit/core/test_biological.py tests/unit/strategic/test_life_stage_transitions.py tests/unit/progression/test_lifecycle.py -v

# Durable-state apply-path parity (only if a new typed field is added)
python3 -m pytest tests/integration/optimization/test_component_patch_apply_parity.py -v

# Feature-flag registry sanity
python3 -m pytest tests/unit/ai/test_guild_need_scorer.py -v

# Full world domain sweep (scoped, not tests/), excludes slow markers per Testing Rule
python3 -m pytest tests/unit/world/ tests/integration/domains/test_fused_loop.py -m "not slow"
```

Never run the bare `pytest tests/`.

## Anti-Drift Test Guards

- **`test_camp_maturity_and_spawn`'s exact asserted values** (`maturity_delta == pytest.approx(0.075)`
  at `trauma_score=60.0`, spawn of `kind == "goblin_warrior"`) must remain byte-identical after this
  ticket lands — any diff here signals the new system accidentally touched `CampService` instead of
  staying a parallel, independent system (Out of Scope violation).
- **`tests/unit/core/test_biological.py`** must keep passing unchanged and keep exercising
  `BiologicalSystem.update()` exactly as today — this ticket must not delete or "clean up" that
  dead-but-tested class as a side effect; it stays inert-but-present.
- **A test must explicitly assert the new system never emits a `BiologicalUpdate`** for MONSTER-role
  entities (test #3 above) — this is the concrete guard against silently drifting into "Generic
  hunger/sleep biological simulation expansion beyond monster-kind entities" (explicit Out of
  Scope).
- **A test must explicitly assert `AuthoritativeState.maturity` (the unrelated global world-level
  field) is untouched** by the new per-entity/per-camp-adjacent mechanism — guards against the
  three-way "maturity" naming collision flagged in investigation.md (global world maturity vs.
  `CampState.maturity` vs. the new per-entity field).
- **A test must assert `CampService.MATURITY_PER_TICK`, `CampService.RAID_MATURITY_THRESHOLD`, and
  `CampService.CAMP_SPAWN_INTERVAL` are unchanged** (import and compare against known literals
  0.05/80.0/30) — guards against accidental modification of the reused-but-not-modified camp
  constants.
- **A test must assert `FeatureMode.OFF` remains the default** for
  `ENABLE_CREATURE_TERRITORY_LIFECYCLE` in a fresh `FeatureFlagManager()` (no overrides) — guards
  against DEV-002 default-OFF policy drift.
- **A test must assert `LifeStageService.get_stage_for_age()` and `LifecycleSystem.
  resolve_lifecycle()`'s existing life-stage-transition behavior for non-monster entities is
  unaffected** (run `test_life_stage_transitions.py` unmodified) — guards against the new
  per-species maturity concept accidentally being folded into the existing global-threshold
  `LifeStage` enum machinery, which investigation.md explicitly recommends against.
