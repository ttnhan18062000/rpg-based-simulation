# TCK-20260607-RESOLVER-BOUNDARY — Test Plan

## Run Command

```bash
pytest tests/unit/worldassembly/ -q
```

## Test Cases

### 1. test_contribution_snapshot_after_normalization (NEW)

**File:** `tests/unit/worldassembly/test_resolver.py`

**Purpose:** Snapshot — assert ResolvedModuleContribution field shapes after normalization
of a minimal empty-field module. Catches structural regressions silently introduced by
changes to `resolve_module_contribution`.

**Setup:** Minimal `WorldModuleSpec` with no regions, factions, biomes, ecologies,
populations, resources, buildings, services, relationships. Requires a CatalogRepository
for resolver construction, but the contribution bodies will all be empty (no catalog
lookups exercised). Uses `base_repo` fixture already in the file.

**Assertions:**
- `contribution.resource_refs == {}`
- `contribution.building_refs == {}`
- `contribution.service_refs == {}`
- `contribution.regions == []`
- `contribution.factions == []`
- `contribution.population_refs == []`
- `contribution.resolved_population_specs == []`
- `contribution.biome_refs == []`
- `contribution.ecology_refs == []`
- `contribution.relationship_refs == []`
- All dict fields are `isinstance(..., dict)`
- All list fields are `isinstance(..., list)`

### 2. test_resolve_module_contribution_rejects_raw_spec (NEW)

**File:** `tests/unit/worldassembly/test_resolver.py`

**Purpose:** Runtime guard — assert `TypeError` is raised when a raw `WorldModuleSpec`
is passed to `resolve_module_contribution` instead of a `NormalizedWorldModule`.

**Setup:** Minimal `WorldModuleSpec`. Calls `resolver.resolve_module_contribution(raw_spec)`.

**Assertions:**
- Raises `TypeError`
- Error message contains `"resolve_module_contribution requires NormalizedWorldModule"`

### 3. Existing tests must continue to pass (REGRESSION)

All existing tests in `tests/unit/worldassembly/`:
- `test_resolver.py` — `test_compile_profile_resolver_overrides`, `test_compiler_backward_compatibility`, `test_v2_service_refs_assembly_is_documented_gap`
- `test_archetype_preservation.py` — all 4+ tests calling `resolve_module_contribution(normalized)`
- `test_assembly.py`, `test_provenance.py` — existing suite

The signature change is backward-compatible for all these tests because they already pass
`NormalizedWorldModule`.

## Coverage Targets

| Path | Covered by |
|---|---|
| Normal flow: NormalizedWorldModule accepted | test_contribution_snapshot_after_normalization |
| Guard: raw WorldModuleSpec rejected | test_resolve_module_contribution_rejects_raw_spec |
| Regression: existing call sites unaffected | all existing tests |
| Snapshot: contribution field structure | test_contribution_snapshot_after_normalization |
