---
status: historical
layer: misc
authority: P2
audience: agent
ticket_id: TCK-20260607-ARCHETYPE-METADATA-EXPLICIT
artifact_type: plan
tags: [archetype, metadata, explicit]
---

# Implementation Plan — TCK-20260607-ARCHETYPE-METADATA-EXPLICIT

## Summary

Add `archetype_id: Optional[str] = None` to `PopulationSpec`, populate it at the one
construction site in `resolve_module_contribution`, then replace the two downstream
string-suffix inference sites with direct field reads — no schema reshaping, no return-type
changes, and no new abstraction layers.

---

## Steps

### Step 1 — Add `archetype_id` field to `PopulationSpec`

**File:** `src/worldbuilding/schema.py`

**Change:**
Insert after line 58 (after `spawn_region` field, before the blank line that ends the class):

```python
archetype_id: Optional[str] = Field(
    default=None,
    description="Archetype that originated this population entry; set at assembly time, never inferred from the id string."
)
```

Add `Optional` to the import at the top of the file if not already present (it is already
imported via `from typing import ...`; verify before touching).

**Do NOT touch:**
- `model_config = ConfigDict(frozen=True)` — must remain unchanged.
- Any other field on `PopulationSpec`.
- `RecipeSpec`, `WorldSpec`, or any other schema class in the same file.
- YAML world spec files under `data/` — `Optional[str] = None` default means they silently
  default and no YAML change is needed.

**Verify:**
```python
from src.worldbuilding.schema import PopulationSpec
p = PopulationSpec(id="x", count=1, role="r", faction="f", spawn_region="s")
assert p.archetype_id is None
p2 = PopulationSpec(id="x", count=1, role="r", faction="f", spawn_region="s", archetype_id="hungry_wolf")
assert p2.archetype_id == "hungry_wolf"
```

---

### Step 2 — Populate `archetype_id` at construction in `resolve_module_contribution`

**File:** `src/worldassembly/resolver.py`

**Function:** `resolve_module_contribution` (v2 populations path, around line 754–761)

**Change:**
Add `archetype_id=resolved_arch.archetype_id` to the `PopulationSpec(...)` constructor call:

```python
pop_key = f"{p_id}_{resolved_arch.archetype_id}"
resolved_population_specs.append(PopulationSpec(
    id=f"{prefix}{pop_key}",
    count=count,
    role=resolved_arch.role_id,
    faction=resolved_arch.faction_id,
    spawn_region=spawn_region,
    archetype_id=resolved_arch.archetype_id,   # ← add this line
))
```

**Do NOT touch:**
- The `pop_key` format string — it continues to serve ID uniqueness only.
- Any other `PopulationSpec(...)` construction site (line 89 validator dummy — no archetype
  is available there; leave `archetype_id` absent so it defaults to `None`).
- The v1 population recipes path (lines ~407–413) — no archetype resolution happens there;
  leave untouched.
- `ResolvedModuleContribution` schema in `src/worldassembly/schema.py` — no change needed
  because `resolved_population_specs: List[PopulationSpec]` already carries the new field.

**Verify:**
After Step 2, running the existing archetype-preservation test
`test_resolved_archetype_preserves_identity_metadata` should still pass. A `PopulationSpec`
coming out of `resolve_module_contribution` must now have a non-None `archetype_id`.

---

### Step 3 — Replace Site 1 string-suffix inference in `_merge_module_contributions`

**File:** `src/worldassembly/resolver.py`

**Function:** `_merge_module_contributions`, around lines 334–348

**Change:**
Replace the provenance-determination block that uses `pop.id.split(pr + "_")[-1]` with a
direct field read:

```python
# Provenance: archetype_id is now an explicit field on PopulationSpec
archetype_id = pop.archetype_id
pop_recipe_id = None
if archetype_id:
    for pr in contribution.population_refs:
        if pr in pop.id:
            pop_recipe_id = pr
            break

resolved_arch = None
if archetype_id:
    try:
        resolved_arch = self.population_recipe_resolver._archetype_resolver.resolve(archetype_id)
    except Exception:
        pass
```

The block below (which uses `resolved_arch` to build provenance metadata) is unchanged.

