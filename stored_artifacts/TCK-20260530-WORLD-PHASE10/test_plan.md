---
status: historical
layer: engine
authority: P2
audience: agent
ticket_id: TCK-20260530-WORLD-PHASE10
artifact_type: test_plan
tags: [world, phase10]
---

# Test Plan - Observability Join and Migration Cleanup (Phase 10)

Verify schema extensions, dry-run local and ClickHouse ingestion pipeline enhancements, and post-run provenance lookup queries.

## Scenarios to Test

1. **Extended RunRecord Model Validation**:
   - Instantiate a `RunRecord` passing all new optional world assembly parameters.
   - Verify serialization and field properties.

2. **Local Warehouse Ingestion Updates**:
   - Create a dummy run directory containing a `run_manifest.json` carrying optional world assembly paths and fingerprints.
   - Call `LocalWarehouseAdapter.ingest_run`.
   - Assert the returned `RunRecord` successfully populates all new fields.

3. **Provenance Lookup Joins**:
   - Create a dummy `ProvenanceManifest` mapping element IDs `"citizen_group"`, `"tavern"`, `"ore_node"`, and `"town_square"` to specific modules and catalog profiles.
   - Save the manifest as `provenance_manifest.json` in the mock run directory.
   - Use `ProvenanceLookupService` to query:
     - Entity group origin.
     - Region origin.
     - Building origin.
     - Resource origin.
   - Assert they match the definitions in `provenance_manifest.json` exactly.

4. **Engine Isolation Guard**:
   - Verify that running a full mock simulation tick does not mutate the state to store any provenance maps, keeping the runtime completely sidecar-only.
