# TCK-20260624-FIX-SPAWN-SCHEMA — Investigation

## Root Cause

`data/content/spawn_tables.yaml` contains two record types with incompatible shapes:

1. `forest_spawn_pool` — has `spawn_weights: Dict[str, float]`; validated by `SpawnTableDefinition`
2. `default_class_table` — has `class_id_by_role: Dict[str, List[str]]`; no matching schema exists

`SpawnTableDefinition` inherits `CatalogBaseDefinition` which has `extra="forbid"`, so `class_id_by_role` triggers `Extra inputs are not permitted`. Additionally `spawn_weights` is `Field(...)` (required), so `default_class_table` also fails `Field required`.

The ticket describes `class_id_by_role` as `Dict[str, str]` but the YAML data has list values: `hero: ["WARRIOR", "MAGE", "ROGUE"]`. The correct type is `Dict[str, List[str]]`.

## Dispatch Mechanism

`CatalogRepository.load_all()` iterates `CANONICAL_FAMILIES` (a `List[ContentFamilySpec]`). For each spec it reads the YAML file and validates every record against `spec.schema(**item)` — one schema per family, applied uniformly to all records in the file.

There is no per-record schema dispatch based on `schema_version` or any other field discriminator.

## Solution Chosen: schema_version_map on ContentFamilySpec

`ContentFamilySpec` is extended with an optional `schema_version_map: Optional[Dict[str, Type[BaseModel]]]` field. When present, the loader uses it to look up the schema by `item["schema_version"]` before falling back to `spec.schema`. This avoids:
- Splitting the YAML (not allowed)
- Adding a `type` discriminator field to the YAML (would change data)
- Registering the same file twice (would double-process all records)

The `spawn_tables` family spec gains:
```python
schema_version_map={
    "spawntabledefinition.v1": SpawnTableDefinition,
    "classtable.v1": ClassTableDefinition,
}
```

## Data Shape Confirmation

```yaml
- id: "default_class_table"
  schema_version: "classtable.v1"
  class_id_by_role:
    hero: ["WARRIOR", "MAGE", "ROGUE"]   # list of str, not str
```

`class_id_by_role` values are `List[str]`, so `ClassTableDefinition` must use `Dict[str, List[str]]`.
