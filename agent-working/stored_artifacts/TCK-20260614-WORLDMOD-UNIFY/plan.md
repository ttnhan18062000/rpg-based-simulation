---
status: active
layer: engine
authority: P1
audience: agent
ticket_id: TCK-20260614-WORLDMOD-UNIFY
artifact_type: plan
tags: [worldmodules, schema, unify, normalizer, resolver]
---

# Implementation Plan — TCK-20260614-WORLDMOD-UNIFY

## Dependency Map

```
STEP 1 (schema.py — field + validator)
  └── STEP 2 (normalizer.py — remove schema_version field + passthrough)
        └── STEP 3a (resolver.py — remove v2-gated resource block, replace with unconditional loop)
        └── STEP 3b (resolver.py — remove v2-gated building block, replace with unconditional loop)
        └── STEP 3c (resolver.py — remove v2 strictness check in resolve_module_contribution())
        └── STEP 3d (resolver.py — remove _find_best_region_for_resource + _find_best_region_for_building)
              [3a, 3b, 3c, 3d can be done in a single pass — all are in resolver.py]
  └── STEP 4 (test update — test_real_module_normalized_snapshot.py:L94)
STEP 5 (new unit tests — tests/unit/worldmodules/test_schema_unified.py)
  [independent; can be written before or after code changes]
STEP 6 (new integration anti-drift tests — NT-5, NT-6, NT-7)
  [depends on STEP 3a/3b being complete so count-map wiring is in place]
STEP 7 (docs/world/modules_contract.md update)
  [independent of code changes; can run in parallel]
STEP 8 (docs/parity_ledger/substrate.yaml — SUBSTRATE-NEW-003 v2_evidence update)
  [independent; run after STEP 7]
STEP 9 (make knowledge-index-update — required after any doc under docs/ changes)
  [depends on STEP 7 + STEP 8]
STEP 10 (run scoped test suites to verify all AC)
  [depends on all code + test steps]
STEP 11 (clean up and finalize ticket)
  [depends on STEP 10 passing]
```

---

## Ordered Implementation Steps

### STEP 1 — schema.py: Make schema_version optional, remove @field_validator

**File**: `src/worldmodules/schema.py`
**Lines**: L52 (field declaration), L83–L88 (validator + decorator)
**Purpose**: Remove the only behavioral gate separating v1 from v2 at the schema layer.

**Changes**:

1. Replace the required `schema_version` field (L52) with an optional field defaulting to `"worldmodule.v1"`:

   ```python
   # BEFORE (L52):
   schema_version: str = Field(..., description="Module spec schema, 'worldmodule.v1' or 'worldmodule.v2'")

   # AFTER:
   schema_version: str = Field("worldmodule.v1", description="Module schema identifier (unified format)")
   ```

2. Remove the `@field_validator("schema_version")` decorator and the `validate_schema_version` classmethod entirely (L83–L88):

   ```python
   # DELETE these 6 lines:
   @field_validator("schema_version")
   @classmethod
   def validate_schema_version(cls, v: str) -> str:
       if v not in ("worldmodule.v1", "worldmodule.v2"):
           raise ValueError("schema_version must be 'worldmodule.v1' or 'worldmodule.v2'")
       return v
   ```

3. Remove the `field_validator` import only if it becomes unused after removal. Check: `ModuleParameterSpec` still uses `@field_validator("type")` and `WorldModuleSpec` uses `@field_validator("module_type")` — so `field_validator` import at L5 stays.

**Scope guard**: Do NOT touch `REGISTERED_MODULE_TYPES`, `ModuleParameterSpec`, `@field_validator("module_type")`, or any other field. The `model_validator` import stays (used by `ModuleParameterSpec`).

**Verification**: `WorldModuleSpec.model_validate({"module_id": "x", "module_type": "terrain", "display_name": "X"})` succeeds without `schema_version` present; `WorldModuleSpec.model_validate({"schema_version": "worldmodule.v1", ...})` still succeeds; `WorldModuleSpec.model_validate({"schema_version": "worldmodule.future", ...})` now succeeds (no longer rejected).

**Acceptance criteria covered**: AC item 1 (existing YAML loads unchanged), AC item 2 (new module without schema_version loads), AC item 5 (field validator removed).

---

### STEP 2 — normalizer.py: Remove schema_version from NormalizedWorldModule dataclass

