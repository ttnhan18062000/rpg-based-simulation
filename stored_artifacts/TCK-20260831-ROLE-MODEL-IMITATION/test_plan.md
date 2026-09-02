---
status: historical
layer: strategy
authority: P2
audience: agent
ticket_id: TCK-20260831-ROLE-MODEL-IMITATION
artifact_type: test_plan
tags: [strategy, cognition]
---

# Test Plan — TCK-20260831-ROLE-MODEL-IMITATION

## Regression Surface

**Unit — `CognitionModel` schema (must keep passing unmodified in behavior, only extended in
shape):**
- `tests/unit/entity/test_phase11_cognition_model_schema.py` — all 6 tests, in particular
  `test_entity_state_has_default_cognition_model`, `test_cognition_model_serializes_deterministically`,
  `test_subjective_model_has_no_self_field`, `test_cognition_canonical_dict_shape_after_self_model_decision`
  (guards the `DEAD-COGNITION-SCHEMA-DECISION` cut this ticket's file-neighbor change must not
  reopen).
- `tests/unit/entity/test_phase2_self_model_components.py` — full file; confirms `SelfModelBundle`
  stays untouched (this ticket must not accidentally nest the new state there instead of under
  `CognitionModel`).

**Unit — `cognition_capacity.py` (must keep passing unmodified if Plan chooses the
separate-service fork; must still pass with the same assertions if Plan extends
`CapacityService.derive_profile` itself):**
- `tests/unit/strategic/test_cognition_capacity.py` — `test_base_profile_derivation`,
  `test_high_intelligence_scaling`, `test_fatigue_penalty`, `test_determinism`.

**Integration — cognition hierarchy / apply pipeline (confirms the wholesale
`cognition_bundle_set` passthrough this ticket relies on is not broken by adding a new
sub-component):**
- `tests/integration/scenarios/test_phase18_cognition_hierarchy_e2e.py`

**Content — `intelligence_tier` (must keep passing unmodified; this ticket is read-only on the
field per Out of Scope):**
- `tests/unit/content/test_catalog.py::test_race_definition_intelligence_tier_field_round_trips`
- `tests/unit/content/test_catalog.py::test_all_13_races_have_documented_intelligence_tier`
- `tests/unit/content/test_catalog.py::test_race_catalog_loads_with_intelligence_tier_authored`

**Adjacent — idea 22 (`RelationshipRole`) must stay fully independent (anti-drift guard already
exists, must keep passing to prove this ticket didn't couple the two systems):**
- Idea 22's own non-overlap guard test (per `stored_artifacts/TCK-20260824-RELATIONSHIP-ROLE-FIELD/test_plan.md`:
  `set(RelationshipRole) & set(PartyRole) == set()`-style test) — locate via
  `grep -rl RelationshipRole tests/` and include whichever file currently holds
  `SocialBond`/`RelationshipRole` unit tests (likely `tests/unit/core/test_social*.py` or similar —
  confirm exact path at Test-phase time since it was not read directly in this investigation).

## New Tests Required

Per AC #2 (typed role-model/imitation state, defined lifecycle, round-trip tested):
- **Test name**: `test_entity_state_cognition_has_role_model_subcomponent` (or matching Plan's
  chosen class/field name)
  **Category**: unit (schema)
  **Verifies**: `EntityState().cognition` exposes the new sub-component with safe empty defaults
  via `isinstance` checks, matching the existing `test_entity_state_has_default_cognition_model`
  pattern.
  **Where**: `tests/unit/entity/test_phase11_cognition_model_schema.py` (extend in place — this is
  the established home for `CognitionModel` sub-component schema tests) or a new sibling file if
  Plan judges the addition large enough to warrant one.

- **Test name**: `test_role_model_state_canonical_dict_deterministic`
  **Category**: unit (schema / determinism)
  **Verifies**: two independently-constructed instances of the new sub-component (and of
  `CognitionModel` as a whole with it populated) produce identical `to_canonical_dict()` output —
  the established "round trip" proxy for this codebase's frozen-dataclass state (see
  `test_cognition_model_serializes_deterministically` precedent). Must also assert the new
  sub-component's dict keys appear inside `CognitionModel.to_canonical_dict()`'s top-level output
  (shape-presence guard, mirroring `test_cognition_canonical_dict_shape_after_self_model_decision`).
  **Where**: `tests/unit/entity/test_phase11_cognition_model_schema.py`.

- **Test name**: `test_role_model_lifecycle_add_and_clear` (exact name depends on Plan's chosen
  lifecycle verbs — watch/admire, stop-watching, role-model-replaced, etc.)
  **Category**: unit (behavior)
  **Verifies**: the defined lifecycle operations (set a role model, change it, clear it) produce
  correct immutable-update results via `dataclasses.replace()`-style reconstruction, matching the
  `test_committed_intention_model.py` precedent for capacity-cap/lifecycle-style tests on a
  `CognitionModel`-adjacent structure.
  **Where**: new test module, e.g. `tests/unit/strategic/test_role_model_state.py` or nested under
  `tests/unit/entity/` alongside the schema test, per Plan's file-organization call.

- **Test name**: `test_cognition_bundle_set_apply_round_trip_includes_role_model`
  **Category**: integration (apply pipeline)
  **Verifies**: an `EntityUpdate` with `cognition_bundle_set` carrying a `CognitionModel` whose new
  sub-component is populated survives `ApplyPath._apply_entity_update`/`apply_generation` end to
  end — i.e. the new sub-component is present, unmodified, on the resulting `EntityState.cognition`
  after going through `CognitionPatch.apply()` → `_fast_replace_entity()`. This is the concrete
  proof (not just an assumption) that nesting under `CognitionModel` avoids a 5th
  `apply.py`-reconstruction silent-drop instance for this specific new field.
  **Where**: `tests/integration/scenarios/test_phase18_cognition_hierarchy_e2e.py` (extend) or a
  new scenario test if Plan judges the existing file too large/unrelated in scope.

