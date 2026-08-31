---
status: historical
layer: strategy
authority: P2
audience: agent
ticket_id: TCK-20260824-LIFE-STAGE-TRANSITIONS
artifact_type: test_plan
tags: [cognition]
---

# Test Plan — TCK-20260824-LIFE-STAGE-TRANSITIONS

## Regression Surface

Unit:
- `tests/unit/strategic/test_personality_goal_modifiers.py::test_life_stage_multipliers` — asserts
  `ScoreModifierSystem`/`LifeStageService.get_goal_multipliers()` still produces
  `score_elder == pytest.approx(80.0 * 1.5)` for a builder-constructed `LifeStage.ELDER` entity vs.
  a `LifeStage.CHILD` one. Must keep passing unchanged — this ticket must not alter multiplier
  values, only how `life_stage` gets set.
- `tests/unit/progression/test_lifecycle.py::test_aging_per_tick` and `::test_death_by_old_age` —
  regression surface for `LifecycleSystem`/age-ticks advancement, the most likely call site for the
  new trigger. Must keep passing unchanged.
- `tests/unit/progression/test_lifecycle.py::test_combat_death_classification`,
  `::test_permadeath_death_classification`, `::test_succession_and_heirloom_transfer`, and the
  `test_default_heir_*` family — regression surface for `LifecycleSystem.resolve_lifecycle()` as a
  whole, since that is the recommended (not mandated) trigger call site; any change there must not
  perturb death/succession logic.
- `tests/unit/core/test_domain_6_hardening.py` and `tests/unit/core/test_rpg_depth.py` — existing
  `IdentityUpdate(...)` construction/merge coverage (traits_add/remove, learned_skills,
  breakthroughs_add) that exercises `IdentityUpdate.is_noop()`/`.merge()`/`IdentityPatch.apply()`
  around the same dataclass being extended with `life_stage_set`. Must keep passing unchanged —
  confirms the new field's `is_noop()`/`merge()` branches don't disturb existing field handling.
- `tests/unit/world/test_demographics.py` (all `compute_elder_attribute_update`/`get_age_bracket`
  tests, e.g. `test_age_bracket_returns_correct_bracket`,
  `test_elder_modifier_reduces_combat_effectiveness`, `test_non_elder_returns_none`) — must keep
  passing unchanged; confirms Decision 2 (not wiring `compute_elder_attribute_update`) leaves the
  cohort-level system untouched.

Integration:
- `tests/integration/optimization/test_component_patch_apply_parity.py` — the existing
  `IdentityUpdate(role_set=...)` → full `apply_generation()` → `new_state.entities[...].identity.role`
  pipeline test. Must keep passing unchanged; this is also the direct template for the new
  `life_stage_set` pipeline test below.
- `tests/integration/pipeline/test_recovery_gaps.py`,
  `tests/integration/pipeline/test_transaction_completion.py`,
  `tests/integration/kernel/test_snapshot_integrity.py` — broader `IdentityUpdate`/apply-pipeline
  regression surface; must keep passing unchanged.

Arena-combat: none — this ticket does not touch combat resolution, damage formulas, or tactical
modifiers. No arena-combat regression surface applies.

## New Tests Required

1. **`test_identity_update_life_stage_set_not_noop`**
   - Category: unit
   - Verifies: `IdentityUpdate(life_stage_set=LifeStage.ELDER).is_noop()` returns `False` (guards
     against the exact silent-discard trap in Investigation's Current Behavior #6 — an update with
     *only* `life_stage_set` populated must not be filtered out by `extract_patches()`).
   - Location: `tests/unit/core/test_rpg_depth.py` or a new `tests/unit/core/test_identity_update.py`
     colocated with the existing `IdentityUpdate` merge/is_noop coverage.

