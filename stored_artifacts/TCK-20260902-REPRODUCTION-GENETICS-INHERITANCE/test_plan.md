---
status: historical
layer: systems
authority: P2
audience: agent
ticket_id: TCK-20260902-REPRODUCTION-GENETICS-INHERITANCE
artifact_type: test_plan
tags: [lifecycle]
---

# Test Plan — TCK-20260902-REPRODUCTION-GENETICS-INHERITANCE

## Regression Surface

**Unit:**
- `tests/unit/progression/test_genetics.py` — all 11 existing tests (`TestGeneticTalentMultipliers`,
  `TestSkillScaling`) must keep passing unchanged. `GeneticsSystem.apply_genetic_profile()`,
  `GeneticsSystem.generate_profile_from_seed()`, and `SkillScalingSystem.compute_skill_power()` must not
  change behavior for any existing call shape.
- `tests/unit/progression/test_lifecycle.py` — the 24 tests from `BIRTH-RECORD-SCHEMA`, including
  `test_builder_birth_record_path_two_parent_case`, `test_builder_birth_record_path_parentless_case`,
  `test_no_marriage_precondition_in_birth_record_schema_or_apply_path`. If this ticket extends
  `V2EntityBuilder.birth_record()`'s signature or `LifecycleComponent`/`LifecycleUpdate`, every pre-existing
  call to these must still work with default values (no positional-arg breakage, no new required kwargs).
- `tests/unit/world/test_natural_creature_reproduction.py` — 9 tests; must keep confirming
  `parent_a_entity_id`/`parent_b_entity_id` stay `None` and no genetics field gets populated for that path.

**Integration:**
- `tests/integration/optimization/test_component_patch_apply_parity.py` — includes the birth-record and
  natural-creature round-trip tests; must keep passing if `EntityUpdate`/`ComponentPatch` gains a new field
  for the genetic profile.
- `tests/integration/optimization/test_apply_plan_parity.py` — authoritative apply-path parity; must not
  regress if a new patch type/field is added.
- `tests/integration/optimization/test_phase_skip_parity.py` — general apply-pipeline regression guard, run
  alongside the above two per the birth-record-schema ticket's own precedent.

**Arena-combat:** none directly applicable — this ticket does not touch combat resolution or
`SkillScalingService.get_effective_stats()` (no production consumer of the stored profile exists yet, see
investigation.md Risk 4). No arena-combat regression surface identified.

## New Tests Required

Per acceptance criteria:

1. **`test_combine_genetic_profiles_stays_within_multiplier_range`**
   - Category: unit
   - Verifies: combining two arbitrary parent `GeneticProfile`s (including edge cases at the 0.8 and 1.3
     bounds) always produces a child profile whose six multipliers all stay within `[0.8, 1.3]`.
   - Location: `tests/unit/progression/test_genetics.py`

2. **`test_combine_genetic_profiles_is_deterministic`**
   - Category: unit
   - Verifies: same two parent profiles + same seed/tick input → identical combined child profile (mirrors
     the existing `test_deterministic_profile_from_seed` determinism law).
   - Location: `tests/unit/progression/test_genetics.py`

3. **`test_adventurer_parents_bias_toward_combat_attributes`** and
   **`test_civilian_parents_produce_flatter_neutral_spread`**
   - Category: unit
   - Verifies AC3 directly: sampling many combined-profile outputs (varied seeds/parent profiles) for a
     two-Adventurer-parent case vs a two-civilian-parent case shows a measurable **distributional**
     difference (e.g. mean of combat-relevant attribute multipliers is statistically/measurably higher for
     the Adventurer case, or variance/spread differs) — not merely that a value exists. Matches the ticket's
     explicit AC wording ("a test asserts the distributional difference, not just that a value exists").
   - Location: `tests/unit/progression/test_genetics.py`

