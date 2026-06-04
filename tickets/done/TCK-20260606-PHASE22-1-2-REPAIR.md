# TCK-20260606-PHASE22-1-2-REPAIR

## Title

Repair fail-closed schemas and composition normalization validation using real files

## Status

DONE

## Request Summary

Ensure active authoring schemas are fail-closed and composition normalization preserves structure using real content files under `data/content/`.
Specifically:
- Schema validation must fail on unknown fields when loading real compositions/modules.
- Normalization must correctly parse real composition files and preserve attributes such as `default_perspectives`.

## Scope

- Create a ticket file and staging artifacts (plan.md, investigation.md, test_plan.md) in `staging_artifacts/TCK-20260606-PHASE22-1-2-REPAIR/`.
- Verify/ensure Pydantic schemas in `src/worldassembly/schema.py` and `src/worldmodules/schema.py` reject unknown top-level fields during loading (using `extra="forbid"` config, which is already present).
- Write unit/integration tests in `tests/unit/worldassembly/test_assembly.py` loading real files from `data/content/world_modules/` and `data/content/world_compositions/`.
- Test that injecting unknown fields in a real module/composition file fails validation.
- Verify `default_perspectives` is preserved during composition normalization.
- Ensure that mixed configurations (both `modules` shorthand and `module_refs` dictionary list) raise a `ValueError`.
- Verify deterministic fingerprinting of composition.

## Out of Scope

- Modifying the combat engine or EntityState.
- Parsing YAML comments as behavior-determining metadata.

## Acceptance Criteria

- [x] Active schemas reject unknown top-level fields.
- [x] Real files are loaded through canonical path in tests.
- [x] Unknown field failure error message includes file, family, and record identifiers.
- [x] Composition normalization is verified with real files.
- [x] `default_perspectives` survives normalization and is preserved.
- [x] Mixed configurations of shorthand `modules` and structured `module_refs` fail with `ValueError`.
- [x] Composition fingerprint is deterministic.

## Related Tickets

- None

## Related Docs

- `world_phase_20_28_repair.md`

## Related Stored Artifacts

- None

## Related Code Areas

- `src/worldassembly/schema.py`
- `src/worldmodules/schema.py`
- `tests/unit/worldassembly/test_assembly.py`

## Assumptions / Open Questions

- None

## Implementation Notes

- Added exception wrappers around `WorldModuleSpec` and `WorldCompositionSpec` loading in the repositories and CLI to enrich validation errors with the file path, content family, and record ID.
- Added test fixtures and test cases to `tests/unit/worldassembly/test_assembly.py` asserting validation failures and verifying real file loading.

## Test Summary

- Added 5 new unit tests under `tests/unit/worldassembly/test_assembly.py` covering fail-closed validation, normalization, perspective survival, and error enrichment.
- Verified all 20 assembly tests pass.

## Files Changed

- `src/worldmodules/repository.py`
- `src/worldbuilding/repository.py`
- `src/worldbuilding/cli.py`
- `tests/unit/worldassembly/test_assembly.py`