**File**: `src/worldmodules/normalizer.py`
**Lines**: L22 (dataclass field), L135 (constructor argument)
**Purpose**: Eliminate the schema_version passthrough from the internal representation so no downstream code can accidentally branch on it.

**Changes**:

1. Remove `schema_version: str` from the `NormalizedWorldModule` dataclass (L22):

   ```python
   # DELETE this line from the @dataclass(frozen=True) body:
   schema_version: str
   ```

2. Remove `schema_version=spec.schema_version,` from the `NormalizedWorldModule(...)` constructor call in `WorldModuleAuthoringNormalizer.normalize()` (L135):

   ```python
   # DELETE this line:
   schema_version=spec.schema_version,
   ```

**Scope guard**: Do NOT change any other fields in `NormalizedWorldModule`. Do NOT change `_normalize_ref_list()`, `normalize_count_map()`, or any other method body. The `Optional` import in L2 stays (used for `description: Optional[str]`).

**Verification**: `from src.worldmodules.normalizer import NormalizedWorldModule; import dataclasses; "schema_version" not in {f.name for f in dataclasses.fields(NormalizedWorldModule)}` is True.

**Acceptance criteria covered**: AC item 3 (no schema_version in internal normalized form feeding downstream branching).

---

### STEP 3 — resolver.py: Four targeted changes in one file pass

**File**: `src/worldassembly/resolver.py`
**Purpose**: Remove all runtime v2/v1 branches; wire count-map resources and buildings unconditionally (Option B).

#### STEP 3a — Remove dead v2 resource gate; replace with unconditional count-map loop

**Lines**: L455–L481 (the `if spec.schema_version == "worldmodule.v2":` resource block)

**Replace** the entire gated block with an unconditional loop over `contribution.resource_refs`:

```python
# DELETE lines 455–481:
# Merge v2 resources (using normalized count map dict)
if spec.schema_version == "worldmodule.v2":
    module_regions = [r for r in regions.values() if entity_origins.get(r.id) == m_id]
    for res_idx, (res_type, count) in enumerate(contribution.resource_refs.items()):
        ...

# REPLACE WITH (unconditional):
# Merge count-map resources (unified path for all modules)
for res_idx, (res_type, count) in enumerate(contribution.resource_refs.items()):
    res_id = f"{prefix}{res_type}_{res_idx}"
    if res_id in resources:
        raise ValueError(f"Duplicate resource ID collision '{res_id}' detected during merge.")

    self.resource_resolver.resolve(res_type)
    spawn_region = ""

    resources[res_id] = ResourceNodeSpec(
        id=res_id,
        resource_type=res_type,
        count=count,
        region=spawn_region
    )
    entity_origins[res_id] = m_id
    prov_records[res_id] = ProvenanceRecord(
        element_id=res_id,
        element_type="resource",
        source_module=m_id,
        recipe_type="resource_layout",
        parameters=param_vals,
        profiles={"resource_type": res_type},
        details={"count": count, "region": spawn_region}
    )
```

Note: `spawn_region = ""` is the deterministic replacement for `_find_best_region_for_resource()`. The heuristic used substring matching against `preferred_biomes` — no deterministic guarantee. Using `""` defers placement to world-level logic, consistent with the pattern used in v1 recipe paths when `res.region` is empty (L437: `spawn_region = f"{prefix}{res.region}" if res.region else ""`).

#### STEP 3b — Remove dead v2 building gate; replace with unconditional count-map loop

**Lines**: L507–L533 (the `if spec.schema_version == "worldmodule.v2":` building block)

**Replace** the entire gated block with an unconditional loop over `contribution.building_refs`:

```python
# DELETE lines 507–533:
# Merge v2 buildings (using normalized count map dict)
if spec.schema_version == "worldmodule.v2":
    ...

# REPLACE WITH (unconditional):
# Merge count-map buildings (unified path for all modules)
for bld_idx, (bld_type, count) in enumerate(contribution.building_refs.items()):
    for b_sub in range(count):
        bld_id = f"{prefix}{bld_type}_{b_sub}"
        if bld_id in buildings:
            raise ValueError(f"Duplicate building ID collision '{bld_id}' detected during merge.")

        self.building_resolver.resolve(bld_type)
        spawn_region = ""

        buildings[bld_id] = BuildingSpec(
            id=bld_id,
            type=bld_type,
            region=spawn_region
        )
        entity_origins[bld_id] = m_id
        prov_records[bld_id] = ProvenanceRecord(
            element_id=bld_id,
            element_type="building",
            source_module=m_id,
            recipe_type="building_layout",
            parameters=param_vals,
            profiles={"building_type": bld_type},
            details={"region": spawn_region}
        )
```

