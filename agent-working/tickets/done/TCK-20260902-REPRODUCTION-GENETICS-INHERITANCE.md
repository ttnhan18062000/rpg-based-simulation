---
status: historical
layer: systems
authority: P1
audience: agent
ticket_id: TCK-20260902-REPRODUCTION-GENETICS-INHERITANCE
phase: done
date: 2026-09-02
tags: [lifecycle]
---

# TCK-20260902-REPRODUCTION-GENETICS-INHERITANCE

## Title
Wire orphaned GeneticsSystem/GeneticProfile into human/humanoid reproduction's inheritance step

## Status
DONE

## Tier
standard

## Type
feature

## Priority
P2

## Request Summary
Child ticket 4 of 6 under the Reproduction epic (TCK-20260902-EPIC-RPG-M3-REPRODUCTION). `GeneticsSystem`/`GeneticProfile` (`src/systems/lifecycle_systems/genetics.py`) already exists and is written, but is confirmed to have zero real callers anywhere in `src/` or `tests/` — it is only referenced via a re-export shim at `src/systems/genetics.py`. This ticket wires it up for the first time, as the inheritance step for human/humanoid reproduction: a produced entity's `GeneticProfile` is sampled/combined from both parents' profiles. Depends on TCK-20260902-REPRODUCTION-BIRTH-RECORD-SCHEMA landing first (needs `parent_a_entity_id`/`parent_b_entity_id` to be resolvable to real parent entities to read their profiles from).

## Scope
- Wire `GeneticsSystem`/`GeneticProfile` (`src/systems/lifecycle_systems/genetics.py`) into a real call path for the first time, invoked whenever a human/humanoid birth (from TCK-20260902-REPRODUCTION-HUMANOID-CADENCE-PHASE) needs to construct the new entity's genetic profile.
- The produced entity's `GeneticProfile` is sampled/combined from both parents' profiles using the existing 0.8–1.3 per-attribute multiplier range already defined in `genetics.py`.
- The combination's bias direction is determined by parent occupation/role: a combat-relevant lean when both parents are Adventurer-occupation, a flatter/neutral spread when both parents hold civilian occupations (exact weighting formula is a Plan-phase decision — this is new, unprecedented territory with no existing numeric analog to copy).
- The resulting `GeneticProfile` is attached to the new entity via a typed `EntityUpdate`, through the authoritative apply path.

## Out of Scope
- The human/humanoid reproduction trigger/cadence logic itself (cooldown checks, entity pairing) — that is TCK-20260902-REPRODUCTION-HUMANOID-CADENCE-PHASE, which calls into this ticket's inheritance step.
- Genetics for the natural-creature or magical/demonic paths — out of scope per those tickets' own boundary notes; confirm at Plan time this ticket is human/humanoid-only.

## Acceptance Criteria
- [x] `GeneticsSystem`/`GeneticProfile` has a real, live caller for the first time — verifiable via a grep showing a non-test, non-shim call site. (`V2EntityBuilder.birth_record()`, `src/core/builder.py`; locked in by `test_genetics_system_has_real_non_test_non_shim_caller`.)
- [x] A new entity produced by human/humanoid reproduction has a `GeneticProfile` sampled/combined from both parents' profiles using the existing 0.8–1.3 per-attribute multiplier range. (`GeneticsSystem.combine_profiles()`; `test_combine_genetic_profiles_stays_within_multiplier_range`.)
- [x] The combination's bias direction is measurably different for two-Adventurer-parent vs two-civilian-parent cases (a test asserts the distributional difference, not just that a value exists). (`test_adventurer_parents_bias_toward_combat_attributes`, `test_civilian_parents_produce_flatter_neutral_spread`.)
- [x] The resulting profile is written via a typed `EntityUpdate` through the authoritative apply path. (`LifecycleUpdate.genetic_profile_set` → `LifecyclePatch.apply()`; `test_birth_record_writes_genetic_profile_via_authoritative_apply_path`.)
- [x] New unit tests added for the inheritance/combination function, following existing `tests/unit/` conventions for `src/systems/lifecycle_systems/`. (7 new tests across `test_genetics.py`, `test_lifecycle.py`, `test_natural_creature_reproduction.py`, plus 1 integration test.)
- [x] `docs/mechanics/01_entity_anatomy.md` documents the inheritance mechanism; a `docs/parity_ledger/` entry cites it. (New "Genetic Inheritance (Combination)" subsection; `docs/parity_ledger/social_narrative.yaml` entry `SOC-260`.)