**Do NOT touch:**
- The `entities[pop.id] = pop` assignment above the replaced block.
- The downstream code that consumes `resolved_arch` and `pop_recipe_id`.
- Any other function in `resolver.py`.

**Verify:**
`archetype_id = pop.archetype_id` replaces the `split` line. The `for pr` loop now
only derives `pop_recipe_id`, not `archetype_id`. After this step, Site 1 performs zero
string splitting for archetype identity.

---

### Step 4 — Replace Site 2 string-suffix inference in `_build_compile_context`

**File:** `src/worldassembly/resolver.py`

**Function:** `_build_compile_context`, around lines 900–917

**Change:**
Replace the O(archetypes) scan that uses `key.endswith(f"_{arch_key}")` with a direct
field read:

```python
# Archetype_id is now explicit on PopulationSpec — no string scan needed
archetype_id = pop_spec.archetype_id

resolved_arch = None
if archetype_id:
    try:
        from src.content.resolver import EntityArchetypeResolver
        arch_resolver = EntityArchetypeResolver(self.repo)
        resolved_arch = arch_resolver.resolve(archetype_id)
    except Exception:
        pass
```

Remove the entire `if "_" in key: for arch_key in self.repo.entity_archetypes: ...` block.
The variable `archetype_id` is now set from `pop_spec.archetype_id` directly.

**Do NOT touch:**
- The `ResolvedEntityProfile(...)` constructor call that consumes `resolved_arch` — it is
  unchanged.
- Any function outside `_build_compile_context`.
- The `EntityArchetypeResolver` import pattern (keep as-is, just move the assignment).

**Verify:**
`_build_compile_context` no longer iterates `self.repo.entity_archetypes` for every entity.
The existing test `test_resolved_archetype_preserves_identity_metadata` must still produce
`entity.archetype_id == "goblin_raider"` etc.

---

### Step 5 — Update Case 2 docstring in `PopulationRecipeResolver.resolve`

**File:** `src/content/resolver.py`

**Function:** `PopulationRecipeResolver.resolve`, around line 580

**Change:**
Extend the inline comment on the Case 2 branch:

```python
# Case 2: shorthand — treat population_id as a direct archetype ID (count=1, no regions).
# The returned ResolvedEntityArchetype.archetype_id carries the explicit identity;
# callers must not re-derive it by splitting the population ID string.
```

**Do NOT touch:**
- The Case 2 logic itself (`self._repo.get_entity_archetype` / `_archetype_resolver.resolve`
  / `return [(resolved_arch, 1)], []`).
- Case 1 or Case 3 branches.
- The function signature or return type annotation.

**Verify:**
Code is textually updated; no behavioral change. TOWN-170 parity test still passes.

---

### Step 6 — Update parity ledger entry TOWN-170

**File:** `docs/parity_ledger/town_resource.yaml`

**Entry:** `id: TOWN-170` (line 1766)

**Change:**
Append to `v2_evidence` to note the explicit field:

```yaml
v2_evidence: >-
  src/content/resolver.py PopulationRecipeResolver.resolve() — case 2 fallback validated
  against entity_archetypes catalog before returning shorthand result; case 3 raises
  ResolverError. As of TCK-20260607-ARCHETYPE-METADATA-EXPLICIT, the returned
  ResolvedEntityArchetype.archetype_id is the authoritative identity; downstream callers
  read PopulationSpec.archetype_id directly instead of inferring from string suffix.
```

Leave `status: verified`, `test_path`, and all other fields unchanged.

**Do NOT touch:**
- Any other parity ledger entry.
- `substrate.yaml`, `infrastructure.yaml`, `combat_movement.yaml`, or any other parity file.

**Verify:**
`grep "TOWN-170" docs/parity_ledger/town_resource.yaml` shows the updated `v2_evidence`.
YAML remains parseable.

---

### Step 7 — Write new tests: `PopulationSpec` field contract

**File:** `tests/unit/content/test_resolvers.py`

**New class:** `TestPopulationSpecArchetypeId`

**Tests to add (in order):**

1. `test_population_spec_archetype_id_field_exists` — construct with explicit `archetype_id`;
   assert value is readable and correct.
