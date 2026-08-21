---
status: active
layer: world
authority: P1
audience: agent
ticket_id: TCK-20260821-NOISE-FILL-SCHEMA
phase: open
date: 2026-08-21
tags: [world, schema]
---

# TCK-20260821-NOISE-FILL-SCHEMA

## Title
Add optional terrain-variant declaration field to RegionRecipeSpec

## Status
OPEN

## Tier
standard

## Type
feature

## Priority
P1

## Request Summary
Extend RegionRecipeSpec with an optional field (naming TBD, to be settled during this ticket) so a region can declare a set of terrain variants instead of a single flat terrain string, laying the schema groundwork for organic in-region terrain. Must be fully backward compatible: modules that don't declare the new field keep today's flat single-terrain fill exactly as-is, with zero behavior change until a later ticket teaches the compiler to consume it.

## Scope
- Add a new optional field to RegionRecipeSpec (src/worldbuilding/recipe.py) with a concrete name and a minimal TerrainVariantSpec model settled during this ticket, e.g. `terrain_variants: Optional[list[TerrainVariantSpec]] = None`.
- Add the matching field to RegionSpec (src/worldbuilding/schema.py) with the same default.
- Explicitly forward the new field in WorldAssemblyResolver.resolve_module_contribution() (src/worldassembly/resolver.py:755-800) via its fully-explicit kwargs — the exact touch point TCK-20260701-HAZARD-KIND-RESOLVER-GAP missed for a prior field.
- Keep the field fully inert (schema-only, no compiler consumption) — WorldCompiler (src/worldbuilding/compiler.py) is untouched by this ticket.
- Add/extend a real-pipeline test in tests/integration/worldassembly/test_real_content_world_modules.py mirroring test_hazard_kind_survives_module_pipeline, covering both the declared-value and default/backward-compat cases.

## Out of Scope
- Compiler consumption of the new field (thresholding noise into per-tile terrain) — that is TCK-20260821-COMPILER-NOISE-FILL.
- Migrating any real world module content to use the field — that is TCK-20260821-WOLF-DEN-NOISE-MIGRATION.
- The second RegionSpec(...) construction site in resolver.py's MODULE-context WorldValidator dummy_spec builder (~line 90-105) — confirmed out of scope for this ticket, explicitly not silently skipped.
- Adding any enum constraint to `terrain` — none exists today on either schema, and this ticket does not introduce one.

## Acceptance Criteria
- [ ] RegionRecipeSpec accepts the new optional field while `extra="forbid"` continues to be enforced on the model.
- [ ] Constructing a RegionRecipeSpec without the new field succeeds and the field defaults to None/empty, with zero behavior change.
- [ ] A module YAML that does NOT declare the field, run through normalize() -> resolve_module_contribution(), yields a RegionSpec whose new field equals the same default — byte-identical to today for non-opted-in modules.
- [ ] A module YAML that DOES declare the field survives normalize() + resolve_module_contribution() with the declared value intact on the resulting RegionSpec, proving explicit forwarding rather than a silent drop.
- [ ] The full test_real_content_world_modules.py MODULE_MATRIX (all 20 real modules) and test_compiler_seeding_determinism pass unchanged, since none of the 20 real modules declare the new field and compiler.py is untouched by this concern.

## Related Tickets
- TCK-20260821-EPIC-WORLDGEN-ORGANIC-TERRAIN
- TCK-20260701-HAZARD-KIND-RESOLVER-GAP
- TCK-20260820-EPIC-WORLD-RENDERING-CORE

## Related Docs
- docs/testing/test_taxonomy.md

## Related Stored Artifacts
None.

## Related Code Areas
- src/worldbuilding/recipe.py
- src/worldbuilding/schema.py
- src/worldassembly/resolver.py
- src/worldmodules/normalizer.py
- src/worldbuilding/compiler.py
- tests/integration/worldassembly/test_real_content_world_modules.py
- tests/unit/worldassembly/test_assembly.py
- tests/unit/worldassembly/test_archetype_preservation.py

## Assumptions / Open Questions
- Exact field name and TerrainVariantSpec model shape are settled during this ticket's implementation (recommended: terrain_variants: Optional[list[TerrainVariantSpec]] = None) — not pre-decided by the investigation.

## Implementation Notes

## Test Summary

## Files Changed

## Completion Summary
