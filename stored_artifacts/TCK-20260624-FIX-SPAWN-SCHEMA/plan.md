# TCK-20260624-FIX-SPAWN-SCHEMA — Plan

## Ordered Steps

1. **schema.py** — Add `ClassTableDefinition(CatalogBaseDefinition)` with `class_id_by_role: Dict[str, List[str]]` and `extra="forbid"` (inherited from `CatalogBaseDefinition`).

2. **repository.py** — Extend `ContentFamilySpec` dataclass with `schema_version_map: Optional[Dict[str, Type[BaseModel]]] = None`. Update loader loop to: if `schema_version_map` and item has `schema_version`, pick schema from map; otherwise use `spec.schema`.

3. **repository.py** — Import `ClassTableDefinition` from schema. Update `spawn_tables` `ContentFamilySpec` entry to include `schema_version_map={"spawntabledefinition.v1": SpawnTableDefinition, "classtable.v1": ClassTableDefinition}`.

4. **repository.py** — Add `class_tables: Dict[str, ClassTableDefinition] = {}` index. Update `get_all_ids_by_type` and `get_deprecated_ids` to include `class_table`. Add `get_class_table()` lookup method. Note: `class_tables` share the `spawn_tables` repository_index OR we use a separate index — but the current architecture uses `repository_index` to set the attribute. We need to decide: share `spawn_tables` index (mixed types) or introduce a second index. Best: introduce `class_tables` index and route `ClassTableDefinition` records there via schema_version_map.

   Actually the `repository_index` field tells `setattr(self, spec.repository_index, results)`. Since we want class tables in a separate dict, we need a second family spec or a custom dispatch. Simpler: store all spawn_tables records in `spawn_tables` dict (mixed — `SpawnTableDefinition | ClassTableDefinition`) OR add a secondary index in the loader for `schema_version_map` results. 

   Minimal: `class_tables` dict in CatalogRepository; loader routes each record to the spec's `repository_index` OR to a `schema_version_map[schema_version].index` if we add that. To keep it minimal, store all records in `spawn_tables` dict regardless of sub-type (Python dict is just `Dict[str, BaseModel]`). The existing `get_spawn_table` lookup will still work for `forest_spawn_pool`, and a new `get_class_table` casts the result.

   Even simpler: add a dedicated `class_tables: Dict[str, ClassTableDefinition]` dict and separate the routing in the loader by checking `isinstance(validated, ClassTableDefinition)`.

5. **docs/mechanics/content_usage_matrix.md** — Add a row for `spawn/class_tables` family.

6. **Run tests** and verify.
