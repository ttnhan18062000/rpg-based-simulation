---
status: historical
layer: core
authority: P1
audience: agent
ticket_id: TCK-20260902-REPRODUCTION-BIRTH-RECORD-SCHEMA
phase: done
date: 2026-09-02
tags: [lifecycle, core]
---

# TCK-20260902-REPRODUCTION-BIRTH-RECORD-SCHEMA

## Title
Foundational birth-record durable schema — new Lifecycle/EntityState fields and builder wiring for individual reproduction

## Status
DONE

## Tier
standard

## Type
feature

## Priority
P1

## Request Summary
This is child ticket 1 of 6 under the Reproduction epic (TCK-20260902-EPIC-RPG-M3-REPRODUCTION), covering idea 32 (Reproduction) from `docs/plans/rpg_design_roadmap/rpg_m3_family_species_epic.md`. Today idea 32 has zero real code — it is design-only in `docs/brainstorm/rpg_feature_atlas.html`. `LifecycleUpdate` (`src/core/updates.py:435-462`) has a `heir_entity_id_set` field but no fields at all for parent identity, birth tick, birth location, or per-parent reproduction cooldown — every other reproduction-path ticket in this epic (natural-creature, magical/demonic, human/humanoid, genetics) depends on this durable schema existing first, so it must land before any of them. Marriage is explicitly NOT a precondition for reproduction — the M3 build-order note (2026-08-29 plan-owner decision) decoupled Marriage (idea 33) from Reproduction (idea 32); do not gate any part of this schema or its write path on an active marriage contract.

## Scope
- Add new typed durable fields to the Lifecycle component/update (parallel to the existing `heir_entity_id`/`heir_entity_id_set` pattern in `src/core/state.py` and `src/core/updates.py:435-462`): `parent_a_entity_id`, `parent_b_entity_id` (Optional[int], None for parentless spawns e.g. natural-creature/magical paths), `birth_tick` (int), `birth_city_id` (Optional[int]), and a per-parent reproduction cooldown field (follow the `CampUpdate.last_raid_tick_set` precedent at `src/core/updates.py:861-868` for the cooldown-field shape).
- Wire these fields through the authoritative apply path (`src/engine/patches.py` / `src/engine/apply_plan.py`) so a birth event can be committed as a typed `EntityUpdate`/`StateUpdate`, never a direct state mutation.
- Extend `src/core/builder.py` (which already has a `heir_entity_id` param at lines 584, 597) with an equivalent birth-record construction path so a newly spawned entity can be built with these fields populated at creation time.
- Seed a `SocialBond` between each parent and the new child entity at high familiarity/sentiment, following the seeding precedent in `src/systems/social_systems/relationships.py:55`.
- This ticket does not implement any of the three reproduction trigger paths (natural-creature, magical/demonic, human/humanoid) — it only builds the schema and the builder-level wiring those paths will call into.

## Out of Scope
- The actual reproduction trigger/decision logic for any of the three species-branching paths (natural-creature, magical/demonic, human/humanoid) — those are separate child tickets (TCK-20260902-REPRODUCTION-NATURAL-CREATURE-PATH, TCK-20260902-REPRODUCTION-MAGICAL-DEMONIC-PATH, TCK-20260902-REPRODUCTION-HUMANOID-CADENCE-PHASE).
- Genetics inheritance (`GeneticsSystem`/`GeneticProfile` wiring) — separate child ticket TCK-20260902-REPRODUCTION-GENETICS-INHERITANCE.
- The population-pressure feedback-loop closure (idea 38) — separate child ticket TCK-20260902-REPRODUCTION-POPULATION-PRESSURE-CLOSURE.
- Any marriage-gating logic — explicitly decoupled per the 2026-08-29 build-order decision; do not add a marriage precondition anywhere in this schema.

