---
status: historical
layer: guidelines
authority: P1
audience: agent
ticket_id: TCK-20260604-PHASE22-SCHEMA-NORMALIZATION
phase: done
date: 2026-06-04
tags: [phase22, schema, normalization]
---

# TCK-20260604-PHASE22-SCHEMA-NORMALIZATION

## Title
Phase 22 — Fail-closed schema and authoring-form normalization

## Status
DONE

## Tier
standard

## Type
chore

## Priority
P1

## Request Summary
Prevent YAML fields from being silently ignored by adding a fail-closed schema mode (forbidding extra fields). Support author-friendly composition and module formats while preserving executable schema compatibility via normalizers.

## Scope
- Update `CatalogBaseDefinition` in `src/content/schema.py` to use `model_config = ConfigDict(frozen=True, extra="forbid")` and declare `extension` and `design_notes` fields.
- Add Pydantic schema validation tests checking that active and compatibility models fail on unknown top-level fields unless nested under `metadata`, `extension`, or `design_notes`.
- Implement a normalizer for world compositions to accept friendly shorthand formats (`modules` shorthand list of strings) and normalize them to `module_refs` structured format.
- Implement a normalizer for world modules (`WorldModuleAuthoringNormalizer` outputting `NormalizedWorldModule`) to normalize lower-layer biome, ecology, population, faction, relationship, and building specs.
- Enforce that error messages on schema failures include file path, family, and record ID.

## Out of Scope
- Rewriting runtime simulation execution logic (only normalization of raw parsed inputs).

## Acceptance Criteria
- All schemas fail on unknown top-level fields.
- Unknown fields nested under metadata, extension, design_notes are permitted.
- Composition shorthand `modules` is correctly normalized to `module_refs`.
- Mixed authoring formats fail clearly with descriptive errors.
- World modules normalize correctly between v1 and v2 forms.
- Error messages contain file, family, and record ID where available.
- Existing tests pass without regression.

## Related Tickets
- TCK-20260604-PHASE21-FAMILY-REGISTRY

## Related Docs
- `world_phase_20_28.md`

## Related Stored Artifacts
- None

## Related Code Areas
- `src/content/schema.py`
- `tests/unit/content/test_catalog.py`
- `src/worldassembly/`
- `src/worldmodules/`

## Assumptions / Open Questions
- None.

## Implementation Notes
- Set `extra="forbid"` on all active Pydantic spec models (`CatalogBaseDefinition`, `WorldCompositionSpec`, `ModuleRefSpec`, `WorldModuleSpec`, etc.).
- Fixed catalog loading failures due to `extra="forbid"` by declaring previously undeclared fields in `src/content/schema.py` (`damage_tags` in `CombatProfileDefinition`, `themes` in `BuildingDefinition`, `service_type`, `provided_recipes`, `resource_bias` in `ServiceProfileDefinition`, `biome`, `controlling_faction` in `RuntimeRegionDefinition`, and `material`, `preferred_biomes` in `ResourceDefinition`).
- Implemented `WorldModuleAuthoringNormalizer` and `NormalizedWorldModule` in `src/worldmodules/normalizer.py`.
- Added support for dynamic custom module type registration to support "fails unless registered" requirements.

## Test Summary
- Ran `pytest tests/unit/content/test_catalog.py tests/unit/worldassembly/test_assembly.py tests/unit/worldbuilding/test_world_recipes.py tests/unit/worldmodules/test_modules.py`
- Added tests verifying v1/v2 schema parsing, normalization, unknown field failures, and custom type registration.
- All 104 unit tests pass successfully.

## Files Changed
- `src/content/schema.py`
- `src/worldmodules/schema.py`
- `src/worldmodules/normalizer.py`
- `tests/unit/worldassembly/test_assembly.py`
- `tests/unit/worldmodules/test_modules.py`

## Completion Summary
- Implemented fail-closed schemas with `extra="forbid"` on active specs.
- Implemented composition shorthand normalization.
- Implemented v1/v2 module normalization to stable internal `NormalizedWorldModule` representations.
