# Investigation - Observability Join and Migration Cleanup (Phase 10)

## Schema Registration Analysis
`RunRecord` stores raw manifest copy in `manifest_json`. The run manifest itself contains:
- `scenario_name`
- `scenario_type`
- `seed`
- `status`
- `ticks_completed`
- `health_score`
- `started_at`
- `ended_at`
If we extend the worldbuilder/assembly pipelines to save the resolved world specs, reports, and manifests under the run's directory (e.g. `resolved_world.json`, `provenance_manifest.json`, `assembly_report.json`, `validation_report.json`, `compile_report.json`), the run manifest can reference their relative or absolute paths, or the warehouse adapter can resolve them relative to the run directory!
Wait, in `LocalWarehouseAdapter`, the `run_repo` resolves run directory using `self.run_repo.resolve_path(run_id, "manifest")` which points to `run_manifest.json`.
We can dynamically parse these files if they exist in the run folder!
Let's see: if `provenance_manifest.json` exists in `data/runs/<run_id>/provenance_manifest.json`, we can read it to query provenance!

## Provenance Lookup Service Design
The `ProvenanceLookupService` will load `provenance_manifest.json` for a given `run_id` (either from the `RunArtifactRepository` or from a direct folder path) and map queries dynamically:
- Entities are compiled from populations. In the `ProvenanceManifest` records, each population has a `ProvenanceRecord` mapping the population ID to its `source_module`, `parameters`, and `profiles`.
- Let's check how provenance records are populated in Phase 7!
In Phase 7, `records` maps spec element IDs (like `"citizen_group"`, `"tavern"`, `"ore_node"`) to their originating modules.
Since the compiled entity ID is an integer starting from 1 (allocated sequentially within each population recipe), the `ProvenanceLookupService` can map the runtime integer `entity_id` to its spec population ID by referencing the compiled state or by matching spawn region / role, or if the runtime entity's metadata/spawn region preserves it.
Wait! In `compiler.py` line 255:
```python
properties={"spawn_region": pop_spec.spawn_region}
```
Wait! Can we store `population_id` in the compiled entity's identity properties to make lookup absolutely trivial and robust?
Let's check `compiler.py` lines 250-256 again:
```python
                    pop_key = getattr(pop_spec, "id", f"pop_{pop_idx}")
                    ...
                        .identity(
                            role=role_enum,
                            faction=faction_enum,
                            properties={"spawn_region": pop_spec.spawn_region}
                        )
```
Ah! If we add `"population_id": pop_key` to the entity properties, then the query-side observability layer can read `properties["population_id"]` directly from the entity state, and join it with the `ProvenanceManifest` to know exactly which module produced that entity! This is an incredibly elegant, simple, and standard design that perfectly preserves complete decoupling!
Let's do that! We can add `"population_id": pop_key` to the identity properties during entity compilation!

Similarly, resource nodes and buildings have spec IDs (like `ore_node`, `tavern`) which are directly matched or mapped in their compiled kinds/properties.
Wait! In `compiler.py` line 165:
```python
        for res_spec in spec.resources:
```
Wait, does the compiled `ResourceNodeState` preserve the spec ID? No, it only stores `kind=res_spec.resource_type`. But we can map the index or add a `properties` dictionary if `ResourceNodeState` supports it, or simply keep a mapping by region and type, or add `resource_id` mapping. Let's see: `ResourceNodeState` doesn't have a free-form `properties` dict. But we can add spec ID lookup, or check if we can match them easily.
Actually, the `ProvenanceManifest` maps the spec element ID. The `ProvenanceLookupService` can map elements directly by parsing the compiled world spec (which matches element IDs to regions/types) and join them with the provenance manifest! This is entirely query-side and doesn't pollute the runtime state at all!