2. `test_population_spec_archetype_id_defaults_to_none` — construct without supplying
   `archetype_id`; assert `None`.
3. `test_population_spec_is_still_frozen_after_field_addition` — attempt mutation; assert
   raises (validates `frozen=True` invariant).
4. `test_case2_result_resolvedentityarchetype_has_archetype_id` — call
   `pop_resolver.resolve("hungry_wolf")` (Case 2); assert `expanded[0][0].archetype_id ==
   "hungry_wolf"`. (This verifies the archetype object from the resolver already carries it.)
5. `test_case1_recipe_members_each_have_archetype_id` — call `pop_resolver.resolve` for a
   Case 1 recipe; for each `(arch, _)` assert `arch.archetype_id` is a non-empty string
   present in the archetype catalog.

**Do NOT touch:**
- Any existing test class or test function in `test_resolvers.py`.
- `TestPopulationRecipeResolver` — all 13 existing tests must stay exactly as written.

**Verify:**
```bash
pytest tests/unit/content/test_resolvers.py::TestPopulationSpecArchetypeId -q
```
All 5 new tests pass.

---

### Step 8 — Write new tests: assembly round-trip and anti-drift guards

**File:** `tests/unit/worldassembly/test_archetype_preservation.py`

**New tests to add:**

1. `test_archetype_id_survives_resolve_module_contribution` — assemble a minimal module
   with `populations=["wolf_pack_small"]`; for each `pop_spec` in
   `contribution.resolved_population_specs`, assert `pop_spec.archetype_id` is not `None`
   and exists in `cat.entity_archetypes`.
2. `test_archetype_id_carried_into_compile_context_without_string_inference` — assemble
   `goblin_camp_conflict`; for each entity with non-None `archetype_id` in
   `bundle.compile_context.entities`, assert the value equals the known archetype string
   (e.g., `"goblin_raider"`).
3. `test_population_spec_archetype_id_is_not_inferred_from_id_string` — construct two
   `PopulationSpec` instances with the same `id` string but different `archetype_id` values
   (`"hungry_wolf"` vs `None`); assert `.archetype_id` returns the explicit field, not a
   derived value.
4. `test_resolve_module_contribution_does_not_use_split_for_archetype_id` — assemble a
   module whose recipe ID and archetype IDs both contain underscores; after assembly, verify
   every entity with non-None `archetype_id` exists verbatim in `cat.entity_archetypes`
   (catches truncated-split regressions).

**Do NOT touch:**
- Existing tests in `test_archetype_preservation.py` — they must remain green.
- Any test in `test_assembly.py`.

**Verify:**
```bash
pytest tests/unit/worldassembly/test_archetype_preservation.py -q
```
All new tests pass; existing tests remain green.

---

### Step 9 — Full scoped regression run

**Command:**
```bash
pytest tests/unit/content/test_resolvers.py tests/unit/worldassembly/ -q -m "not slow"
```

**What to assert:**
- All 93+ existing `test_resolvers.py` tests pass (TOWN-170 guard included).
- All existing `test_archetype_preservation.py` tests pass.
- All new tests (Steps 7–8) pass.
- Zero failures, zero errors.

**Do NOT run:**
- `pytest tests/` (full suite) — out of scope per Testing Rule.

---

## Scope Guards

| Category | Explicitly excluded |
|---|---|
| Schema reshaping | Do not introduce `ExpandedPopulationMember` dataclass |
| Return type change | `PopulationRecipeResolver.resolve()` return type stays `List[Tuple[ResolvedEntityArchetype, int]]` |
| YAML authoring | No changes to any YAML world spec files under `data/` |
| Other schema models | `RecipeSpec`, `WorldSpec`, `ResourceNodeSpec`, `BuildingSpec` — untouched |
| v1 population path | Lines ~407–413 in `resolver.py` — no archetype resolution there; leave as-is |
| Validator dummy spec | Line 89 `PopulationSpec(id=f"pop_{idx}", ...)` — no archetype available; leave `archetype_id` absent |
| Other parity entries | Only TOWN-170 is updated |
| `pop_key` format string | Unchanged — still `f"{p_id}_{resolved_arch.archetype_id}"`; string is for ID uniqueness only |
| 3-case contract | Case 1, 2, 3 logic in `PopulationRecipeResolver.resolve()` — not changed |