## Acceptance Criteria
- [x] `parent_a_entity_id`, `parent_b_entity_id`, `birth_tick`, `birth_city_id`, and a per-parent reproduction-cooldown field exist as new typed fields on the Lifecycle component/update, following the existing `heir_entity_id`/`heir_entity_id_set` naming and write-path pattern.
- [x] These fields are written only through a typed `EntityUpdate`/`StateUpdate` applied via the authoritative apply path — no direct mutation of frozen state.
- [x] `src/core/builder.py` gains a birth-record construction path that can populate all new fields at entity creation time, alongside the existing `heir_entity_id` param.
- [x] A `SocialBond` is seeded between each parent and the new child at high familiarity/sentiment when a birth record is constructed via the new builder path.
- [x] New unit tests cover: field serialization/deserialization (canonical-dict round-trip, matching the pattern the POPULATION-COHORT-SEEDING ticket fixed for `PopulationCohort.to_canonical_dict()` — see `docs/parity_ledger/world_dynamics.yaml:1671-1691`), and that the builder path produces correctly-populated fields for a two-parent case and a parentless (natural-creature/magical) case.
- [x] `docs/core/entities.md` and/or `docs/mechanics/01_entity_anatomy.md` documents the new fields; a new `docs/parity_ledger/` entry (likely `world_dynamics.yaml` or a new social_narrative.yaml entry) cites this schema.
- [x] No marriage-contract precondition exists anywhere in the new schema or its write path.

## Related Tickets
- TCK-20260902-EPIC-RPG-M3-REPRODUCTION (parent epic)
- TCK-20260831-SPECIES-INTELLIGENCE-TIER (idea 14, DONE — hard dependency satisfied)
- TCK-20260831-POPULATION-COHORT-SEEDING (idea 43, DONE — hard dependency satisfied)
- TCK-20260824-DEFAULT-HEIR-ASSIGNMENT (precedent for a Lifecycle-field write path)

## Related Docs
- docs/plans/rpg_design_roadmap/rpg_m3_family_species_epic.md
- docs/brainstorm/rpg_feature_atlas.html (idea 32 card)
- docs/mechanics/01_entity_anatomy.md
- docs/parity_ledger/world_dynamics.yaml (WORLD-DEMO-005, WORLD-DEMO-006)
- CLAUDE.md (Durable State Rule, Authoritative Mutation Pipeline Contract)

## Related Stored Artifacts
None.

## Related Code Areas
- src/core/state.py
- src/core/updates.py
- src/core/builder.py
- src/engine/patches.py
- src/engine/apply_plan.py
- src/systems/social_systems/relationships.py

## Assumptions / Open Questions
- Whether the per-parent cooldown lives on the Lifecycle component itself or a separate sidecar structure is an implementation decision for the Plan phase — `CampUpdate.last_raid_tick_set` is the closest existing precedent but is on a different component type (Camp, not entity Lifecycle).
- This ticket must land first — every other Reproduction-epic child ticket depends on it.

## Implementation Notes
Implemented per staging_artifacts plan.md, Steps 1-7:
- **Step 1** (`src/core/state.py`): added `parent_a_entity_id`, `parent_b_entity_id` (`Optional[int]`,
  default `None`), `birth_tick` (`int`, default `0` — sentinel for "no birth record"), `birth_city_id`
  (`Optional[int]`, default `None`), and `reproduction_cooldowns` (`Dict[int, int]`, default `{}`) to
  `LifecycleComponent`, immediately after `heirlooms`. Extended `to_canonical_dict()` to include all
  five, sorting `reproduction_cooldowns` via `dict(sorted(...))` for deterministic canonicalization.
  `LifecycleComponent` now spans `state.py:151-190` (was `151-180`).
