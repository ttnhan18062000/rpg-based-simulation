---
status: historical
layer: engine
authority: P2
audience: agent
ticket_id: TCK-20260902-REPRODUCTION-HUMANOID-CADENCE-PHASE
artifact_type: test_plan
tags: [lifecycle, engine]
---

# Test Plan — TCK-20260902-REPRODUCTION-HUMANOID-CADENCE-PHASE

## Regression Surface

Existing tests that must keep passing, unchanged, after this ticket lands (grouped by domain,
reusing the exact scoped file lists the three hard-dependency/sibling reproduction tickets already
established as this area's regression surface):

**Unit — lifecycle/birth-record/genetics:**
- `tests/unit/progression/test_lifecycle.py` — birth-record schema fields, canonical-dict
  round-trip, update merge/is_noop, patch-apply-through-authoritative-path, builder two-parent
  and parentless cases, child-side bond seeding, parent-side reciprocal bond apply, the
  no-marriage-precondition guard, genetic-profile canonical round-trip.
- `tests/unit/progression/test_genetics.py` — `combine_profiles()` range/determinism, occupation
  bias, `GeneticsSystem` real-caller guard.

**Unit — world/reproduction siblings:**
- `tests/unit/world/test_natural_creature_reproduction.py` — camp-maturity spawn, no-tracked-
  parents, short maturation clock, scarcity suppression (allowed/suppressed/no-cohort-data),
  no-population-cohorts-write guard, no-genetics-reference guard, genetics-boundary guard
  (natural-creature/magical paths never attach a `GeneticProfile`).
- `tests/unit/world/test_calamity_magical_demonic_reproduction.py` — magical/demonic sibling path
  regression (same genetics-boundary guard's second assertion).
- `tests/unit/world/test_camp_lifecycle.py` — `test_camp_maturity_and_spawn`,
  `test_camp_raid_trigger` (garrison-spawn/raid-trigger blocks must be byte-for-byte unaffected).
- `tests/unit/world/test_demographics.py` — `compute_regional_scarcity`, migration,
  `PopulationCohort` behavior this ticket's scarcity gate reuses read-only.
- `tests/unit/world/test_spawn_cadence.py` — unrelated spawn-cadence tuning, must not regress from
  any `SystemCadence`/`should_run` change.

**Unit — social:**
- `tests/unit/social/test_social_bonds.py`, `tests/unit/social/test_social_lifecycle.py`,
  `tests/unit/social/test_social_party_regression.py` — `SocialBond`/`RelationshipService`
  behavior this ticket's parent-side reciprocal bond write depends on.

**Integration — authoritative apply path:**
- `tests/integration/optimization/test_component_patch_apply_parity.py` — birth-record and
  genetics-profile round-trip through `ApplyPath.apply_generation()`; the natural-creature
  spawn's own round-trip test.
- `tests/integration/optimization/test_apply_plan_parity.py`,
  `tests/integration/optimization/test_phase_skip_parity.py` — apply-plan parity, cadence-driven
  phase-skip behavior (directly relevant since this ticket may add a new `SystemCadence` field
  read by `should_run`).
- `tests/integration/scenarios/test_demographics.py` — end-to-end demographic-cycle scenario
  behavior, must remain unaffected by a purely-additive reproduction trigger.

**Unit — cadence/apply-plan cadence consumers (new to this ticket's regression surface, since it
is the first ticket in the epic to touch `cadence.py` itself):**
- Any existing test file directly importing `SystemCadence`/`should_run` (confirm via `grep -rl
  "from src.engine.cadence import\|SystemCadence(" tests/` at implementation time) — a new field
  addition to a `frozen=True` Pydantic model must not break existing keyword-only construction
  call sites (`SystemCadence(strategic_intelligence=1)`-style partial construction is used
  pervasively — `apply.py:205`, `policy.py:29,91,112,133,154`, `redirection.py:26`,
  `intelligence.py:302,664`, `role_model_phase.py:38`, `perf/profiles.py:29`,
  `perf/profile_governance.py:20` — a new field with a sane default cannot break any of these,
  but this should be confirmed, not assumed).

## New Tests Required

Per acceptance criteria:

1. **`test_new_cadence_entry_fires_per_should_run_pattern`**
   - Category: unit
   - Verifies: the new `SystemCadence` field (whatever name Plan assigns, e.g.
     `reproduction_humanoid`) exists with a sane World/Environmental-tier default, and
     `should_run(tick, None, cadence.<field>)` fires on the expected tick modulo and does not fire
     off-cadence — following the exact pattern `test_spawn_cadence.py`/`apply_plan.py`'s existing
     `is_bio_due`/`is_life_due` tests use for other cadence fields.
   - Location: `tests/unit/engine/test_cadence.py` (new file if one does not already exist for
     `cadence.py` in isolation — confirm at implementation time) or
     `tests/unit/world/test_reproduction_humanoid_cadence.py` (new file, matching the sibling
     tickets' one-new-file-per-path convention).

2. **`test_eligible_adult_alive_same_location_same_race_pair_produces_birth`**
   - Category: unit
   - Verifies: two entities meeting every eligibility condition (ADULT `life_stage`, `alive`,
     co-located per the plan's chosen "same-location" definition, same `kind`, both
     `reproduction_cooldowns` clear) produce a new entity via the builder path with
     `parent_a_id`/`parent_b_id`/`birth_tick`/`birth_city_id` correctly recorded and a
     `GeneticProfile` attached via `GeneticsSystem.combine_profiles()` (through
     `birth_record()`).
   - Location: `tests/unit/world/test_reproduction_humanoid_cadence.py`.

3. **`test_no_marriage_contract_referenced_in_humanoid_reproduction_path`**
   - Category: architecture guard
   - Verifies (per AC3's explicit grep-verifiability requirement): no
     `ContractKind.MARRIAGE`/`MarriageState`/`ContractState` reference exists anywhere in the new
     source file(s) — mirrors the birth-record schema ticket's
     `test_no_marriage_precondition_in_birth_record_schema_or_apply_path` pattern (source-text
     grep + behavioral confirmation with `strategic.contracts == {}`).
   - Location: `tests/unit/world/test_reproduction_humanoid_cadence.py`.

4. **`test_social_bond_seeded_between_each_parent_and_child_at_high_familiarity_sentiment`**
   - Category: unit
   - Verifies: both the child-side bonds (via `birth_record()`'s own `.social(bonds=...)`) and
     the parent-side reciprocal bonds (via `build_parent_bond_updates_for_birth()` applied through
     the authoritative apply path against the two real, already-existing parent entities) land at
     `familiarity=0.8`/`sentiment=0.8`.
   - Location: `tests/unit/world/test_reproduction_humanoid_cadence.py` (child-side) +
     `tests/integration/optimization/test_component_patch_apply_parity.py` (parent-side
     round-trip, matching the birth-record schema ticket's own
     `test_parent_bond_updates_for_birth_apply_through_authoritative_path` precedent).

5. **`test_both_parents_cooldown_set_and_repeat_check_before_cooldown_clears_produces_no_second_birth`**
   - Category: unit
   - Verifies: on a successful birth, both parents' `reproduction_cooldowns[partner_id]` are set
     to a future expiry tick via `LifecycleUpdate.reproduction_cooldowns_add`; a second
     eligibility check on the same pair before that tick is reached does not produce a birth
     (explicitly required by AC5's "test proves this" wording — not just that the field was set,
     but that a repeated same-tick-window check is behaviorally blocked).
   - Location: `tests/unit/world/test_reproduction_humanoid_cadence.py`.

6. **`test_eligibility_suppressed_when_regional_scarcity_exceeds_migration_threshold`** and
   **`test_eligibility_allowed_when_regional_scarcity_below_migration_threshold`**
   - Category: unit
   - Verifies: both the allowed and suppressed cases of the `compute_regional_scarcity()` gate
     (AC6 explicitly requires both), following the exact fixture shape
     `test_natural_creature_reproduction.py`'s equivalent pair already uses (seeded
     `population_cohorts={"young": PopulationCohort(...)}`, resource nodes constructed to push
     scarcity above/below the threshold).
   - Location: `tests/unit/world/test_reproduction_humanoid_cadence.py`.

7. **`test_no_population_cohorts_write_in_humanoid_reproduction_path`**
   - Category: architecture guard
   - Verifies (anti-drift, mirroring both shipped siblings' identical guard): the new code path
     never constructs a `WorldUpdate` with `population_cohorts_set` — that write path remains
     exclusively `DemographicCycleService.process_demographics()`/`_check_migration()`, per AC7 and
     the epic's build order (closed later by `TCK-20260902-REPRODUCTION-POPULATION-PRESSURE-CLOSURE`).
   - Location: `tests/unit/world/test_reproduction_humanoid_cadence.py`.

8. **`test_ineligible_pairs_produce_no_birth`** (child-stage / dead / cross-race / cross-location
   cases)
   - Category: unit — normal-flow negative cases required by the Testing Rule's "edge cases"
     coverage, not separately named in the ticket ACs but implied by "eligible ADULT, alive,
     same-location, same-race" being a compound condition each clause of which needs its own
     negative proof: one CHILD/ELDER participant, one dead participant, different `kind` values,
     different positions (per whatever "same-location" definition Plan settles on).
   - Location: `tests/unit/world/test_reproduction_humanoid_cadence.py`.

9. **`test_flag_off_produces_no_birth_regression_guard`**
   - Category: architecture guard
   - Verifies: with the new `ENABLE_REPRODUCTION_HUMANOID_PATH`-style flag at its default `OFF`,
     the new code path produces zero behavior change — mirrors both shipped siblings' flag-off
     regression guard.
   - Location: `tests/unit/world/test_reproduction_humanoid_cadence.py`.

10. **`test_humanoid_reproduction_commits_through_authoritative_apply_path`**
    - Category: integration
    - Verifies: the full `ApplyPath.apply_generation()` round-trip of the new entity plus both
      parents' cooldown/bond updates in a single tick — mirrors
      `test_natural_creature_spawn_commits_through_authoritative_apply_path`'s pattern, extended
      to also cover the parent-side mutations this ticket introduces (which the parentless sibling
      never exercised, since it has no real parents to update).
    - Location: `tests/integration/optimization/test_component_patch_apply_parity.py`.

## Scoped Pytest Commands

```
pytest tests/unit/world/test_reproduction_humanoid_cadence.py \
  tests/unit/world/test_natural_creature_reproduction.py \
  tests/unit/world/test_calamity_magical_demonic_reproduction.py \
  tests/unit/world/test_camp_lifecycle.py \
  tests/unit/world/test_demographics.py \
  tests/unit/world/test_spawn_cadence.py \
  tests/unit/progression/test_lifecycle.py \
  tests/unit/progression/test_genetics.py \
  tests/unit/social/test_social_bonds.py \
  tests/unit/social/test_social_lifecycle.py \
  tests/unit/social/test_social_party_regression.py \
  -q
```

```
pytest tests/integration/optimization/test_component_patch_apply_parity.py \
  tests/integration/optimization/test_apply_plan_parity.py \
  tests/integration/optimization/test_phase_skip_parity.py \
  tests/integration/scenarios/test_demographics.py \
  -q
```

If the new `SystemCadence` field's call-site placement (per investigation.md Risk #2) ends up
inside `src/engine/world_dynamics.py` or `src/engine/apply_plan.py`, also run whatever existing
scoped test file directly exercises that file's phase ordering (e.g. any
`tests/unit/engine/test_world_dynamics*.py` / `tests/integration/engine/test_apply_plan*.py` —
confirm exact paths at implementation time via `grep -rl "resolve_dynamics\|apply_generation"
tests/`).

Never: `pytest tests/`.

## Anti-Drift Test Guards

- **Marriage-precondition guard** (test #3 above) — locks in the ticket's single most explicit
  hard constraint (AC3); mirrors the birth-record schema's own guard pattern exactly, so a future
  refactor that accidentally reintroduces a marriage check anywhere in this call path fails loudly.
- **No-`population_cohorts`-write guard** (test #7) — prevents this ticket from silently
  encroaching on `TCK-20260902-REPRODUCTION-POPULATION-PRESSURE-CLOSURE`'s scope; both shipped
  siblings already carry the identical guard, so this ticket's own guard keeps parity with an
  established epic-wide convention rather than introducing a gap.
- **Flag-off regression guard** (test #9) — since this ticket, like both siblings, ships behind a
  brand-new default-`OFF` flag, this guard is the cheapest possible proof that landing the ticket
  changes zero live simulation behavior until the flag is explicitly flipped — catches an
  accidental unconditional call-site wiring mistake immediately.
- **Cooldown-blocks-repeat-birth guard** (test #5) — the single acceptance criterion most likely
  to be satisfied only partially by implementation (e.g. writing the cooldown field but never
  actually reading it back on the next eligibility check) — this test must assert the *behavioral*
  outcome (no second birth), not just that the field was written, exactly as AC5's own wording
  ("test proves this") demands.
- **`SystemCadence` construction-compatibility check** (Regression Surface, final bullet) — a new
  field on a `frozen=True` Pydantic model with keyword-only partial-construction call sites spread
  across at least 10 files is a real silent-break risk if the new field is added without a default
  or with a name colliding with an existing one; this should be confirmed explicitly rather than
  inferred from "the existing tests still pass," since none of those call sites construct
  `SystemCadence` with every field named, so a naming collision could silently shadow an existing
  field's intended value in a way generic regression tests would not catch.
- **Genetics real-parent-data guard** — a test asserting that when both parents pass a real
  `identity.role == EntityRole.HERO`, the resulting child's `GeneticProfile` shows the combat-lean
  bias (reusing `GeneticsSystem.combine_profiles()`'s already-tested behavior, but proving *this
  ticket's caller* actually threads `parent_a_role`/`parent_b_role` through correctly — investigation.md
  Risk #6 flags this as a silent-omission risk that would not otherwise be caught by any existing
  test, since `combine_profiles()`'s own tests only exercise the function directly, not this
  ticket's new call site).
