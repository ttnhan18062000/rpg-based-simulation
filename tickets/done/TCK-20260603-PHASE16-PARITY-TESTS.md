# TCK-20260603-PHASE16-PARITY-TESTS

## Title

Phase 16 — Catalog-vs-Legacy Runtime Parity Tests

## Status

DONE

## Tier
standard

## Type
chore

## Priority
P1

## Request Summary

Ensure dynamic content catalog configuration matches or exceeds legacy capabilities. Implement content parity validation, cross-reference behavior checks, simulation smoke test, and legacy fallback configuration logic.

## Scope

- Create a comparison parity check verifying legacy vs production catalog configurations (items, resources, enemies, recipes, services, regions).
- Implement cross-reference validation tests (loot tables, recipe inputs/outputs, service requirements, spawn region links).
- Implement a simulation smoke test running a minimal tick count using catalog-seeded registries.
- Implement legacy fallback logic in `seed_phase1_content` with optional (`catalog_optional`) vs strict (`catalog_required`) modes.

## Out of Scope

- Removing legacy hardcoded content backup completely.
- Balancing combat parameters.

## Acceptance Criteria

- Content parity comparison runs and passes (allowing tags and spawn region supersets).
- Cross-reference behavior tests pass successfully.
- Smoke simulation runs deterministic tick loop without hard-law violations under catalog seeding.
- Falling back to legacy defaults behaves as expected: optional mode allows fallback, required mode raises error on missing/invalid catalog.

## Related Tickets

- `TCK-20260603-PHASE15-REGISTRY-BRIDGE`

## Related Docs

- `world_phases_11_19.md`

## Related Stored Artifacts

- None

## Related Code Areas

- `src/core/registries.py`
- `tests/unit/core/test_registry_parity.py`

## Assumptions / Open Questions

- None

## Implementation Notes

- None

## Test Summary

- Executed `pytest tests/unit/core/test_registry_bridge.py tests/unit/core/test_registry_parity.py tests/unit/core/test_catalog_fallback.py tests/unit/core/test_registry_cross_reference.py tests/unit/core/test_catalog_smoke_simulation.py` (All 9 tests passed)
- Executed `pytest tests/unit/core/test_rpg_math.py tests/unit/strategic/test_registries.py` (All 6 tests passed)

## Files Changed

- `src/core/registries.py`
- `tests/unit/core/test_registry_parity.py`
- `tests/unit/core/test_catalog_fallback.py`
- `tests/unit/core/test_registry_cross_reference.py`
- `tests/unit/core/test_catalog_smoke_simulation.py`

## Completion Summary

- Implemented optional vs strict catalogrequired modes inside `seed_phase1_content()`, checking for validation errors with `CatalogValidator`.
- Expanded comparison checks in `test_registry_parity.py` with proper subset validation for tags/spawn regions.
- Added cross-reference verification suite in `test_registry_cross_reference.py` verifying relational integrity.
- Implemented simulator kernel smoke tick test in `test_catalog_smoke_simulation.py` demonstrating tick progress.
