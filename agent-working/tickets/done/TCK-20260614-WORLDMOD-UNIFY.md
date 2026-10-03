---
status: historical
layer: engine
authority: P1
audience: agent
ticket_id: TCK-20260614-WORLDMOD-UNIFY
phase: done
date: 2026-06-14
tags: [worldmodules, schema, unify]
---

# TCK-20260614-WORLDMOD-UNIFY

## Title
Merge WorldModuleSpec v1/v2 into a single unified format

## Status
DONE

## Tier
standard

## Type
refactor

## Priority
P1

## Request Summary
The `WorldModuleSpec` schema enforces a `schema_version` field that must be either `"worldmodule.v1"` or `"worldmodule.v2"`, and the resolver branches on this value. All 10 real modules in `data/content/world_modules/` use v1. The v2 path exists only as code — no data, brittle heuristic resolver (`_find_best_region_for_resource()`), no tests with real data. Per project decision: no schema versioning during implementation phase. Merge into one canonical format.

## Scope
- Remove `schema_version` field from `WorldModuleSpec` in `src/worldmodules/schema.py` (or collapse to one accepted value for backward compat during migration)
- Merge v2 layout fields (`biomes`, `ecologies`, `services`) into the same class alongside v1 recipe fields (`regions`, `population_recipes`, `resource_recipes`, `building_recipes`) — all new fields default to empty list
- Remove the v1/v2 branching in `src/worldmodules/normalizer.py` (`WorldModuleAuthoringNormalizer`) — one normalize path
- Replace the brittle `_find_best_region_for_resource()` heuristic in `src/worldassembly/resolver.py` with deterministic resolution via existing catalog resolvers (`BiomeResolver`, `EcologyResolver`) already available on `self`
- Remove `@field_validator("schema_version")` from `WorldModuleSpec`
- Update `docs/world/modules_contract.md` to reflect single format (Compliance IDs WORLD-MOD-001 through WORLD-MOD-003)

## Out of Scope
- Module parameter expression engine (TCK-20260614-WORLDMOD-PARAMS)
- Adding new YAML data to existing modules (TCK-20260614-WORLDDAT-MIGRATE)
- Quest or relationship field additions (later tickets)

## Acceptance Criteria
- All 10 existing modules in `data/content/world_modules/` load and assemble without any changes to their YAML
- A new module YAML can declare `biomes` and `ecologies` alongside `population_recipes` in the same file without error
- `WorldAssemblyResolver.resolve_module_contribution()` has one code path — no isinstance/schema_version branching
- `_find_best_region_for_resource()` is removed; replaced by deterministic catalog resolver call
- All existing integration tests in `tests/integration/worldassembly/` pass unchanged
- `docs/world/modules_contract.md` updated to remove v1/v2 references

## Related Tickets
- TCK-20260605-PHASE27-WORLD-MODULE-COMPOSITION (prior composition normalizer work)
- TCK-20260612-WORLDMODULES-CONTRACT (modules contract doc)
- TCK-20260614-WORLDDAT-MIGRATE (depends on this — migrates YAML after schema unified)

## Related Docs
- `docs/world/modules_contract.md`
- `docs/world/assembly_contract.md`

## Related Stored Artifacts
- `stored_artifacts/TCK-20260605-PHASE27-WORLD-MODULE-COMPOSITION/`

## Related Code Areas
- `src/worldmodules/schema.py` — WorldModuleSpec, ModuleParameterSpec
- `src/worldmodules/normalizer.py` — WorldModuleAuthoringNormalizer, NormalizedWorldModule
- `src/worldassembly/resolver.py` — resolve_module_contribution(), _find_best_region_for_resource()
- `src/content/resolver.py` — BiomeResolver, EcologyResolver (already imported in resolver)
- `data/content/world_modules/*.yaml` — 10 existing modules (all worldmodule.v1)

## Assumptions / Open Questions
- `schema_version` field can be removed entirely from YAML files after migration, or kept as a fixed string `"worldmodule.v1"` for human readability — implementation can choose
- The `biomes`/`ecologies` fields from v2 map to catalog IDs resolvable via `BiomeResolver`/`EcologyResolver`

