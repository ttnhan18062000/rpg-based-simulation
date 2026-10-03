---
status: active
layer: engine
authority: P1
audience: agent
ticket_id: TCK-20260614-WORLDMOD-UNIFY
artifact_type: test_plan
tags: [worldmodules, schema, unify, normalizer, resolver, testing]
---

# Test Plan — TCK-20260614-WORLDMOD-UNIFY

## Regression Surface

These existing tests must pass unchanged (or with minimal targeted fixes) after the
schema unification:

### `tests/integration/worldassembly/test_real_content_world_modules.py`

All four test functions cover the 7-module matrix:
- `test_real_world_modules_load_from_data_content` — schema validation via Pydantic
- `test_real_world_modules_normalize` — `WorldModuleAuthoringNormalizer.normalize()`
- `test_real_world_modules_preserve_count_maps` — count-map structure preserved
- `test_real_world_modules_resolve_contributions` — contribution resolution via catalog

These tests do not reference `schema_version` directly and should pass without
modification, provided the unified normalize() and resolve_module_contribution() produce
identical outputs for the existing v1 modules.

**One potential issue**: `test_real_world_modules_preserve_count_maps` at L63 asserts
`len(normalized.regions) == len(spec.regions)`. If the `schema_version` field is
removed from `NormalizedWorldModule` the attribute access in normalize() changes, but
the regions field is unrelated — this assertion is safe.

### `tests/integration/worldassembly/test_real_module_normalized_snapshot.py`

**Requires targeted update**: `test_snapshot_loaded_from_repository_not_synthetic`
at L94 asserts `normalized_frontier.schema_version is not None`. After removing
`schema_version` from `NormalizedWorldModule`, this will raise `AttributeError`.

**Fix**: Replace:
```python
assert normalized_frontier.schema_version is not None
```
With:
```python
assert normalized_frontier.module_type != ""
```
All other 9 snapshot tests are field-specific (biome_refs, ecology_refs, etc.) and are
unaffected.

### `tests/integration/worldassembly/test_real_content_world_compositions.py`

All four composition tests exercise the full assembly pipeline end-to-end. They must
pass unchanged. In particular:
- `test_real_world_compositions_assembly` verifies `len(bundle.world_spec.regions) > 0`
- `test_real_world_compositions_determinism_and_provenance` verifies fingerprint stability
  across two assembly runs

These tests will also verify (implicitly) that the unified resource/building paths
produce deterministic output if Option B (wiring count-map assembly) is implemented.

### `tests/integration/worldassembly/test_world_entity_spawner.py`

Entity spawner tests are downstream of CompileContext and do not touch schema_version.
Expect no changes needed.

### `tests/integration/content/test_strict_world_matrix.py`

This matrix test (`make lane-strict-matrix`) exercises catalog validation against all
world content. It does not reference worldmodule schema_version. Must pass unchanged.

---

## New Tests Required

### NT-1: Unified module loads with v1 and v2 fields simultaneously

**File**: `tests/unit/worldmodules/test_schema_unified.py` (new)

**Purpose**: Verify AC "A new module YAML can declare `biomes` and `ecologies` alongside
`population_recipes` in the same file without error."

```python
def test_unified_module_accepts_v1_and_v2_fields_together():
    """A module with both recipe fields and catalog-ref fields must load and normalize."""
    spec = WorldModuleSpec(
        module_id="test_hybrid_module",
        module_type="settlement",
        display_name="Hybrid Module",
        regions=[...],                    # v1 recipe field
        population_recipes=[...],        # v1 recipe field
        biomes=["frontier_village"],     # v2-named field
        ecologies=["frontier_village_ecology"],  # v2-named field
        buildings={"shop": 1},           # v2 count-map field
    )
    normalized = WorldModuleAuthoringNormalizer.normalize(spec)
    assert normalized.module_id == "test_hybrid_module"
    assert len(normalized.regions) == 1
    assert len(normalized.population_recipes) == 1
    assert normalized.biome_refs == ("frontier_village",)
    assert normalized.ecology_refs == ("frontier_village_ecology",)
    assert normalized.buildings == {"shop": 1}
```

**Verifies**: AC item 2 — mixed field module normalizes without error.

### NT-2: Module loads without schema_version field

**File**: `tests/unit/worldmodules/test_schema_unified.py` (new)

