---
status: historical
layer: world
authority: P2
audience: agent
ticket_id: TCK-20260831-SPECIES-INTELLIGENCE-TIER
artifact_type: test_plan
tags: [content]
---

# Test Plan — TCK-20260831-SPECIES-INTELLIGENCE-TIER

## Regression Surface

Existing tests that must keep passing (unit only — this is a pure content-schema/data change with
zero engine/resolver wiring, so there is no integration or arena-combat surface to protect):

**unit — schema (`tests/unit/content/test_catalog.py`)**
- `test_base_catalog_loading` — full real catalog, including `data/content/living/races.yaml`,
  still loads end to end.
- `test_schema_fail_closed_unknown_field` — `extra="forbid"` fail-closed behavior on
  `CatalogBaseDefinition` subclasses must be unaffected by the new field.
- `test_schema_metadata_nested_field_allowed` — unrelated but same module, cheap to keep green.
- `test_faction_definition_hazard_immunities_field`,
  `test_faction_catalog_loads_with_hazard_immunities_authored` — nearest precedent pattern for a
  new `CatalogBaseDefinition`-family field; must still pass unmodified (different schema class,
  proves the pattern this ticket's new tests follow is not itself broken).
- `test_schema_compatibility_model_fail_closed` — same fail-closed family.

**unit — layered catalog (`tests/unit/content/test_layered_catalog.py`)**
- `test_layered_catalog_validation_errors`
- `test_phase23_reference_graph_and_dead_active_data`
- `test_graph_module_count_maps_and_metadata`

**unit — resolvers (`tests/unit/content/test_resolvers.py::TestLivingDefaultsResolver`)**
- All race-defaults propagation tests, in particular the ones that read real race data by exact
  value and would silently mask a corrupted `races.yaml` edit:
  - `test_resolve_wolf_need_profile_from_race`
  - `test_resolve_wolf_sense_profile_from_race`
  - The `natural_traits`-order test (line ~284: "Natural traits must be returned in the same order
    as declared in the race definition") and `test_resolve_wolf_race_traits_appended_if_not_in_archetype`
    (line ~526) — these read `natural_traits` list contents/order directly; adding a new sibling
    field (`intelligence_tier`) to `RaceDefinition` must not perturb `natural_traits` ordering or
    content for any race, especially wolf (used as the explicit fixture race here).
  - The `compatible_roles`-order test (line ~309) — same rationale, different list field.
  - `test_resolve_missing_race_raises` — race lookup failure path unaffected.
  - `test_resolve_village_worker_need_profile_from_human_race` — human-race fixture path.

**unit — content usage matrix (`tests/unit/content/test_content_usage_matrix.py`)**
- `test_matrix_exists_and_can_be_imported`, `test_matrix_validation_and_states` — confirms this
  ticket genuinely requires no `src/content/matrix.py` change (see investigation.md "Docs Requiring
  Update"); these should pass unmodified as evidence the family-level matrix entry didn't need
  touching.

## New Tests Required

1. **`test_race_definition_intelligence_tier_field_round_trips`**
   - Category: unit (schema)
   - Verifies: `RaceDefinition` accepts `intelligence_tier="high"` and `intelligence_tier="low"`
     and round-trips the value; rejects an invalid value (e.g. `"medium"`) with a `ValidationError`
     if Plan specifies field-level validation (mirrors `test_faction_definition_hazard_immunities_field`'s
     shape, adjusted since `intelligence_tier` is a required field with no safe default rather than
     an optional list — construct two `RaceDefinition` instances directly with the minimum required
     sibling fields, one `high` one `low`, and assert `.intelligence_tier` reads back correctly. If
     Plan makes the field required with no default, also assert that omitting it raises
     `ValidationError` — this is the primary regression guard against a future 14th race silently
     passing validation without an authored value).
   - Location: `tests/unit/content/test_catalog.py` (co-located with the other
     `RaceDefinition`/schema field-addition tests, same file as the `hazard_immunities` precedent).

2. **`test_all_13_races_have_documented_intelligence_tier`** (the core acceptance-criteria test)
   - Category: unit (schema + real-data regression)
   - Verifies: loads the real catalog (`CatalogRepository("data/content").load_all()`), iterates
     `repo.races`, and asserts `race.intelligence_tier` for every one of the 13 races matches an
     explicit, hardcoded expected-value table encoding the documented anchor rule with the
     dragonkin/spirit exceptions Plan justifies. Suggested table shape (values TBD from Plan's
     dragonkin/spirit decision — everything else is fixed by this investigation's confirmed data):

     ```python
     EXPECTED_INTELLIGENCE_TIER = {
         "human": "high", "goblin": "high", "orc": "high",
         "elf": "high", "dwarf": "high", "lizardfolk": "high",
         "wolf": "low", "spider": "low", "undead": "low",
         "troll": "low", "slime": "low",
         "dragonkin": "<Plan's decision>", "spirit": "<Plan's decision>",
     }
     ```
   - Also assert `set(EXPECTED_INTELLIGENCE_TIER) == set(repo.races)` (or equivalent) so the test
     fails loudly — not silently skips — if a 14th race is ever added without updating this test,
     rather than only checking the races currently known.
   - Also assert, for the 6 races with `tool_user` in `natural_traits`, `intelligence_tier == "high"`,
     and for the races without it (excluding whichever of dragonkin/spirit Plan classifies as an
     exception), `intelligence_tier == "low"` — i.e. encode the anchor *rule*, not just a flat
     lookup table, so the test documents the rule's shape and would catch a future race's authored
     `intelligence_tier` silently drifting from its own `tool_user` status without an explicit,
     equally-documented exception.
   - Location: `tests/unit/content/test_catalog.py`, alongside
     `test_faction_catalog_loads_with_hazard_immunities_authored` (same "load the real catalog and
     assert real authored values" pattern).

3. **`test_race_catalog_loads_with_intelligence_tier_authored`**
   - Category: unit (integration-with-real-data, schema-adjacent)
   - Verifies: the full real `data/content` catalog loads without error after `intelligence_tier`
     is added to every race in `races.yaml` — catches a YAML authoring typo (e.g. a 14th value
     outside `{"high","low"}`, or a missing field on one race if it's required) that a narrower
     per-field unit test might miss because the base catalog load already succeeds without the new
     field present in test fixtures.
   - Location: `tests/unit/content/test_catalog.py` (can likely be folded into test #2 above rather
     than kept fully separate, since both load the real catalog — Plan/Implement's call whether to
     merge them, listed separately here since the AC explicitly asks for "a regression test", not
     necessarily a single test function).

## Scoped Pytest Commands

```
pytest tests/unit/content/ -v
```

Rationale: this is the narrowest directory that contains every regression-surface file listed above
(`test_catalog.py`, `test_layered_catalog.py`, `test_resolvers.py`, `test_content_usage_matrix.py`)
plus wherever the new tests land. No other domain (combat, strategy, economy, worldassembly) reads
`RaceDefinition.intelligence_tier` today, so there is no reason to widen beyond `tests/unit/content/`.

If Implement adds a stub consumer/predicate per the ticket's Assumptions (still an open decision —
see investigation.md), re-scope to also include whatever module hosts that predicate's own tests at
that time; do not preemptively widen the command now for a decision not yet made.

Never: `pytest tests/` (repo-wide) or `pytest tests/unit/` (still far wider than the affected
surface).

## Anti-Drift Test Guards

- **The `natural_traits`/`compatible_roles`-order tests in `test_resolvers.py` (see Regression
  Surface above) are the guard against accidentally reordering or corrupting existing list fields
  while adding the new `intelligence_tier` field to the same YAML records.** If Implement appends
  `intelligence_tier` as a new YAML key per race, these tests catch any accidental YAML-list
  reordering side effect from a careless bulk edit.
- **`test_schema_fail_closed_unknown_field` and `test_schema_compatibility_model_fail_closed`** are
  the guard against silently degrading `extra="forbid"` on `CatalogBaseDefinition` while touching
  `schema.py` for an unrelated reason.
- **`test_matrix_validation_and_states`** is the guard against an unnecessary/accidental edit to
  `src/content/matrix.py` sneaking in — per investigation.md, no matrix change is needed; if this
  test's assertions about `living/races`'s entry ever need to change, that is a signal scope has
  quietly expanded beyond this ticket's stated boundary.
- **The AC's explicit exclusion of `settlement_capacity`** has no direct test surface (it doesn't
  exist yet), so the anti-drift guard here is procedural, not automated: `test_all_13_races_have_documented_intelligence_tier`
  should assert only on `intelligence_tier`, and any diff touching `settlement_capacity` in the same
  PR is out of scope per the ticket and should be flagged at review, not merged.