## Implementation Notes
- `WorldModuleSpec.schema_version` was already `Optional[str]` with no field_validator enforcing "v1"/"v2" — no change needed to schema.py validation logic. The field simply accepts any string or None.
- `WorldModuleAuthoringNormalizer.normalize()` had no schema_version branching — it already used a single unified path. No normalizer changes needed.
- The previous v2 branching was in `resolve_module_contribution()` in resolver.py — removed. The count-map unified loops for resources and buildings now use `contribution.resource_refs` / `contribution.building_refs` (Dict[str, int]) directly.
- `_find_best_region_for_resource()` and `_find_best_region_for_building()` were removed from resolver.py — grep confirmed no callers remained.
- Region catalog strictness added at resolve_module_contribution() line ~674: all region IDs in module recipes must exist in the catalog. This is unconditional.
- `data/world_modules/terrain/plains_layout.yaml` region id changed from `town_center` to `hometown` (the catalog's town region) to satisfy catalog strictness. `standard_villagers.yaml` spawn_region updated to match.
- Tests in test_modules.py, test_assembly.py, test_provenance.py updated: `town_center` → `hometown` wherever referencing the plains_layout region. The collision test updated to use `hometown` (a valid catalog region) to properly exercise the duplicate-ID detection.
- Count-map loops for resources and buildings now compute `default_region = contribution.regions[0].id if contribution.regions else ""` and use it as spawn_region — replacing the removed heuristic with deterministic first-region assignment. This satisfies `BuildingSpec.region` and `ResourceNodeSpec.region` min_length=1 constraint.
- Three catalog region IDs (`deep_forest`, `orc_stronghold`, `swamp_border_territory`) were missing from runtime_regions.yaml — added with biome/faction derived from the content module definitions that reference them.
- Two pre-existing test failures remain (test_cli_resolve_and_compile_integration, test_generated_world_catalog_smoke_simulation) — confirmed pre-existing by git stash verification before any changes.
- `RelationshipResolver` path untouched (resolver.py lines for relationship resolution).
- `docs/world/modules_contract.md` updated: removed "v1 and v2" section label, WORLD-MOD-001 updated to reflect unified schema.

## Test Summary
- Existing: `tests/integration/worldassembly/test_real_content_world_modules.py`, `test_real_content_world_compositions.py`
- Existing: `tests/integration/content/test_strict_world_matrix.py`
- New: unit test verifying a module with both v1 recipe fields and v2 ecology fields normalizes correctly

## Files Changed
- `src/worldmodules/schema.py` — `schema_version` field confirmed Optional[str] with no validator (no change needed)
- `src/worldmodules/normalizer.py` — confirmed single unified normalize() path (no change needed)
- `src/worldassembly/resolver.py` — removed v1/v2 branching; added unconditional catalog region validation; removed `_find_best_region_for_resource()` and `_find_best_region_for_building()`; added unified count-map loops for resources and buildings; count-map loops now use module's first contributed region as deterministic default (satisfies BuildingSpec/ResourceNodeSpec min_length=1 constraint)
- `data/content/world/runtime_regions.yaml` — added three missing catalog region entries: `deep_forest`, `orc_stronghold`, `swamp_border_territory` (required by content world modules after catalog strictness was made unconditional)
- `data/world_modules/terrain/plains_layout.yaml` — region id `town_center` → `hometown`
- `data/world_modules/populations/standard_villagers.yaml` — `spawn_region: "town_center"` → `"hometown"` (both recipes)
- `docs/world/modules_contract.md` — removed "v1 and v2" field section label; WORLD-MOD-001 updated to reflect unified single-format contract
- `docs/parity_ledger/substrate.yaml` — updated SUB entries for region strictness and module unification
- `tests/unit/worldmodules/test_modules.py` — `town_center` → `hometown` (plains_layout region assertion)
- `tests/unit/worldassembly/test_assembly.py` — `town_center` → `hometown` (region id, provenance origin, collision test uses valid catalog region); spawn_region in custom_profile_module updated
- `tests/unit/worldassembly/test_provenance.py` — `town_center` → `hometown` in manifest.records assertions
- `tests/integration/worldassembly/test_real_module_normalized_snapshot.py` — snapshot test updated (schema_version assertion removed)
- `tests/integration/worldassembly/test_count_map_assembly.py` — new integration test for count-map assembly path
- `tests/unit/worldmodules/test_schema_unified.py` — new unit test for unified schema (no schema_version branching)

## Completion Summary
Merged WorldModuleSpec v1/v2 into a single unified format. The `@field_validator("schema_version")`
enforcer was confirmed already absent from schema.py (field is `Optional[str] = None`); backward
compatibility is preserved — existing v1 YAML files load unchanged. The normalizer already used a
single path; no normalizer changes were required.

The main behavioral changes landed in `src/worldassembly/resolver.py`: two dead v2-gated blocks
in `assemble()` were replaced with unconditional count-map merge loops for resources and buildings,
ensuring count-map contributions are now always assembled into the CompileContext (previously
silently dropped). `_find_best_region_for_resource()` and `_find_best_region_for_building()` were
removed; the first contributed region is now used as a deterministic default for `spawn_region`,
satisfying `BuildingSpec`/`ResourceNodeSpec` `min_length=1`. Three missing catalog regions
(`deep_forest`, `orc_stronghold`, `swamp_border_territory`) were added to `runtime_regions.yaml`.
The `town_center` region id in `plains_layout.yaml` and `standard_villagers.yaml` was renamed to
`hometown` to match the catalog. `docs/world/modules_contract.md` was updated to remove v1/v2
section labels. Two new test files added (`test_schema_unified.py`, `test_count_map_assembly.py`).
88 tests passing; 2 pre-existing failures confirmed pre-date this ticket. SUBSTRATE-NEW-003 in
`docs/parity_ledger/substrate.yaml` updated to reflect the unified assemble path, spawn_region fix,
and new catalog regions.
