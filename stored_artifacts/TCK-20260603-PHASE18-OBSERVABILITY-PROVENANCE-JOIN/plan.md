# Implementation Plan: Phase 18 Observability Provenance Join

This plan details the integration of resolved world assembly provenance sidecars and compile-time metadata into the post-run analytics pipeline.

## Proposed Changes

### Observability Schemas and Warehouse Models
- Modify `RunManifest` (`src/observability/reporting/artifact_repository.py`) and `RunRecord` (`src/observability/warehouse/models.py`) to add:
  - `compile_context_path: Optional[str] = None`
  - `runtime_content_source: Optional[str] = None`
- Update warehouse adapters (`LocalWarehouseAdapter` in `src/observability/warehouse/adapters.py` and ClickHouse client in `src/observability/warehouse/clickhouse.py`) to map and ingest these two fields.

### Kernel Registration
- Update `Kernel.__init__` in `src/engine/kernel.py` to accept resolved artifact path arguments and save them during `RunManifest` creation.
- Set up automatic fallback to globally set content catalog source and fingerprints from `src/core/registries`.

### Lab Orchestrator
- Modify `ScenarioLabOrchestrator.run_lab` in `src/lab/orchestrator.py` to detect if the world has a resolved profile directory, load `compile_context.json`, pass the compile context to the world compiler, and forward all resolved artifact paths to the `Kernel`.

### Provenance Lookup Service
- Update `ProvenanceLookupService` in `src/observability/warehouse/provenance_lookup.py` to map:
  - Numeric `entity_id` (or string representing numeric ID) to its `population_id` (using the deterministic spawning order from `world.resolved.yaml`).
  - Numeric `resource_id` to its source resource spec ID.
  - Numeric `building_id` to its source building spec ID.
- Ensure the lookup methods join these mapped IDs to their module, profile, faction, or role origin.

### Provenance-Aware Grouping
- Update `AnalysisPipeline` and anomaly miners to query the provenance lookup service and group anomalies or violations by their provenance source.

## Verification Plan

### Automated Tests
- Run `pytest tests/unit/observability/test_provenance_lookup.py`
- Add new unit tests to check the updated mapping methods of `ProvenanceLookupService`.
- Verify the entire test suite passes cleanly.
