---
status: historical
layer: content
authority: P1
audience: agent
ticket_id: TCK-20260624-FIX-SPAWN-SCHEMA
phase: done
date: 2026-06-24
tags: [content, schema, spawn-table, pydantic, class-table]
---

# TCK-20260624-FIX-SPAWN-SCHEMA

## Title
Add ClassTableDefinition schema for spawn_tables.yaml class_id_by_role record type

## Status
DONE

## Tier
standard

## Type
bug

## Priority
P1

## Request Summary
`spawn_tables.yaml` contains two logically different record types:
1. `forest_spawn_pool` — uses `spawn_weights: Dict[str, float]` → matches existing `SpawnTableDefinition` schema ✓
2. `default_class_table` — uses `class_id_by_role: Dict[str, List[str]]` → added by `TCK-20260619-P0-ENTITY-INIT` but `SpawnTableDefinition` was never updated

`SpawnTableDefinition` has `extra="forbid"` so `class_id_by_role` triggers `Extra inputs are not permitted`, and `spawn_weights` is `Required` so the second record type also fails that check. The test `test_strict_load_on_real_content_dir` catches both violations.

The data is intentional and newer than the schema — the schema must be extended, not the data.

## Scope
- Define a new `ClassTableDefinition` Pydantic model with `class_id_by_role: Dict[str, List[str]]` and appropriate `extra="forbid"`
- Register it via `schema_version_map` on the `spawn_tables` `ContentFamilySpec` for per-record dispatch
- Add `NON_CATALOG_FILES` frozenset to cover 3 pre-existing `DESIGN_ONLY` files unmasked by fixing the schema error
- Update `docs/mechanics/content_usage_matrix.md` with a new row for `spawn/class_tables`

## Out of Scope
- Changing `data/content/spawn_tables.yaml`
- Changing `SpawnTableDefinition` itself (it is correct for `forest_spawn_pool`)
- Changing `test_strict_load_on_real_content_dir` (the test is correct)

## Acceptance Criteria
- `tests/unit/content/test_content_paths.py::test_strict_load_on_real_content_dir` passes ✓
- `default_class_table` validates correctly against `ClassTableDefinition` ✓
- `forest_spawn_pool` still validates correctly against `SpawnTableDefinition` ✓
- No regression in other content schema tests ✓ (218/218 pass)

## Related Tickets
- `TCK-20260619-P0-ENTITY-INIT` — added `default_class_table` to `spawn_tables.yaml`

## Related Docs
- `docs/mechanics/content_usage_matrix.md`

## Related Stored Artifacts
`stored_artifacts/TCK-20260624-FIX-SPAWN-SCHEMA`

## Related Code Areas
- `src/content/schema.py` — new `ClassTableDefinition`
- `src/content/repository.py` — `ContentFamilySpec.schema_version_map`, `NON_CATALOG_FILES`, `class_tables` index
- `data/content/spawn_tables.yaml` — unchanged
- `tests/unit/content/test_content_paths.py` — unchanged

## Assumptions / Open Questions
- `class_id_by_role` values are `List[str]` (not `str` as the ticket stated) — confirmed from YAML data.
- `schema_version_map` dispatch was chosen over a union schema: cleaner, explicit, extensible.
- `NON_CATALOG_FILES` is the right abstraction for `DESIGN_ONLY` files that are not directory-scoped: `compatibility/migration_map.yaml`, `packs/swamp_border_pack.yaml`, `packs/frontier_extended_pack.yaml`. These were pre-existing unregistered files masked by the schema error; fixing the schema error exposed them.

## Implementation Notes
Added `schema_version_map: Optional[Dict[str, Type[BaseModel]]] = None` to `ContentFamilySpec`. The loader checks this field; if present and the record has `schema_version`, picks the matching schema from the map (falling back to `spec.schema`). After validation, records are routed to `spawn_tables` (primary, `SpawnTableDefinition`) or `class_tables` (secondary, `ClassTableDefinition`) by `isinstance` check.

Also added `NON_CATALOG_FILES` frozenset (analogous to `NON_CATALOG_DIRS`) to exclude known `DESIGN_ONLY` files from the ignored-files strict check without modifying `NON_CATALOG_DIRS` or `ContentPathConfig`.

## Test Summary
- `tests/unit/content/test_content_paths.py` — 11/11 passed
- `tests/unit/content/` — 218/218 passed

## Files Changed
- `src/content/schema.py` — added `ClassTableDefinition`
- `src/content/repository.py` — `ContentFamilySpec.schema_version_map`, loader dispatch, `NON_CATALOG_FILES`, `class_tables` index, `get_class_table()`, updated `get_all_ids_by_type` and `get_deprecated_ids`
- `docs/mechanics/content_usage_matrix.md` — new row for `spawn/class_tables`

## Completion Summary
Added `ClassTableDefinition(CatalogBaseDefinition)` with `class_id_by_role: Dict[str, List[str]]` and wired it into the `spawn_tables` content family via a new `schema_version_map` dispatch mechanism on `ContentFamilySpec`. Also added `NON_CATALOG_FILES` to suppress 3 pre-existing `DESIGN_ONLY` YAML files exposed by the fix. All 218 content unit tests pass.