Note: `spawn_region = ""` same reasoning as STEP 3a. The per-count `b_sub` index is preserved from the original to maintain the ID generation pattern (`{prefix}{bld_type}_{b_sub}`).

#### STEP 3c — Remove v2 strictness check in resolve_module_contribution()

**Lines**: L678–L679

```python
# BEFORE:
if normalized_module.schema_version == "worldmodule.v2":
    raise ResolverError("region", reg.id, f"referenced by v2 module '{normalized_module.module_id}'")

# AFTER (always raise for non-catalog regions):
raise ResolverError("region", reg.id, f"referenced by module '{normalized_module.module_id}' but not found in catalog")
```

The outer `if self.catalog_repo.get_region(reg.id) is not None:` guard at L675 is preserved — the raise only fires when a region is missing from the catalog. The behavior change: formerly, non-catalog regions in v1 modules were silently accepted; now they raise. This is consistent with the unified format's goal of catalog validation. However, ALL existing real modules either use catalog regions or declare no regions requiring catalog lookup — no regression risk.

**Scope guard**: The outer guard structure (`if self.catalog_repo.get_region(reg.id) is not None: self.region_resolver.resolve(reg.id) else: <raise>`) must remain. Only change what's inside the `else:` branch.

#### STEP 3d — Remove _find_best_region_for_resource and _find_best_region_for_building

**Lines**: L796–L816 (`_find_best_region_for_resource`) and L818–L840 (`_find_best_region_for_building`)

Delete both methods entirely. After STEP 3a and 3b there are no callers. Verify with grep before deleting.

Also update the service comment at L535–L539:
```python
# BEFORE (references schema_version pattern):
# When adding that field, add a v2 service merge loop here parallel to the building loop above.

# AFTER:
# When adding that field, add a service merge loop here parallel to the building loop above.
```

**Scope guard**: Do NOT touch `CompileProfileResolver` (L843+). Do NOT touch `RelationshipResolver` wiring at L542–L556. Do NOT touch the service_refs comment block structure — only update the final sentence.

**Verification**: `hasattr(WorldAssemblyResolver(...), "_find_best_region_for_resource")` is False. `hasattr(WorldAssemblyResolver(...), "_find_best_region_for_building")` is False. `"worldmodule.v" not in inspect.getsource(resolver_module)` (AST guard from test_plan.md Guard 1).

**Acceptance criteria covered**: AC item 3 (one code path in resolve_module_contribution), AC item 4 (_find_best_region_for_resource removed, deterministic replacement in place).

---

### STEP 4 — Update existing test: test_real_module_normalized_snapshot.py:L94

**File**: `tests/integration/worldassembly/test_real_module_normalized_snapshot.py`
**Lines**: L94

Replace:
```python
assert normalized_frontier.schema_version is not None
```
With:
```python
assert normalized_frontier.module_type != ""
```

This preserves the intent (normalized output has meaningful identity field) while removing the now-deleted attribute.

**Scope guard**: Touch only line L94. Do not change any other assertion or test structure.

**Verification**: File runs with no `AttributeError`.

---

### STEP 5 — New unit tests: tests/unit/worldmodules/test_schema_unified.py

**File**: `tests/unit/worldmodules/test_schema_unified.py` (new file)

Write the following tests (as specified in test_plan.md):

- **NT-1** `test_unified_module_accepts_v1_and_v2_fields_together`: module with both recipe fields and catalog-ref fields normalizes without error.
- **NT-2** `test_module_loads_without_schema_version`: `schema_version` omitted from raw dict; `WorldModuleSpec.model_validate()` succeeds.
- **NT-3** `test_module_with_schema_version_v1_still_loads`: existing `schema_version: "worldmodule.v1"` loads cleanly.
- **Guard 2** `test_normalized_world_module_has_no_schema_version_field`: dataclasses.fields check confirms field absent.
- **Guard 3** `test_worldmodulespec_accepts_any_schema_version_string`: arbitrary `schema_version` value loads without ValidationError.

