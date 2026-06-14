---
status: active
layer: engine
authority: P1
audience: agent
ticket_id: TCK-20260614-WORLDMOD-PACKS
phase: open
date: 2026-06-14
tags: [worldmodules, content-packs, assembly, validation]
---

# TCK-20260614-WORLDMOD-PACKS

## Title
Content pack dependency validation at assembly time

## Status
OPEN

## Tier
standard

## Type
feature

## Priority
P1

## Request Summary
`ContentPackManifest` (`src/content/pack_manifest.py`) defines a complete pack contract with `pack_id`, `enabled`, `dependencies`, `included_families`, `sample_compositions`. `WorldCompositionSpec` has a `catalog_refs` field for referencing content families. However, `WorldAssemblyResolver` never validates whether referenced content packs are available, enabled, or have their dependencies resolved. A composition can silently reference a disabled pack and assembly will proceed without error.

## Scope
- At the start of `WorldAssemblyResolver.assemble()`, after loading the composition, validate pack dependencies:
  - For each entry in `WorldCompositionSpec.catalog_refs` that matches a known pack path, load the corresponding `ContentPackManifest`
  - Check `enabled == True`; raise `AssemblyPackError` if disabled, naming the pack_id
  - Check all `dependencies` packs are also enabled; raise `AssemblyPackError` if any dependency is missing or disabled
- Define `AssemblyPackError(ValueError)` in `src/worldassembly/resolver.py`
- Pack manifests loaded from `data/content/packs/*.yaml`; use existing `ContentPackManifestValidator` from `src/content/pack_manifest.py`
- Compositions with no pack refs pass validation unconditionally (no breaking change)

## Out of Scope
- Automatic pack discovery or dependency resolution
- Pack version pinning
- Downloading or installing missing packs

## Acceptance Criteria
- Assembly of a composition referencing a disabled pack raises `AssemblyPackError` with the pack_id in the message
- Assembly of a composition whose pack has an unresolved dependency raises `AssemblyPackError` naming the missing dependency
- Assembly of a composition with no pack refs succeeds unchanged
- All existing integration tests pass

## Related Tickets
- TCK-20260614-WORLDMOD-UNIFY (prerequisite)
- TCK-20260609-CONTENT-PACK-FORMAT (pack manifest schema origin)

## Related Docs
- `docs/content/pipeline_contract.md`
- `docs/world/assembly_contract.md`

## Related Code Areas
- `src/worldassembly/resolver.py` — WorldAssemblyResolver.assemble()
- `src/worldassembly/schema.py` — WorldCompositionSpec.catalog_refs
- `src/content/pack_manifest.py` — ContentPackManifest, ContentPackManifestValidator
- `data/content/packs/*.yaml` — pack manifest files

## Assumptions / Open Questions
- `catalog_refs` may reference catalog family paths (e.g. `"entities/combat_profiles"`) rather than pack IDs — implementation must determine which refs are pack-addressed vs. family-addressed

## Test Summary
- Unit: `tests/unit/worldassembly/test_pack_validation.py` — disabled pack fails, missing dependency fails, no-pack composition passes
- Integration: add a composition with a pack ref to `test_real_content_world_compositions.py`

## Files Changed
<!-- filled during implementation -->

## Completion Summary
<!-- filled during implementation -->
