---
status: historical
layer: strategy
authority: P2
audience: agent
ticket_id: TCK-20260902-COMING-OF-AGE-ARCHETYPE-CHOICE
artifact_type: test_plan
tags: [lifecycle, strategy]
---

# Test Plan — TCK-20260902-COMING-OF-AGE-ARCHETYPE-CHOICE

## Regression Surface

Unit:
- `tests/unit/progression/test_lifecycle.py` — all `LifecycleSystem.resolve_lifecycle()` coverage,
  in particular `test_life_stage_flips_at_age_boundary`, `test_life_stage_transition_is_monotonic_forward_only`
  (lines 339-372, the exact CHILD→ADULT/ADULT→ELDER fixture this ticket's new branch sits beside),
  and the birth-record fields tests (`test_lifecycle_component_canonical_dict_round_trip_includes_birth_fields`,
  `test_lifecycle_patch_apply_writes_birth_fields_through_authoritative_path`,
  `test_builder_birth_record_path_two_parent_case`, `test_builder_birth_record_path_parentless_case`)
  — must remain green since this ticket reads `parent_a_entity_id`/`parent_b_entity_id`/`birth_tick`
  without touching their write path.
- `tests/unit/strategic/test_life_stage_transitions.py` — pure `LifeStageService` boundary/monotonicity
  coverage, unrelated to this ticket's write logic but must stay green (no changes to `life_stage.py`
  are in scope).
- `tests/unit/strategic/test_occupation_change_scorer.py` — `OccupationChangeGoalScorer` coverage;
  this ticket must not modify that scorer, so all cases must remain unchanged and green.
- `tests/unit/world/test_demographics.py::TestLifecycleSystemElderWiring` — the ELDER-branch sibling
  precedent inside `resolve_lifecycle()`; must remain unaffected by the new ADULT-branch addition.

Integration:
- `tests/integration/strategic/test_occupation_change_reachability.py` — confirms
  `OccupationChangeGoalScorer` is reachable through `StrategicIntelligenceSystem.evaluate_strategic_intent()`;
  unaffected but must stay green (proves no accidental coupling was introduced).
- `tests/integration/optimization/test_component_patch_apply_parity.py`,
  `tests/integration/optimization/test_apply_plan_parity.py` — authoritative apply-path parity
  checks; must remain green since the new `IdentityUpdate(role_set=...)` write goes through the
  same `IdentityPatch`/apply-plan machinery already exercised by these tests.

Arena-combat: none — this ticket does not touch combat resolution, damage, or tactical modifiers;
no arena-combat regression surface applies.

## New Tests Required

1. **`test_coming_of_age_fires_exactly_once_on_child_to_adult_transition`**
   - Category: unit
   - Verifies: a CHILD entity at `age_ticks=3000` (the CHILD→ADULT boundary) produces exactly one
     `EntityUpdate` with both `identity.life_stage_set == LifeStage.ADULT` and
     `identity.role_set` set to one of `{SHOPKEEPER, WORKER, GUARD}` (or whatever the Plan phase's
     final candidate set is) from a single `LifecycleSystem.resolve_lifecycle()` call, mirroring
     `test_life_stage_transition_is_monotonic_forward_only`'s fixture shape.
   - Location: `tests/unit/progression/test_lifecycle.py` (extends the existing CHILD→ADULT fixture
     coverage in that file).

2. **`test_coming_of_age_does_not_fire_for_already_adult_or_elder_entities`**
   - Category: unit
   - Verifies: an entity already ADULT or ELDER at the start of the tick produces no `role_set` write
     from this mechanism (re-derivation on a later tick must not re-fire the roll) — regression guard
     for the "exactly once" AC given `resolve_lifecycle()` runs every tick.
   - Location: `tests/unit/progression/test_lifecycle.py`.

3. **`test_coming_of_age_role_set_uses_authoritative_identity_patch_path`**
   - Category: architecture guard
   - Verifies: the produced `role_set` value is only ever committed through
     `IdentityPatch.apply()`/the authoritative apply pipeline — i.e. run the full
     `AuthoritativeApplyPipeline`/`ApplyPath` (not just `resolve_lifecycle()` in isolation) against a
     CHILD-at-boundary fixture and assert the resulting frozen `EntityState.identity.role` reflects
     the new value, proving no direct-mutation shortcut was taken.
   - Location: `tests/unit/progression/test_lifecycle.py` or
     `tests/integration/optimization/test_apply_plan_parity.py` (whichever the implementer's chosen
     apply-path entry point matches — follow the existing pattern in
     `test_lifecycle_patch_apply_writes_birth_fields_through_authoritative_path`).