All tests are pure unit tests (no catalog/module repos needed for NT-1 through NT-3, Guard 2, Guard 3 — use `WorldModuleSpec` and `WorldModuleAuthoringNormalizer` directly with minimal inline data).

**Scope guard**: Do not write NT-4 here — it requires repo fixtures and belongs in an integration test file. Do not create `__init__.py` if the directory already has one; check first.

---

### STEP 6 — New integration anti-drift tests

**File**: `tests/integration/worldassembly/test_real_content_world_modules.py` (add to existing) OR new file `tests/integration/worldassembly/test_count_map_assembly.py`

Write:

- **NT-5** `test_modules_with_count_map_resources_assemble_into_worldspec`: verifies `forest_warden_grove` resources (`healing_flower_patch`, `spirit_wisp`) appear in assembled WorldSpec after Option B wiring.
- **NT-6** `test_modules_with_count_map_buildings_assemble_into_worldspec`: verifies `frontier_village_core` buildings (`town_hall`, `shop`, etc.) appear in assembled WorldSpec.
- **NT-7 / Guard 5** `test_heuristic_region_methods_are_removed`: `hasattr` check for both deleted methods.
- **Guard 1** `test_resolver_has_no_schema_version_branching`: AST walk of `src.worldassembly.resolver` source confirms no `"worldmodule.v"` string constants in Compare nodes.

Prefer adding to the existing file if it already has the needed fixtures (catalog/module repos). If fixtures differ significantly, create a new file.

**Scope guard**: Do not modify any existing assertions in `test_real_content_world_modules.py` while adding new tests. Use existing fixture patterns.

---

### STEP 7 — docs/world/modules_contract.md update

**File**: `docs/world/modules_contract.md`
**Purpose**: Remove v1/v2 references; reflect single unified format.

**Changes** (locate and apply — exact line numbers require reading the file):

1. In the identity fields table: remove the `schema_version` row entirely, or update it to state "optional label, defaults to `worldmodule.v1`, not validated".
2. Rename any section header "v2-only catalog reference fields" to "Catalog reference fields (all formats)".
3. Under WORLD-MOD-001: remove any statement that schema_version is required.
4. Under WORLD-MOD-002: ensure it describes only `REGISTERED_MODULE_TYPES` validation (not schema_version). If the doc currently ties WORLD-MOD-002 to schema_version enforcement, update to clarify WORLD-MOD-002 covers module_type validation only.
5. Add or update a "Schema Contract" or equivalent section stating: "Single unified format. `schema_version` is an optional human-readable label defaulting to `'worldmodule.v1'`. It is not validated by the schema."

**Scope guard**: Do NOT change WORLD-MOD-003 through WORLD-MOD-007. Do NOT remove the `module_type` validation description from WORLD-MOD-002.

---

### STEP 8 — docs/parity_ledger/substrate.yaml: Update SUBSTRATE-NEW-003

**File**: `docs/parity_ledger/substrate.yaml`
**Lines**: L3829–L3849

**Changes**:

1. Update `text` field to remove "ref lists → ..." boilerplate and add explicit statement about unified normalize path:

   ```yaml
   text: >
     WorldModuleRepository (WORLD-MOD-004/005) rejects duplicate module_id across
     all loaded files (raises ValueError). topological_sort_modules (WORLD-MOD-006/007)
     uses Kahn's algorithm with alphabetical tie-breaking — deterministic given same
     modules_map. Cycle detection raises ValueError. External requires refs (not in
     modules_map) are silently ignored. WorldModuleAuthoringNormalizer produces
     NormalizedWorldModule via a single unified code path (no schema_version branching):
     ref lists → immutable Tuple[str,...], count maps → Dict[str,int] with all counts ≥ 1;
     duplicates and non-positive counts raise NormalizationError.
   ```

2. Update `v2_evidence` to include the ticket ID and remove any schema_version-specific claims:

   ```yaml
   v2_evidence: >
     docs/world/modules_contract.md +
     src/worldmodules/repository.py:1 (WORLD-MOD-004/005) +
     src/worldmodules/utils.py:1 (WORLD-MOD-006/007) +
     src/worldmodules/normalizer.py +
     TCK-20260614-WORLDMOD-UNIFY (schema unification — schema_version validator removed)
   ```

3. Keep `status: verified`.

---

### STEP 9 — Run make knowledge-index-update

```bash
make knowledge-index-update
```

