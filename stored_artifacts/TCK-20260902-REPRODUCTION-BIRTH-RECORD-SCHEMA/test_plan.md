---
status: historical
layer: core
authority: P2
audience: agent
ticket_id: TCK-20260902-REPRODUCTION-BIRTH-RECORD-SCHEMA
artifact_type: test_plan
tags: [lifecycle, core]
---

# Test Plan — TCK-20260902-REPRODUCTION-BIRTH-RECORD-SCHEMA

## Regression Surface

**Unit — Lifecycle / updates / patches:**
- `tests/unit/progression/test_lifecycle.py` — `test_aging_per_tick`, `test_death_by_old_age`,
  `test_combat_death_classification`, `test_permadeath_death_classification`,
  `test_succession_and_heirloom_transfer`, `test_manual_heir_entity_id_transfers_even_if_heir_inactive`
  (and any other tests in this file). Must keep passing byte-for-byte: `LifecycleUpdate.merge()`/
  `is_noop()` are being extended field-by-field and a mistake there is the highest-probability
  regression source for existing heir/death logic.
- `tests/unit/social/test_social_bonds.py` — `test_social_bond_learning`,
  `test_social_bond_role_defaults_to_neutral`, `test_social_bond_role_canonical_dict_serializes_as_plain_string`.
  Confirms `SocialBond`/`BondUpdate`/`RelationshipService.process_update` are unmodified by this
  ticket's parent-side bond-seeding wiring.

**Unit — builder / entity construction:**
- Any existing `V2EntityBuilder` tests exercising `.lifecycle(...)` and `.social(...)` (via
  `tests/unit/progression/test_lifecycle.py`'s builder usage and any dedicated builder test module,
  e.g. `tests/unit/core/test_rpg_depth.py` if it constructs entities via `V2EntityBuilder.lifecycle`/
  `.social`). Must confirm existing keyword-argument behavior (`heir_entity_id`, `heirlooms`,
  `bonds`) is unchanged by the new keyword additions.

**Unit — apply-plan / component-patch parity:**
- `tests/integration/optimization/test_component_patch_apply_parity.py` —
  `test_component_patch_apply_parity`, `test_life_stage_set_survives_full_apply_pipeline`,
  `test_new_maturity_field_survives_apply_generation_round_trip`,
  `test_self_model_patch_apply_parity_durable_materialization`. Confirms `LifecyclePatch.apply`
  changes don't break the fast-path/full-pipeline parity guarantee for other component patches.
- `tests/integration/optimization/test_apply_plan_parity.py`
- `tests/unit/domains/optimization/test_apply_plan_builder.py` —
  `test_apply_plan_builder_grouping`, `test_apply_plan_builder_noop`.
- `tests/integration/optimization/test_phase_skip_parity.py`

**Unit — world/demographics (adjacent, must show NO change):**
- `tests/unit/world/test_demographics.py` — `test_region_canonical_dict_includes_cohorts` and the
  rest of the `PopulationCohort`/`RegionState` canonical-dict suite. Anti-drift guard: this ticket
  must not touch `RegionState`/`PopulationCohort`/`WorldUpdate.population_cohorts_set` at all.
- `tests/unit/world/test_spawn_cadence.py` — confirms `SpawnService.process_spawns`'s
  `entities_add`/`next_entity_id_set` mid-tick entity-creation path (the mechanism this ticket's
  builder output must remain compatible with) is unaffected.

**Unit — social/general regression:**
- `tests/unit/social/test_social_lifecycle.py`
- `tests/unit/social/test_social_party_regression.py`

## New Tests Required

- **`test_lifecycle_component_canonical_dict_round_trip_includes_birth_fields`**
  Category: unit.
  Verifies: `LifecycleComponent(parent_a_entity_id=..., parent_b_entity_id=..., birth_tick=...,
  birth_city_id=..., <cooldown_field>=...).to_canonical_dict()` includes every new field with the
  correct value, and that a `None`-valued optional field (parentless spawn case) serializes as
  `None`/absent consistently rather than raising. Mirrors the
  `test_region_canonical_dict_includes_cohorts` pattern cited by AC 5
  (`docs/parity_ledger/world_dynamics.yaml:1671-1691`, `TCK-20260831-POPULATION-COHORT-SEEDING`).
  Location: `tests/unit/progression/test_lifecycle.py`.

- **`test_lifecycle_update_merges_birth_fields`**
  Category: unit.
  Verifies: `LifecycleUpdate` with the new `*_set` fields correctly participates in `is_noop()` (a
  `LifecycleUpdate` with only a new field set is NOT a no-op) and `merge()` (last-non-None-wins
  semantics for each new scalar `_set` field, consistent with `heir_entity_id_set`'s existing
  behavior). Location: `tests/unit/progression/test_lifecycle.py` or a new
  `tests/unit/core/test_updates_lifecycle.py` if a dedicated `updates.py`-level test module exists —
  confirm placement against existing `LifecycleUpdate`-only test coverage before choosing.

- **`test_lifecycle_patch_apply_writes_birth_fields_through_authoritative_path`**
  Category: integration (component-patch apply parity, same family as
  `test_component_patch_apply_parity`).
  Verifies: an `EntityUpdate(lifecycle=LifecycleUpdate(parent_a_entity_id_set=..., ...))` applied via
  `LifecyclePatch.apply` (or the full `AuthoritativeState.apply()` path) durably writes the new
  fields onto the resulting `LifecycleComponent`, and that no direct field mutation occurred (assert
  the prior-tick entity object is unchanged — `is` identity check on the untouched baseline).
  Location: `tests/integration/optimization/test_component_patch_apply_parity.py`.