2. **`test_identity_update_life_stage_set_merge_last_write_wins`**
   - Category: unit
   - Verifies: `IdentityUpdate(life_stage_set=LifeStage.CHILD).merge(IdentityUpdate(life_stage_set=
     LifeStage.ELDER)).life_stage_set == LifeStage.ELDER` (last-write-wins, matching the
     `role_set`/`faction_set` precedent), and that merging a `life_stage_set=None` update preserves
     the base's existing `life_stage_set`.
   - Location: same file as test 1.

3. **`test_identity_patch_apply_sets_life_stage`**
   - Category: unit
   - Verifies: `IdentityPatch(entity_id, identity=IdentityUpdate(life_stage_set=LifeStage.ELDER)).
     apply(entity, changes)` produces `changes["identity"].life_stage == LifeStage.ELDER`, directly
     exercising the `replace()` branch identified in Investigation as the real silent-drop risk
     (not `_fast_replace_identity`, which is unreachable for this field).
   - Location: `tests/unit/domains/optimization/test_component_patches.py` (or wherever
     `IdentityPatch` gets direct unit coverage today) — colocate with other `IdentityPatch` tests if
     any exist, otherwise add alongside `extract_patches` coverage.

4. **`test_life_stage_set_survives_full_apply_pipeline`** (mandatory — the ticket's own AC
   template)
   - Category: integration
   - Verifies: an `EntityUpdate(entity_id=N, identity=IdentityUpdate(life_stage_set=LifeStage.
     ELDER))` run through `ApplyPath.apply_generation()` (full pipeline, not just `IdentityPatch.
     apply()` in isolation) results in `new_state.entities[N].identity.life_stage ==
     LifeStage.ELDER` — directly mirrors the existing `role_set`→`"PALADIN"` pattern in
     `test_component_patch_apply_parity.py`.
   - Location: `tests/integration/optimization/test_component_patch_apply_parity.py`.