- **Step 2** (`src/core/updates.py`): added matching `parent_a_entity_id_set`, `parent_b_entity_id_set`,
  `birth_tick_set`, `birth_city_id_set` (`Optional[int]`), and `reproduction_cooldowns_add`
  (`Dict[int, int]`, per-key upsert) to `LifecycleUpdate`. Extended `is_noop()` and `merge()` to
  hand-enumerate all five new fields; `reproduction_cooldowns_add` merges via `{**self.x, **other.x}`
  (per-key union, `other` wins on key conflict) — mirrors `EntityUpdate.property_updates`'s existing
  merge shape, so two same-tick writers updating different partners' cooldowns don't clobber each
  other.
- **Step 3** (`src/engine/patches.py`): extended `LifecyclePatch.apply()`'s `replace(new_lifecycle, ...)`
  call with all five fields, `*_set`-wins-over-baseline for scalars and per-key dict merge for
  `reproduction_cooldowns`. This is the sole authoritative write path for the new fields — invoked via
  `ApplyPath.apply_generation()` → `ApplyPlanBuilder.build_plan()`, no changes needed to `apply_plan.py`
  itself.
- **Step 4** (`src/core/builder.py`): extended `V2EntityBuilder.lifecycle()` with the five new keyword
  params, filtered through the existing `if value is not None` pattern.
- **Step 5** (`src/core/builder.py`): added `V2EntityBuilder.birth_record()`, which calls `.lifecycle(...)`
  for the five new fields and seeds the new entity's own `bonds` toward each non-`None` parent via
  `.social(bonds=...)` at `familiarity=0.8`/`sentiment=0.8` (`role` stays `NEUTRAL`, no new enum value
  added). Also added the module-level `build_parent_bond_updates_for_birth()` helper, which builds the
  parents' reciprocal `EntityUpdate(social=SocialUpdate(bond_updates=[SocialBondUpdate(...)]))` at the
  same 0.8/0.8 deltas (starting from `SocialBond` defaults of 0.0/0.0, so the deltas land exactly at
  0.8/0.8) — for a future reproduction-trigger ticket to apply through the normal authoritative pipeline.
  Required adding a top-level `from src.core.updates import EntityUpdate, SocialUpdate, SocialBondUpdate`
  import to `builder.py` (previously builder.py had no runtime import from `updates.py` at all — confirmed
  no circular-import risk since `updates.py` does not import from `builder.py`).
- **Step 6**: added `test_no_marriage_precondition_in_birth_record_schema_or_apply_path`, which both
  greps the source of the four touched call sites for "Contract"/"marriage" and behaviorally confirms
  `birth_record()` builds successfully with `strategic.contracts == {}`.
- **Step 7**: updated `docs/core/entities.md`'s Lifecycle table row (new field names + corrected line
  range) and added a new "Birth Record (Reproduction Schema)" subsection to
  `docs/mechanics/01_entity_anatomy.md` (after the Elder Attribute Modifiers subsection). Added parity
  ledger entry `SOC-259` to `docs/parity_ledger/social_narrative.yaml` via the sanctioned
  `tools/parity_ledger_writer.py:write_entry()` (schema-validated, index rebuilt in-process, followed by
  a separate visible `python3 tools/parity_index.py build` Bash call per the parity-updater convention).
  Ran `make knowledge-index-update` (16 files re-embedded) since `docs/` files changed, and
  `graphify update .` (AST-only, no topology changes detected) since `src/`/`tests/` changed.

**Citation correction applied per architecture-review note:** plan.md's Step 4 cites
`src/systems/social_systems/relationships.py:55-64` for the `_component()` helper — this is wrong;
`_component()` is actually defined in `src/core/builder.py:55-64`. Used the correct location; no design
change. Recorded in plan.md's new Deviations section.

No reproduction trigger logic, no genetics wiring, and no marriage/contract precondition was added
anywhere — verified both by direct source inspection and by the new architecture-guard test.

## Test Summary
All new and existing tests pass (venv: `/home/u24desktop/Working/venv/bin/python3`):
- `pytest tests/unit/progression/test_lifecycle.py -v` — 24 passed (16 pre-existing + 8 new: canonical-dict
  round-trip, update merge/is_noop, patch-apply-through-authoritative-path, builder two-parent case,
  builder parentless case, child-side bond seeding, parent-side reciprocal bond apply, marriage-precondition
  guard).