## Related Tickets
- TCK-20260902-EPIC-RPG-M3-REPRODUCTION (parent epic)
- TCK-20260902-REPRODUCTION-BIRTH-RECORD-SCHEMA (hard dependency — must land first)
- TCK-20260902-REPRODUCTION-HUMANOID-CADENCE-PHASE (sibling — the trigger path that will call into this inheritance step; lands after this ticket per the epic's build order)

## Related Docs
- docs/plans/rpg_design_roadmap/rpg_m3_family_species_epic.md
- docs/brainstorm/rpg_feature_atlas.html (idea 32 card)
- docs/mechanics/01_entity_anatomy.md

## Related Stored Artifacts
None.

## Related Code Areas
- src/systems/lifecycle_systems/genetics.py
- src/systems/genetics.py (re-export shim)
- src/core/updates.py

## Assumptions / Open Questions
- The exact occupation-bias weighting formula has no existing numeric precedent anywhere in the codebase and must be designed fresh at Plan time — do not assume a specific formula here.

## Implementation Notes

Followed `staging_artifacts/TCK-20260902-REPRODUCTION-GENETICS-INHERITANCE/plan.md` exactly, in
its suggested order (Step 1 → 2 → 3 → 4 → 5 → 6 → 7). No deviations from the plan's design.

1. **`src/core/state.py`** — added `genetic_profile: Optional[GeneticProfile] = None` as the last
   field of `LifecycleComponent` (before the `_canonical_cache` sentinel), imported `GeneticProfile`
   from `src.systems.lifecycle_systems.genetics` (the canonical defining module, not the
   `src/systems/genetics.py` shim — confirmed no circular-import risk, `genetics.py` has zero
   `src.*` imports). `to_canonical_dict()` adds `"genetic_profile": asdict(self.genetic_profile) if
   self.genetic_profile else None`, matching the existing `latest_result` pattern.
2. **`src/core/updates.py`** — added `genetic_profile_set: Optional[GeneticProfile] = None` as the
   last field of `LifecycleUpdate`; extended `is_noop()`'s boolean expression and `merge()`'s
   changes-dict with the identical `if other.X is not None: changes["X"] = other.X` pattern used by
   every sibling `*_set` field. Verified (by grep) none of the five other `LifecycleUpdate` writers
   (`combat_actions.py`, `aoe_actions.py`, `lifecycle.py`, `movement.py`, `skill_actions.py`)
   reference the new field — all use keyword-only construction with a strict field subset, so the
   `None` default leaves them unaffected.
3. **`src/engine/patches.py`** — added one more `replace()` kwarg in `LifecyclePatch.apply()`:
   `genetic_profile=u_life.genetic_profile_set if u_life.genetic_profile_set is not None else
   new_lifecycle.genetic_profile`, matching the exact pattern of every sibling field in the same
   call. `is_noop()` needed no change — it already delegates to `LifecycleUpdate.is_noop()`.
4. **`src/systems/lifecycle_systems/genetics.py`** — added `GeneticsSystem.combine_profiles()` as a
   pure `@staticmethod`: per-attribute convex-combination of both parents' multipliers, convex-blended
   0.6/0.4 with a `generate_profile_from_seed(seed)` perturbation draw, then (only when
   `combat_lean=True` and the attribute is `strength_mult`/`agility_mult`/`constitution_mult`) pulled
   35% of the remaining distance toward the 1.3 ceiling, with an explicit `min`/`max` clamp as
   defense-in-depth. Stays within `[0.8, 1.3]` by construction — verified against the floor/ceiling
   edge case in `test_combine_genetic_profiles_stays_within_multiplier_range`. Did not touch
   `apply_genetic_profile()`, `generate_profile_from_seed()`, `SkillType`/`SkillDefinition`/
   `SkillScalingSystem` (unrelated, LEG-RPG-145) — existing 11 tests in `test_genetics.py` still pass
   unchanged.
5. **`src/core/builder.py`** — added `genetic_profile: Optional[GeneticProfile] = None` kwarg to
   `V2EntityBuilder.lifecycle()` (added to the `updates` dict following the established
   `if value is not None` pattern; `_lifecycle_to_dict()`/`_to_dict()` is generic over
   `dataclasses.fields()`, so it required no change to pick up the new field). Added four new
   optional kwargs to `birth_record()`: `parent_a_genetic_profile`, `parent_b_genetic_profile`,
   `parent_a_role`, `parent_b_role` (all `None`-default, primitives-only per the builder's
   established convention). When at least one parent profile is passed, `combat_lean` is computed
   from `parent_a_role == EntityRole.HERO and parent_b_role == EntityRole.HERO` (`EntityRole` was
   already imported at `builder.py:49` — no new import needed for it; added
   `GeneticsSystem, GeneticProfile` import from `src.systems.lifecycle_systems.genetics`), missing
   parent profiles fall back to `generate_profile_from_seed(parent_id or 0)`, and the combined
   profile is written via a second `self.lifecycle(genetic_profile=combined)` call. Verified manually
   (before running the full suite) that the authoritative apply path round-trips the field correctly
   and that the baseline entity object is never mutated in place.
6. **Anti-drift test** — added `test_natural_creature_and_magical_demonic_paths_never_attach_genetic_profile`
   to `tests/unit/world/test_natural_creature_reproduction.py`, asserting both parentless spawn paths'
   output entities have `lifecycle.genetic_profile is None`. Zero production changes required — both
   paths already never pass the new `birth_record()` kwargs (confirmed by the existing
   `test_natural_creature_reproduction_does_not_reference_genetics` source-text guard, which already
   covered `spawn_natural_creature_offspring`).
7. **Docs** — added a "Genetic Inheritance (Combination)" subsection to
   `docs/mechanics/01_entity_anatomy.md` §5 (after the existing Birth Record subsection); added an
   "Assignment via parent combination (inheritance)" subsection to
   `docs/simulation/lifecycle_systems_contract.md`'s Genetics section (parallel to "Assignment at
   spawn"); registered new entry `SOC-260` in `docs/parity_ledger/social_narrative.yaml` via
   `tools/parity_ledger_writer.py` (validated write path, in-process index rebuild), cross-referencing
   `SOC-259`, then issued the second, visible `python3 tools/parity_index.py build` Bash call per
   `.claude/agents/parity-updater.md`'s convention for retro-metric visibility; updated
   `docs/core/entities.md`'s `LifecycleComponent` table row (field list + line-range citation,
   `state.py:151-190` → `state.py:152-193`) since that row already existed for this component.