---

## Dependency Map

```
Step 1  (add field to PopulationSpec)
  └─► Step 2  (populate at construction — requires the field to exist)
        └─► Step 3  (Site 1 reads pop.archetype_id — requires Step 2 to populate it)
        └─► Step 4  (Site 2 reads pop_spec.archetype_id — requires Step 2 to populate it)
              └─► Step 5  (docstring — no code dep, but logically after Steps 3–4)
                    └─► Step 6  (parity ledger — describes the completed change)
                          └─► Step 7  (new tests — require Steps 1–2 to be in place)
                                └─► Step 8  (assembly round-trip tests — require Steps 2–4)
                                      └─► Step 9  (full regression — requires all steps)
```

Steps 3 and 4 are independent of each other (can be done in either order after Step 2).
Step 5 and Step 6 are independent of each other (both depend only on Steps 3–4 being done).
Steps 7 and 8 are independent of each other (both depend on Steps 1–4).

---

## Acceptance Criteria Map

| AC | Steps that satisfy it |
|---|---|
| `PopulationSpec` carries explicit `archetype_id` | Step 1 (field added), Step 2 (populated at construction) |
| `PopulationRecipeResolver` no longer infers from string suffix | Steps 3 and 4 (both inference sites replaced) |
| Updated Case 2 docstring | Step 5 |
| Test covers archetype_id round-trip | Step 8 (`test_archetype_id_survives_resolve_module_contribution`) |
| All existing resolver tests pass | Step 9 (regression run) |

---

## Anti-Drift Notes

1. **`pop_key` is for ID uniqueness only.** After this ticket, the `pop_key` string encodes
   the archetype ID as a suffix solely to keep population IDs unique across a module. It no
   longer carries semantic meaning for identity lookups. If anyone changes the format in the
   future, the explicit `archetype_id` field is unaffected.

2. **`frozen=True` must survive.** Step 1 adds a field to a frozen Pydantic model. Pydantic
   V2 `model_config = ConfigDict(frozen=True)` applies to instances, not to the class
   definition. Adding a new optional field does not break frozen behavior.

3. **No extra="forbid".** `PopulationSpec` uses only `frozen=True` in `model_config` — no
   `extra="forbid"`. Any YAML `WorldSpec` that already supplies a `entities` list with
   `PopulationSpec` entries will silently default `archetype_id=None`. Verify once after
   Step 1 by loading a sample world spec YAML.

4. **TOWN-170 test path is unchanged.** The test
   `test_case2_direct_archetype_id_returns_single_entity` in `test_resolvers.py` guards
   parity entry TOWN-170. This test touches only `PopulationRecipeResolver.resolve()`, which
   is not modified by this ticket. It must remain green at every intermediate step.

5. **Site 2 import stays local.** The `from src.content.resolver import EntityArchetypeResolver`
   import inside `_build_compile_context` is a deliberate local import (avoids circular
   dependency). Do not move it to a module-level import.

6. **Validator dummy spec (line 89) intentionally excluded.** That `PopulationSpec` is a
   minimal placeholder for schema validation; no archetype is resolved at that point.
   Leaving `archetype_id` absent (defaulting to `None`) is correct.

---

## Deviations

**Step 8 — Test implementation method changed for two tests.**

Plan called for `test_archetype_id_carried_into_compile_context_without_string_inference` and
`test_resolve_module_contribution_does_not_use_split_for_archetype_id` to call `assemble()`.
A pre-existing branch failure (`CAT-REL-099`: `moon_cult_ruins` references non-existent
archetype `apprentice_mage`) causes `assemble()` to raise `InvalidWorldSpecError` for any
world containing the full catalog — these two tests were therefore rewritten to call
`resolve_module_contribution()` + `CompileProfileResolver.resolve()` directly, bypassing
the global catalog validator. This tests the same behavior (explicit archetype_id field carried
into CompileContext) without coupling to the unrelated catalog integrity failure.

Intent of both tests is fully preserved: archetype_id on PopulationSpec flows through to
CompileContext entities without string-suffix inference.