Per AC #3 (imitation-sophistication scaling reads `intelligence_tier`):
- **Test name**: `test_imitation_scaling_reads_intelligence_tier_high_vs_low`
  **Category**: unit (behavior)
  **Verifies**: two otherwise-identical entities differing only in resolved race
  (`identity.properties["race_id"]` pointing at a `RaceDefinition` with `intelligence_tier="high"`
  vs `"low"`) produce different (and correctly ordered — high >= low) imitation-sophistication
  output from whichever function/service Plan designates as the integration point. Must construct
  entities via `V2EntityBuilder` (established pattern from `test_cognition_capacity.py`) with a
  `CatalogRepository`/race fixture, following the `get_race_id_str` → `CatalogRepository.get_race`
  path confirmed live in investigation.md.
  **Where**: `tests/unit/strategic/test_cognition_capacity.py` (if Plan extends `CapacityService`)
  or a new `tests/unit/strategic/test_imitation_service.py` (if Plan chooses the separate-service
  fork) — file choice depends on Plan's design decision, flagged as open in investigation.md.

- **Test name**: `test_imitation_scaling_missing_race_or_tier_fails_safe`
  **Category**: unit (edge case / failure mode)
  **Verifies**: an entity with no `race_id` in `identity.properties`, or a `race_id` that does not
  resolve via `CatalogRepository.get_race()`, does not crash the scaling logic — either a documented
  default tier is applied or the function returns a safe no-op value. This is a real edge case since
  `IdentityComponent.properties` is a free-form dict with no guarantee `race_id` is ever set (e.g.
  for non-race-bearing `kind`s like resource nodes if this logic were ever misapplied — though
  scoped to hero/NPC entities in practice).
  **Where**: same file as the previous test.

Per AC #4 (stub/defer path, if ever taken):
- **Test name**: `test_imitation_scaling_stub_documented_when_tier_unavailable` — **only required
  if Plan/Implement actually takes the stub/defer branch**; per investigation.md,
  `TCK-20260831-SPECIES-INTELLIGENCE-TIER` is already confirmed landed, so this branch is not
  expected to be exercised. Skip this test entirely if the dependency is present at implementation
  time (confirm via `tests/unit/content/test_catalog.py::test_all_13_races_have_documented_intelligence_tier`
  passing) — do not write a stub-path test for a stub that was never built.

## Scoped Pytest Commands

```
pytest tests/unit/entity/test_phase11_cognition_model_schema.py tests/unit/entity/test_phase2_self_model_components.py -v
pytest tests/unit/strategic/ -v
pytest tests/unit/content/test_catalog.py -v
pytest tests/integration/scenarios/test_phase18_cognition_hierarchy_e2e.py -v
```

Do not run `pytest tests/` or any unscoped full-suite invocation. If Plan's chosen implementation
touches `src/engine/apply.py`, `src/engine/patches.py`, or `src/core/updates.py` directly (expected
NOT to happen per investigation.md's confirmation that the passthrough needs no changes), add:

```
pytest tests/unit/engine/ -k "apply or patch" -v
```

as an additional regression guard before Verify.

## Anti-Drift Test Guards

- **`RelationshipRole`/`PartyRole` non-overlap guard** (idea 22's existing test, located via
  `grep -rl RelationshipRole tests/`) must keep passing unmodified — proves this ticket did not
  extend or couple into the `SocialBond.role` enum despite the optional pairing suggestion.
- **`test_subjective_model_has_no_self_field` / `test_cognition_canonical_dict_shape_after_self_model_decision`**
  (`tests/unit/entity/test_phase11_cognition_model_schema.py`) must keep passing unmodified —
  proves this ticket's new sibling sub-component did not reintroduce the cut `SubjectiveModel.self`
  field or otherwise regress the `DEAD-COGNITION-SCHEMA-DECISION` cleanup.
- **`intelligence_tier` read-only guard**: before Verify, confirm no diff touches
  `src/content/schema.py`'s `RaceDefinition` class or `data/content/living/races.yaml` (a simple
  `git diff --stat` check is sufficient) — per Out of Scope this ticket is read-only on that field.
- **`CapacityService.derive_profile` signature/return-shape guard**: if Plan chooses the
  separate-service fork (not extending `CapacityService` itself), add a explicit regression
  assertion that `CognitionProfile`'s field count/names are unchanged
  (`{f.name for f in dataclasses.fields(CognitionProfile)}` equality against the known 11-field set
  from investigation.md) — catches accidental scope creep into the wrong "cognition" concept (see
  investigation.md's four-distinct-"cognition"-concepts hazard).
- **`cognition_bundle_set` merge-collision guard** (new, motivated by the `EntityUpdate.merge()`
  risk found in investigation.md): a targeted unit test constructing two `EntityUpdate`s for the
  same entity, each setting `cognition_bundle_set` from a stale/divergent base snapshot, then
  calling `.merge()`, asserting which one wins is the documented (last-write-wins) behavior rather
  than an unverified assumption — this doesn't have to be new production code, but should exist as
  a regression-locking test so a future change to `EntityUpdate.merge()` can't silently alter this
  ticket's correctness assumptions without a test failing first.