**Doc-precision note applied (Step 7):** both new doc subsections state plainly that the
neutral/non-combat-lean path is the default fallthrough for *any* non-double-HERO pairing
(civilian, `WORKER`/`GUARD`, or a mismatch) — not narrowly scoped to `CITIZEN`/`SHOPKEEPER` only —
per the review note in the task brief.

No deviations from `plan.md`. No PROG-028 fix attempted (pre-existing, out of scope, confirmed
untouched). No `HUMANOID-CADENCE-PHASE` trigger logic built. No genetic data stored in
`IdentityComponent.properties`.

## Test Summary

Ran the full scope from `test_plan.md`'s "Scoped Pytest Commands" plus the sibling
`test_calamity_magical_demonic_reproduction.py` suite (magical/demonic path regression check for
the anti-drift test's second assertion):

```
pytest tests/unit/progression/test_genetics.py tests/unit/progression/test_lifecycle.py \
  tests/unit/world/test_natural_creature_reproduction.py \
  tests/unit/world/test_calamity_magical_demonic_reproduction.py \
  tests/integration/optimization/test_component_patch_apply_parity.py \
  tests/integration/optimization/test_apply_plan_parity.py \
  tests/integration/optimization/test_phase_skip_parity.py -q
```

Result: **67 passed, 0 failed** (60 in the plan's own scope + 7 in the added calamity suite).

New tests added (7 unit/architecture-guard + 1 integration, matching `test_plan.md`'s 7-item list
via 7 concrete tests plus AC1's architecture guard folded into the same function):
- `tests/unit/progression/test_genetics.py`: `test_combine_genetic_profiles_stays_within_multiplier_range`,
  `test_combine_genetic_profiles_is_deterministic`, `test_adventurer_parents_bias_toward_combat_attributes`,
  `test_civilian_parents_produce_flatter_neutral_spread`, `test_genetics_system_has_real_non_test_non_shim_caller`.
- `tests/unit/progression/test_lifecycle.py`: `test_canonical_dict_round_trip_includes_genetic_profile`.
- `tests/unit/world/test_natural_creature_reproduction.py`: `test_natural_creature_and_magical_demonic_paths_never_attach_genetic_profile`.
- `tests/integration/optimization/test_component_patch_apply_parity.py`: `test_birth_record_writes_genetic_profile_via_authoritative_apply_path`.

All pre-existing tests in the regression surface (11 in `test_genetics.py`, 24+ in
`test_lifecycle.py`, 9+1 in the natural-creature/calamity suites, the three apply-path integration
suites) pass unchanged.

## Files Changed

Production code:
- `src/core/state.py` — `LifecycleComponent.genetic_profile` field + `to_canonical_dict()`.
- `src/core/updates.py` — `LifecycleUpdate.genetic_profile_set` field + `is_noop()`/`merge()`.
- `src/engine/patches.py` — `LifecyclePatch.apply()` writes `genetic_profile`.
- `src/systems/lifecycle_systems/genetics.py` — `GeneticsSystem.combine_profiles()`.
- `src/core/builder.py` — `V2EntityBuilder.lifecycle()`/`birth_record()` new kwargs + wiring.

Tests:
- `tests/unit/progression/test_genetics.py`
- `tests/unit/progression/test_lifecycle.py`
- `tests/unit/world/test_natural_creature_reproduction.py`
- `tests/integration/optimization/test_component_patch_apply_parity.py`

Docs:
- `docs/mechanics/01_entity_anatomy.md`
- `docs/simulation/lifecycle_systems_contract.md`
- `docs/core/entities.md`
- `docs/parity_ledger/social_narrative.yaml` (new entry `SOC-260`)

Staging artifacts (already present at the start of this Implement run; part of this run's real
changeset per repo convention):
- `staging_artifacts/TCK-20260902-REPRODUCTION-GENETICS-INHERITANCE/plan.md`
- `staging_artifacts/TCK-20260902-REPRODUCTION-GENETICS-INHERITANCE/investigation.md`
- `staging_artifacts/TCK-20260902-REPRODUCTION-GENETICS-INHERITANCE/test_plan.md`

Ticket:
- `tickets/inprogress/TCK-20260902-REPRODUCTION-GENETICS-INHERITANCE.md`

## Completion Summary

Wired the previously-orphaned `GeneticsSystem`/`GeneticProfile` into a real, live call path for the
first time: a new `GeneticsSystem.combine_profiles()` pure function combines two parents'
`GeneticProfile`s via convex combination plus a seeded perturbation term, with a structurally
bounded (0.8–1.3) occupation-bias pull toward combat attributes when both parents are
`EntityRole.HERO` (any other pairing gets the same neutral default). `LifecycleComponent` gained a
new `genetic_profile` field with a matching `LifecycleUpdate.genetic_profile_set` →
`LifecyclePatch.apply()` authoritative write path, and `V2EntityBuilder.birth_record()` was
extended with optional parent-profile/parent-role kwargs that invoke the combination and store the
result — the real, non-test caller satisfying AC1. The natural-creature and magical/demonic
parentless spawn paths remain untouched and genetics-free, locked in by a new anti-drift test.
Documentation (Mechanics Bible §5, the lifecycle-systems contract, and a new parity ledger entry
`SOC-260` cross-referencing `SOC-259`) was updated to describe the mechanism, explicitly stating the
neutral path is the default fallthrough for any non-double-HERO pairing. During the Parity phase, a
real `test_path` collectibility bug was found and fixed (the newly-added `SOC-260` entry's
`test_path` was not being picked up by `tools/parity_index.py`'s collection step) so the new entry
is verifiably wired into parity tracking rather than only present in the YAML file. All 6 acceptance
criteria are satisfied; 67+ tests pass in the ticket's regression + new-test scope.

**Files changed:** 5 production files (`src/core/state.py`, `src/core/updates.py`,
`src/engine/patches.py`, `src/systems/lifecycle_systems/genetics.py`, `src/core/builder.py`), 4 test
files, 4 doc files (including the new `SOC-260` parity ledger entry), plus the ticket and its three
staging artifacts — verified 1:1 against `git status` during Verify (see Files Changed section
above).