- `pytest tests/unit/social/test_social_bonds.py tests/unit/social/test_social_lifecycle.py tests/unit/social/test_social_party_regression.py -q` — 13 passed.
- `pytest tests/integration/optimization/test_component_patch_apply_parity.py tests/integration/optimization/test_apply_plan_parity.py tests/integration/optimization/test_phase_skip_parity.py -q` — 6 passed.
- `pytest tests/unit/domains/optimization/test_apply_plan_builder.py tests/unit/world/test_demographics.py tests/unit/world/test_spawn_cadence.py -q` — 77 passed.
No regressions in any pre-existing test.

## Files Changed
- `src/core/state.py` — `LifecycleComponent`: 5 new fields + `to_canonical_dict()` extension.
- `src/core/updates.py` — `LifecycleUpdate`: 5 new `*_set`/`_add` fields + `is_noop()`/`merge()` extension.
- `src/engine/patches.py` — `LifecyclePatch.apply()`: writes the 5 new fields through the authoritative path.
- `src/core/builder.py` — `V2EntityBuilder.lifecycle()` extended with 5 new kwargs; new `V2EntityBuilder.birth_record()` method; new module-level `build_parent_bond_updates_for_birth()` function; new top-level import of `EntityUpdate`/`SocialUpdate`/`SocialBondUpdate`.
- `tests/unit/progression/test_lifecycle.py` — 8 new tests + updated imports.
- `docs/core/entities.md` — Lifecycle component-table row updated with new field names and corrected line range.
- `docs/mechanics/01_entity_anatomy.md` — new "Birth Record (Reproduction Schema)" subsection.
- `docs/parity_ledger/social_narrative.yaml` — new entry `SOC-259`.
- `staging_artifacts/TCK-20260902-REPRODUCTION-BIRTH-RECORD-SCHEMA/plan.md` — added Deviations section (citation correction, test addition note).
- `tickets/inprogress/TCK-20260902-REPRODUCTION-BIRTH-RECORD-SCHEMA.md` — this file (Status, Acceptance Criteria, Implementation Notes, Test Summary, Files Changed, Completion Summary).

## Completion Summary
Implemented a durable birth-record schema — 5 new typed fields (`parent_a_entity_id`,
`parent_b_entity_id`, `birth_tick`, `birth_city_id`, `reproduction_cooldowns`) on
`LifecycleComponent`/`LifecycleUpdate`, wired through the sole authoritative write path
(`LifecyclePatch.apply`), plus a new `V2EntityBuilder.birth_record()` construction method and the
`build_parent_bond_updates_for_birth()` helper seeding `SocialBond`s at 0.8/0.8 familiarity/sentiment
between each parent and the new child. No marriage precondition was introduced anywhere, per the
explicit 2026-08-29 build-order decoupling constraint — verified both by direct source inspection and
by a dedicated architecture-guard test. Tests added: 8 new unit tests in
`tests/unit/progression/test_lifecycle.py` (canonical-dict round-trip, update merge/is_noop,
patch-apply-through-authoritative-path, builder two-parent case, builder parentless case, child-side
bond seeding, parent-side reciprocal bond apply, marriage-precondition guard); 447 total regression
tests passing across the lifecycle/social/apply-parity/demographics/core/rendering suites exercised
through Test/Parity/Verify, with no regressions. Files changed: `src/core/state.py`,
`src/core/updates.py`, `src/engine/patches.py`, `src/core/builder.py`,
`tests/unit/progression/test_lifecycle.py`, `docs/core/entities.md`,
`docs/mechanics/01_entity_anatomy.md`, `docs/parity_ledger/social_narrative.yaml` (new entry
`SOC-259`). Every reproduction-epic sibling ticket can now build on this schema. All gates
(Scope → Implement → Test → Parity → Verify → Finalize) passed.
