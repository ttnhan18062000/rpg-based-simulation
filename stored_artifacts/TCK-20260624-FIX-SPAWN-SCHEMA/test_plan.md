# TCK-20260624-FIX-SPAWN-SCHEMA — Test Plan

## Existing Tests (must pass)

- `tests/unit/content/test_content_paths.py::test_strict_load_on_real_content_dir` — PRIMARY target; must pass after fix
- `tests/unit/content/test_content_paths.py` — full suite; no regression
- `tests/unit/content/` — full directory; no schema regression

## Validation Points

1. `forest_spawn_pool` still validates against `SpawnTableDefinition` correctly
2. `default_class_table` validates against `ClassTableDefinition` correctly
3. `load_all(strict=True)` on real `data/content/` dir returns no schema errors
4. `schema_version_map` dispatch falls back to `spec.schema` when no `schema_version` field or no match
5. `CatalogRepository` initializes `class_tables` dict without error

## Commands

```bash
python3 -m pytest tests/unit/content/test_content_paths.py -v --tb=short 2>&1 | tail -20
python3 -m pytest tests/unit/content/ -v --tb=short -q 2>&1 | tail -20
```
