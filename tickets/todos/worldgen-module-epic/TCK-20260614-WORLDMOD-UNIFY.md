---
status: active
layer: engine
authority: P1
audience: agent
ticket_id: TCK-20260614-WORLDMOD-UNIFY
phase: open
date: 2026-06-14
tags: [worldmodules, schema, unify]
---

# TCK-20260614-WORLDMOD-UNIFY

## Title
Merge WorldModuleSpec v1/v2 into a single unified format

## Status
OPEN

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
- Check `WorldModuleAuthoringNormalizer.normalize()` carefully — it branches on `schema_version` to handle v1 vs v2 field layout
- `RelationshipResolver` is already wired (resolver.py:209, 543, 711) — do not touch that path
- Run `make lane-worldassembly` and `make lane-strict-matrix` to verify

## Test Summary
- Existing: `tests/integration/worldassembly/test_real_content_world_modules.py`, `test_real_content_world_compositions.py`
- Existing: `tests/integration/content/test_strict_world_matrix.py`
- New: unit test verifying a module with both v1 recipe fields and v2 ecology fields normalizes correctly

## Files Changed
<!-- filled during implementation -->

## Completion Summary
<!-- filled during implementation -->
