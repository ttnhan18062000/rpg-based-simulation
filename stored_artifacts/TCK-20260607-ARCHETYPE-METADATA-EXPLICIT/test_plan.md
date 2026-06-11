---
status: historical
layer: misc
authority: P2
audience: agent
ticket_id: TCK-20260607-ARCHETYPE-METADATA-EXPLICIT
artifact_type: test_plan
tags: [archetype, metadata, explicit]
---

# Test Plan — TCK-20260607-ARCHETYPE-METADATA-EXPLICIT

## Regression Surface

The following existing tests must continue to pass without modification:

| Test file | Class / function | What it guards |
|---|---|---|
| `tests/unit/content/test_resolvers.py::TestPopulationRecipeResolver::test_case2_direct_archetype_id_returns_single_entity` | Case 2 shorthand contract | `PopulationRecipeResolver.resolve("hungry_wolf")` returns `[(arch, 1)], []` |
| `tests/unit/content/test_resolvers.py::TestPopulationRecipeResolver::test_case1_valid_recipe_expands_members` | Case 1 recipe expansion | Recipe expansion still works |
| `tests/unit/content/test_resolvers.py::TestPopulationRecipeResolver::test_case3_unknown_id_raises_resolver_error` | Case 3 error | Unknown ID still raises `ResolverError` |
| `tests/unit/content/test_resolvers.py::TestPopulationRecipeResolver` (full class) | All 13 population resolver tests | No regression in resolver layer |
| `tests/unit/worldassembly/test_archetype_preservation.py::test_resolved_archetype_preserves_identity_metadata` | Archetype metadata flows to `CompileContext` | `entity.archetype_id == "goblin_raider"` etc. still holds after refactor |
| `tests/unit/worldassembly/test_archetype_preservation.py::test_population_preferred_region_validation_fails_on_missing_region` | Region validation | Unrelated to archetype_id; must remain green |
| `tests/unit/worldassembly/test_assembly.py` (all) | Full assembly pipeline | No regression from `PopulationSpec` field addition |
| `tests/unit/content/test_resolvers.py` (all 93 tests) | Full resolver layer | No resolver regression |

---

## New Tests Required

All new tests go in `tests/unit/content/test_resolvers.py` (continuing the Phase 25 class) and `tests/unit/worldassembly/test_archetype_preservation.py`.

### AC-1: `PopulationSpec` carries explicit `archetype_id`

**File:** `tests/unit/content/test_resolvers.py` — class `TestPopulationRecipeResolver`

```
test_case2_result_resolvedentityarchetype_has_archetype_id
```
- Call `pop_resolver.resolve("hungry_wolf")` (Case 2 shorthand).
- Assert `expanded[0][0].archetype_id == "hungry_wolf"` — the resolved archetype already carries the ID.
- This verifies the explicit archetype_id field is accessible on the returned object.

```
test_case1_recipe_members_each_have_archetype_id
```
- Call `pop_resolver.resolve("wolf_pack_small")` (Case 1 recipe).
- For each `(resolved_arch, count)` in expanded: assert `resolved_arch.archetype_id` is a non-empty string that matches a known archetype catalog ID.
- Confirms every archetype coming out of recipe expansion carries an explicit identity.

### AC-2: `PopulationRecipeResolver` no longer infers archetype ID from string suffix

**File:** `tests/unit/content/test_resolvers.py` — new class `TestPopulationSpecArchetypeId`

```
test_population_spec_archetype_id_field_exists
```
- Construct a `PopulationSpec` with `archetype_id="hungry_wolf"` (and all required fields).
- Assert `pop_spec.archetype_id == "hungry_wolf"`.
- Assert the field is accessible without error (validates that `PopulationSpec` now declares the field).

```
test_population_spec_archetype_id_defaults_to_none
```
- Construct a `PopulationSpec` without supplying `archetype_id`.
- Assert `pop_spec.archetype_id is None` (backward-compatible default).

```
test_population_spec_is_still_frozen_after_field_addition
```
- Construct a `PopulationSpec` with `archetype_id="hungry_wolf"`.
- Attempt to assign `pop_spec.archetype_id = "other"`.
- Assert this raises an exception (frozen model invariant preserved).