**Purpose**: Verify `schema_version` is no longer required in YAML (backward compat
without the field).

```python
def test_module_loads_without_schema_version():
    """schema_version must be optional after unification."""
    raw = {
        "module_id": "no_version_module",
        "module_type": "terrain",
        "display_name": "No Version Module",
    }
    spec = WorldModuleSpec.model_validate(raw)
    assert spec.module_id == "no_version_module"
    # schema_version defaults to "worldmodule.v1" or is absent — no ValidationError
```

**Verifies**: `@field_validator("schema_version")` removed; field optional.

### NT-3: Module loads with existing schema_version value

**File**: `tests/unit/worldmodules/test_schema_unified.py` (new)

**Purpose**: Confirm backward compatibility — existing YAMLs that declare
`schema_version: "worldmodule.v1"` continue to load.

```python
def test_module_with_schema_version_v1_still_loads():
    raw = {
        "schema_version": "worldmodule.v1",
        "module_id": "compat_module",
        "module_type": "terrain",
        "display_name": "Compat Module",
    }
    spec = WorldModuleSpec.model_validate(raw)
    assert spec.module_id == "compat_module"
```

**Verifies**: Existing YAML files unchanged, backward compat preserved.

### NT-4: resolve_module_contribution() has one code path — no schema_version branching

**File**: `tests/unit/worldmodules/test_schema_unified.py` (new)

**Purpose**: Verify AC "WorldAssemblyResolver.resolve_module_contribution() has one
code path".

```python
def test_resolve_module_contribution_is_version_agnostic(repos):
    """resolve_module_contribution must not branch on schema_version."""
    cat, mod = repos
    resolver = WorldAssemblyResolver(cat, mod)
    # Create two identical modules, one with "worldmodule.v1" label
    spec_v1 = WorldModuleSpec(schema_version="worldmodule.v1", ...)
    normalized = WorldModuleAuthoringNormalizer.normalize(spec_v1)
    contribution = resolver.resolve_module_contribution(normalized)
    assert contribution is not None
    # Verify that biome_refs, ecology_refs, resource_refs, building_refs all populate
```

### NT-5: Count-map resources assemble into WorldSpec (anti-drift for anti-gap)

**File**: `tests/integration/worldassembly/test_real_content_world_modules.py` (add
test to existing file) or new integration test.

**Purpose**: Prevent anti-drift hazard #5 — verify that modules declaring
`resources: {key: count}` produce non-zero resources in the assembled WorldSpec.

```python
def test_modules_with_count_map_resources_assemble_into_worldspec(repos):
    """forest_warden_grove declares resources: {healing_flower_patch: 5, spirit_wisp: 2}.
    After unification these must appear in the assembled WorldSpec."""
    cat, mod = repos
    # Compose a minimal composition including forest_warden_grove and its deps
    comp = WorldCompositionSpec(
        world_id="test_resource_assembly",
        name="Test",
        modules=["frontier_village_core", "wolf_den_near_forest", "forest_warden_grove"]
    )
    resolver = WorldAssemblyResolver(cat, mod)
    bundle = resolver.assemble(comp)
    resource_types = {r.resource_type for r in bundle.world_spec.resources}
    assert "healing_flower_patch" in resource_types
    assert "spirit_wisp" in resource_types
```

**Verifies**: Option B is implemented — count-map resources are actually assembled.

### NT-6: Count-map buildings assemble into WorldSpec

**File**: Same file as NT-5.

**Purpose**: Parallel to NT-5 for buildings. `frontier_village_core` declares
`buildings: {town_hall: 1, shop: 1, blacksmith: 1, inn: 1, healer_hut: 1}`.

```python
def test_modules_with_count_map_buildings_assemble_into_worldspec(repos):
    cat, mod = repos
    comp = WorldCompositionSpec(
        world_id="test_building_assembly",
        name="Test",
        modules=["frontier_village_core"]
    )
    resolver = WorldAssemblyResolver(cat, mod)
    bundle = resolver.assemble(comp)
    building_types = {b.type for b in bundle.world_spec.buildings}
    assert "town_hall" in building_types
    assert "shop" in building_types
```

**Verifies**: Option B implemented for buildings; `frontier_village_core` buildings
appear in assembled WorldSpec.

### NT-7: _find_best_region_for_resource removed — no AttributeError on resolver