5. **`test_life_stage_flips_at_age_boundary`** (mandatory — explicit ticket AC: "a test asserts
   identity.life_stage flips at the defined boundary")
   - Category: unit (or integration if the chosen call site is `LifecycleSystem.resolve_lifecycle`
     / a full-pipeline tick, per Plan's decision on trigger location)
   - Verifies: an entity with `LifecycleComponent(age_ticks=6999)` and `IdentityComponent(
     life_stage=LifeStage.ADULT)` does NOT transition; the same entity with `age_ticks=7000` DOES
     transition to `LifeStage.ELDER` (boundary is inclusive at 7000, matching `get_age_bracket()`'s
     numeric law per Decision 1). Assert via whichever mechanism the trigger uses (a direct pure
     function call, or a produced `EntityUpdate`/`IdentityUpdate`, or a post-tick
     `AuthoritativeState` read — Plan determines the exact shape).
   - Location: co-locate with wherever the trigger function/call site lands (recommended:
     `tests/unit/progression/test_lifecycle.py` if wired into `LifecycleSystem.resolve_lifecycle`,
     or a new `tests/unit/strategic/test_life_stage_transitions.py` if implemented as a standalone
     `LifeStageService` function).

6. **`test_life_stage_transition_is_monotonic_forward_only`**
   - Category: unit
   - Verifies: an entity explicitly constructed with `life_stage=LifeStage.ADULT` and
     `age_ticks=0` does **not** get demoted to `LifeStage.CHILD` by the trigger (directly guards
     against the world-wide-regression risk in Investigation's Risks section — every
     world-generated entity starts at `age_ticks=0` with `life_stage=ADULT`). Also verify an entity
     explicitly constructed as `life_stage=LifeStage.CHILD` at `age_ticks=0` correctly promotes to
     `ADULT` at `age_ticks=3000` and to `ELDER` at `age_ticks=7000` (multi-step monotonic
     progression).
   - Location: same file as test 5.

7. **`test_get_stage_for_age_matches_get_age_bracket_numeric_boundaries`**
   - Category: unit (architecture-guard-flavored — cross-checks Decision 1's numeric-alignment
     claim so it can't silently drift)
   - Verifies: for a representative sweep of `age_ticks` values (e.g. `0, 2999, 3000, 6999, 7000,
     9000`), the new per-entity `LifeStage`-returning function's transition points occur at exactly
     the same `age_ticks` values as `get_age_bracket()`'s transition points (comparing *where the
     boundary falls*, not the string/enum values themselves, since the vocabularies are
     intentionally different per Decision 1). This is the regression guard for "a future maintainer
     changes one set of thresholds without noticing the other" flagged in Investigation's
     Anti-Drift Hazards.
   - Location: `tests/unit/strategic/test_life_stage_transitions.py` (new) or wherever test 5/6
     land; may import `get_age_bracket` from `src/domains/demographics/cohort.py` for the
     comparison only (a read-only cross-check import, not a production dependency — does not
     violate Out of Scope, which forbids *modifying* `cohort.py`/`test_demographics.py`, not
     reading from it in a new test file).

## Scoped Pytest Commands

```
pytest tests/unit/strategic/ tests/unit/progression/test_lifecycle.py tests/unit/core/test_rpg_depth.py tests/unit/core/test_domain_6_hardening.py tests/unit/domains/optimization/ tests/unit/world/test_demographics.py -m "not slow"
```

```
pytest tests/integration/optimization/ tests/integration/pipeline/test_recovery_gaps.py tests/integration/pipeline/test_transaction_completion.py tests/integration/kernel/test_snapshot_integrity.py -m "not slow"
```

Never `pytest tests/`.

## Anti-Drift Test Guards

- `test_life_stage_multipliers` (existing, regression surface above) already asserts the exact
  multiplier magnitudes (`CHILD` 0.8 fatigue, `ELDER` 1.5 fatigue in that test's scenario) — any
  change to `LifeStageService.get_goal_multipliers()`'s values as a side effect of this ticket
  would fail it immediately. Do not touch that method's multiplier dict.
- `test_non_elder_returns_none` / `test_elder_modifier_reduces_combat_effectiveness` /
  `test_elder_knowledge_bonus_positive` (existing) guard against Decision 2 drift — if
  `compute_elder_attribute_update()` gets accidentally wired into a production call path as a side
  effect of adding the new trigger, these tests won't catch it directly (they test the function in
  isolation), so **test 6 above (monotonic forward-only) doubles as the practical guard**: if an
  implementer wires the elder-attribute mechanism into the same per-tick check as the life-stage
  trigger without an idempotency guard, a repeated-tick test run would show `AttributeComponent`
  values drifting tick-over-tick, which test 6's fixture (constructing entities at fixed
  `age_ticks` and checking a single transition point) would surface as an unexpected assertion
  failure if attributes are asserted alongside life_stage — Plan should decide whether to make this
  explicit or add a dedicated `test_elder_attribute_update_still_orphaned`-style guard asserting no
  production call site exists (e.g. via the same `grep`-style check used in this investigation,
  encoded as an architecture test if one already exists for orphan-detection patterns in this
  repo).
- `test_component_patch_apply_parity.py`'s existing `role_set` pipeline test must keep passing
  unchanged alongside the new `life_stage_set` pipeline test (test 4) — both exercise the same
  `replace()` call in `IdentityPatch.apply()`; a change that fixes `life_stage` but breaks `role`
  (e.g. by mis-ordering kwargs) would be caught here.
- Architecture guard: confirm the new trigger reads `AuthoritativeState`/`EntityState` and returns
  a typed `EntityUpdate`/`IdentityUpdate` — never calls `object.__setattr__` or otherwise mutates a
  frozen component in place — matching this repo's "Decision logic reads state, does not
  authoritatively mutate durable state" rule. If `LifecycleSystem.resolve_lifecycle()` is the
  chosen call site, this is implicitly covered by that function's existing shape (it already
  returns `StateUpdate`/`EntityUpdate` throughout); if a new function is added elsewhere, a direct
  "returns typed update, does not mutate input" assertion should be added.