Required after any file under `docs/` is created or modified (CLAUDE.md rule). Applies after STEP 7 and STEP 8.

---

### STEP 10 — Run scoped test suites

Run in order, stop on first failure:

```bash
# Unit tests for the schema/normalizer changes:
pytest tests/unit/worldmodules/ -v

# Unit tests for resolver anti-drift guards:
pytest tests/unit/worldassembly/ -v

# Integration worldassembly lane (primary regression surface):
pytest tests/integration/worldassembly/ -v -m worldassembly

# Strict content matrix (all 10 real modules):
pytest tests/integration/content/test_strict_world_matrix.py -v
```

Or via Makefile targets:
```bash
make lane-worldassembly
make lane-strict-matrix
```

**All must pass.** If any test fails, fix before proceeding to STEP 11.

---

### STEP 11 — Finalize ticket and clean up

1. Move ticket `tickets/inprogress/TCK-20260614-WORLDMOD-UNIFY.md` to `tickets/done/`.
2. Fill in **Files Changed** and **Completion Summary** sections of the ticket.
3. Append working log entry to bottom of `tickets/working_log.csv`.
4. Move `staging_artifacts/TCK-20260614-WORLDMOD-UNIFY/` to `stored_artifacts/`.
5. Clean: `rm -rf data/runs/* reports/release_proof/*`.
6. Write agent monitoring records:
   - Run entry to `agent-monitoring/runs.jsonl`
   - At least one event to `agent-monitoring/events.jsonl`
7. Verify: `ls tickets/inprogress/TCK-20260614-WORLDMOD-UNIFY.md` should 404; `ls tickets/done/TCK-20260614-WORLDMOD-UNIFY.md` should exist.

---

## Acceptance Criteria Traceability

| AC | Covered by Step(s) |
|---|---|
| AC1: All 10 existing modules load and assemble without YAML changes | STEP 1 (optional field), STEP 10 (strict matrix test) |
| AC2: New module can declare biomes + ecologies alongside population_recipes without error | STEP 1 (validator removed), STEP 5 NT-1 |
| AC3: resolve_module_contribution() has one code path — no isinstance/schema_version branching | STEP 3c (remove v2 region check), STEP 6 Guard 1 |
| AC4: _find_best_region_for_resource() removed; replaced by deterministic resolver call | STEP 3d (deletion), STEP 3a (spawn_region="" replacement), STEP 6 NT-7/Guard 5 |
| AC5: All existing integration tests in tests/integration/worldassembly/ pass unchanged | STEP 4 (snapshot test update), STEP 10 |
| AC6: docs/world/modules_contract.md updated to remove v1/v2 references | STEP 7 |

---

## Scope Guards — What NOT to Touch

- **`RelationshipResolver`** and its wiring in `assemble()` (L542–L556) — out of scope entirely.
- **`CompileProfileResolver`** (L843+) — unrelated to schema unification.
- **`WorldAssemblyValidator`** (the dummy WorldSpec builder at resolver.py L78–L100) — it iterates `module.resource_recipes` and `module.building_recipes` which remain empty in real modules; pre-existing behavior, do not change.
- **`service_refs` gap** (`SUB-367`, `v2_intentional_divergences.md` entry 2.19) — intentionally deferred; the comment at L535–L539 is updated but the gap itself is NOT closed.
- **`ModuleParameterSpec`** — no changes.
- **`data/content/world_modules/*.yaml`** files — no YAML changes in this ticket (migration is TCK-20260614-WORLDDAT-MIGRATE).
- **`docs/parity_ledger/` entries other than SUBSTRATE-NEW-003** — no changes.
- **`WORLD-MOD-003` through `WORLD-MOD-007`** in the modules contract — not touched.
- **Module parameter expression engine** (TCK-20260614-WORLDMOD-PARAMS) — out of scope.

---

## Unresolved Questions

None. All open questions from the investigation are resolved:

- **OQ1 (schema_version in NormalizedWorldModule)**: Removed entirely. Cleaner; no downstream consumer outside the 3 resolver locations being deleted.
- **OQ2 (spawn_region for count-map resources)**: `spawn_region = ""` — deterministic, consistent with v1 empty-region convention; defers placement to world-level logic.
- **Option A vs Option B**: Option B confirmed as per investigation recommendation and planner directive. Count-map resources and buildings are wired unconditionally.