### AC-3: Archetype ID round-trip through expand → `PopulationSpec`

**File:** `tests/unit/worldassembly/test_archetype_preservation.py`

```
test_archetype_id_survives_resolve_module_contribution
```
- Create a minimal `NormalizedWorldModule` that uses `populations=["wolf_pack_small"]` with a module region `"wolf_den"`.
- Call `resolver.resolve_module_contribution(normalized_spec)`.
- For each `pop_spec` in `contribution.resolved_population_specs`:
  - Assert `pop_spec.archetype_id` is not `None`.
  - Assert `pop_spec.archetype_id` is a known key in `cat.entity_archetypes`.
- This is the canonical round-trip test: explicit `archetype_id` is set at construction time and readable on the `PopulationSpec`.

```
test_archetype_id_carried_into_compile_context_without_string_inference
```
- Assemble `goblin_camp_conflict` module as in the existing preservation test.
- For each entity in `bundle.compile_context.entities` where `entity.archetype_id is not None`:
  - Assert `entity.archetype_id` equals the known archetype (e.g., `"goblin_raider"`).
  - Assert this value does NOT depend on string suffix parsing — verified by checking that an archetype whose ID is a substring of another archetype's ID still resolves correctly (no ambiguity).

### AC-4: Updated Case 2 docstring (non-test)

The Case 2 docstring in `src/content/resolver.py` already states:
> "Case 2: shorthand — treat population_id as a direct archetype ID (count=1, no regions)."

After this ticket, add a note: "The returned `ResolvedEntityArchetype.archetype_id` carries the explicit identity; callers must not re-derive it by splitting the population ID string."

No test required for the docstring itself.

### AC-5: All existing resolver tests pass (regression)

```
pytest tests/unit/content/test_resolvers.py -q
```
All 93+ tests must pass. Verify this includes the three-case contract tests that guard TOWN-170.

---

## Anti-Drift Test Guards

These guard against regressions introduced by future ID format changes or field removals.

```
test_population_spec_archetype_id_is_not_inferred_from_id_string
```
**File:** `tests/unit/worldassembly/test_archetype_preservation.py`

- Construct two `PopulationSpec` instances:
  - `PopulationSpec(id="module_prefix_wolf_pack_small_hungry_wolf", archetype_id="hungry_wolf", ...)`
  - `PopulationSpec(id="module_prefix_wolf_pack_small_hungry_wolf", archetype_id=None, ...)`
- Assert that reading `.archetype_id` on the first returns `"hungry_wolf"` — not derived from `.id`.
- Assert that reading `.archetype_id` on the second returns `None` — not inferred from the string.
- This guard fails if any code path re-introduces string inference logic.

```
test_resolve_module_contribution_does_not_use_split_for_archetype_id
```
**File:** `tests/unit/worldassembly/test_archetype_preservation.py`

- Assemble a module whose population recipe ID contains an underscore (`wolf_pack_small`) and whose archetype IDs also contain underscores (`hungry_wolf`).
- After assembly, verify every entity in `compile_context.entities` with a non-None `archetype_id` has an `archetype_id` that exists in `cat.entity_archetypes` — not a truncated fragment or split artifact.
- Rationale: if split-based inference is reintroduced, edge cases like `wolf_pack_small_hungry_wolf` splitting on `wolf_pack_small_` gives `hungry_wolf` (correct), but splitting `alpha_wolf` from a recipe named `wolf` gives `alpha_wolf` split on `wolf_` gives `alpha_wolf` (incorrect) — the guard catches such ambiguities.

---

## Scoped Pytest Commands

```bash
# Core resolver layer — must always be run before claiming done
pytest tests/unit/content/test_resolvers.py -q

# Archetype preservation and assembly integration
pytest tests/unit/worldassembly/test_archetype_preservation.py -q

# Full worldassembly unit suite
pytest tests/unit/worldassembly/ -q

# Combined scope (standard run for this ticket)
pytest tests/unit/content/test_resolvers.py tests/unit/worldassembly/ -q

# Exclude slow tests if needed
pytest tests/unit/content/test_resolvers.py tests/unit/worldassembly/ -q -m "not slow"
```

Do NOT run `pytest tests/` — scope to the domain under modification only.
