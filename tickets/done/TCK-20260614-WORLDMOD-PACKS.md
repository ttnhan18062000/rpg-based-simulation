---
status: done
layer: engine
authority: P1
audience: agent
ticket_id: TCK-20260614-WORLDMOD-PACKS
phase: done
date: 2026-06-14
tags: [worldmodules, content-packs, assembly, validation]
---

# TCK-20260614-WORLDMOD-PACKS

## Title
Content pack dependency validation at assembly time

## Status
DONE

## Tier
standard

## Type
feature

## Priority
P1

## Request Summary
`ContentPackManifest` (`src/content/pack_manifest.py`) defines a complete pack contract with `pack_id`, `enabled`, `dependencies`, `included_families`, `sample_compositions`. `WorldCompositionSpec` currently has a `catalog_refs` field for referencing content families, but this field is overloaded — it conflates catalog family paths (e.g. `"entities/combat_profiles"`) with content pack IDs. Pack dependency validation requires a clean, dedicated field. This ticket adds an explicit `pack_refs: list[str]` field to `WorldCompositionSpec` and validates those pack dependencies at assembly time.

## Scope
- Add `pack_refs: List[str] = []` to `WorldCompositionSpec` in `src/worldassembly/schema.py`
  - Do NOT overload `catalog_refs` — keep it for catalog family references only
- At the start of `WorldAssemblyResolver.assemble()`, after loading the composition, validate pack dependencies:
  - For each `pack_id` in `WorldCompositionSpec.pack_refs`, load the corresponding `ContentPackManifest`
  - Check `enabled == True`; raise `AssemblyPackError` if disabled, naming the pack_id
  - Check all `dependencies` packs are also enabled; raise `AssemblyPackError` if any dependency is missing or disabled
- Define `AssemblyPackError(ValueError)` in `src/worldassembly/resolver.py`
- Pack manifests loaded from `data/content/packs/*.yaml`; use existing `ContentPackManifestValidator` from `src/content/pack_manifest.py`
- Compositions with empty `pack_refs` pass validation unconditionally (no breaking change)

## Out of Scope
- Automatic pack discovery or dependency resolution
- Pack version pinning
- Downloading or installing missing packs

## Acceptance Criteria
- `WorldCompositionSpec` has a `pack_refs: List[str]` field (separate from `catalog_refs`)
- Assembly of a composition with `pack_refs: ["frontier_extended_pack"]` where that pack is disabled raises `AssemblyPackError` with the pack_id in the message
- Assembly of a composition whose pack has an unresolved dependency raises `AssemblyPackError` naming the missing dependency
- Assembly of a composition with empty `pack_refs` succeeds unchanged
- `catalog_refs` behaviour is unchanged (family-level refs are not treated as pack IDs)
- All existing integration tests pass

## Related Tickets
- TCK-20260614-WORLDMOD-UNIFY (prerequisite)
- TCK-20260609-CONTENT-PACK-FORMAT (pack manifest schema origin)

## Related Docs
- `docs/content/pipeline_contract.md`
- `docs/world/assembly_contract.md`

## Related Stored Artifacts
- `staging_artifacts/TCK-20260614-WORLDMOD-PACKS/plan.md`
- `staging_artifacts/TCK-20260614-WORLDMOD-PACKS/investigation.md`
- `staging_artifacts/TCK-20260614-WORLDMOD-PACKS/test_plan.md`

## Related Code Areas
- `src/worldassembly/resolver.py` — WorldAssemblyResolver.assemble(), AssemblyPackError
- `src/worldassembly/schema.py` — WorldCompositionSpec (add pack_refs field)
- `src/content/pack_manifest.py` — ContentPackManifest, ContentPackManifestValidator
- `data/content/packs/*.yaml` — pack manifest files

## Assumptions / Open Questions
- `catalog_refs` remains for catalog family references and is NOT modified by this ticket
- `NormalizedWorldComposition` does not carry `pack_refs` — validation is a pre-assembly gate

## Implementation Notes
- Pack validation inserted in `assemble()` right after `WorldCompositionNormalizer.normalize(composition)` and before the `enabled_refs` collection
- `assemble()` accepts both `WorldCompositionSpec` and `dict` — pack_refs extracted from both forms
- Load manifest via `ContentPackManifest.model_validate(yaml.safe_load(...))` using `pathlib.Path`

## Test Summary
- Unit: `tests/unit/worldassembly/test_pack_validation.py` — 4 tests
- Integration: extended `test_real_content_world_compositions.py` with 1 pack-ref test

## Files Changed
- `src/worldassembly/schema.py` — added `pack_refs` field to `WorldCompositionSpec`
- `src/worldassembly/resolver.py` — added `AssemblyPackError`, pack validation block in `assemble()`
- `tests/unit/worldassembly/test_pack_validation.py` — new file, 4 unit tests
- `tests/integration/worldassembly/test_real_content_world_compositions.py` — 1 new integration test

## Completion Summary
Added `pack_refs: List[str]` field to `WorldCompositionSpec`. Defined `AssemblyPackError(ValueError)` in `resolver.py`. Added pack validation block at the start of `WorldAssemblyResolver.assemble()` that loads each referenced pack's `ContentPackManifest`, gates on `enabled` and all `dependencies`, and raises `AssemblyPackError` with the offending pack_id in the message. Fixed `WorldCompositionNormalizer` to strip `pack_refs` before passing data to `NormalizedWorldComposition` (extra="forbid"). Created 4 unit tests and 1 integration test. Added parity ledger entry `SUBSTRATE-NEW-006`. All 76 worldassembly tests pass (1 pre-existing unrelated failure).
