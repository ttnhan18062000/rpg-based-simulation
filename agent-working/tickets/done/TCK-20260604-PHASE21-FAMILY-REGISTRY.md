---
status: historical
layer: guidelines
authority: P1
audience: agent
ticket_id: TCK-20260604-PHASE21-FAMILY-REGISTRY
phase: done
date: 2026-06-04
tags: [phase21, family, registry]
---

# TCK-20260604-PHASE21-FAMILY-REGISTRY

## Title
Phase 21 — Content family registry and strict load report

## Status
DONE

## Tier
standard

## Type
chore

## Priority
P1

## Request Summary
Create a central registry `ContentFamilySpec` describing each content family and make `CatalogRepository` load all content dynamically based on this registry. Add a strict load report output/storage from `CatalogRepository.load_all()`.

## Scope
- Define `ContentFamilySpec` dataclass/model.
- Populate `CANONICAL_FAMILIES` registry representing all content families.
- Refactor `CatalogRepository.load_all()` to dynamic loading based on the registry.
- Enforce strict loading modes (unknown extra files, missing required files, empty families, duplicate paths) and compile a load report.
- Extend `tests/unit/content/test_catalog.py` to verify the family registry and strict report.

## Out of Scope
- Rewriting downstream validators or runtime registry projection (that is for Phase 22+).

## Acceptance Criteria
- All canonical content families are declared in `ContentFamilySpec`.
- `CatalogRepository.load_all()` uses `ContentFamilySpec` for dynamic file discovery and loading.
- Unknown/declared required families fail in strict mode (raise exception or report accordingly).
- Load report is returned/available after `load_all()`.
- Load report includes counts, missing files, ignored files, duplicate ids, schema errors, and fingerprints.
- Existing tests (such as `test_base_catalog_loading`) still pass cleanly.

## Related Tickets
- TCK-20260604-PHASE20-CONTRACT-AND-TESTMAP

## Related Docs
- `world_phase_20_28.md`

## Related Stored Artifacts
- None

## Related Code Areas
- `src/content/repository.py`
- `tests/unit/content/test_catalog.py`

## Assumptions / Open Questions
- Does strict mode fail by raising an error on missing required files, or does it return the report with errors?
  - Task 21.2 says: "Missing required files fail in strict mode. Unknown declared required family fails in strict mode."
  - So we should raise an exception (like `ValueError` or a custom exception) in strict mode when there are missing required files or duplicate paths.

## Implementation Notes
- Defined `ContentFamilySpec` dataclass for central content family declaration.
- Populated `CANONICAL_FAMILIES` registry containing all 33 canonical families.
- Refactored `CatalogRepository.load_all(strict=False)` to dynamically load files based on registry metadata.
- Implemented `CatalogLoadReport` to capture loaded families/files, record counts, missing optional/required files, unknown/ignored files, duplicate IDs, and schema errors.
- Enforced strict checks: raises `ValueError` in strict mode if required files are missing, if specs contain duplicate paths, or if schema validation fails.

## Test Summary
- Ran unit tests verifying the registry and report behavior: `pytest tests/unit/content/test_catalog.py` (7 passed).
- Added test coverage for:
  - Missing required files in strict mode.
  - Ignored/unknown files.
  - Empty catalog family files.
  - Duplicate path specifications in specs registry.
  - Fingerprint uniqueness and determinism.
- Ran all existing core registries and world assembly tests to verify no regressions: `pytest tests/unit/core/` and `pytest tests/unit/worldassembly/` (all passed cleanly).

## Files Changed
- `src/content/repository.py`
- `tests/unit/content/test_catalog.py`

## Completion Summary
- Successfully implemented Phase 21: Content family registry and strict load report.
- The `CatalogRepository` loader is now dynamic and fully auditable, raising clear exceptions in strict mode and compiling detailed diagnostic load reports. All existing test suites pass without regression.
