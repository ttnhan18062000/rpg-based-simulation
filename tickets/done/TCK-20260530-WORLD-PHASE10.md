---
status: historical
layer: engine
authority: P1
audience: agent
ticket_id: TCK-20260530-WORLD-PHASE10
phase: done
date: 2026-05-30
tags: [world, phase10]
---

# TCK-20260530-WORLD-PHASE10

## Title

Observability Join and Migration Cleanup

## Status

DONE

## Tier
standard

## Type
chore

## Priority
P1

## Request Summary

Implement Phase 10: "Observability Join and Migration Cleanup" of `world_phases_0_10_updated.md` to connect world assembly provenance to observability and clean up migration debt.

## Scope

- **Task 10.1: Register resolved world artifacts with run records**:
  - Extend `RunRecord` in `src/observability/warehouse/models.py` with optional resolved world attributes (`resolved_world_path`, `provenance_manifest_path`, `assembly_report_path`, `validation_report_path`, `compile_report_path`, `catalog_fingerprint`, `module_fingerprints`, `state_hash`).
  - Update `LocalWarehouseAdapter.ingest_run` in `src/observability/warehouse/adapters.py` to dynamically parse these attributes from the run manifest.
  - Update `ClickHouseWarehouseAdapter` and `ClickHouseSchemaManager` in `src/observability/warehouse/clickhouse.py` to align ClickHouse database schemas and insert queries.
- **Task 10.2: Add observability provenance lookup**:
  - Implement a dedicated sidecar lookup service `ProvenanceLookupService` inside `src/observability/warehouse/provenance_lookup.py` allowing post-run analysis to map entity, group, region, building, and resource IDs to their originating modules and catalog profiles.
- **Task 10.3: Mark legacy adapters and migration debt**:
  - Create `docs/mechanics/migration_debt.md` explicitly detailing remaining compatibility layers (direct `get_role_enum`, `get_faction_enum`, direct faction enum checks, and default compiler parameters), describing risks and the transition roadmap.
- **Verification**:
  - Add comprehensive unit tests verifying the run record registry changes and the new `ProvenanceLookupService` mapping.

## Out of Scope

- Runtime state mutations during tick execution.
- Full deprecation/removal of legacy adapters (migration mapping only).

## Acceptance Criteria

- `RunRecord` model and database schemas support all specified optional world assembly fields.
- `LocalWarehouseAdapter` and `ClickHouseWarehouseAdapter` successfully ingest these fields.
- `ProvenanceLookupService` successfully resolves module origin and catalog profiles for entities, regions, buildings, and resources from sidecar provenance files.
- `docs/mechanics/migration_debt.md` exists and contains a complete, detailed audit of legacy adapters.
- All existing and new tests pass cleanly.

## Related Tickets

- `TCK-20260530-WORLD-PHASE9`

## Related Docs

- `world_phases_0_10_updated.md`

## Related Stored Artifacts

- None

## Related Code Areas

- `src/observability/warehouse/models.py`
- `src/observability/warehouse/adapters.py`
- `src/observability/warehouse/clickhouse.py`
- `src/observability/warehouse/provenance_lookup.py`
- `docs/mechanics/migration_debt.md`

## Assumptions / Open Questions

- None

## Implementation Notes

- Extended `RunRecord` and `RunManifest` with optional resolved world assembly properties.
- Refactored `LocalWarehouseAdapter` and `ClickHouseWarehouseAdapter` to safely support and query these fields.
- Implemented `ProvenanceLookupService` doing query-side post-run provenance joins against manifests.
- Wrote `docs/mechanics/migration_debt.md` auditing legacy adapters.

## Test Summary

- Created `tests/unit/observability/test_provenance_lookup.py` containing 3 comprehensive test cases.
- Executed full test suite - all 81 tests passed successfully.

## Files Changed

- `src/observability/warehouse/models.py`
- `src/observability/reporting/artifact_repository.py`
- `src/observability/warehouse/adapters.py`
- `src/observability/warehouse/clickhouse.py`
- `src/worldbuilding/compiler.py`
- `src/observability/warehouse/provenance_lookup.py`
- `docs/mechanics/migration_debt.md`
- `tests/unit/observability/test_provenance_lookup.py`

## Completion Summary

- Successfully connected resolved world assembly provenance to telemetry observability.
- Created robust query-side post-run lookup service mapping elements to originating module and catalog schemas.
- Completed full audit of all migration debt.