4. **`test_coming_of_age_metamorphic_regional_need_weight_increases_variance`** (REQUIRED — AC 2)
   - Category: unit (metamorphic), new test class (`TestComingOfAgeMetamorphicConvergenceGuard` or
     similar — none exists today for weighted/stochastic archetype selection, confirmed by grep).
   - Verifies: holding personality and parental-occupation weight terms fixed, increasing the
     regional-need weight coefficient strictly increases the variance/entropy of the resulting
     occupation distribution across a same-tick synthetic batch of same-region CHILD entities all at
     the CHILD→ADULT boundary. Must run the selection function (or `resolve_lifecycle()` over a
     multi-entity same-tick state) at ≥2 distinct regional-need weight values and assert
     `variance(weight_high) > variance(weight_low)` (or Shannon entropy, whichever the Plan phase's
     chosen selection function makes natural to compute) — never asserting a fixed/hardcoded
     distribution, since the point of the guard is that it must hold across the parameter sweep, not
     for one snapshot.
   - Location: `tests/unit/strategic/test_coming_of_age_archetype_choice.py` (new file, following the
     `test_occupation_change_scorer.py`/`test_life_stage_transitions.py` naming and fixture-helper
     conventions — e.g. a `_child_at_boundary(eid, pos, **identity_kwargs)` builder helper mirroring
     `test_occupation_change_scorer.py`'s `_citizen()`).

5. **`test_coming_of_age_same_tick_batch_does_not_collapse_to_identical_occupation`** (REQUIRED — AC 3)
   - Category: unit (regression guard, direct AC)
   - Verifies: a batch of N (N ≥ 5 recommended) CHILD entities in the same region under the same
     regional shortage, all at the CHILD→ADULT boundary in the same tick, do NOT all resolve to the
     identical `role_set` value when the regional-need weight is nonzero — assert
     `len(set(role_set values)) > 1` for at least one representative nonzero-weight configuration.
     This is distinct from test 4 (which sweeps the weight parameter); this test fixes weights at one
     realistic nonzero configuration and checks the direct non-collapse property.
   - Location: `tests/unit/strategic/test_coming_of_age_archetype_choice.py`.

6. **`test_coming_of_age_no_birth_record_exclusion_tracked_or_stubbed`**
   - Category: unit
   - Verifies: whichever resolution the Plan phase picks for AC 4 (compound
     `birth_tick == 0 and parent_a_entity_id is None and parent_b_entity_id is None` check, or an
     explicit documented stub) behaves as specified — e.g. if implemented, a synthetic
     construction-default CHILD entity (no `.birth_record()` call at all, i.e. `birth_tick=0`,
     `parent_a_entity_id=None`, `parent_b_entity_id=None`, the only state reachable via bare
     `.lifecycle()`) is excluded from the roll, while a Humanoid-path-style CHILD entity with real
     `parent_a_entity_id`/`parent_b_entity_id` and `birth_tick=0` is NOT excluded (the false-exclusion
     regression case this investigation identified as a live risk).
   - Location: `tests/unit/progression/test_lifecycle.py`.

7. **`test_coming_of_age_handles_missing_or_inactive_parent_entity`**
   - Category: unit (edge case / failure mode)
   - Verifies: when `parent_a_entity_id`/`parent_b_entity_id` point to an entity no longer present in
     `state.entities` (died and was removed) or present but `lifecycle.active == False`, the
     parental-occupation weight term degrades gracefully (e.g. treated as neutral/zero) rather than
     raising `KeyError`/`AttributeError`.
   - Location: `tests/unit/strategic/test_coming_of_age_archetype_choice.py`.

8. **`test_coming_of_age_parentless_child_uses_neutral_parental_term`**
   - Category: unit (edge case)
   - Verifies: a Natural-Creature-path-style parentless CHILD entity (`parent_a_entity_id=None`,
     `parent_b_entity_id=None`, `birth_tick` nonzero) still receives a valid weighted roll — the
     parental-occupation term must not crash or default to zero-probability-everywhere when there is
     no parent to read a role from.
   - Location: `tests/unit/strategic/test_coming_of_age_archetype_choice.py`.

9. **`test_coming_of_age_selection_uses_seeded_rng_not_unseeded_random`** (architecture guard)
   - Category: architecture guard
   - Verifies: two `resolve_lifecycle()` calls with identical input state and seed produce identical
     `role_set` outcomes (determinism), and — if the implementation uses a weighted-random draw
     rather than deterministic softmax+argmax — that it routes through `src/core/rng.py`'s seeded
     `Domain`-keyed RNG rather than Python's unseeded `random` module (grep-based or call-count-based
     assertion, following whatever existing architecture-guard pattern the codebase uses for RNG
     provenance, e.g. `TCK-20260902-REPRODUCTION-BIRTH-RECORD-SCHEMA`'s marriage-precondition guard
     pattern of grepping source for a forbidden reference).
   - Location: `tests/unit/progression/test_lifecycle.py` or a new architecture-guard test module,
     implementer's choice depending on final RNG mechanism.

