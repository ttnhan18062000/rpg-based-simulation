# TCK-20260603-PHASE18-OBSERVABILITY-PROVENANCE-JOIN

## Title

Observability Provenance Join

## Status

DONE

## Request Summary

Connect resolved world assembly provenance sidecars and compile-time metadata with post-run analytics and investigation reports to allow grouping anomalies/violations by source module, profile, faction, and seed.

## Scope

- Extend `RunManifest` schema with `compile_context_path` and `runtime_content_source`.
- Update `RunRecord` model in database/warehouse and corresponding Local/ClickHouse adapters to support `compile_context_path` and `runtime_content_source`.
- Populated resolved artifact paths and metadata (`compile_context_path`, `runtime_content_source`, `module_fingerprints`, `catalog_fingerprint`, etc.) in `RunManifest` during Kernel initialization, CLI compilation, and lab run orchestrator simulation runs.
- Enhance `ProvenanceLookupService` to map concrete compiled entity, region, building, and resource IDs to their respective source modules, profiles, factions, or roles.
- Enhance investigation tools or reports to group anomalies and violations by provenance source modules and profiles, reporting unknown origins explicitly.

## Out of Scope

- Direct runtime tracking of provenance in `EntityState`, `WorldState`, or other simulation loops. Keep it query-side only.

## Acceptance Criteria

- `RunManifest` includes fields for `compile_context_path` and `runtime_content_source`.
- Simulation runs register all resolved artifact paths correctly during startup and record them in the run directory `run_manifest.json`.
- `ProvenanceLookupService` successfully joins entity/region/resource/building IDs to their source module, profile, faction, or role.
- Post-run analysis groups anomalies/violations by source module or profile in reports.
- All unit, integration, and performance tests pass cleanly.

## Related Tickets

- None

## Related Docs

- `world_phases_11_19.md`

## Related Stored Artifacts

- None

## Related Code Areas

- `src/observability/reporting/artifact_repository.py`
- `src/engine/kernel.py`
- `src/observability/warehouse/models.py`
- `src/observability/warehouse/adapters.py`
- `src/observability/warehouse/clickhouse.py`
- `src/observability/warehouse/provenance_lookup.py`
- `src/observability/anomaly/pipeline.py`
- `src/lab/orchestrator.py`

## Assumptions / Open Questions

- We assume `entity_id`, `building_id`, and `resource_id` compilation ordering remains deterministic and predictable based on `world.resolved.yaml`.

## Implementation Notes

- Added `compile_context_path` and `runtime_content_source` fields to `RunManifest` and `RunRecord`.
- Updated DB mappings (LocalWarehouseAdapter, ClickHouse warehouse adapter) to handle these fields.
- Kernel initialization and lab orchestrator now populate and persist resolved world artifact paths.
- Enriched `ProvenanceLookupService` to map numeric runtime entity, building, resource, and region IDs to source templates and profiles, retrieving role and faction dynamically from `world.resolved.yaml` when necessary.
- Enhanced `RunReportGenerator` to aggregate anomalies/violations by source module, profile, and faction, displaying details in formatted tables in `run_report.md` and serializing them in `run_report.json`.

## Test Summary

- Run and passed unit tests: `tests/unit/observability/test_provenance_lookup.py` (added `test_provenance_lookup_with_mapped_ids` test).
- Run and passed integration tests: `tests/integration/observability/test_report_v2.py` (added `test_provenance_grouping_in_report` test) and `tests/integration/observability/test_run_report_generator.py`.
- Run and passed full scenario lab execution sweep tests: `tests/integration/lab/test_lab_observatory_integration.py`.

## Files Changed

- `src/observability/reporting/artifact_repository.py`
- `src/observability/reporting/run_report.py`
- `src/observability/warehouse/models.py`
- `src/observability/warehouse/adapters.py`
- `src/observability/warehouse/clickhouse.py`
- `src/observability/warehouse/provenance_lookup.py`
- `src/engine/kernel.py`
- `src/lab/orchestrator.py`
- `tests/unit/observability/test_provenance_lookup.py`
- `tests/integration/observability/test_report_v2.py`

## Completion Summary

All schema extensions, kernel registrations, and mapping services are fully implemented and verified via unit and integration tests. The pipeline is successfully query-side joined with compile-time sidecars, grouping anomalies by source module, profile, and faction in generated Markdown and JSON reports.
