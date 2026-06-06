# TCK-20260527-COG-PHASE1-REGISTRIES

## Title

Implement Phase 1 Data Registries and Content Pack Loaders

## Status

DONE

## Tier
standard

## Type
chore

## Priority
P1

## Request Summary

Implement static read-only world registries (ItemRegistry, ResourceRegistry, EnemyRegistry, RecipeRegistry, ServiceRegistry, and RegionRegistry) that load Phase 1 content packs dynamically from JSON or YAML data files. Ensure that the registries are fast, static, read-only at runtime, and throw clear validation errors if invalid ID bindings are resolved.

## Scope

- Implement static registry modules and dataclass models under `src/core/registries.py`.
- Define Phase 1 adventure content pack definitions inside `src/data/registries/phase1_adventure_seed.json` (or YAML).
- Add startup validation tests ensuring material matching integrity under `tests/unit/strategic/test_registries.py`.

## Out of Scope

- Implementing the requirement evaluator or providers (these belong to Tasks 4-7).

## Acceptance Criteria

- Registries are read-only at runtime and allow O(1) lookups by ID.
- Validation checks ensure recipe ingredient IDs exist in registries.
- Unit tests under `tests/unit/strategic/test_registries.py` pass.

## Related Tickets

- None

## Related Docs

- `entity_enhance_phase1.md` (Tasks 2 & 3)

## Related Stored Artifacts

- None

## Related Code Areas

- `src/core/registries.py`
- `src/data/registries/`
- `tests/unit/strategic/test_registries.py`

## Assumptions / Open Questions

- None

## Implementation Notes

- None

## Test Summary

- Automated referential integrity checks pass successfully: `pytest tests/unit/strategic/test_registries.py`.

## Files Changed

- `tickets/inprogress/TCK-20260527-COG-PHASE1-REGISTRIES.md`
- `src/core/registries.py`
- `tests/unit/strategic/test_registries.py`

## Completion Summary

- Implemented structured read-only `ItemRegistry`, `ResourceRegistry`, `EnemyRegistry`, `RecipeRegistry`, `ServiceRegistry`, and `RegionRegistry` under `src/core/registries.py`. Bootstrapped registries with comprehensive Phase 1 Adventure Seed data pack. Created unit test suite test_registries.py validating key checks and full database referential integrity. All tests pass successfully!
