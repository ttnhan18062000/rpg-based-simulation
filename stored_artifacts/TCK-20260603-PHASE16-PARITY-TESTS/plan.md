# Implementation Plan - Phase 16 Parity Tests

This plan describes the implementation and verification strategy for testing legacy-to-catalog parity, downstream behaviors, and smoke simulation runs in catalog mode.

## Proposed Changes

### Component 1: src/core/registries.py
* Update `seed_phase1_content(catalog_repo: Optional[Any] = None, required: bool = False)` signature.
* If `required` is `True`:
  - If `catalog_repo` is `None`, raise a `ValueError` indicating a catalog repository is required in strict mode.
  - If `catalog_repo` is provided, validate it using `CatalogValidator(catalog_repo).validate()`. If any issues with `severity == "ERROR"` are found, raise a `CatalogValidationError`.

### Component 2: tests/unit/core/test_registry_parity.py
* We have already implemented the base parity checks comparing legacy vs production catalog configurations.
* Ensure it cleanly covers all items, enemies, recipes, resources, and regions tags/spawn region subsets.

### Component 3: tests/unit/core/test_registry_cross_reference.py
* Create a new test suite to verify referential integrity of catalog-loaded records.
* Asserts:
  - Enemy drop IDs exist in catalog items.
  - Recipe ingredients and output IDs exist in catalog items.
  - Starting inventory item references exist in catalog items.
  - Service provider referenced items exist in catalog items.
  - Spawn region references link to valid catalog regions.

### Component 4: tests/unit/core/test_catalog_smoke_simulation.py
* Run a minimal simulation run of e.g. 5 ticks using catalog-seeded registries.
* Asserts:
  - World compilation works with compiled entities.
  - Ticks proceed with no lookup errors or hard-law violations.

## Verification Plan

### Automated Tests
* Run `pytest tests/unit/core/test_registry_parity.py`
* Run `pytest tests/unit/core/test_registry_cross_reference.py`
* Run `pytest tests/unit/core/test_catalog_smoke_simulation.py`