10. **`test_coming_of_age_monster_role_child_role_untouched_on_transition`** (REQUIRED — architecture
    review regression, 2026-09-02)
    - Category: unit (regression guard, role gate)
    - Verifies: a MONSTER-role CHILD entity constructed the same way
      `spawn_natural_creature_offspring()` does (`src/systems/world_systems/generator.py:87-120`) —
      `identity.role == EntityRole.MONSTER`, `identity.faction == Faction.MONSTER_HORDE`,
      `identity.life_stage == LifeStage.CHILD`, `lifecycle.parent_a_entity_id is None`,
      `lifecycle.parent_b_entity_id is None`, `lifecycle.birth_tick` set to a real nonzero tick,
      `lifecycle.age_ticks` fast-forwarded to just below the CHILD/ADULT boundary — must NOT have its
      `role_set` touched by the Coming of Age mechanism when it crosses the CHILD→ADULT boundary in
      `resolve_lifecycle()`. Assert the resulting `EntityUpdate.identity.role_set is None` (or no
      role-bearing `IdentityUpdate` at all), and that `identity.role` remains `EntityRole.MONSTER`
      after apply. This is the direct regression test for the architecture-review finding that
      `is_excluded_no_birth_record()` alone does not exclude this entity (its `birth_tick` is nonzero),
      so only the new `entity.identity.role == EntityRole.CITIZEN` gate (plan.md Decision 5) prevents
      the incoherent write.
    - Location: `tests/unit/progression/test_lifecycle.py`, beside test 6's no-birth-record fixtures.

## Scoped Pytest Commands

```
pytest tests/unit/progression/test_lifecycle.py tests/unit/strategic/test_life_stage_transitions.py tests/unit/strategic/test_occupation_change_scorer.py tests/unit/strategic/test_coming_of_age_archetype_choice.py -v

pytest tests/integration/strategic/test_occupation_change_reachability.py tests/integration/optimization/test_component_patch_apply_parity.py tests/integration/optimization/test_apply_plan_parity.py -q

pytest tests/unit/world/test_demographics.py -k "LifecycleSystemElderWiring" -q
```

Never `pytest tests/` — all commands above are scoped to the lifecycle/strategic-cognition/apply-parity
domains this ticket touches.

## Anti-Drift Test Guards

- **`OccupationChangeGoalScorer` untouched guard**: re-run `tests/unit/strategic/test_occupation_change_scorer.py`
  unmodified and confirm 100% of its existing assertions (fixed-priority-first-fit behavior,
  `_CANDIDATE_ROLES` order, `metadata["raw_score"]` usage) still hold byte-for-byte — any diff in
  that scorer's own selection behavior is out-of-scope drift, not a legitimate side effect of this
  ticket.
- **No new `GoalKind`/`GoalScorer` registration guard**: assert `GoalRegistry` (`src/ai/goals/base.py`)
  contains no new entry introduced by this ticket — Coming of Age must remain a direct
  `LifecycleSystem` write, not a goal-hierarchy candidate. A simple `len(GoalRegistry.all())`
  before/after comparison (or explicit absence check) in a lifecycle test catches accidental
  goal-hierarchy scope creep.
- **Determinism replay guard**: two identical `resolve_lifecycle()` runs (same seed, same input
  state) over a multi-entity CHILD-at-boundary batch must produce byte-identical `role_set` outputs
  — catches any accidental introduction of unseeded randomness or dict-iteration-order dependence
  (the batch must be built from a `dict` keyed by entity id, and the test should assert output
  stability across at least two distinct Python dict insertion orders for the same entities, given
  `state.entities.items()` iteration order matters for tie-breaking in the selection formula).
- **No-collapse guard is itself an anti-drift guard**: test 5 above (AC 3) directly catches a
  regression to `OccupationChangeGoalScorer`-style fixed-priority-first-fit reasoning being
  copy-pasted into the new selection function — if a future edit collapses the weighting back to a
  deterministic first-fit, this test fails immediately rather than silently degrading balance.
- **Birth-record schema write-path isolation guard**: confirm no test or implementation code path in
  this ticket adds a `LifecycleUpdate.birth_tick_set`/`parent_a_entity_id_set`/etc. write — this
  ticket only *reads* those fields (Out of Scope: "must not modify that scorer's own selection
  behavior" extends analogously to "must not modify the birth-record write path" per the Reproduction
  epic's own ticket boundaries). A grep-based architecture guard (no `birth_tick_set=` outside
  `src/engine/patches.py`/`src/core/builder.py`/`generator.py`, the pre-existing sanctioned sites)
  is sufficient and cheap.