**File**: `tests/unit/worldassembly/test_resolver.py` (existing or new function)

**Purpose**: Verify the heuristic method is gone; resolver instance has no such attribute.

```python
def test_find_best_region_for_resource_is_removed(repos):
    cat, mod = repos
    resolver = WorldAssemblyResolver(cat, mod)
    assert not hasattr(resolver, "_find_best_region_for_resource"), \
        "_find_best_region_for_resource must be removed per TCK-20260614-WORLDMOD-UNIFY"
```

---

## Scoped Pytest Commands

Run only the worldassembly integration lane (the primary regression surface):

```bash
pytest tests/integration/worldassembly/ -v -m worldassembly
```

Run only the new unit tests for the schema/normalizer changes:

```bash
pytest tests/unit/worldmodules/test_schema_unified.py -v
```

Run the strict content matrix (AC: "all 10 existing modules load and assemble without
any changes to their YAML"):

```bash
pytest tests/integration/content/test_strict_world_matrix.py -v
```

Run the worldmodules unit tests if they exist:

```bash
pytest tests/unit/worldmodules/ -v 2>/dev/null || echo "no worldmodules unit tests yet"
```

Run the full worldassembly resolver unit tests:

```bash
pytest tests/unit/worldassembly/ -v
```

Combined command to hit all affected surfaces (never bare `pytest tests/`):

```bash
pytest tests/integration/worldassembly/ tests/unit/worldmodules/ tests/unit/worldassembly/ tests/integration/content/test_strict_world_matrix.py -v -m "worldassembly or not worldassembly"
```

Makefile targets referenced in ticket:

```bash
make lane-worldassembly
make lane-strict-matrix
```

---

## Anti-Drift Test Guards

### Guard 1: No schema_version branching in resolver

Add an AST-level or import-time guard that would fail CI if `schema_version` string
comparisons reappear in the resolver:

```python
# tests/unit/worldassembly/test_resolver_no_version_branch.py
def test_resolver_has_no_schema_version_branching():
    """Compile-time guard: resolver.py must not compare schema_version strings."""
    import ast, inspect
    import src.worldassembly.resolver as mod
    source = inspect.getsource(mod)
    tree = ast.parse(source)
    for node in ast.walk(tree):
        if isinstance(node, ast.Compare):
            for comparator in node.comparators:
                if isinstance(comparator, ast.Constant):
                    val = str(comparator.value)
                    assert "worldmodule.v" not in val, \
                        f"schema_version string comparison found in resolver.py at line {node.lineno}: {val!r}"
```

### Guard 2: NormalizedWorldModule has no schema_version field

```python
# tests/unit/worldmodules/test_schema_unified.py
def test_normalized_world_module_has_no_schema_version_field():
    """After unification, NormalizedWorldModule must not carry schema_version."""
    from src.worldmodules.normalizer import NormalizedWorldModule
    import dataclasses
    field_names = {f.name for f in dataclasses.fields(NormalizedWorldModule)}
    assert "schema_version" not in field_names, \
        "schema_version must be removed from NormalizedWorldModule per TCK-20260614-WORLDMOD-UNIFY"
```

### Guard 3: WorldModuleSpec schema_version has no restrictive validator

```python
def test_worldmodulespec_accepts_any_schema_version_string():
    """schema_version must accept arbitrary strings (no enumerated validator)."""
    from src.worldmodules.schema import WorldModuleSpec
    spec = WorldModuleSpec(
        schema_version="worldmodule.future_format",
        module_id="guard_test",
        module_type="terrain",
        display_name="Guard Test",
    )
    assert spec.module_id == "guard_test"
```

### Guard 4: count-map resources and buildings are non-empty after assembly for real modules

This is NT-5 and NT-6 above — they permanently guard against the assembly gap silently
re-emerging. If the wiring is lost in a refactor, these tests will catch it immediately.

### Guard 5: `_find_best_region_for_resource` and `_find_best_region_for_building` absent

This is NT-7 above. Also apply to `_find_best_region_for_building`:

```python
def test_heuristic_region_methods_are_removed(repos):
    cat, mod = repos
    resolver = WorldAssemblyResolver(cat, mod)
    assert not hasattr(resolver, "_find_best_region_for_resource")
    assert not hasattr(resolver, "_find_best_region_for_building")
```
