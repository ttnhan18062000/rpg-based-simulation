---
status: historical
layer: guidelines
authority: P2
audience: agent
ticket_id: TCK-20260604-PHASE21-FAMILY-REGISTRY
artifact_type: plan
tags: [phase21, family, registry]
---

# Implementation Plan: Phase 21 Family Registry & Strict Load Report

## Proposed Changes

### Content Component

#### [MODIFY] [repository.py](file:///home/vboxuser/Work/rpg-based-simulation/src/content/repository.py)
- Implement `ContentFamilySpec` class describing each content family:
  - `family`: dotted name (e.g. `foundation.materials`)
  - `path`: relative path (e.g. `foundation/materials.yaml`)
  - `schema`: Pydantic class
  - `repository_index`: attribute on `CatalogRepository`
  - `required`: bool
  - `state_policy`: str
- Define `CANONICAL_FAMILIES` as the master registry list.
- Define `CatalogLoadReport` model/class containing:
  - `loaded_families`: list of family dotted names.
  - `loaded_files`: list of loaded file paths.
  - `record_counts`: dict of family to record count.
  - `missing_required_files`: list of required files that were missing.
  - `missing_optional_files`: list of optional files that were missing.
  - `ignored_files`: list of unknown/ignored file paths.
  - `duplicate_ids`: list of duplicate IDs found during load.
  - `schema_errors`: dict of file path to list/dict of Pydantic validation errors.
  - `fingerprint`: SHA256 signature of loaded content.
- Refactor `CatalogRepository.load_all(self, strict: bool = False) -> CatalogLoadReport`:
  - Dynamically load all families using `CANONICAL_FAMILIES`.
  - Scan directory to detect any untracked/ignored YAML files.
  - Track missing required and optional files.
  - Handle duplicate path checks (fail if duplicate paths exist in specs).
  - Catch Pydantic schema validation errors and record them.
  - If `strict` is True:
    - If `missing_required_files` is not empty: raise `ValueError`.
    - If any `schema_errors` occur: raise `ValueError` (or custom exception).
  - Compute fingerprint and return `CatalogLoadReport`.

### Test Component

#### [MODIFY] [test_catalog.py](file:///home/vboxuser/Work/rpg-based-simulation/tests/unit/content/test_catalog.py)
- Extend `test_base_catalog_loading` to assert load report values.
- Add strict validation tests for missing files, unknown files, empty files, and duplicate paths.

## Verification Plan

### Automated Tests
Run:
```bash
pytest tests/unit/content/test_catalog.py
```
Verify that existing tests and new strict tests pass cleanly.