4. **`test_genetics_system_has_real_non_test_non_shim_caller`**
   - Category: architecture guard
   - Verifies AC1: greps/inspects `src/` (excluding `src/systems/lifecycle_systems/genetics.py` itself and
     `src/systems/genetics.py`'s shim) for at least one real call site referencing
     `GeneticsSystem`/`GeneticProfile` — regression guard so this doesn't silently regress back to "zero
     callers" if the wiring is later refactored out.
   - Location: `tests/unit/progression/test_genetics.py` or a dedicated architecture-guard test module,
     following whatever convention `test_no_marriage_precondition_...` in `test_lifecycle.py` set.

5. **`test_birth_record_writes_genetic_profile_via_authoritative_apply_path`**
   - Category: integration
   - Verifies AC4: constructs two parent profiles, invokes the new combination + builder/patch wiring, and
     confirms the resulting `EntityUpdate`/`StateUpdate` round-trips through the authoritative apply path
     (`ApplyPath.apply_generation()` or equivalent) onto a real `EntityState`, landing the combined
     `GeneticProfile` in its new storage location — never via a direct mutation.
   - Location: `tests/integration/optimization/test_component_patch_apply_parity.py` (matches the pattern
     `test_natural_creature_spawn_commits_through_authoritative_apply_path` set for the sibling ticket) or
     `tests/unit/progression/test_lifecycle.py`, depending on which component Plan chooses as the storage
     home.

6. **`test_canonical_dict_round_trip_includes_genetic_profile`**
   - Category: unit
   - Verifies: whichever component gains the new field, its `to_canonical_dict()` includes and correctly
     round-trips the `GeneticProfile` data (mirrors
     `test_lifecycle_component_canonical_dict_round_trip_includes_birth_fields` from the birth-record-schema
     ticket).
   - Location: `tests/unit/progression/test_lifecycle.py` or `tests/unit/progression/test_genetics.py`,
     matching the chosen storage component's existing test file.

7. **`test_natural_creature_and_magical_demonic_paths_never_attach_genetic_profile`**
   - Category: architecture guard
   - Verifies: `EntityGenerator.spawn_natural_creature_offspring()` and
     `EntityGenerator.spawn_magical_demonic_entity()` never construct or attach a `GeneticProfile` — locks in
     the "human/humanoid-only" scope boundary against future accidental scope creep.
   - Location: `tests/unit/world/test_natural_creature_reproduction.py` (extend) or a new shared test.

## Scoped Pytest Commands

```
pytest tests/unit/progression/test_genetics.py tests/unit/progression/test_lifecycle.py \
  tests/unit/world/test_natural_creature_reproduction.py \
  tests/integration/optimization/test_component_patch_apply_parity.py \
  tests/integration/optimization/test_apply_plan_parity.py \
  tests/integration/optimization/test_phase_skip_parity.py -v
```

Never `pytest tests/`. This scope covers: genetics unit tests (direct regression surface), lifecycle unit
tests (builder/component/patch regression surface, since the new storage field most likely lives adjacent
to or on `LifecycleComponent`), natural-creature reproduction tests (anti-drift guard for the parentless
path), and the three authoritative-apply-path integration suites (round-trip correctness for any new
`EntityUpdate`/`ComponentPatch` field).

## Anti-Drift Test Guards

- Test 7 above directly guards against genetics leaking into the natural-creature or magical/demonic
  reproduction paths — both are confirmed genetics-free by their own shipped tickets.
- Re-running `test_no_marriage_precondition_in_birth_record_schema_or_apply_path`
  (`tests/unit/progression/test_lifecycle.py`) unchanged guards against this ticket accidentally
  reintroducing a marriage-contract dependency while touching the same builder/component surface.
- Re-running the existing `TestSkillScaling` class in `test_genetics.py` unchanged guards against any
  accidental modification to `SkillScalingSystem.compute_skill_power()` while editing the same file for the
  new inheritance function.
- Re-running `test_deterministic_profile_from_seed` / `test_different_seeds_different_profiles` /
  `test_profile_multipliers_in_range` unchanged guards against the new combination method accidentally
  altering `generate_profile_from_seed()`'s existing spawn-time behavior (both methods must coexist,
  independently correct).
- Test 4 (`test_genetics_system_has_real_non_test_non_shim_caller`) is itself an anti-drift guard: it
  converts this ticket's core AC1 claim ("real, live caller for the first time") into a permanent regression
  check so a future refactor can't silently remove the only call site and revert to the "orphaned system"
  state this ticket fixes.
