# Implementation Plan - Observability Join and Migration Cleanup (Phase 10)

Connect world assembly provenance sidecars to post-run telemetry observability, and formally document remaining legacy migration debt.

## User Review Required

> [!IMPORTANT]
> - telemetries query and warehouse database schemas are expanded with optional columns. Database migrations (ClickHouse schema statements) are fully backward-compatible.
> - Provenance joins are performed exclusively on the query side post-run and have zero impact on tick execution or memory performance during simulation execution.

## Proposed Changes

### Observability Database Schema & Ingestion

#### [MODIFY] [models.py](file:///home/vboxuser/Work/rpg-based-simulation/src/observability/warehouse/models.py)
- Extend `RunRecord` with optional fields:
  - `resolved_world_path: Optional[str] = None`
  - `provenance_manifest_path: Optional[str] = None`
  - `assembly_report_path: Optional[str] = None`
  - `validation_report_path: Optional[str] = None`
  - `compile_report_path: Optional[str] = None`
  - `catalog_fingerprint: Optional[str] = None`
  - `module_fingerprints: Optional[Dict[str, str]] = None`
  - `state_hash: Optional[str] = None`

#### [MODIFY] [adapters.py](file:///home/vboxuser/Work/rpg-based-simulation/src/observability/warehouse/adapters.py)
- Update `LocalWarehouseAdapter.ingest_run` and `query_runs` to extract these optional fields from `run_manifest.json` and map them into `RunRecord`.

#### [MODIFY] [clickhouse.py](file:///home/vboxuser/Work/rpg-based-simulation/src/observability/warehouse/clickhouse.py)
- Update `ClickHouseSchemaManager.init_schema` to declare the new fields in the `runs` table.
- Update `ClickHouseWarehouseAdapter.ingest_run` and `query_runs` to store and load these new columns.

### Query-Side Provenance Analytics

#### [NEW] [provenance_lookup.py](file:///home/vboxuser/Work/rpg-based-simulation/src/observability/warehouse/provenance_lookup.py)
- Implement `ProvenanceLookupService` supporting query joins against `ProvenanceManifest`:
  - `get_entity_origin(entity_id: str)` -> Module origin + profile metadata.
  - `get_region_origin(region_id: str)` -> Region bounds, type, and source module.
  - `get_building_origin(building_id: str)` -> Building type and source module.
  - `get_resource_origin(resource_id: str)` -> Resource type, ticks, and source module.

### Documentation & Debt Tracking

#### [NEW] [migration_debt.md](file:///home/vboxuser/Work/rpg-based-simulation/docs/mechanics/migration_debt.md)
- Detail direct enums uses (`get_role_enum`, `get_faction_enum`), compiler parameter fallbacks, and enum matching hacks. Map transition roadmaps, compatibility reasons, and risks.

## Verification Plan

### Automated Tests
- Create `tests/unit/observability/test_provenance_lookup.py` covering:
  - Dry-run schema ingestion checks for extended `RunRecord` columns.
  - `ProvenanceLookupService` joins mapping entity, region, building, and resource IDs back to their catalog/module origin.