- **`test_builder_birth_record_path_two_parent_case`**
  Category: unit.
  Verifies: the new `V2EntityBuilder` birth-record construction path (extended `.lifecycle(...)`
  kwargs, or a dedicated method per the Plan phase's chosen shape), given two parent entity IDs and a
  birth tick/city, produces an `EntityState` whose `lifecycle.parent_a_entity_id`,
  `lifecycle.parent_b_entity_id`, `lifecycle.birth_tick`, `lifecycle.birth_city_id` are populated
  exactly as passed in. Location: `tests/unit/progression/test_lifecycle.py` (co-located with the
  existing `V2EntityBuilder`-based lifecycle tests) or a new `tests/unit/core/test_builder.py` if one
  does not already exist — check first.

- **`test_builder_birth_record_path_parentless_case`**
  Category: unit.
  Verifies: the same construction path called with `parent_a_entity_id=None,
  parent_b_entity_id=None` (natural-creature/magical spawn case per the ticket's Scope) produces a
  valid `EntityState` with both parent fields `None` and no exception — confirms the schema does not
  implicitly require two parents. Location: same file as above.

- **`test_builder_birth_record_seeds_child_social_bonds_toward_parents`**
  Category: unit.
  Verifies: the two-parent construction case seeds `EntityState.social.bonds` with entries keyed by
  each parent's entity ID, at the "high familiarity/sentiment" values the Plan phase documents
  (AC 4), using `RelationshipRole`/`SocialBond` field shapes unchanged from
  `src/core/models/social.py`. Location: same file as above, or
  `tests/unit/social/test_social_bonds.py` if that module is judged the better home for
  bond-shape assertions — check existing file organization before choosing.

- **`test_no_marriage_precondition_in_birth_record_schema_or_apply_path`**
  Category: architecture guard.
  Verifies: (a) the new `LifecycleComponent`/`LifecycleUpdate` fields and `LifecyclePatch.apply`
  logic contain no reference to `ContractState`/`ContractStatus`/any marriage-shaped identifier —
  either via an explicit unit test asserting the birth-record construction path succeeds with *no*
  active contract present in `AuthoritativeState.strategic`/wherever contracts live, or via a static
  grep-based architecture test (matching the project's existing "architecture tests verify... typed
  records serialize/deserialize correctly" convention) that fails if "marriage" or a contract-status
  check appears in the diff's touched files. Location: `tests/unit/progression/test_lifecycle.py`
  (behavioral form) — a static-grep guard, if added, belongs under `tests/unit/core/` alongside other
  architecture-guard tests; confirm an existing pattern/module before adding a new one.

## Scoped Pytest Commands

```
pytest tests/unit/progression/test_lifecycle.py -v
pytest tests/unit/social/test_social_bonds.py tests/unit/social/test_social_lifecycle.py tests/unit/social/test_social_party_regression.py -v
pytest tests/integration/optimization/test_component_patch_apply_parity.py tests/integration/optimization/test_apply_plan_parity.py tests/integration/optimization/test_phase_skip_parity.py -v
pytest tests/unit/domains/optimization/test_apply_plan_builder.py -v
pytest tests/unit/world/test_demographics.py tests/unit/world/test_spawn_cadence.py -v
```

Do not run `pytest tests/` (full suite). If a dedicated builder test module is created or
identified during implementation, add it explicitly to the first command above rather than widening
scope to `tests/unit/core/`.

## Anti-Drift Test Guards

- **Cohort/regional-demographics isolation**: `tests/unit/world/test_demographics.py`'s existing
  `PopulationCohort`/`RegionState` assertions must produce byte-identical results before and after
  this ticket — catches any accidental coupling between the new per-entity birth-record schema and
  the unrelated regional cohort model (both use the word "birth"/"population" but are structurally
  independent; see investigation.md's Docs Requiring Update section).
- **Heir/succession non-regression**: `test_succession_and_heirloom_transfer` and
  `test_manual_heir_entity_id_transfers_even_if_heir_inactive` in
  `tests/unit/progression/test_lifecycle.py` must keep passing unchanged — catches accidental
  breakage of `LifecycleUpdate.merge()`/`is_noop()` from the new field additions (the highest-risk
  edit in this ticket, since both methods hand-enumerate every field).
- **No marriage coupling**: the new `test_no_marriage_precondition_in_birth_record_schema_or_apply_path`
  guard above is itself the anti-drift check for the ticket's single hardest explicit constraint —
  keep it in the regression suite for every subsequent Reproduction-epic child ticket, since those
  tickets will build directly on this schema and could reintroduce a marriage precondition without
  this guard catching it.
- **Direct-mutation guard**: assert (via `is`/`==` identity comparison on the pre-apply baseline
  entity) that no test path calls `replace(entity.lifecycle, parent_a_entity_id=...)` or similar
  direct field mutation outside `LifecyclePatch.apply` — matches the project's "Architecture tests:
  verify read-only logic did not mutate live state, authoritative application path was used" rule
  from `CLAUDE.md`'s Testing Rule section.
- **Builder/apply-path compatibility guard**: confirm an `EntityState` produced by the new builder
  birth-record path can be placed directly into `StateUpdate.entities_add` and survive
  `AuthoritativeState.apply()` unchanged (round-trip through `src/engine/apply.py:267-272`) — catches
  a mismatch between what the builder constructs and what the mid-tick entity-creation path
  (`src/world/spawn.py`'s existing precedent) expects.
