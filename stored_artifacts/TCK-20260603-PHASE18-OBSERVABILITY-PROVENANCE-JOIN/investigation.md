# Investigation Notes: Phase 18 Observability Provenance Join

## Context & Findings

1. **RunManifest Schema**: Located in `src/observability/reporting/artifact_repository.py`. It holds paths to resolved files. We need to add `compile_context_path` and `runtime_content_source` to `RunManifest` and update database/warehouse mappings.
2. **Simulation Lifecycle & Kernel**: The `Kernel` initializes the run manifest at startup. The orchestrators (`src/lab/orchestrator.py`, `src/observability/sweeper.py`, and `src/cli/entry.py`) run the simulation. If a world is resolved/composition-based, we must retrieve these resolved paths and pass them to the `Kernel` (e.g. through the constructor or via `flags`).
3. **Provenance Lookup Service**: Defined in `src/observability/warehouse/provenance_lookup.py`. It takes a `run_id` and an element ID. Since the element IDs in the provenance manifest are high-level population or template IDs, we must add mapping functionality from compiled runtime IDs (like integer `entity_id`, building ID, resource ID, region ID) to their source records.
4. **Deterministic Compilation Mapping**:
   - Entities: IDs start at `1` and increment consecutively. They are compiled from `spec.entities`. We can map `entity_id` to its source `population_id` (the ID of the entity spec).
   - Resources: IDs start at `10000` and increment consecutively. We can map `resource_id` to the corresponding resource spec ID.
   - Buildings: IDs start at `20000` and increment consecutively. We can map `building_id` to the corresponding building spec ID.
   - Regions: Identifiers are strings directly corresponding to `spec.regions` IDs.
5. **Anomaly & Violation Grouping**: Anomalies/violations are mined post-run. We need to extend analysis pipelines to group violations or anomalies by their provenance source module or profile.

## Impact Surface
- `src/observability/reporting/artifact_repository.py`
- `src/observability/warehouse/models.py`
- `src/observability/warehouse/adapters.py`
- `src/observability/warehouse/clickhouse.py`
- `src/observability/warehouse/provenance_lookup.py`
- `src/engine/kernel.py`
- `src/lab/orchestrator.py`
- `src/observability/anomaly/pipeline.py`
